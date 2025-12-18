#!/usr/bin/env python3
"""FastAPI router for WSDB soap alignment functionality."""

import json
import logging
import traceback
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import yaml
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
from rapidfuzz import fuzz

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/wsdb-alignment", tags=["wsdb-alignment"])

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent.parent


def normalize_string(text: str) -> str:
    """
    Normalize a string to Unicode NFC (Normalization Form Canonical Composed).
    
    This ensures that visually identical characters are treated the same regardless
    of their Unicode encoding (e.g., composed "é" vs decomposed "e" + combining accent).
    
    Args:
        text: The string to normalize
        
    Returns:
        The normalized string in NFC form
    """
    if not text:
        return text
    return unicodedata.normalize("NFC", text)


def normalize_accents(text: str) -> str:
    """Remove accents from characters (e.g., 'Café' → 'Cafe').
    
    Uses Unicode decomposition to separate base characters from combining marks.
    
    Args:
        text: The string to normalize
        
    Returns:
        String with accents removed
    """
    if not text:
        return text
    # Decompose to NFD (base + combining marks), then remove combining marks
    nfd = unicodedata.normalize("NFD", text)
    return ''.join(c for c in nfd if unicodedata.category(c) != 'Mn')


def normalize_and_ampersand(text: str) -> str:
    """Normalize 'and' and '&' to a consistent form.
    
    Converts both 'and' and '&' (with or without spaces) to 'and'.
    
    Args:
        text: The string to normalize
        
    Returns:
        String with 'and' and '&' normalized to 'and'
    """
    if not text:
        return text
    import re
    # Replace '&' (with optional spaces) with 'and'
    text = re.sub(r'\s*&\s*', ' and ', text)
    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_for_matching(text: str) -> str:
    """Apply all virtual pattern normalizations for matching.
    
    This is the main normalization function that should be used for all
    WSDB matching operations. It applies:
    - Lowercase and trim
    - Unicode NFC normalization
    - Accent removal
    - "and"/"&" normalization
    
    Args:
        text: The string to normalize
        
    Returns:
        Fully normalized string for matching
    """
    if not text:
        return text
    # Apply all normalizations
    normalized = text.lower().strip()
    normalized = normalize_string(normalized)  # Unicode NFC
    normalized = normalize_accents(normalized)  # Remove accents
    normalized = normalize_and_ampersand(normalized)  # Normalize and/&
    return normalized


def strip_trailing_soap(text: str) -> str | None:
    """Strip trailing 'soap' (case-insensitive) from text.
    
    This is a virtual alias helper that computes a stripped version on-the-fly.
    The result is NOT saved to soaps.yaml.
    
    Args:
        text: The string to process
        
    Returns:
        Stripped version if 'soap' found at end, None otherwise
    """
    if not text:
        return None
    text_lower = text.lower().rstrip()
    if text_lower.endswith('soap'):
        stripped = text[:-4].rstrip()  # Remove 'soap' and trailing whitespace
        return stripped if stripped else None
    return None


def pre_normalize_wsdb_entries(wsdb_soaps: list[dict]) -> list[dict]:
    """Pre-normalize all WSDB entries for fast matching.
    
    Returns list of dicts with normalized fields:
    - brand_norm: normalized brand
    - name_norm: normalized name (if present)
    - brand_virtual_norm: normalized brand with trailing "soap" stripped (if applicable)
    - name_virtual_norm: normalized name with trailing "soap" stripped (if applicable)
    - original: original WSDB soap dict (for slug, etc.)
    
    Args:
        wsdb_soaps: List of WSDB soap dictionaries
        
    Returns:
        List of pre-normalized entry dictionaries
    """
    normalized_entries = []
    for soap in wsdb_soaps:
        brand = soap.get("brand", "")
        name = soap.get("name", "")
        
        brand_norm = normalize_for_matching(brand)
        name_norm = normalize_for_matching(name) if name else ""
        
        # Pre-compute virtual aliases
        brand_virtual = strip_trailing_soap(brand_norm)
        brand_virtual_norm = normalize_for_matching(brand_virtual) if brand_virtual else None
        
        name_virtual = strip_trailing_soap(name_norm)
        name_virtual_norm = normalize_for_matching(name_virtual) if name_virtual else None
        
        normalized_entries.append({
            "brand_norm": brand_norm,
            "name_norm": name_norm,
            "brand_virtual_norm": brand_virtual_norm,
            "name_virtual_norm": name_virtual_norm,
            "original": soap,  # Keep original for slug, etc.
        })
    
    return normalized_entries


def pre_normalize_pipeline_brand(brand_entry: dict) -> dict:
    """Pre-normalize a pipeline brand entry with all aliases and virtual aliases.
    
    Returns dict with:
    - brand_norm: normalized brand
    - aliases_norm: list of normalized aliases
    - brand_virtual_norm: normalized brand with trailing "soap" stripped (if applicable)
    - names_to_try: list of all normalized names to try (canonical + aliases + virtual)
    - original: original brand entry
    
    Args:
        brand_entry: Pipeline brand entry dictionary
        
    Returns:
        Pre-normalized brand entry dictionary
    """
    # Handle case where brand_entry might not have "brand" key (defensive)
    brand = brand_entry.get("brand")
    if not brand:
        # Try to get brand from the entry itself if it's a string key
        # This handles cases where brand_entry might be malformed
        raise ValueError(f"brand_entry missing 'brand' key: {brand_entry}")
    # Handle case where brand_entry might not have "brand" key (defensive)
    brand = brand_entry.get("brand")
    if not brand:
        # This should not happen if brand_lookup is created correctly
        raise ValueError(f"brand_entry missing 'brand' key. Keys: {list(brand_entry.keys())}")
    brand_norm = normalize_for_matching(brand)
    
    aliases_norm = []
    if brand_entry.get("aliases"):
        aliases_norm = [normalize_for_matching(alias) for alias in brand_entry["aliases"]]
    
    brand_virtual = strip_trailing_soap(brand_norm)
    brand_virtual_norm = normalize_for_matching(brand_virtual) if brand_virtual else None
    
    names_to_try = [brand_norm] + aliases_norm
    if brand_virtual_norm and brand_virtual_norm not in names_to_try:
        names_to_try.append(brand_virtual_norm)
    
    return {
        "brand_norm": brand_norm,
        "aliases_norm": aliases_norm,
        "brand_virtual_norm": brand_virtual_norm,
        "names_to_try": names_to_try,
        "original": brand_entry,
    }


