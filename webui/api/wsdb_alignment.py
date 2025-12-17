#!/usr/bin/env python3
"""FastAPI router for WSDB soap alignment functionality."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wsdb-alignment", tags=["wsdb-alignment"])

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


class WSDBSoap(BaseModel):
    """WSDB soap item model."""

    brand: str
    name: str
    slug: str
    scent_notes: list[str] | None = None
    collaborators: list[str] | None = None
    tags: list[str] | None = None
    category: str | None = None


class PipelineSoap(BaseModel):
    """Pipeline soap model."""

    brand: str
    scents: list[dict[str, Any]]


class FuzzyMatchRequest(BaseModel):
    """Request model for fuzzy matching."""

    source_type: str  # "pipeline" or "wsdb"
    brand: str
    scent: str
    threshold: float = 0.7
    limit: int = 5
    mode: str = "brand_scent"  # "brands" or "brand_scent"


class FuzzyMatchResult(BaseModel):
    """Result model for fuzzy match."""

    brand: str
    name: str
    confidence: float
    brand_score: float
    scent_score: float
    source: str
    details: dict[str, Any] | None = None


class WSDBRefreshResponse(BaseModel):
    """Response model for WSDB refresh operation."""

    success: bool
    soap_count: int
    updated_at: str
    error: str | None = None


class NonMatchRequest(BaseModel):
    """Request model for non-match operations."""

    match_type: str  # "brand" or "scent"
    pipeline_brand: str
    wsdb_brand: str
    pipeline_scent: str | None = None  # Only for scent-level
    wsdb_scent: str | None = None  # Only for scent-level


@router.get("/load-wsdb")
async def load_wsdb_soaps() -> dict[str, Any]:
    """
    Load WSDB soaps from software.json, filtering for type="Soap" only.

    Returns:
        Dict containing list of WSDB soaps and metadata
    """
    try:
        logger.info("📂 Loading WSDB soaps from software.json")
        software_file = PROJECT_ROOT / "data" / "wsdb" / "software.json"

        if not software_file.exists():
            logger.error(f"❌ software.json not found at {software_file}")
            raise HTTPException(status_code=404, detail="software.json file not found")

        with software_file.open("r", encoding="utf-8") as f:
            all_software = json.load(f)

        # Filter for soaps only
        soaps = [item for item in all_software if item.get("type") == "Soap"]

        logger.info(f"✅ Loaded {len(soaps)} soaps from WSDB (filtered from {len(all_software)} total items)")

        return {
            "soaps": soaps,
            "total_count": len(soaps),
            "total_software_items": len(all_software),
            "loaded_at": datetime.now().isoformat(),
        }

    except HTTPException:
        raise  # Re-raise HTTPExceptions without wrapping
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse software.json: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse software.json: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to load WSDB soaps: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load WSDB soaps: {str(e)}")


@router.get("/load-pipeline")
async def load_pipeline_soaps() -> dict[str, Any]:
    """
    Load pipeline soaps from soaps.yaml.

    Returns:
        Dict containing list of pipeline soaps with brands and scents
    """
    try:
        logger.info("📂 Loading pipeline soaps from soaps.yaml")
        soaps_file = PROJECT_ROOT / "data" / "soaps.yaml"

        if not soaps_file.exists():
            logger.error(f"❌ soaps.yaml not found at {soaps_file}")
            raise HTTPException(status_code=404, detail="soaps.yaml file not found")

        with soaps_file.open("r", encoding="utf-8") as f:
            soaps_data = yaml.safe_load(f)

        # Transform to list format
        pipeline_soaps = []
        total_scents = 0

        for brand, brand_data in soaps_data.items():
            scents = []
            aliases = []
            
            if isinstance(brand_data, dict):
                # Extract aliases if present
                if "aliases" in brand_data:
                    aliases = brand_data["aliases"] if isinstance(brand_data["aliases"], list) else []
                
                # Extract scents
                if "scents" in brand_data:
                    for scent_name, scent_data in brand_data["scents"].items():
                        scent_info = {
                            "name": scent_name,
                            "patterns": scent_data.get("patterns", []) if isinstance(scent_data, dict) else [],
                        }
                        scents.append(scent_info)
                        total_scents += 1

            pipeline_soaps.append({"brand": brand, "aliases": aliases, "scents": scents})

        logger.info(f"✅ Loaded {len(pipeline_soaps)} brands with {total_scents} scents from pipeline")

        return {
            "soaps": pipeline_soaps,
            "total_brands": len(pipeline_soaps),
            "total_scents": total_scents,
            "loaded_at": datetime.now().isoformat(),
        }

    except yaml.YAMLError as e:
        logger.error(f"❌ Failed to parse soaps.yaml: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to parse soaps.yaml: {str(e)}")
    except Exception as e:
        logger.error(f"❌ Failed to load pipeline soaps: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load pipeline soaps: {str(e)}")


@router.post("/fuzzy-match")
async def fuzzy_match(request: FuzzyMatchRequest) -> dict[str, Any]:
    """
    Generate fuzzy match suggestions for a given brand/scent combination.

    Args:
        request: FuzzyMatchRequest with source_type, brand, scent, threshold, limit

    Returns:
        Dict containing match suggestions with confidence scores
    """
    try:
        logger.info(
            f"🔍 Fuzzy matching: {request.brand} - {request.scent} "
            f"(source: {request.source_type}, threshold: {request.threshold})"
        )

        # Load both datasets
        wsdb_data = await load_wsdb_soaps()
        pipeline_data = await load_pipeline_soaps()

        # Normalize query
        query_brand = request.brand.lower().strip()
        query_scent = request.scent.lower().strip()

        matches = []

        if request.source_type == "pipeline":
            # Match against WSDB soaps
            for soap in wsdb_data["soaps"]:
                wsdb_brand = soap.get("brand", "").lower().strip()
                wsdb_name = soap.get("name", "").lower().strip()

                # Calculate similarity scores
                brand_score = fuzz.ratio(query_brand, wsdb_brand)
                scent_score = fuzz.token_sort_ratio(query_scent, wsdb_name)

                # Combined score based on mode
                if request.mode == "brands":
                    # Brands only: 100% brand matching
                    confidence = brand_score
                else:
                    # Brand + Scent: 60% brand + 40% scent
                    confidence = (brand_score * 0.6) + (scent_score * 0.4)

                if confidence >= request.threshold * 100:
                    matches.append(
                        {
                            "brand": soap.get("brand"),
                            "name": soap.get("name"),
                            "confidence": round(confidence, 2),
                            "brand_score": round(brand_score, 2),
                            "scent_score": round(scent_score, 2),
                            "source": "wsdb",
                            "details": {
                                "slug": soap.get("slug"),
                                "scent_notes": soap.get("scent_notes", []),
                                "collaborators": soap.get("collaborators", []),
                                "tags": soap.get("tags", []),
                                "category": soap.get("category"),
                            },
                        }
                    )

        elif request.source_type == "wsdb":
            # Match against pipeline soaps
            for brand_entry in pipeline_data["soaps"]:
                pipeline_brand = brand_entry["brand"].lower().strip()

                for scent in brand_entry["scents"]:
                    pipeline_scent = scent["name"].lower().strip()

                    # Calculate similarity scores
                    brand_score = fuzz.ratio(query_brand, pipeline_brand)
                    scent_score = fuzz.token_sort_ratio(query_scent, pipeline_scent)

                    # Combined score based on mode
                    if request.mode == "brands":
                        # Brands only: 100% brand matching
                        confidence = brand_score
                    else:
                        # Brand + Scent: 60% brand + 40% scent
                        confidence = (brand_score * 0.6) + (scent_score * 0.4)

                    if confidence >= request.threshold * 100:
                        matches.append(
                            {
                                "brand": brand_entry["brand"],
                                "name": scent["name"],
                                "confidence": round(confidence, 2),
                                "brand_score": round(brand_score, 2),
                                "scent_score": round(scent_score, 2),
                                "source": "pipeline",
                                "details": {"patterns": scent.get("patterns", [])},
                            }
                        )

        # Sort by confidence and limit results
        matches.sort(key=lambda x: x["confidence"], reverse=True)
        matches = matches[: request.limit]

        logger.info(f"✅ Found {len(matches)} matches above threshold {request.threshold}")

        return {
            "matches": matches,
            "query": {"brand": request.brand, "scent": request.scent, "source_type": request.source_type},
            "threshold": request.threshold,
            "total_matches": len(matches),
            "matched_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Fuzzy matching failed: {e}")
        raise HTTPException(status_code=500, detail=f"Fuzzy matching failed: {str(e)}")


def is_non_match(
    source: dict, match: dict, brand_non_matches: list, scent_non_matches: list, mode: str
) -> bool:
    """
    Check if this match pair is in the non-matches list.

    Args:
        source: Source item with source_brand and source_scent
        match: Match item with brand and name
        brand_non_matches: List of brand-level non-matches
        scent_non_matches: List of scent-level non-matches
        mode: "brands" or "brand_scent"

    Returns:
        True if this match should be filtered out
    """
    if mode == "brands":
        # Check brand-level non-matches (bidirectional)
        return any(
            (source["source_brand"].lower() == nm.get("pipeline_brand", "").lower()
             and match["brand"].lower() == nm.get("wsdb_brand", "").lower())
            or (source["source_brand"].lower() == nm.get("wsdb_brand", "").lower()
                and match["brand"].lower() == nm.get("pipeline_brand", "").lower())
            for nm in brand_non_matches
        )
    else:  # brand_scent mode
        # Check scent-level non-matches (bidirectional)
        return any(
            (source["source_brand"].lower() == nm.get("pipeline_brand", "").lower()
             and source.get("source_scent", "").lower() == nm.get("pipeline_scent", "").lower()
             and match["brand"].lower() == nm.get("wsdb_brand", "").lower()
             and match.get("name", "").lower() == nm.get("wsdb_scent", "").lower())
            or (source["source_brand"].lower() == nm.get("wsdb_brand", "").lower()
                and source.get("source_scent", "").lower() == nm.get("wsdb_scent", "").lower()
                and match["brand"].lower() == nm.get("pipeline_brand", "").lower()
                and match.get("name", "").lower() == nm.get("pipeline_scent", "").lower())
            for nm in scent_non_matches
        )


@router.post("/batch-analyze")
async def batch_analyze(
    threshold: float = 0.7, limit: int = 100, mode: str = "brand_scent"
) -> dict[str, Any]:
    """
    Perform batch analysis of all pipeline and WSDB soaps.
    Much faster than individual fuzzy-match calls.

    Args:
        threshold: Minimum confidence threshold (0.0-1.0)
        limit: Maximum results per view
        mode: "brands" or "brand_scent"

    Returns:
        Dict with pipeline_results and wsdb_results
    """
    try:
        logger.info(f"🔄 Starting batch analysis (mode: {mode}, threshold: {threshold})")

        # Load both datasets
        wsdb_data = await load_wsdb_soaps()
        pipeline_data = await load_pipeline_soaps()

        wsdb_soaps = wsdb_data["soaps"]
        pipeline_soaps = pipeline_data["soaps"]

        # Load non-matches for filtering
        non_matches_data = await load_non_matches()
        brand_non_matches = non_matches_data.get("brand_non_matches", [])
        scent_non_matches = non_matches_data.get("scent_non_matches", [])

        pipeline_results = []
        wsdb_results = []

        # Pipeline → WSDB matches
        logger.info(f"📊 Analyzing Pipeline → WSDB ({len(pipeline_soaps)} brands)")
        
        # In brands mode, analyze all brands (result limit is applied by frontend filtering)
        # In brand_scent mode, stop when we hit the result limit
        for brand_entry in pipeline_soaps:
            pipeline_brand = brand_entry["brand"]

            # In brands mode, analyze once per brand; in brand_scent mode, once per scent
            if mode == "brands":
                # Brands only: match brand against all WSDB brands
                query_brand = pipeline_brand.lower().strip()
                
                # Get all names to try: canonical + aliases
                names_to_try = [query_brand]
                if brand_entry.get("aliases"):
                    names_to_try.extend([alias.lower().strip() for alias in brand_entry["aliases"]])
                
                matches = []

                for wsdb_soap in wsdb_soaps:
                    wsdb_brand = wsdb_soap.get("brand", "").lower().strip()
                    
                    # Try matching with each name (canonical + aliases)
                    best_score = 0
                    matched_via = "canonical"
                    
                    for idx, name in enumerate(names_to_try):
                        score = fuzz.ratio(name, wsdb_brand)
                        if score > best_score:
                            best_score = score
                            matched_via = "canonical" if idx == 0 else "alias"
                    
                    brand_score = best_score
                    confidence = brand_score

                    if confidence >= threshold * 100:
                        matches.append(
                            {
                                "brand": wsdb_soap.get("brand"),
                                "name": wsdb_soap.get("name"),
                                "confidence": round(confidence, 2),
                                "brand_score": round(brand_score, 2),
                                "scent_score": 0.0,
                                "source": "wsdb",
                                "matched_via": matched_via,
                                "details": {
                                    "slug": wsdb_soap.get("slug"),
                                    "scent_notes": wsdb_soap.get("scent_notes", []),
                                    "collaborators": wsdb_soap.get("collaborators", []),
                                    "tags": wsdb_soap.get("tags", []),
                                    "category": wsdb_soap.get("category"),
                                },
                            }
                        )

                # Filter non-matches before sorting
                source_item = {"source_brand": pipeline_brand, "source_scent": ""}
                matches = [
                    m for m in matches if not is_non_match(source_item, m, brand_non_matches, scent_non_matches, mode)
                ]

                # Sort and limit
                matches.sort(key=lambda x: x["confidence"], reverse=True)
                matches = matches[:5]

                pipeline_results.append(
                    {
                        "source_brand": pipeline_brand,
                        "source_scent": "",  # Empty for brands mode
                        "matches": matches,
                        "expanded": False,
                    }
                )
            else:
                # Brand + Scent mode: match each scent individually
                for scent in brand_entry["scents"]:
                    # Check if we've reached the limit
                    if len(pipeline_results) >= limit:
                        break
                    
                    query_brand = pipeline_brand.lower().strip()
                    query_scent = scent["name"].lower().strip()
                    
                    # Get all names to try: canonical + aliases
                    names_to_try = [query_brand]
                    if brand_entry.get("aliases"):
                        names_to_try.extend([alias.lower().strip() for alias in brand_entry["aliases"]])
                    
                    matches = []

                    for wsdb_soap in wsdb_soaps:
                        wsdb_brand = wsdb_soap.get("brand", "").lower().strip()
                        wsdb_name = wsdb_soap.get("name", "").lower().strip()

                        # Try matching with each brand name (canonical + aliases)
                        best_brand_score = 0
                        matched_via = "canonical"
                        
                        for idx, name in enumerate(names_to_try):
                            score = fuzz.ratio(name, wsdb_brand)
                            if score > best_brand_score:
                                best_brand_score = score
                                matched_via = "canonical" if idx == 0 else "alias"
                        
                        brand_score = best_brand_score
                        scent_score = fuzz.token_sort_ratio(query_scent, wsdb_name)
                        confidence = (brand_score * 0.6) + (scent_score * 0.4)

                        if confidence >= threshold * 100:
                            matches.append(
                                {
                                    "brand": wsdb_soap.get("brand"),
                                    "name": wsdb_soap.get("name"),
                                    "confidence": round(confidence, 2),
                                    "brand_score": round(brand_score, 2),
                                    "scent_score": round(scent_score, 2),
                                    "source": "wsdb",
                                    "matched_via": matched_via,
                                    "details": {
                                        "slug": wsdb_soap.get("slug"),
                                        "scent_notes": wsdb_soap.get("scent_notes", []),
                                        "collaborators": wsdb_soap.get("collaborators", []),
                                        "tags": wsdb_soap.get("tags", []),
                                        "category": wsdb_soap.get("category"),
                                    },
                                }
                            )

                    # Filter non-matches before sorting
                    source_item = {"source_brand": pipeline_brand, "source_scent": scent["name"]}
                    matches = [
                        m
                        for m in matches
                        if not is_non_match(source_item, m, brand_non_matches, scent_non_matches, mode)
                    ]

                    # Sort and limit
                    matches.sort(key=lambda x: x["confidence"], reverse=True)
                    matches = matches[:5]

                    pipeline_results.append(
                        {
                            "source_brand": pipeline_brand,
                            "source_scent": scent["name"],
                            "matches": matches,
                            "expanded": False,
                        }
                    )
            
            # Check if we've reached the limit (for Brand + Scent mode)
            if mode != "brands" and len(pipeline_results) >= limit:
                break

        # WSDB → Pipeline matches
        logger.info(f"📊 Analyzing WSDB → Pipeline ({len(wsdb_soaps)} soaps)")
        
        if mode == "brands":
            # In brands mode, group WSDB soaps by brand first
            wsdb_brands_map = {}
            for wsdb_soap in wsdb_soaps:
                brand = wsdb_soap.get("brand", "")
                if brand not in wsdb_brands_map:
                    wsdb_brands_map[brand] = []
                wsdb_brands_map[brand].append(wsdb_soap)
            
            # Sort brands alphabetically
            sorted_brands = sorted(wsdb_brands_map.items(), key=lambda x: x[0].lower())
            
            # In brands mode, analyze all brands (typically not too many)
            # Analyze once per brand
            for wsdb_brand, soaps in sorted_brands:
                query_brand = wsdb_brand.lower().strip()
                matches = []

                for brand_entry in pipeline_soaps:
                    pipeline_brand = brand_entry["brand"].lower().strip()
                    
                    # Get all names to try: canonical + aliases
                    names_to_try = [pipeline_brand]
                    if brand_entry.get("aliases"):
                        names_to_try.extend([alias.lower().strip() for alias in brand_entry["aliases"]])
                    
                    # Try matching with each name
                    best_score = 0
                    matched_via = "canonical"
                    
                    for idx, name in enumerate(names_to_try):
                        score = fuzz.ratio(query_brand, name)
                        if score > best_score:
                            best_score = score
                            matched_via = "canonical" if idx == 0 else "alias"
                    
                    brand_score = best_score
                    confidence = brand_score

                    if confidence >= threshold * 100:
                        matches.append(
                            {
                                "brand": brand_entry["brand"],
                                "name": "",
                                "confidence": round(confidence, 2),
                                "brand_score": round(brand_score, 2),
                                "scent_score": 0.0,
                                "source": "pipeline",
                                "matched_via": matched_via,
                                "details": {"patterns": []},
                            }
                        )

                # Filter non-matches before sorting
                source_item = {"source_brand": wsdb_brand, "source_scent": ""}
                matches = [
                    m for m in matches if not is_non_match(source_item, m, brand_non_matches, scent_non_matches, mode)
                ]

                # Sort and limit
                matches.sort(key=lambda x: x["confidence"], reverse=True)
                matches = matches[:5]

                wsdb_results.append(
                    {
                        "source_brand": wsdb_brand,
                        "source_scent": "",  # Empty in brands mode
                        "matches": matches,
                        "expanded": False,
                    }
                )
        else:
            # Brand + Scent mode: analyze each scent individually
            # Sort soaps alphabetically by brand, then scent name
            sorted_wsdb_soaps = sorted(
                wsdb_soaps, 
                key=lambda x: (x.get("brand", "").lower(), x.get("name", "").lower())
            )
            
            for wsdb_soap in sorted_wsdb_soaps[:limit]:
                query_brand = wsdb_soap.get("brand", "").lower().strip()
                query_scent = wsdb_soap.get("name", "").lower().strip()
                matches = []

                for brand_entry in pipeline_soaps:
                    pipeline_brand = brand_entry["brand"].lower().strip()
                    
                    # Get all names to try: canonical + aliases
                    names_to_try = [pipeline_brand]
                    if brand_entry.get("aliases"):
                        names_to_try.extend([alias.lower().strip() for alias in brand_entry["aliases"]])

                    for scent in brand_entry["scents"]:
                        pipeline_scent = scent["name"].lower().strip()

                        # Try matching with each brand name (canonical + aliases)
                        best_brand_score = 0
                        matched_via = "canonical"
                        
                        for idx, name in enumerate(names_to_try):
                            score = fuzz.ratio(query_brand, name)
                            if score > best_brand_score:
                                best_brand_score = score
                                matched_via = "canonical" if idx == 0 else "alias"
                        
                        brand_score = best_brand_score
                        scent_score = fuzz.token_sort_ratio(query_scent, pipeline_scent)
                        confidence = (brand_score * 0.6) + (scent_score * 0.4)

                        if confidence >= threshold * 100:
                            matches.append(
                                {
                                    "brand": brand_entry["brand"],
                                    "name": scent["name"],
                                    "confidence": round(confidence, 2),
                                    "brand_score": round(brand_score, 2),
                                    "scent_score": round(scent_score, 2),
                                    "source": "pipeline",
                                    "matched_via": matched_via,
                                    "details": {"patterns": scent.get("patterns", [])},
                                }
                            )

                # Filter non-matches before sorting
                source_item = {"source_brand": wsdb_soap.get("brand"), "source_scent": wsdb_soap.get("name")}
                matches = [
                    m for m in matches if not is_non_match(source_item, m, brand_non_matches, scent_non_matches, mode)
                ]

                # Sort and limit
                matches.sort(key=lambda x: x["confidence"], reverse=True)
                matches = matches[:5]

                wsdb_results.append(
                    {
                        "source_brand": wsdb_soap.get("brand"),
                        "source_scent": wsdb_soap.get("name"),
                        "matches": matches,
                        "expanded": False,
                    }
                )

        logger.info(
            f"✅ Batch analysis complete: {len(pipeline_results)} pipeline results, {len(wsdb_results)} WSDB results"
        )

        return {
            "pipeline_results": pipeline_results,
            "wsdb_results": wsdb_results,
            "mode": mode,
            "threshold": threshold,
            "analyzed_at": datetime.now().isoformat(),
        }

    except Exception as e:
        logger.error(f"❌ Batch analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.post("/refresh-wsdb-data")
async def refresh_wsdb_data() -> WSDBRefreshResponse:
    """
    Refresh WSDB data by fetching latest software.json from wetshavingdatabase.com API.

    Returns:
        WSDBRefreshResponse with success status and metadata
    """
    try:
        logger.info("🔄 Refreshing WSDB data from API")
        url = "https://wetshavingdatabase.com/api/software.json"

        # Fetch data with timeout
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            data = response.json()

        # Validate response is a list
        if not isinstance(data, list):
            raise ValueError("Invalid response format: expected list of software items")

        # Count soaps
        soap_count = sum(1 for item in data if item.get("type") == "Soap")

        # Write to file atomically
        software_file = PROJECT_ROOT / "data" / "wsdb" / "software.json"
        temp_file = software_file.with_suffix(".tmp")

        with temp_file.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # Atomic replace
        temp_file.replace(software_file)

        logger.info(f"✅ WSDB data refreshed: {len(data)} total items, {soap_count} soaps")

        return WSDBRefreshResponse(
            success=True, soap_count=soap_count, updated_at=datetime.now().isoformat(), error=None
        )

    except httpx.HTTPError as e:
        error_msg = f"HTTP error fetching WSDB data: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return WSDBRefreshResponse(success=False, soap_count=0, updated_at=datetime.now().isoformat(), error=error_msg)
    except Exception as e:
        error_msg = f"Failed to refresh WSDB data: {str(e)}"
        logger.error(f"❌ {error_msg}")
        return WSDBRefreshResponse(success=False, soap_count=0, updated_at=datetime.now().isoformat(), error=error_msg)


@router.get("/non-matches")
async def load_non_matches() -> dict[str, Any]:
    """
    Load known non-matches from YAML file.

    Returns:
        Dict containing brand_non_matches and scent_non_matches lists
    """
    try:
        logger.info("📂 Loading known non-matches")
        non_matches_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches.yaml"

        if not non_matches_file.exists():
            logger.warning("⚠️ non_matches.yaml not found, returning empty lists")
            return {"brand_non_matches": [], "scent_non_matches": []}

        with non_matches_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        brand_non_matches = data.get("brand_non_matches", [])
        scent_non_matches = data.get("scent_non_matches", [])

        logger.info(
            f"✅ Loaded {len(brand_non_matches)} brand non-matches, {len(scent_non_matches)} scent non-matches"
        )

        return {"brand_non_matches": brand_non_matches, "scent_non_matches": scent_non_matches}

    except Exception as e:
        logger.error(f"❌ Failed to load non-matches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load non-matches: {str(e)}")


@router.post("/non-matches")
async def add_non_match(request: NonMatchRequest) -> dict[str, Any]:
    """
    Add a new non-match entry (auto-saves to YAML).

    Args:
        request: Non-match request with match type and brand/scent info

    Returns:
        Dict with success status and message
    """
    try:
        logger.info(f"➕ Adding non-match: {request.match_type} - {request.pipeline_brand} != {request.wsdb_brand}")

        non_matches_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches.yaml"

        # Load existing non-matches
        if non_matches_file.exists():
            with non_matches_file.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
        else:
            data = {}

        brand_non_matches = data.get("brand_non_matches", [])
        scent_non_matches = data.get("scent_non_matches", [])

        # Create new entry
        new_entry = {
            "pipeline_brand": request.pipeline_brand,
            "wsdb_brand": request.wsdb_brand,
            "added_at": datetime.now().isoformat(),
        }

        if request.match_type == "scent":
            new_entry["pipeline_scent"] = request.pipeline_scent
            new_entry["wsdb_scent"] = request.wsdb_scent

            # Check for duplicates in scent non-matches
            is_duplicate = any(
                nm.get("pipeline_brand", "").lower() == request.pipeline_brand.lower()
                and nm.get("pipeline_scent", "").lower() == (request.pipeline_scent or "").lower()
                and nm.get("wsdb_brand", "").lower() == request.wsdb_brand.lower()
                and nm.get("wsdb_scent", "").lower() == (request.wsdb_scent or "").lower()
                for nm in scent_non_matches
            )

            if is_duplicate:
                logger.info("ℹ️ Non-match already exists, skipping")
                return {"success": True, "message": "Non-match already exists"}

            scent_non_matches.append(new_entry)
        else:  # brand
            # Check for duplicates in brand non-matches
            is_duplicate = any(
                nm.get("pipeline_brand", "").lower() == request.pipeline_brand.lower()
                and nm.get("wsdb_brand", "").lower() == request.wsdb_brand.lower()
                for nm in brand_non_matches
            )

            if is_duplicate:
                logger.info("ℹ️ Non-match already exists, skipping")
                return {"success": True, "message": "Non-match already exists"}

            brand_non_matches.append(new_entry)

        # Save atomically
        data["brand_non_matches"] = brand_non_matches
        data["scent_non_matches"] = scent_non_matches

        temp_file = non_matches_file.with_suffix(".tmp")
        with temp_file.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        temp_file.replace(non_matches_file)

        logger.info("✅ Non-match added and saved successfully")
        return {"success": True, "message": "Non-match added successfully"}

    except Exception as e:
        logger.error(f"❌ Failed to add non-match: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add non-match: {str(e)}")


@router.delete("/non-matches")
async def remove_non_match(request: NonMatchRequest) -> dict[str, Any]:
    """
    Remove a non-match entry (in case of mistakes).

    Args:
        request: Non-match request identifying the entry to remove

    Returns:
        Dict with success status and message
    """
    try:
        logger.info(
            f"➖ Removing non-match: {request.match_type} - {request.pipeline_brand} != {request.wsdb_brand}"
        )

        non_matches_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches.yaml"

        if not non_matches_file.exists():
            logger.warning("⚠️ non_matches.yaml not found")
            return {"success": True, "message": "Non-matches file not found, nothing to remove"}

        # Load existing non-matches
        with non_matches_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        brand_non_matches = data.get("brand_non_matches", [])
        scent_non_matches = data.get("scent_non_matches", [])

        # Remove matching entry
        if request.match_type == "scent":
            original_count = len(scent_non_matches)
            scent_non_matches = [
                nm
                for nm in scent_non_matches
                if not (
                    nm.get("pipeline_brand", "").lower() == request.pipeline_brand.lower()
                    and nm.get("pipeline_scent", "").lower() == (request.pipeline_scent or "").lower()
                    and nm.get("wsdb_brand", "").lower() == request.wsdb_brand.lower()
                    and nm.get("wsdb_scent", "").lower() == (request.wsdb_scent or "").lower()
                )
            ]
            removed_count = original_count - len(scent_non_matches)
        else:  # brand
            original_count = len(brand_non_matches)
            brand_non_matches = [
                nm
                for nm in brand_non_matches
                if not (
                    nm.get("pipeline_brand", "").lower() == request.pipeline_brand.lower()
                    and nm.get("wsdb_brand", "").lower() == request.wsdb_brand.lower()
                )
            ]
            removed_count = original_count - len(brand_non_matches)

        if removed_count == 0:
            logger.info("ℹ️ No matching non-match found to remove")
            return {"success": True, "message": "No matching non-match found"}

        # Save atomically
        data["brand_non_matches"] = brand_non_matches
        data["scent_non_matches"] = scent_non_matches

        temp_file = non_matches_file.with_suffix(".tmp")
        with temp_file.open("w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        temp_file.replace(non_matches_file)

        logger.info(f"✅ Non-match removed successfully ({removed_count} entries)")
        return {"success": True, "message": f"Non-match removed successfully ({removed_count} entries)"}

    except Exception as e:
        logger.error(f"❌ Failed to remove non-match: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove non-match: {str(e)}")


class AddAliasRequest(BaseModel):
    """Request model for adding an alias to a pipeline brand."""

    pipeline_brand: str
    alias: str


@router.post("/add-alias")
async def add_alias(request: AddAliasRequest) -> dict[str, Any]:
    """
    Add an alias to a pipeline brand in soaps.yaml.

    Args:
        request: AddAliasRequest with pipeline_brand and alias

    Returns:
        Dict with success status and message
    """
    try:
        logger.info(f"➕ Adding alias '{request.alias}' to brand '{request.pipeline_brand}'")

        soaps_file = PROJECT_ROOT / "data" / "soaps.yaml"

        if not soaps_file.exists():
            logger.error(f"❌ soaps.yaml not found at {soaps_file}")
            raise HTTPException(status_code=404, detail="soaps.yaml file not found")

        # Load existing soaps data
        with soaps_file.open("r", encoding="utf-8") as f:
            soaps_data = yaml.safe_load(f) or {}

        # Check if brand exists
        if request.pipeline_brand not in soaps_data:
            logger.error(f"❌ Brand '{request.pipeline_brand}' not found in soaps.yaml")
            raise HTTPException(status_code=404, detail=f"Brand '{request.pipeline_brand}' not found in pipeline")

        brand_data = soaps_data[request.pipeline_brand]

        # Get existing aliases or create new list
        aliases = brand_data.get("aliases", [])
        if not isinstance(aliases, list):
            aliases = []

        # Check if alias already exists (case-insensitive)
        alias_lower = request.alias.lower()
        if any(a.lower() == alias_lower for a in aliases):
            logger.info(f"ℹ️ Alias '{request.alias}' already exists for '{request.pipeline_brand}'")
            return {"success": True, "message": f"Alias '{request.alias}' already exists"}

        # Add the new alias
        aliases.append(request.alias)
        brand_data["aliases"] = aliases

        # Save atomically
        temp_file = soaps_file.with_suffix(".tmp")
        with temp_file.open("w", encoding="utf-8") as f:
            yaml.dump(soaps_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        temp_file.replace(soaps_file)

        logger.info(f"✅ Alias '{request.alias}' added to '{request.pipeline_brand}' successfully")
        return {
            "success": True,
            "message": f"Added alias '{request.alias}' to '{request.pipeline_brand}'",
            "aliases": aliases,
        }

    except HTTPException:
        raise  # Re-raise HTTPExceptions without wrapping
    except Exception as e:
        logger.error(f"❌ Failed to add alias: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add alias: {str(e)}")