def pre_normalize_pipeline_scent(scent: dict, scent_name: str) -> dict:
    """Pre-normalize a pipeline scent with alias and virtual alias.
    
    Returns dict with normalized scent names to try.
    
    Args:
        scent: Scent dictionary (may contain alias)
        scent_name: Scent name string
        
    Returns:
        Dictionary with scent_names_to_try list
    """
    scent_norm = normalize_for_matching(scent_name)
    scent_names_to_try = [scent_norm]
    
    if scent.get("alias"):
        scent_alias_norm = normalize_for_matching(scent["alias"])
        scent_names_to_try.append(scent_alias_norm)
    
    scent_virtual = strip_trailing_soap(scent_norm)
    if scent_virtual:
        scent_virtual_norm = normalize_for_matching(scent_virtual)
        if scent_virtual_norm not in scent_names_to_try:
            scent_names_to_try.append(scent_virtual_norm)
    
    return {
        "scent_names_to_try": scent_names_to_try,
    }


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
                        scent_alias = None
                        if isinstance(scent_data, dict) and "alias" in scent_data:
                            scent_alias = scent_data["alias"] if isinstance(scent_data["alias"], str) else None
                        
                        scent_info = {
                            "name": scent_name,
                            "alias": scent_alias,
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

    except HTTPException:
        # Re-raise HTTP exceptions as-is (e.g., 404 for missing file)
        raise
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

        # Normalize and lowercase query (case-insensitive matching)
        query_brand = normalize_for_matching(request.brand)
        query_scent = normalize_for_matching(request.scent)

        matches = []

        if request.source_type == "pipeline":
            # Match against WSDB soaps
            for soap in wsdb_data["soaps"]:
                wsdb_brand = normalize_for_matching(soap.get("brand", ""))
                wsdb_name = normalize_for_matching(soap.get("name", ""))

                # Calculate similarity scores (case-insensitive due to lowercasing above)
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
                pipeline_brand = normalize_for_matching(brand_entry["brand"])

                for scent in brand_entry["scents"]:
                    pipeline_scent = normalize_for_matching(scent["name"])

                    # Calculate similarity scores (case-insensitive due to lowercasing above)
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
    source: dict, match: dict, brand_non_matches: dict, scent_non_matches: dict, mode: str
) -> bool:
    """
    Check if this match pair is in the non-matches list.

    Args:
        source: Source item with source_brand and source_scent
        match: Match item with brand and name
        brand_non_matches: Dict of pipeline_brand -> [wsdb_brands]
        scent_non_matches: Dict of pipeline_brand -> pipeline_scent -> [wsdb_scents]
        mode: "brands" or "brand_scent"

    Returns:
        True if this match should be filtered out
    """
    if mode == "brands":
        # Check brand-level non-matches
        source_brand = normalize_for_matching(source["source_brand"])
        match_brand = normalize_for_matching(match["brand"])

        # Check if source is pipeline and match is WSDB (forward direction)
        if source["source_brand"] in brand_non_matches:
            if any(normalize_for_matching(nm) == match_brand for nm in brand_non_matches[source["source_brand"]]):
                return True

        # Check if source is WSDB and match is pipeline (reverse direction)
        # Need to check all pipeline brands to see if source_brand is in their non-match list
        for pipeline_brand, wsdb_brands in brand_non_matches.items():
            if any(normalize_for_matching(nm) == source_brand for nm in wsdb_brands):
                if normalize_for_matching(pipeline_brand) == match_brand:
                    return True

        return False

    else:  # brand_scent mode
        # Check scent-level non-matches
        source_brand = normalize_for_matching(source["source_brand"])
        source_scent = normalize_for_matching(source.get("source_scent", ""))
        match_brand = normalize_for_matching(match["brand"])
        match_scent = normalize_for_matching(match.get("name", ""))

        # Check if source is pipeline and match is WSDB (forward direction)
        if source["source_brand"] in scent_non_matches:
            if source["source_scent"] in scent_non_matches[source["source_brand"]]:
                if any(normalize_for_matching(nm) == match_scent for nm in scent_non_matches[source["source_brand"]][source["source_scent"]]):
                    # Also verify the brand matches (same brand, different scent)
                    if source_brand == match_brand:
                        return True

        # Check if source is WSDB and match is pipeline (reverse direction)
        # For scents: if pipeline brand has scent X with non-matches [Y],
        # then checking WSDB scent Y against pipeline scent X should also return True
        if match["brand"] in scent_non_matches:
            if match["name"] in scent_non_matches[match["brand"]]:
                if any(normalize_for_matching(nm) == source_scent for nm in scent_non_matches[match["brand"]][match["name"]]):
                    if match_brand == source_brand:
                        return True

        return False


@router.post("/batch-analyze")
async def batch_analyze(
    threshold: float = 0.7, limit: int = 100, mode: str = "brand_scent", brand_threshold: float = 0.8
) -> dict[str, Any]:
    """
    Perform batch analysis of all pipeline and WSDB soaps.
    Much faster than individual fuzzy-match calls.

    Args:
        threshold: Minimum confidence threshold (0.0-1.0)
        limit: Maximum results per view
        mode: "brands" or "brand_scent"
        brand_threshold: Minimum brand match threshold for brand+scent mode (0.0-1.0, default 0.8)

    Returns:
        Dict with pipeline_results and wsdb_results
    """
    try:
        logger.info(f"🔄 Starting batch analysis (mode: {mode}, threshold: {threshold}, brand_threshold: {brand_threshold})")

        # Load both datasets
        wsdb_data = await load_wsdb_soaps()
        pipeline_data = await load_pipeline_soaps()

        wsdb_soaps = wsdb_data["soaps"]
        pipeline_soaps = pipeline_data["soaps"]

        # Pre-normalize WSDB entries once for performance
        wsdb_normalized = pre_normalize_wsdb_entries(wsdb_soaps)

        # Load non-matches for filtering
        non_matches_data = await load_non_matches()
        brand_non_matches = non_matches_data.get("brand_non_matches", [])
        scent_non_matches = non_matches_data.get("scent_non_matches", [])

        pipeline_results = []
        wsdb_results = []

        # Pipeline → WSDB matches
        logger.info(f"📊 Analyzing Pipeline → WSDB ({len(pipeline_soaps)} brands)")
        # In both modes, analyze all items (result limit is applied by frontend filtering)
        logger.info(f"🔄 Starting Pipeline → WSDB analysis ({len(brand_scent_groups)} brand+scent combinations)...")
        for idx, (key, group_data) in enumerate(brand_scent_groups.items()):
            if (idx + 1) % 100 == 0:
                logger.info(f"📊 Processed {idx + 1}/{len(brand_scent_groups)} brand+scent combinations...")
            pipeline_brand = group_data["brand"]
            pipeline_scent = group_data["scent"]
            
            # Look up brand in pipeline soaps to get aliases
            brand_entry = brand_lookup.get(pipeline_brand, {"brand": pipeline_brand, "aliases": [], "scents": []})
            # Pre-normalize pipeline brand once
            pipeline_brand_norm = pre_normalize_pipeline_brand(brand_entry)
            names_to_try = pipeline_brand_norm["names_to_try"]
            brand_virtual_alias = pipeline_brand_norm["brand_virtual_norm"]

            # In brands mode, analyze once per brand; in brand_scent mode, once per scent
            if mode == "brands":
                matches = []

                for wsdb_entry in wsdb_normalized:
                    wsdb_brand = wsdb_entry["brand_norm"]
                    wsdb_brand_virtual = wsdb_entry["brand_virtual_norm"]
                    wsdb_soap = wsdb_entry["original"]
                    
                    # Try matching with each name (canonical + aliases + virtual alias)
                    best_score = 0
                    matched_via = "canonical"
                    
                    for idx, name in enumerate(names_to_try):
                        # Try against original WSDB brand
                        score = fuzz.ratio(name, wsdb_brand)
                        # Also try against virtual alias (stripped "soap")
                        if wsdb_brand_virtual:
                            virtual_score = fuzz.ratio(name, wsdb_brand_virtual)
                            score = max(score, virtual_score)
                        if score > best_score:
                            best_score = score
                            # Determine matched_via: canonical (first), alias (middle), or virtual_alias (last if virtual alias exists)
                            if idx == 0:
                                matched_via = "canonical"
                            elif brand_virtual_alias and idx == len(names_to_try) - 1:
                                matched_via = "virtual_alias"
                            else:
                                matched_via = "alias"
                    
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
                source_item = {"source_brand": brand_entry["brand"], "source_scent": ""}
                matches = [
                    m for m in matches if not is_non_match(source_item, m, brand_non_matches, scent_non_matches, mode)
                ]

                # Sort and limit
                matches.sort(key=lambda x: x["confidence"], reverse=True)
                matches = matches[:5]

                pipeline_results.append(
                    {
                        "source_brand": brand_entry["brand"],
                        "source_scent": "",  # Empty for brands mode
                        "matches": matches,
                        "expanded": False,
                    }
                )
            else:
                # Brand + Scent mode: match each scent individually
                for scent in brand_entry["scents"]:
                    # Use pre-normalized brand data
                    names_to_try = pipeline_brand_norm["names_to_try"]
                    brand_virtual_alias = pipeline_brand_norm["brand_virtual_norm"]
                    
                    # Pre-normalize scent once
                    scent_norm = pre_normalize_pipeline_scent(scent, scent["name"])
                    scent_names_to_try = scent_norm["scent_names_to_try"]
                    
                    matches = []

                    for wsdb_entry in wsdb_normalized:
                        wsdb_brand = wsdb_entry["brand_norm"]
                        wsdb_name = wsdb_entry["name_norm"]
                        wsdb_brand_virtual = wsdb_entry["brand_virtual_norm"]
                        wsdb_name_virtual = wsdb_entry["name_virtual_norm"]
                        wsdb_soap = wsdb_entry["original"]

                        # Try matching with each brand name (canonical + aliases + virtual alias)
                        best_brand_score = 0
                        matched_via = "canonical"
                        
                        for idx, name in enumerate(names_to_try):
                            # Try against original WSDB brand
                            score = fuzz.ratio(name, wsdb_brand)
                            # Also try against virtual alias (stripped "soap")
                            if wsdb_brand_virtual:
                                virtual_score = fuzz.ratio(name, wsdb_brand_virtual)
                                score = max(score, virtual_score)
                            if score > best_brand_score:
                                best_brand_score = score
                                # Determine matched_via: canonical (first), alias (middle), or virtual_alias (last if virtual alias exists)
                                if idx == 0:
                                    matched_via = "canonical"
                                elif brand_virtual_alias and idx == len(names_to_try) - 1:
                                    matched_via = "virtual_alias"
                                else:
                                    matched_via = "alias"
                        
                        brand_score = best_brand_score
                        
                        # Only proceed if brand matches above threshold (convert to percentage)
                        if brand_score >= brand_threshold * 100:
                            # Try matching with each scent name (canonical + alias + virtual alias)
                            best_scent_score = 0
                            scent_matched_via = "canonical"
                            
                            for idx, scent_name in enumerate(scent_names_to_try):
                                # Try against original WSDB name
                                score = fuzz.token_sort_ratio(scent_name, wsdb_name)
                                # Also try against virtual alias (stripped "soap")
                                if wsdb_name_virtual:
                                    virtual_score = fuzz.token_sort_ratio(scent_name, wsdb_name_virtual)
                                    score = max(score, virtual_score)
                                if score > best_scent_score:
                                    best_scent_score = score
                                    # Determine scent_matched_via: canonical (first), alias (middle), or virtual_alias (last)
                                    if idx == 0:
                                        scent_matched_via = "canonical"
                                    elif idx == len(scent_names_to_try) - 1 and any(
                                        s.get("alias") for s in [scent] if s.get("alias")
                                    ):
                                        scent_matched_via = "virtual_alias"
                                    else:
                                        scent_matched_via = "alias"
                            
                            scent_score = best_scent_score
                            confidence = scent_score  # Use scent score directly
                            
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
                                        "scent_matched_via": scent_matched_via,
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
                    source_item = {"source_brand": brand_entry["brand"], "source_scent": scent["name"]}
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
                            "source_brand": brand_entry["brand"],
                            "source_scent": scent["name"],
                            "matches": matches,
                            "expanded": False,
                        }
                    )
        # WSDB → Pipeline matches
        logger.info(f"📊 Analyzing WSDB → Pipeline ({len(wsdb_soaps)} soaps)")
        
        if mode == "brands":
            # In brands mode, group WSDB entries by brand first
            wsdb_brands_map = {}
            for wsdb_entry in wsdb_normalized:
                brand = wsdb_entry["original"].get("brand", "")
                if brand not in wsdb_brands_map:
                    wsdb_brands_map[brand] = []
                wsdb_brands_map[brand].append(wsdb_entry)
            
            # Sort brands alphabetically
            sorted_brands = sorted(wsdb_brands_map.items(), key=lambda x: x[0].lower())
            
            # In brands mode, analyze all brands (typically not too many)
            # Analyze once per brand
            for wsdb_brand, wsdb_entries in sorted_brands:
                # Use first entry for normalized values (all entries for same brand have same normalized brand)
                first_entry = wsdb_entries[0]
                query_brand = first_entry["brand_norm"]
                query_brand_virtual = first_entry["brand_virtual_norm"]
                matches = []

                for brand_entry in pipeline_soaps:
                    # Pre-normalize pipeline brand once
                    pipeline_brand_norm = pre_normalize_pipeline_brand(brand_entry)
                    names_to_try = pipeline_brand_norm["names_to_try"]
                    pipeline_brand_virtual = pipeline_brand_norm["brand_virtual_norm"]
                    
                    # Try matching with each name (against both original and virtual WSDB brand)
                    best_score = 0
                    matched_via = "canonical"
                    
                    for idx, name in enumerate(names_to_try):
                        # Try against original WSDB brand
                        score = fuzz.ratio(query_brand, name)
                        # Also try against virtual alias (stripped "soap")
                        if query_brand_virtual:
                            virtual_score = fuzz.ratio(query_brand_virtual, name)
                            score = max(score, virtual_score)
                        if score > best_score:
                            best_score = score
                            # Determine matched_via: canonical (first), alias (middle), or virtual_alias (last if virtual alias exists)
                            if idx == 0:
                                matched_via = "canonical"
                            elif pipeline_brand_virtual and idx == len(names_to_try) - 1:
                                matched_via = "virtual_alias"
                            else:
                                matched_via = "alias"
                    
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
            
            for wsdb_soap in sorted_wsdb_soaps:
                query_brand = normalize_for_matching(wsdb_soap.get("brand", ""))
                query_scent = normalize_for_matching(wsdb_soap.get("name", ""))
                # Also try matching against WSDB brand/name with stripped "soap" (virtual alias)
                query_brand_virtual = strip_trailing_soap(query_brand)
                if query_brand_virtual:
                    query_brand_virtual = normalize_for_matching(query_brand_virtual)
                query_scent_virtual = strip_trailing_soap(query_scent)
                if query_scent_virtual:
                    query_scent_virtual = normalize_for_matching(query_scent_virtual)
                matches = []

                for brand_entry in pipeline_soaps:
                    pipeline_brand = normalize_for_matching(brand_entry["brand"])
                    
                    # Get all names to try: canonical + aliases + virtual alias (stripped "soap")
                    names_to_try = [pipeline_brand]
                    if brand_entry.get("aliases"):
                        names_to_try.extend([normalize_for_matching(alias) for alias in brand_entry["aliases"]])
                    # Add virtual alias: strip trailing "soap" if present
                    pipeline_brand_virtual = strip_trailing_soap(pipeline_brand)
                    if pipeline_brand_virtual:
                        pipeline_brand_virtual_normalized = normalize_for_matching(pipeline_brand_virtual)
                        if pipeline_brand_virtual_normalized not in names_to_try:
                            names_to_try.append(pipeline_brand_virtual_normalized)

                    for scent in brand_entry["scents"]:
                        # Get scent names to try: canonical + single alias + virtual alias (stripped "soap")
                        pipeline_scent = normalize_for_matching(scent["name"])
                        scent_alias = scent.get("alias")
                        scent_names_to_try = [pipeline_scent]
                        if scent_alias:
                            scent_alias = normalize_for_matching(scent_alias)
                            scent_names_to_try.append(scent_alias)
                        # Add virtual alias: strip trailing "soap" if present
                        pipeline_scent_virtual = strip_trailing_soap(pipeline_scent)
                        if pipeline_scent_virtual:
                            pipeline_scent_virtual_normalized = normalize_for_matching(pipeline_scent_virtual)
                            if pipeline_scent_virtual_normalized not in scent_names_to_try:
                                scent_names_to_try.append(pipeline_scent_virtual_normalized)

                        # Try matching with each brand name (canonical + aliases + virtual alias)
                        best_brand_score = 0
                        matched_via = "canonical"
                        
                        for idx, name in enumerate(names_to_try):
                            # Try against original WSDB brand
                            score = fuzz.ratio(query_brand, name)
                            # Also try against virtual alias (stripped "soap")
                            if query_brand_virtual:
                                virtual_score = fuzz.ratio(query_brand_virtual, name)
                                score = max(score, virtual_score)
                            if score > best_brand_score:
                                best_brand_score = score
                                # Determine matched_via: canonical (first), alias (middle), or virtual_alias (last if virtual alias exists)
                                if idx == 0:
                                    matched_via = "canonical"
                                elif pipeline_brand_virtual and idx == len(names_to_try) - 1:
                                    matched_via = "virtual_alias"
                                else:
                                    matched_via = "alias"
                        
                        brand_score = best_brand_score
                        
                        # Only proceed if brand matches above threshold (convert to percentage)
                        if brand_score >= brand_threshold * 100:
                            # Try matching with each scent name (canonical + alias + virtual alias)
                            best_scent_score = 0
                            scent_matched_via = "canonical"
                            
                            for idx, scent_name in enumerate(scent_names_to_try):
                                # Try against original WSDB scent
                                score = fuzz.token_sort_ratio(query_scent, scent_name)
                                # Also try against virtual alias (stripped "soap")
                                if query_scent_virtual:
                                    virtual_score = fuzz.token_sort_ratio(query_scent_virtual, scent_name)
                                    score = max(score, virtual_score)
                                if score > best_scent_score:
                                    best_scent_score = score
                                    # Determine scent_matched_via: canonical (first), alias (middle), or virtual_alias (last)
                                    if idx == 0:
                                        scent_matched_via = "canonical"
                                    elif idx == len(scent_names_to_try) - 1 and any(
                                        s.get("alias") for s in [scent] if s.get("alias")
                                    ):
                                        scent_matched_via = "virtual_alias"
                                    else:
                                        scent_matched_via = "alias"
                            
                            scent_score = best_scent_score
                            confidence = scent_score  # Use scent score directly
                            
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
                                        "scent_matched_via": scent_matched_via,
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
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Batch analysis failed: {str(e)}")


@router.post("/refresh-wsdb-data")
async def refresh_wsdb_data() -> WSDBRefreshResponse:
    """
    Refresh WSDB data by fetching latest software.json from wetshavingdatabase.com API.

    Returns:
        WSDBRefreshResponse with success status and metadata
    """
    data = None
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
    Load known non-matches from brand and scent YAML files.

    Returns:
        Dict with brand_non_matches and scent_non_matches in hierarchical format
    """
    try:
        logger.info("📂 Loading known non-matches")
        brands_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches_brands.yaml"
        scents_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches_scents.yaml"

        # Load brand non-matches
        brand_non_matches = {}
        if brands_file.exists():
            with brands_file.open("r", encoding="utf-8") as f:
                brand_non_matches = yaml.safe_load(f) or {}

        # Load scent non-matches
        scent_non_matches = {}
        if scents_file.exists():
            with scents_file.open("r", encoding="utf-8") as f:
                scent_non_matches = yaml.safe_load(f) or {}

        brand_count = sum(len(v) for v in brand_non_matches.values())
        scent_count = sum(len(scents) for brand_scents in scent_non_matches.values() for scents in brand_scents.values())

        logger.info(f"✅ Loaded {brand_count} brand non-matches, {scent_count} scent non-matches")

        return {"brand_non_matches": brand_non_matches, "scent_non_matches": scent_non_matches}

    except Exception as e:
        logger.error(f"❌ Failed to load non-matches: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to load non-matches: {str(e)}")


@router.post("/non-matches")
async def add_non_match(request: NonMatchRequest) -> dict[str, Any]:
    """
    Add a new non-match entry (auto-saves to YAML).
    Only saves if the pipeline brand/scent exists in soaps.yaml.

    Args:
        request: Non-match request with match type and brand/scent info

    Returns:
        Dict with success status and message
    """
    try:
        logger.info(f"➕ Adding non-match: {request.match_type} - {request.pipeline_brand} != {request.wsdb_brand}")

        # Load pipeline soaps to check if brand/scent exists (for validation, but allow saving even if not found)
        # In match files mode, brands may not exist in soaps.yaml, but we still want to save non-matches
        soaps_file = PROJECT_ROOT / "data" / "soaps.yaml"
        soaps_data = {}
        if soaps_file.exists():
            with soaps_file.open("r", encoding="utf-8") as f:
                soaps_data = yaml.safe_load(f) or {}

        # Warn if brand doesn't exist, but still allow saving (for match files mode)
        if request.pipeline_brand not in soaps_data:
            logger.warning(
                f"⚠️ Pipeline brand '{request.pipeline_brand}' not found in soaps.yaml, but saving non-match anyway (match files mode)"
            )

        if request.match_type == "scent":
            # Check if pipeline scent exists within the brand (if brand exists)
            if request.pipeline_brand in soaps_data:
                brand_data = soaps_data[request.pipeline_brand]
                scents = brand_data.get("scents", {})
                if request.pipeline_scent not in scents:
                    logger.warning(
                        f"⚠️ Pipeline scent '{request.pipeline_scent}' not found in '{request.pipeline_brand}' in soaps.yaml, but saving non-match anyway (match files mode)"
                    )

            # Load scent non-matches
            scents_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches_scents.yaml"
            scent_non_matches = {}
            if scents_file.exists():
                with scents_file.open("r", encoding="utf-8") as f:
                    scent_non_matches = yaml.safe_load(f) or {}

            # Add non-match (bidirectional)
            # Format: brand -> scent -> [list of non-matching wsdb scents]
            if request.pipeline_brand not in scent_non_matches:
                scent_non_matches[request.pipeline_brand] = {}
            if request.pipeline_scent not in scent_non_matches[request.pipeline_brand]:
                scent_non_matches[request.pipeline_brand][request.pipeline_scent] = []

            # Check for duplicate
            if request.wsdb_scent in scent_non_matches[request.pipeline_brand][request.pipeline_scent]:
                logger.info("ℹ️ Non-match already exists, skipping")
                return {"success": True, "message": "Non-match already exists"}

            # Add the non-match
            scent_non_matches[request.pipeline_brand][request.pipeline_scent].append(request.wsdb_scent)

            # Save atomically
            temp_file = scents_file.with_suffix(".tmp")
            with temp_file.open("w", encoding="utf-8") as f:
                yaml.dump(scent_non_matches, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            temp_file.replace(scents_file)

            logger.info("✅ Scent non-match added and saved successfully")
            return {"success": True, "message": "Scent non-match added successfully"}

        else:  # brand
            # Load brand non-matches
            brands_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches_brands.yaml"
            brand_non_matches = {}
            if brands_file.exists():
                with brands_file.open("r", encoding="utf-8") as f:
                    brand_non_matches = yaml.safe_load(f) or {}

            # Add non-match
            # Format: pipeline_brand -> [list of non-matching wsdb brands]
            if request.pipeline_brand not in brand_non_matches:
                brand_non_matches[request.pipeline_brand] = []

            # Check for duplicate
            if request.wsdb_brand in brand_non_matches[request.pipeline_brand]:
                logger.info("ℹ️ Non-match already exists, skipping")
                return {"success": True, "message": "Non-match already exists"}

            # Add the non-match
            brand_non_matches[request.pipeline_brand].append(request.wsdb_brand)

            # Save atomically
            temp_file = brands_file.with_suffix(".tmp")
            with temp_file.open("w", encoding="utf-8") as f:
                yaml.dump(brand_non_matches, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            temp_file.replace(brands_file)

            logger.info("✅ Brand non-match added and saved successfully")
            return {"success": True, "message": "Brand non-match added successfully"}

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

        if request.match_type == "scent":
            scents_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches_scents.yaml"

            if not scents_file.exists():
                logger.warning("⚠️ non_matches_scents.yaml not found")
                return {"success": True, "message": "Scent non-matches file not found, nothing to remove"}

            # Load existing scent non-matches
            with scents_file.open("r", encoding="utf-8") as f:
                scent_non_matches = yaml.safe_load(f) or {}

            # Try to remove the entry
            removed = False
            if request.pipeline_brand in scent_non_matches:
                if request.pipeline_scent in scent_non_matches[request.pipeline_brand]:
                    scent_list = scent_non_matches[request.pipeline_brand][request.pipeline_scent]
                    if request.wsdb_scent in scent_list:
                        scent_list.remove(request.wsdb_scent)
                        removed = True

                        # Clean up empty entries
                        if not scent_list:
                            del scent_non_matches[request.pipeline_brand][request.pipeline_scent]
                        if not scent_non_matches[request.pipeline_brand]:
                            del scent_non_matches[request.pipeline_brand]

            if not removed:
                logger.info("ℹ️ No matching scent non-match found to remove")
                return {"success": True, "message": "No matching scent non-match found"}

            # Save atomically
            temp_file = scents_file.with_suffix(".tmp")
            with temp_file.open("w", encoding="utf-8") as f:
                yaml.dump(scent_non_matches, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            temp_file.replace(scents_file)

            logger.info("✅ Removed scent non-match successfully")
            return {"success": True, "message": "Scent non-match removed"}

        else:  # brand
            brands_file = PROJECT_ROOT / "data" / "wsdb" / "non_matches_brands.yaml"

            if not brands_file.exists():
                logger.warning("⚠️ non_matches_brands.yaml not found")
                return {"success": True, "message": "Brand non-matches file not found, nothing to remove"}

            # Load existing brand non-matches
            with brands_file.open("r", encoding="utf-8") as f:
                brand_non_matches = yaml.safe_load(f) or {}

            # Try to remove the entry
            removed = False
            if request.pipeline_brand in brand_non_matches:
                if request.wsdb_brand in brand_non_matches[request.pipeline_brand]:
                    brand_non_matches[request.pipeline_brand].remove(request.wsdb_brand)
                    removed = True

                    # Clean up empty entry
                    if not brand_non_matches[request.pipeline_brand]:
                        del brand_non_matches[request.pipeline_brand]

            if not removed:
                logger.info("ℹ️ No matching brand non-match found to remove")
                return {"success": True, "message": "No matching brand non-match found"}

            # Save atomically
            temp_file = brands_file.with_suffix(".tmp")
            with temp_file.open("w", encoding="utf-8") as f:
                yaml.dump(brand_non_matches, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
            temp_file.replace(brands_file)

            logger.info("✅ Removed brand non-match successfully")
            return {"success": True, "message": "Brand non-match removed"}

    except Exception as e:
        logger.error(f"❌ Failed to remove non-match: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to remove non-match: {str(e)}")


class AddAliasRequest(BaseModel):
    """Request model for adding an alias to a pipeline brand."""

    pipeline_brand: str
    alias: str


class AddScentAliasRequest(BaseModel):
    """Request model for adding an alias to a pipeline scent."""

    pipeline_brand: str
    pipeline_scent: str
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


@router.post("/add-scent-alias")
async def add_scent_alias(request: AddScentAliasRequest) -> dict[str, Any]:
    """
    Add an alias to a pipeline scent in soaps.yaml.

    Args:
        request: AddScentAliasRequest with pipeline_brand, pipeline_scent, and alias

    Returns:
        Dict with success status and message
    """
    try:
        logger.info(
            f"➕ Adding scent alias '{request.alias}' to scent '{request.pipeline_scent}' in brand '{request.pipeline_brand}'"
        )

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

        # Check if scent exists
        if "scents" not in brand_data or request.pipeline_scent not in brand_data["scents"]:
            logger.error(
                f"❌ Scent '{request.pipeline_scent}' not found in brand '{request.pipeline_brand}' in soaps.yaml"
            )
            raise HTTPException(
                status_code=404, detail=f"Scent '{request.pipeline_scent}' not found in brand '{request.pipeline_brand}'"
            )

        scent_data = brand_data["scents"][request.pipeline_scent]

        # Ensure scent_data is a dict
        if not isinstance(scent_data, dict):
            scent_data = {}
            brand_data["scents"][request.pipeline_scent] = scent_data

        # Check if alias already exists (case-insensitive)
        existing_alias = scent_data.get("alias")
        if existing_alias and existing_alias.lower() == request.alias.lower():
            logger.info(
                f"ℹ️ Scent alias '{request.alias}' already exists for '{request.pipeline_scent}' in '{request.pipeline_brand}'"
            )
            return {"success": True, "message": f"Scent alias '{request.alias}' already exists"}

        # Set the alias (replacing any existing alias)
        scent_data["alias"] = request.alias

        # Save atomically
        temp_file = soaps_file.with_suffix(".tmp")
        with temp_file.open("w", encoding="utf-8") as f:
            yaml.dump(soaps_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

        temp_file.replace(soaps_file)

        logger.info(
            f"✅ Scent alias '{request.alias}' added to '{request.pipeline_scent}' in '{request.pipeline_brand}' successfully"
        )
        return {
            "success": True,
            "message": f"Added scent alias '{request.alias}' to '{request.pipeline_scent}' in '{request.pipeline_brand}'",
            "alias": request.alias,
        }

    except HTTPException:
        raise  # Re-raise HTTPExceptions without wrapping
    except Exception as e:
        logger.error(f"❌ Failed to add scent alias: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add scent alias: {str(e)}")


def is_valid_month(month: str) -> bool:
    """Validate month format (YYYY-MM)."""
    try:
        year, month_num = month.split("-")
        if len(year) != 4 or len(month_num) != 2:
            return False
        int(year)
        month_int = int(month_num)
        return 1 <= month_int <= 12
    except ValueError:
        return False


@router.post("/batch-analyze-match-files")
async def batch_analyze_match_files(
    months: str = Query(..., description="Comma-separated months (e.g., '2025-05,2025-06')"),
    threshold: float = Query(0.7, ge=0.0, le=1.0, description="Minimum confidence threshold (0.0-1.0)"),
    limit: int = Query(100, ge=1, description="Maximum results per view"),
    mode: str = Query("brand_scent", description="Analysis mode: 'brands' or 'brand_scent'"),
    brand_threshold: float = Query(0.8, ge=0.0, le=1.0, description="Minimum brand match threshold (0.0-1.0)"),
    match_type_filter: str = Query("brand", description="Filter for match_type (default: 'brand', use 'all' for all types)"),
) -> dict[str, Any]:
    """
    Perform batch analysis of match file data against WSDB soaps.
    Loads soap matches from match files and matches them against WSDB.

    Args:
        months: Comma-separated list of months (e.g., "2025-05,2025-06")
        threshold: Minimum confidence threshold (0.0-1.0)
        limit: Maximum results per view
        mode: "brands" or "brand_scent"
        brand_threshold: Minimum brand match threshold for brand+scent mode (0.0-1.0, default 0.8)
        match_type_filter: Filter for match_type (default: "brand", use "all" for all types)

    Returns:
        Dict with pipeline_results and wsdb_results
    """
    import time
    start_time = time.time()
    try:
        logger.info(f"🔄 Starting batch_analyze_match_files: months={months}, mode={mode}, threshold={threshold}")
        # Parse and validate months
        month_list = [m.strip() for m in months.split(",")]
        for month in month_list:
            if not is_valid_month(month):
                raise HTTPException(status_code=400, detail=f"Invalid month format: {month}. Use YYYY-MM format.")

        logger.info(
            f"🔄 Starting batch analysis from match files (mode: {mode}, threshold: {threshold}, "
            f"brand_threshold: {brand_threshold}, match_type_filter: {match_type_filter}, months: {month_list})"
        )

        # Load match files
        logger.info(f"📂 Loading match files for {len(month_list)} months...")
        data_dir = PROJECT_ROOT / "data" / "matched"
        all_soap_matches = []

        for month in month_list:
            logger.info(f"📂 Loading match file: {month}.json")
            month_file = data_dir / f"{month}.json"
            if not month_file.exists():
                logger.warning(f"⚠️ No match data found for month: {month}")
                continue

            try:
                with month_file.open("r", encoding="utf-8") as f:
                    match_data = json.load(f)

                # Extract soap data from the data array
                if "data" in match_data and isinstance(match_data["data"], list):
                    for record in match_data["data"]:
                        if "soap" in record and record["soap"]:
                            soap = record["soap"]
                            # Defensive check: ensure soap is a dict
                            if not isinstance(soap, dict):
                                logger.warning(f"⚠️ Skipping non-dict soap entry in {month}: {type(soap)}")
                                continue
                            # Filter by match_type if specified
                            if match_type_filter != "all" and soap.get("match_type") != match_type_filter:
                                continue
                            # Only include entries with matched brand and scent
                            matched = soap.get("matched")
                            if not matched or not isinstance(matched, dict):
                                continue
                            if matched.get("brand") and matched.get("scent"):
                                # Add comment_id if available
                                soap_entry = soap.copy()
                                soap_entry["comment_id"] = record.get("id", record.get("comment_id", ""))
                                all_soap_matches.append(soap_entry)

            except Exception as e:
                logger.error(f"❌ Error loading month {month}: {e}")
                continue

        if not all_soap_matches:
            logger.warning("⚠️ No soap matches found in match files for the specified criteria")
            return {
                "pipeline_results": [],
                "wsdb_results": [],
                "mode": mode,
                "threshold": threshold,
                "analyzed_at": datetime.now().isoformat(),
                "months_processed": month_list,
                "total_entries": 0,
            }

        logger.info(f"📊 Loaded {len(all_soap_matches)} soap matches from match files")

        # Group by unique brand+scent combinations and collect metadata
        brand_scent_groups: dict[str, dict[str, Any]] = {}
        for soap in all_soap_matches:
            matched = soap.get("matched", {})
            brand = matched.get("brand", "").strip()
            scent = matched.get("scent", "").strip()
            if not brand or not scent:
                continue

            # Use brand+scent as key (case-insensitive for grouping)
            key = f"{brand} - {scent}".lower()

            if key not in brand_scent_groups:
                brand_scent_groups[key] = {
                    "brand": brand,
                    "scent": scent,
                    "original_texts": [],
                    "match_types": [],
                    "comment_ids": [],
                    "count": 0,
                }

            # Collect metadata
            brand_scent_groups[key]["original_texts"].append(soap.get("original", ""))
            brand_scent_groups[key]["match_types"].append(soap.get("match_type", "unknown"))
            if soap.get("comment_id"):
                brand_scent_groups[key]["comment_ids"].append(soap.get("comment_id"))
            brand_scent_groups[key]["count"] += 1

        logger.info(f"📊 Grouped into {len(brand_scent_groups)} unique brand+scent combinations")

        # Load WSDB data
        wsdb_data = await load_wsdb_soaps()
        wsdb_soaps = wsdb_data["soaps"]

        # Pre-normalize WSDB entries once for performance
        wsdb_normalized = pre_normalize_wsdb_entries(wsdb_soaps)

        # Load pipeline soaps for alias lookup
        pipeline_data = await load_pipeline_soaps()
        pipeline_soaps = pipeline_data["soaps"]

        # Create lookup map: brand_name -> brand_entry (for aliases)
        brand_lookup = {entry["brand"]: entry for entry in pipeline_soaps}

        # Load non-matches for filtering
        non_matches_data = await load_non_matches()
        brand_non_matches = non_matches_data.get("brand_non_matches", {})
        scent_non_matches = non_matches_data.get("scent_non_matches", {})

        pipeline_results = []
        wsdb_results = []

        # Match each brand+scent combination against WSDB
        for key, group_data in brand_scent_groups.items():
            pipeline_brand = group_data["brand"]
            pipeline_scent = group_data["scent"]

            # Look up brand in pipeline soaps to get aliases
            brand_entry = brand_lookup.get(pipeline_brand, {"brand": pipeline_brand, "aliases": [], "scents": []})

            if mode == "brands":
                # Brands only: match brand against all WSDB brands
                # Pre-normalize pipeline brand once
                pipeline_brand_norm = pre_normalize_pipeline_brand(brand_entry)
                names_to_try = pipeline_brand_norm["names_to_try"]
                brand_virtual_alias = pipeline_brand_norm["brand_virtual_norm"]
                
                matches = []

                for wsdb_entry in wsdb_normalized:
                    wsdb_brand = wsdb_entry["brand_norm"]
                    wsdb_brand_virtual = wsdb_entry["brand_virtual_norm"]
                    wsdb_soap = wsdb_entry["original"]
                    
                    # Try matching with each name (canonical + aliases + virtual alias)
                    best_score = 0
                    matched_via = "canonical"
                    
                    for idx, name in enumerate(names_to_try):
                        # Try against original WSDB brand
                        score = fuzz.ratio(name, wsdb_brand)
                        # Also try against virtual alias (stripped "soap")
                        if wsdb_brand_virtual:
                            virtual_score = fuzz.ratio(name, wsdb_brand_virtual)
                            score = max(score, virtual_score)
                        if score > best_score:
                            best_score = score
                            # Determine matched_via: canonical (first), alias (middle), or virtual_alias (last if virtual alias exists)
                            if idx == 0:
                                matched_via = "canonical"
                            elif brand_virtual_alias and idx == len(names_to_try) - 1:
                                matched_via = "virtual_alias"
                            else:
                                matched_via = "alias"
                    
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
                        "source_scent": "",
                        "matches": matches,
                        "expanded": False,
                        "original_texts": list(set(group_data["original_texts"]))[:5],  # Top 5 unique originals
                        "match_types": list(set(group_data["match_types"])),
                        "count": group_data["count"],
                        "comment_ids": group_data["comment_ids"][:10],  # Limit comment IDs
                    }
                )
            else:
                # Brand + Scent mode: match each scent individually
                # Pre-normalize pipeline brand once
                pipeline_brand_norm = pre_normalize_pipeline_brand(brand_entry)
                names_to_try = pipeline_brand_norm["names_to_try"]
                brand_virtual_alias = pipeline_brand_norm["brand_virtual_norm"]
                
                # Get scent alias and pre-normalize scent
                scent_dict = None
                for scent_info in brand_entry.get("scents", []):
                    if scent_info.get("name") == pipeline_scent:
                        scent_dict = scent_info
                        break
                if not scent_dict:
                    scent_dict = {"name": pipeline_scent}
                
                scent_norm = pre_normalize_pipeline_scent(scent_dict, pipeline_scent)
                scent_names_to_try = scent_norm["scent_names_to_try"]
                
                matches = []

                for wsdb_entry in wsdb_normalized:
                    wsdb_brand = wsdb_entry["brand_norm"]
                    wsdb_name = wsdb_entry["name_norm"]
                    wsdb_brand_virtual = wsdb_entry["brand_virtual_norm"]
                    wsdb_name_virtual = wsdb_entry["name_virtual_norm"]
                    wsdb_soap = wsdb_entry["original"]

                    # Try matching with each brand name (canonical + aliases + virtual alias)
                    best_brand_score = 0
                    matched_via = "canonical"
                    
                    for idx, name in enumerate(names_to_try):
                        # Try against original WSDB brand
                        score = fuzz.ratio(name, wsdb_brand)
                        # Also try against virtual alias (stripped "soap")
                        if wsdb_brand_virtual:
                            virtual_score = fuzz.ratio(name, wsdb_brand_virtual)
                            score = max(score, virtual_score)
                        if score > best_brand_score:
                            best_brand_score = score
                            # Determine matched_via: canonical (first), alias (middle), or virtual_alias (last if virtual alias exists)
                            if idx == 0:
                                matched_via = "canonical"
                            elif brand_virtual_alias and idx == len(names_to_try) - 1:
                                matched_via = "virtual_alias"
                            else:
                                matched_via = "alias"
                    
                    brand_score = best_brand_score

                    # Only proceed if brand matches above threshold
                    if brand_score >= brand_threshold * 100:
                        # Try matching with each scent name (canonical + alias + virtual alias)
                        best_scent_score = 0
                        scent_matched_via = "canonical"
                        
                        for idx, scent_name in enumerate(scent_names_to_try):
                            # Try against original WSDB name
                            score = fuzz.token_sort_ratio(scent_name, wsdb_name)
                            # Also try against virtual alias (stripped "soap")
                            if wsdb_name_virtual:
                                virtual_score = fuzz.token_sort_ratio(scent_name, wsdb_name_virtual)
                                score = max(score, virtual_score)
                            if score > best_scent_score:
                                best_scent_score = score
                                # Determine scent_matched_via: canonical (first), alias (middle), or virtual_alias (last)
                                if idx == 0:
                                    scent_matched_via = "canonical"
                                elif idx == len(scent_names_to_try) - 1 and scent_dict.get("alias"):
                                    scent_matched_via = "virtual_alias"
                                else:
                                    scent_matched_via = "alias"
                        
                        scent_score = best_scent_score
                        confidence = scent_score  # Use scent score directly

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
                                    "scent_matched_via": scent_matched_via,
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
                source_item = {"source_brand": pipeline_brand, "source_scent": pipeline_scent}
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
                        "source_scent": pipeline_scent,
                        "matches": matches,
                        "expanded": False,
                        "original_texts": list(set(group_data["original_texts"]))[:5],  # Top 5 unique originals
                        "match_types": list(set(group_data["match_types"])),
                        "count": group_data["count"],
                        "comment_ids": group_data["comment_ids"][:10],  # Limit comment IDs
                    }
                )

        # WSDB → Pipeline matches (reverse direction)
        # For match files mode, we primarily care about Pipeline → WSDB, but we can also do reverse
        # This would match WSDB soaps against the match file data
        logger.info(f"📊 Analyzing WSDB → Pipeline ({len(wsdb_soaps)} soaps)")

        if mode == "brands":
            # Group WSDB entries by brand
            wsdb_brands_map = {}
            for wsdb_entry in wsdb_normalized:
                brand = wsdb_entry["original"].get("brand", "")
                if brand not in wsdb_brands_map:
                    wsdb_brands_map[brand] = []
                wsdb_brands_map[brand].append(wsdb_entry)

            sorted_brands = sorted(wsdb_brands_map.items(), key=lambda x: x[0].lower())

            for wsdb_brand, wsdb_entries in sorted_brands:
                # Use first entry for normalized values (all entries for same brand have same normalized brand)
                first_entry = wsdb_entries[0]
                query_brand = first_entry["brand_norm"]
                query_brand_virtual = first_entry["brand_virtual_norm"]
                matches = []

                # Match against unique brands from match files
                unique_brands = {group_data["brand"] for group_data in brand_scent_groups.values()}
                for pipeline_brand in unique_brands:
                    # Look up brand in pipeline soaps to get aliases
                    brand_entry = brand_lookup.get(pipeline_brand, {"brand": pipeline_brand, "aliases": [], "scents": []})
                    
                    # Pre-normalize pipeline brand once
                    pipeline_brand_norm = pre_normalize_pipeline_brand(brand_entry)
                    names_to_try = pipeline_brand_norm["names_to_try"]
                    pipeline_brand_virtual = pipeline_brand_norm["brand_virtual_norm"]
                    
                    # Try matching with each name (against both original and virtual WSDB brand)
                    best_score = 0
                    matched_via = "canonical"
                    
                    for idx, name in enumerate(names_to_try):
                        # Try against original WSDB brand
                        score = fuzz.ratio(query_brand, name)
                        # Also try against virtual alias (stripped "soap")
                        if query_brand_virtual:
                            virtual_score = fuzz.ratio(query_brand_virtual, name)
                            score = max(score, virtual_score)
                        if score > best_score:
                            best_score = score
                            # Determine matched_via: canonical (first), alias (middle), or virtual_alias (last if virtual alias exists)
                            if idx == 0:
                                matched_via = "canonical"
                            elif pipeline_brand_virtual and idx == len(names_to_try) - 1:
                                matched_via = "virtual_alias"
                            else:
                                matched_via = "alias"
                    
                    brand_score = best_score
                    confidence = brand_score

                    if confidence >= threshold * 100:
                        matches.append(
                            {
                                "brand": pipeline_brand,
                                "name": "",
                                "confidence": round(confidence, 2),
                                "brand_score": round(brand_score, 2),
                                "scent_score": 0.0,
                                "source": "pipeline",
                                "matched_via": matched_via,
                                "details": {"patterns": []},
                            }
                        )

                # Filter non-matches
                source_item = {"source_brand": wsdb_brand, "source_scent": ""}
                matches = [
                    m for m in matches if not is_non_match(source_item, m, brand_non_matches, scent_non_matches, mode)
                ]

                matches.sort(key=lambda x: x["confidence"], reverse=True)
                matches = matches[:5]

                wsdb_results.append(
                    {
                        "source_brand": wsdb_brand,
                        "source_scent": "",
                        "matches": matches,
                        "expanded": False,
                    }
                )
        else:
            # Brand + Scent mode: match each WSDB entry against match file data
            # Pre-normalize all pipeline brands and scents ONCE before the loop
            logger.info(f"🔄 Pre-normalizing {len(brand_scent_groups)} pipeline brand+scent combinations...")
            pipeline_brand_cache = {}
            pipeline_scent_cache = {}
            for key, group_data in brand_scent_groups.items():
                pipeline_brand = group_data["brand"]
                pipeline_scent = group_data["scent"]
                
                # Cache normalized brand if not already cached
                if pipeline_brand not in pipeline_brand_cache:
                    brand_entry = brand_lookup.get(pipeline_brand, {"brand": pipeline_brand, "aliases": [], "scents": []})
                    pipeline_brand_cache[pipeline_brand] = pre_normalize_pipeline_brand(brand_entry)
                
                # Cache normalized scent if not already cached
                cache_key = (pipeline_brand, pipeline_scent)
                if cache_key not in pipeline_scent_cache:
                    brand_entry = brand_lookup.get(pipeline_brand, {"brand": pipeline_brand, "aliases": [], "scents": []})
                    scent_dict = None
                    for scent_info in brand_entry.get("scents", []):
                        if scent_info.get("name") == pipeline_scent:
                            scent_dict = scent_info
                            break
                    if not scent_dict:
                        scent_dict = {"name": pipeline_scent}
                    pipeline_scent_cache[cache_key] = pre_normalize_pipeline_scent(scent_dict, pipeline_scent)
            
            sorted_wsdb_entries = sorted(
                wsdb_normalized, key=lambda x: (x["original"].get("brand", "").lower(), x["original"].get("name", "").lower())
            )
            logger.info(f"🔄 Processing {len(sorted_wsdb_entries)} WSDB entries against {len(brand_scent_groups)} pipeline combinations...")

            for idx, wsdb_entry in enumerate(sorted_wsdb_entries):
                if (idx + 1) % 100 == 0:
                    logger.info(f"📊 Processed {idx + 1}/{len(sorted_wsdb_entries)} WSDB entries...")
                query_brand = wsdb_entry["brand_norm"]
                query_scent = wsdb_entry["name_norm"]
                query_brand_virtual = wsdb_entry["brand_virtual_norm"]
                query_scent_virtual = wsdb_entry["name_virtual_norm"]
                wsdb_soap = wsdb_entry["original"]
                matches = []

                for key, group_data in brand_scent_groups.items():
                    pipeline_brand = group_data["brand"]
                    pipeline_scent = group_data["scent"]

                    # Use cached normalized values (pre-computed above)
                    # Safety check: if not in cache, compute on-the-fly (shouldn't happen, but defensive)
                    if pipeline_brand not in pipeline_brand_cache:
                        logger.warning(f"⚠️ Brand {pipeline_brand} not in cache, computing on-the-fly")
                        brand_entry = brand_lookup.get(pipeline_brand, {"brand": pipeline_brand, "aliases": [], "scents": []})
                        pipeline_brand_cache[pipeline_brand] = pre_normalize_pipeline_brand(brand_entry)
                    pipeline_brand_norm = pipeline_brand_cache[pipeline_brand]
                    names_to_try = pipeline_brand_norm["names_to_try"]
                    pipeline_brand_virtual = pipeline_brand_norm["brand_virtual_norm"]
                    
                    # Use cached normalized scent
                    cache_key = (pipeline_brand, pipeline_scent)
                    if cache_key not in pipeline_scent_cache:
                        logger.warning(f"⚠️ Scent {cache_key} not in cache, computing on-the-fly")
                        brand_entry = brand_lookup.get(pipeline_brand, {"brand": pipeline_brand, "aliases": [], "scents": []})
                        scent_dict = None
                        for scent_info in brand_entry.get("scents", []):
                            if scent_info.get("name") == pipeline_scent:
                                scent_dict = scent_info
                                break
                        if not scent_dict:
                            scent_dict = {"name": pipeline_scent}
                        pipeline_scent_cache[cache_key] = pre_normalize_pipeline_scent(scent_dict, pipeline_scent)
                    scent_norm = pipeline_scent_cache[cache_key]
                    scent_names_to_try = scent_norm["scent_names_to_try"]

                    # Try matching with each brand name (canonical + aliases + virtual alias)
                    best_brand_score = 0
                    matched_via = "canonical"
                    
                    for idx, name in enumerate(names_to_try):
                        # Try against original WSDB brand
                        score = fuzz.ratio(query_brand, name)
                        # Also try against virtual alias (stripped "soap")
                        if query_brand_virtual:
                            virtual_score = fuzz.ratio(query_brand_virtual, name)
                            score = max(score, virtual_score)
                        if score > best_brand_score:
                            best_brand_score = score
                            # Determine matched_via: canonical (first), alias (middle), or virtual_alias (last if virtual alias exists)
                            if idx == 0:
                                matched_via = "canonical"
                            elif pipeline_brand_virtual and idx == len(names_to_try) - 1:
                                matched_via = "virtual_alias"
                            else:
                                matched_via = "alias"
                    
                    brand_score = best_brand_score

                    if brand_score >= brand_threshold * 100:
                        # Try matching with each scent name (canonical + alias + virtual alias)
                        best_scent_score = 0
                        scent_matched_via = "canonical"
                        
                        for idx, scent_name in enumerate(scent_names_to_try):
                                # Try against original WSDB scent
                                score = fuzz.token_sort_ratio(query_scent, scent_name)
                                # Also try against virtual alias (stripped "soap")
                                if query_scent_virtual:
                                    virtual_score = fuzz.token_sort_ratio(query_scent_virtual, scent_name)
                                    score = max(score, virtual_score)
                                if score > best_scent_score:
                                    best_scent_score = score
                                    # Determine scent_matched_via: canonical (first), alias (middle), or virtual_alias (last)
                                    if idx == 0:
                                        scent_matched_via = "canonical"
                                    elif idx == len(scent_names_to_try) - 1 and scent_dict.get("alias"):
                                        scent_matched_via = "virtual_alias"
                                    else:
                                        scent_matched_via = "alias"
                        
                        scent_score = best_scent_score
                        confidence = scent_score

                        if confidence >= threshold * 100:
                            matches.append(
                                {
                                    "brand": pipeline_brand,
                                    "name": pipeline_scent,
                                    "confidence": round(confidence, 2),
                                    "brand_score": round(brand_score, 2),
                                    "scent_score": round(scent_score, 2),
                                    "source": "pipeline",
                                    "matched_via": matched_via,
                                    "scent_matched_via": scent_matched_via,
                                    "details": {"patterns": []},
                                }
                            )

                # Filter non-matches
                source_item = {"source_brand": wsdb_soap.get("brand"), "source_scent": wsdb_soap.get("name")}
                matches = [
                    m for m in matches if not is_non_match(source_item, m, brand_non_matches, scent_non_matches, mode)
                ]

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

        elapsed = time.time() - start_time
        logger.info(
            f"✅ Batch analysis from match files complete in {elapsed:.2f}s: {len(pipeline_results)} pipeline results, "
            f"{len(wsdb_results)} WSDB results"
        )

        return {
            "pipeline_results": pipeline_results,
            "wsdb_results": wsdb_results,
            "mode": mode,
            "threshold": threshold,
            "analyzed_at": datetime.now().isoformat(),
            "months_processed": month_list,
            "total_entries": len(all_soap_matches),
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Batch analysis from match files failed: {e}")
        logger.error(f"❌ Traceback: {traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=f"Batch analysis from match files failed: {str(e)}")

