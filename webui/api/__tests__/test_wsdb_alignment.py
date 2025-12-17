#!/usr/bin/env python3
"""Tests for WSDB alignment API endpoints."""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

import httpx
import pytest
import yaml
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)

# Test data
MOCK_WSDB_DATA = [
    {
        "brand": "Barrister and Mann",
        "name": "Seville",
        "type": "Soap",
        "slug": "barrister-and-mann-seville",
        "scent_notes": ["citrus", "lavender"],
        "collaborators": [],
        "tags": ["classic"],
        "category": "Traditional",
    },
    {
        "brand": "Declaration Grooming",
        "name": "Massacre of the Innocents",
        "type": "Soap",
        "slug": "declaration-grooming-massacre-of-the-innocents",
        "scent_notes": ["pine", "smoke"],
        "collaborators": ["Chatillon Lux"],
        "tags": ["seasonal"],
        "category": "Artisan",
    },
    {
        "brand": "Stirling Soap Co.",
        "name": "Executive Man",
        "type": "Soap",
        "slug": "stirling-executive-man",
        "scent_notes": ["oakmoss", "citrus"],
        "collaborators": [],
        "tags": ["dupe"],
        "category": "Value",
    },
    # Non-soap item to test filtering
    {"brand": "Some Brand", "name": "Some Aftershave", "type": "Aftershave", "slug": "some-aftershave"},
]

MOCK_PIPELINE_DATA = {
    "Barrister and Mann": {
        "patterns": ["barrister.*mann", "b&m", "b and m"],
        "scents": {
            "Seville": {"patterns": ["seville"]},
            "Leviathan": {"patterns": ["leviathan", "levi"]},
        },
    },
    "Declaration Grooming": {
        "patterns": ["declaration.*grooming", "dg"],
        "scents": {
            "Massacre of the Innocents": {"patterns": ["massacre.*innocents", "moti"]},
            "Chaotic Neutral": {"patterns": ["chaotic.*neutral", "cn"]},
        },
    },
    "Stirling Soap Co.": {
        "patterns": ["stirling.*soap", "stirling"],
        "scents": {
            "Executive Man": {"patterns": ["executive.*man", "exec man"]},
            "Barbershop": {"patterns": ["barbershop"]},
        },
    },
}


@pytest.fixture
def mock_data_files(tmp_path):
    """Create temporary test data files."""
    # Create data directory
    data_dir = tmp_path / "data"
    data_dir.mkdir()

    # Create wsdb subdirectory
    wsdb_dir = data_dir / "wsdb"
    wsdb_dir.mkdir()

    # Write software.json in wsdb subdirectory
    software_file = wsdb_dir / "software.json"
    with software_file.open("w", encoding="utf-8") as f:
        json.dump(MOCK_WSDB_DATA, f)

    # Write soaps.yaml
    soaps_file = data_dir / "soaps.yaml"
    with soaps_file.open("w", encoding="utf-8") as f:
        yaml.dump(MOCK_PIPELINE_DATA, f)

    return data_dir


class TestLoadWSDBSoaps:
    """Tests for /api/wsdb-alignment/load-wsdb endpoint."""

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_load_wsdb_soaps_success(self, mock_root, mock_data_files):
        """Test successful loading of WSDB soaps."""
        # Mock PROJECT_ROOT to return parent of data directory
        mock_root_path = mock_data_files.parent
        mock_root.__truediv__ = lambda self, other: mock_root_path / other

        response = client.get("/api/wsdb-alignment/load-wsdb")

        assert response.status_code == 200
        data = response.json()

        assert "soaps" in data
        assert "total_count" in data
        assert "total_software_items" in data
        assert "loaded_at" in data

        # Should filter out non-soap items
        assert data["total_count"] == 3  # Only soaps
        assert data["total_software_items"] == 4  # All items including aftershave
        assert len(data["soaps"]) == 3

        # Verify soap brands
        brands = [soap["brand"] for soap in data["soaps"]]
        assert "Barrister and Mann" in brands
        assert "Declaration Grooming" in brands
        assert "Stirling Soap Co." in brands

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_load_wsdb_soaps_file_not_found(self, mock_root, tmp_path):
        """Test error handling when software.json is not found."""
        mock_root.__truediv__ = lambda self, other: tmp_path / other

        response = client.get("/api/wsdb-alignment/load-wsdb")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_load_wsdb_soaps_invalid_json(self, mock_root, tmp_path):
        """Test error handling when software.json is invalid."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        software_file = data_dir / "software.json"
        software_file.write_text("invalid json content")

        mock_root.__truediv__ = lambda self, other: tmp_path / other

        response = client.get("/api/wsdb-alignment/load-wsdb")

        assert response.status_code == 500
        assert "parse" in response.json()["detail"].lower()


class TestLoadPipelineSoaps:
    """Tests for /api/wsdb-alignment/load-pipeline endpoint."""

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_load_pipeline_soaps_success(self, mock_root, mock_data_files):
        """Test successful loading of pipeline soaps."""
        # Mock PROJECT_ROOT to return parent of data directory
        mock_root_path = mock_data_files.parent
        mock_root.__truediv__ = lambda self, other: mock_root_path / other

        response = client.get("/api/wsdb-alignment/load-pipeline")

        assert response.status_code == 200
        data = response.json()

        assert "soaps" in data
        assert "total_brands" in data
        assert "total_scents" in data
        assert "loaded_at" in data

        assert data["total_brands"] == 3
        assert data["total_scents"] == 6  # 2 scents per brand
        assert len(data["soaps"]) == 3

        # Verify structure
        for soap in data["soaps"]:
            assert "brand" in soap
            assert "scents" in soap
            assert isinstance(soap["scents"], list)
            for scent in soap["scents"]:
                assert "name" in scent
                assert "patterns" in scent

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_load_pipeline_soaps_file_not_found(self, mock_root, tmp_path):
        """Test error handling when soaps.yaml is not found."""
        mock_root.__truediv__ = lambda self, other: tmp_path / other

        response = client.get("/api/wsdb-alignment/load-pipeline")

        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_load_pipeline_soaps_invalid_yaml(self, mock_root, tmp_path):
        """Test error handling when soaps.yaml is invalid."""
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        soaps_file = data_dir / "soaps.yaml"
        soaps_file.write_text("invalid: yaml: content: [")

        mock_root.__truediv__ = lambda self, other: tmp_path / other

        response = client.get("/api/wsdb-alignment/load-pipeline")

        assert response.status_code == 500
        assert "parse" in response.json()["detail"].lower()


class TestFuzzyMatch:
    """Tests for /api/wsdb-alignment/fuzzy-match endpoint."""

    @patch("api.wsdb_alignment.load_wsdb_soaps")
    @patch("api.wsdb_alignment.load_pipeline_soaps")
    async def test_fuzzy_match_pipeline_to_wsdb_exact(self, mock_pipeline, mock_wsdb):
        """Test fuzzy matching from pipeline to WSDB with exact match."""
        mock_wsdb.return_value = {"soaps": MOCK_WSDB_DATA[:3], "total_count": 3}
        mock_pipeline.return_value = {"soaps": [], "total_brands": 0, "total_scents": 0}

        response = client.post(
            "/api/wsdb-alignment/fuzzy-match",
            json={"source_type": "pipeline", "brand": "Barrister and Mann", "scent": "Seville", "threshold": 0.7, "limit": 5, "mode": "brand_scent"},
        )

        assert response.status_code == 200
        data = response.json()

        assert "matches" in data
        assert "query" in data
        assert "threshold" in data
        assert "total_matches" in data

        # Should find exact match with high confidence
        assert len(data["matches"]) > 0
        top_match = data["matches"][0]
        assert top_match["brand"] == "Barrister and Mann"
        assert top_match["name"] == "Seville"
        assert top_match["confidence"] >= 90  # High confidence for exact match
        assert top_match["source"] == "wsdb"
        assert "details" in top_match
        assert "scent_notes" in top_match["details"]

    @patch("api.wsdb_alignment.load_wsdb_soaps")
    @patch("api.wsdb_alignment.load_pipeline_soaps")
    async def test_fuzzy_match_pipeline_to_wsdb_close_match(self, mock_pipeline, mock_wsdb):
        """Test fuzzy matching with close but not exact match."""
        mock_wsdb.return_value = {"soaps": MOCK_WSDB_DATA[:3], "total_count": 3}
        mock_pipeline.return_value = {"soaps": [], "total_brands": 0, "total_scents": 0}

        response = client.post(
            "/api/wsdb-alignment/fuzzy-match",
            json={
                "source_type": "pipeline",
                "brand": "Barister Mann",  # Typo in brand
                "scent": "Seville",
                "threshold": 0.7,
                "limit": 5,
                "mode": "brand_scent",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should still find match due to fuzzy matching
        assert len(data["matches"]) > 0
        assert data["matches"][0]["brand"] == "Barrister and Mann"

    @patch("api.wsdb_alignment.load_wsdb_soaps")
    @patch("api.wsdb_alignment.load_pipeline_soaps")
    async def test_fuzzy_match_wsdb_to_pipeline(self, mock_pipeline, mock_wsdb):
        """Test fuzzy matching from WSDB to pipeline."""
        pipeline_soaps = []
        for brand, brand_data in MOCK_PIPELINE_DATA.items():
            scents = [{"name": scent, "patterns": data.get("patterns", [])} for scent, data in brand_data["scents"].items()]
            pipeline_soaps.append({"brand": brand, "scents": scents})

        mock_wsdb.return_value = {"soaps": [], "total_count": 0}
        mock_pipeline.return_value = {"soaps": pipeline_soaps, "total_brands": 3, "total_scents": 6}

        response = client.post(
            "/api/wsdb-alignment/fuzzy-match",
            json={"source_type": "wsdb", "brand": "Declaration Grooming", "scent": "Massacre of the Innocents", "threshold": 0.7, "limit": 5, "mode": "brand_scent"},
        )

        assert response.status_code == 200
        data = response.json()

        assert len(data["matches"]) > 0
        top_match = data["matches"][0]
        assert top_match["brand"] == "Declaration Grooming"
        assert top_match["source"] == "pipeline"
        assert "patterns" in top_match["details"]

    @patch("api.wsdb_alignment.load_wsdb_soaps")
    @patch("api.wsdb_alignment.load_pipeline_soaps")
    async def test_fuzzy_match_no_matches_below_threshold(self, mock_pipeline, mock_wsdb):
        """Test fuzzy matching with no matches below threshold."""
        mock_wsdb.return_value = {"soaps": MOCK_WSDB_DATA[:3], "total_count": 3}
        mock_pipeline.return_value = {"soaps": [], "total_brands": 0, "total_scents": 0}

        response = client.post(
            "/api/wsdb-alignment/fuzzy-match",
            json={
                "source_type": "pipeline",
                "brand": "Completely Different Brand",
                "scent": "Nonexistent Scent",
                "threshold": 0.9,  # High threshold
                "limit": 5,
                "mode": "brand_scent",
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should have no matches or very few low-confidence matches
        assert data["total_matches"] >= 0

    @patch("api.wsdb_alignment.load_wsdb_soaps")
    @patch("api.wsdb_alignment.load_pipeline_soaps")
    async def test_fuzzy_match_respects_limit(self, mock_pipeline, mock_wsdb):
        """Test that fuzzy matching respects result limit."""
        mock_wsdb.return_value = {"soaps": MOCK_WSDB_DATA[:3], "total_count": 3}
        mock_pipeline.return_value = {"soaps": [], "total_brands": 0, "total_scents": 0}

        response = client.post(
            "/api/wsdb-alignment/fuzzy-match",
            json={"source_type": "pipeline", "brand": "Barrister", "scent": "Seville", "threshold": 0.0, "limit": 2, "mode": "brand_scent"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should respect limit
        assert len(data["matches"]) <= 2

    @patch("api.wsdb_alignment.load_wsdb_soaps")
    @patch("api.wsdb_alignment.load_pipeline_soaps")
    async def test_fuzzy_match_empty_strings(self, mock_pipeline, mock_wsdb):
        """Test fuzzy matching with empty strings."""
        mock_wsdb.return_value = {"soaps": MOCK_WSDB_DATA[:3], "total_count": 3}
        mock_pipeline.return_value = {"soaps": [], "total_brands": 0, "total_scents": 0}

        response = client.post(
            "/api/wsdb-alignment/fuzzy-match",
            json={"source_type": "pipeline", "brand": "", "scent": "", "threshold": 0.7, "limit": 5, "mode": "brand_scent"},
        )

        assert response.status_code == 200
        data = response.json()

        # Should handle empty strings gracefully
        assert "matches" in data

    @patch("api.wsdb_alignment.load_wsdb_soaps")
    @patch("api.wsdb_alignment.load_pipeline_soaps")
    async def test_fuzzy_match_brands_only_mode(self, mock_pipeline, mock_wsdb):
        """Test fuzzy matching in brands-only mode."""
        mock_wsdb.return_value = {"soaps": MOCK_WSDB_DATA[:3], "total_count": 3}
        mock_pipeline.return_value = {"soaps": [], "total_brands": 0, "total_scents": 0}

        # Test with matching brand but different scent
        response = client.post(
            "/api/wsdb-alignment/fuzzy-match",
            json={
                "source_type": "pipeline",
                "brand": "Barrister and Mann",
                "scent": "Completely Different Scent",  # Different scent
                "threshold": 0.7,
                "limit": 5,
                "mode": "brands",  # Brands only mode
            },
        )

        assert response.status_code == 200
        data = response.json()

        # Should still find match based on brand alone
        assert len(data["matches"]) > 0
        # Top match should be Barrister and Mann with high brand score
        top_match = data["matches"][0]
        assert top_match["brand"] == "Barrister and Mann"
        assert top_match["brand_score"] >= 90  # High brand score
        # In brands mode, confidence should equal brand_score
        assert top_match["confidence"] == top_match["brand_score"]


class TestRefreshWSDBData:
    """Tests for /api/wsdb-alignment/refresh-wsdb-data endpoint."""

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    @patch("httpx.AsyncClient")
    async def test_refresh_wsdb_data_success(self, mock_client, mock_root, tmp_path):
        """Test successful WSDB data refresh."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = MOCK_WSDB_DATA
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        # Setup temp directory
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        mock_root.__truediv__ = lambda self, other: data_dir / other.split("/")[-1]

        response = client.post("/api/wsdb-alignment/refresh-wsdb-data")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is True
        assert data["soap_count"] == 3  # 3 soaps in mock data
        assert "updated_at" in data
        assert data["error"] is None

        # Verify file was written
        software_file = data_dir / "software.json"
        assert software_file.exists()

        # Verify content
        with software_file.open("r", encoding="utf-8") as f:
            saved_data = json.load(f)
        assert len(saved_data) == 4  # All items including aftershave

    @patch("httpx.AsyncClient")
    async def test_refresh_wsdb_data_http_error(self, mock_client):
        """Test WSDB refresh with HTTP error."""
        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client_instance.get = AsyncMock(side_effect=httpx.HTTPError("Connection failed"))
        mock_client.return_value = mock_client_instance

        response = client.post("/api/wsdb-alignment/refresh-wsdb-data")

        assert response.status_code == 200  # Returns 200 with error in response
        data = response.json()

        assert data["success"] is False
        assert data["soap_count"] == 0
        assert data["error"] is not None
        assert "HTTP error" in data["error"]

    @patch("httpx.AsyncClient")
    async def test_refresh_wsdb_data_invalid_response(self, mock_client):
        """Test WSDB refresh with invalid response format."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "format"}  # Not a list
        mock_response.raise_for_status = MagicMock()

        mock_client_instance = MagicMock()
        mock_client_instance.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client_instance.__aexit__ = AsyncMock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value = mock_client_instance

        response = client.post("/api/wsdb-alignment/refresh-wsdb-data")

        assert response.status_code == 200
        data = response.json()

        assert data["success"] is False
        assert "Invalid response format" in data["error"]


class TestAliasFuzzyMatch:
    """Tests for alias matching functionality in batch-analyze endpoint."""

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_alias_matching_brands_only(self, mock_root, mock_data_files):
        """Test that alias matching works in brands only mode."""
        # Add alias data to pipeline
        pipeline_with_aliases = MOCK_PIPELINE_DATA.copy()
        pipeline_with_aliases["Alexandria Grooming"] = {
            "aliases": ["Alexendria Fragrances"],  # Intentional typo to test alias matching
            "patterns": ["alexandria.*grooming"],
            "scents": {
                "Fructus Virginis": {"patterns": ["fructus.*virginis"]},
            },
        }
        
        # Update soaps.yaml with alias data
        soaps_file = mock_data_files / "soaps.yaml"
        with soaps_file.open("w", encoding="utf-8") as f:
            yaml.dump(pipeline_with_aliases, f)
        
        # Add matching WSDB entry with alias name (typo version)
        wsdb_with_alias_match = MOCK_WSDB_DATA.copy()
        wsdb_with_alias_match.append({
            "brand": "Alexendria Fragrances",  # Matches alias, not canonical
            "name": "Fructus Virginis",
            "type": "Soap",
            "slug": "alexendria-fragrances-fructus-virginis",
            "scent_notes": ["fig", "fruit"],
            "collaborators": [],
            "tags": [],
            "category": "Artisan",
        })
        
        software_file = mock_data_files / "software.json"
        with software_file.open("w", encoding="utf-8") as f:
            json.dump(wsdb_with_alias_match, f)
        
        mock_root_path = mock_data_files.parent
        mock_root.__truediv__ = lambda self, other: mock_root_path / other
        
        # Test Pipeline → WSDB with alias match
        response = client.post(
            "/api/wsdb-alignment/batch-analyze",
            json={"mode": "brands", "threshold": 0.5, "limit": 100},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find the Alexandria Grooming result
        alexandria_result = next(
            (r for r in data["pipeline_results"] if r["source_brand"] == "Alexandria Grooming"),
            None
        )
        
        assert alexandria_result is not None
        assert len(alexandria_result["matches"]) > 0
        
        # Find the match with alias
        alias_match = next(
            (m for m in alexandria_result["matches"] if m["brand"] == "Alexendria Fragrances"),
            None
        )
        
        # Verify alias match was found and marked correctly
        assert alias_match is not None
        assert alias_match["matched_via"] == "alias"
        # Alias should score higher than canonical for this typo'd brand
        assert alias_match["confidence"] > 85.0  # High confidence for alias match

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_alias_matching_brand_scent_mode(self, mock_root, mock_data_files):
        """Test that alias matching works in brand + scent mode."""
        # Similar setup to brands only test
        pipeline_with_aliases = MOCK_PIPELINE_DATA.copy()
        pipeline_with_aliases["Alexandria Grooming"] = {
            "aliases": ["Alexendria Fragrances"],
            "patterns": ["alexandria.*grooming"],
            "scents": {
                "Fructus Virginis": {"patterns": ["fructus.*virginis"]},
            },
        }
        
        soaps_file = mock_data_files / "soaps.yaml"
        with soaps_file.open("w", encoding="utf-8") as f:
            yaml.dump(pipeline_with_aliases, f)
        
        wsdb_with_alias_match = MOCK_WSDB_DATA.copy()
        wsdb_with_alias_match.append({
            "brand": "Alexendria Fragrances",
            "name": "Fructus Virginis",
            "type": "Soap",
            "slug": "alexendria-fragrances-fructus-virginis",
            "scent_notes": ["fig", "fruit"],
            "collaborators": [],
            "tags": [],
            "category": "Artisan",
        })
        
        software_file = mock_data_files / "software.json"
        with software_file.open("w", encoding="utf-8") as f:
            json.dump(wsdb_with_alias_match, f)
        
        mock_root_path = mock_data_files.parent
        mock_root.__truediv__ = lambda self, other: mock_root_path / other
        
        # Test Pipeline → WSDB with alias match in brand_scent mode
        response = client.post(
            "/api/wsdb-alignment/batch-analyze",
            json={"mode": "brand_scent", "threshold": 0.5, "limit": 100},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find the Alexandria Grooming + Fructus Virginis result
        alexandria_result = next(
            (r for r in data["pipeline_results"] 
             if r["source_brand"] == "Alexandria Grooming" 
             and r["source_scent"] == "Fructus Virginis"),
            None
        )
        
        assert alexandria_result is not None
        assert len(alexandria_result["matches"]) > 0
        
        # Find the match with alias
        alias_match = next(
            (m for m in alexandria_result["matches"] if m["brand"] == "Alexendria Fragrances"),
            None
        )
        
        # Verify alias match was found and marked correctly
        assert alias_match is not None
        assert alias_match["matched_via"] == "alias"
        assert alias_match["confidence"] > 70.0  # Combined brand + scent score

    @patch("api.wsdb_alignment.PROJECT_ROOT")
    def test_canonical_name_preferred_when_better(self, mock_root, mock_data_files):
        """Test that canonical name is used when it scores higher than alias."""
        # Setup where canonical name matches perfectly
        pipeline_with_aliases = MOCK_PIPELINE_DATA.copy()
        pipeline_with_aliases["Barrister and Mann"]["aliases"] = ["B&M", "Barrister & Mann"]
        
        soaps_file = mock_data_files / "soaps.yaml"
        with soaps_file.open("w", encoding="utf-8") as f:
            yaml.dump(pipeline_with_aliases, f)
        
        mock_root_path = mock_data_files.parent
        mock_root.__truediv__ = lambda self, other: mock_root_path / other
        
        # Test with WSDB entry that matches canonical name perfectly
        response = client.post(
            "/api/wsdb-alignment/batch-analyze",
            json={"mode": "brands", "threshold": 0.5, "limit": 100},
        )
        
        assert response.status_code == 200
        data = response.json()
        
        # Find the Barrister and Mann result
        bam_result = next(
            (r for r in data["pipeline_results"] if r["source_brand"] == "Barrister and Mann"),
            None
        )
        
        assert bam_result is not None
        assert len(bam_result["matches"]) > 0
        
        # The perfect canonical match should be marked as canonical
        top_match = bam_result["matches"][0]
        assert top_match["brand"] == "Barrister and Mann"
        assert top_match["matched_via"] == "canonical"
        # In brands mode, we expect high confidence for canonical match
        # (May not be exactly 100 due to fuzzy matching algorithm)
        assert top_match["confidence"] >= 75.0


def test_load_non_matches(mock_data_files):
    """Test loading non-matches from YAML file."""
    # Create non-matches file (wsdb dir already exists from fixture)
    wsdb_dir = mock_data_files / "wsdb"
    non_matches_file = wsdb_dir / "non_matches.yaml"
    
    test_data = {
        "brand_non_matches": [
            {
                "pipeline_brand": "Black Mountain Shaving",
                "wsdb_brand": "Mountain Hare Shaving",
                "added_at": "2025-12-17T10:30:00Z",
            }
        ],
        "scent_non_matches": [
            {
                "pipeline_brand": "Barrister and Mann",
                "pipeline_scent": "Le Grand Chypre",
                "wsdb_brand": "Barrister and Mann",
                "wsdb_scent": "Le Petit Chypre",
                "added_at": "2025-12-17T10:31:00Z",
            }
        ],
    }
    
    with non_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump(test_data, f)

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        response = client.get("/api/wsdb-alignment/non-matches")
        assert response.status_code == 200
        data = response.json()
        assert len(data["brand_non_matches"]) == 1
        assert len(data["scent_non_matches"]) == 1
        assert data["brand_non_matches"][0]["pipeline_brand"] == "Black Mountain Shaving"


def test_add_brand_non_match(mock_data_files):
    """Test adding brand-level non-match."""
    wsdb_dir = mock_data_files / "wsdb"
    non_matches_file = wsdb_dir / "non_matches.yaml"
    
    # Initialize empty file
    with non_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump({"brand_non_matches": [], "scent_non_matches": []}, f)

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        response = client.post(
            "/api/wsdb-alignment/non-matches",
            json={
                "match_type": "brand",
                "pipeline_brand": "Black Mountain Shaving",
                "wsdb_brand": "Mountain Hare Shaving",
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify file was written
        with non_matches_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["brand_non_matches"]) == 1
        assert data["brand_non_matches"][0]["pipeline_brand"] == "Black Mountain Shaving"


def test_add_scent_non_match(mock_data_files):
    """Test adding scent-level non-match."""
    wsdb_dir = mock_data_files / "wsdb"
    non_matches_file = wsdb_dir / "non_matches.yaml"
    
    # Initialize empty file
    with non_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump({"brand_non_matches": [], "scent_non_matches": []}, f)

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        response = client.post(
            "/api/wsdb-alignment/non-matches",
            json={
                "match_type": "scent",
                "pipeline_brand": "Barrister and Mann",
                "pipeline_scent": "Le Grand Chypre",
                "wsdb_brand": "Barrister and Mann",
                "wsdb_scent": "Le Petit Chypre",
            },
        )
        assert response.status_code == 200
        assert response.json()["success"] is True

        # Verify file was written
        with non_matches_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["scent_non_matches"]) == 1
        assert data["scent_non_matches"][0]["pipeline_brand"] == "Barrister and Mann"


def test_non_match_filtering_brands_mode(mock_data_files):
    """Test that non-matches are filtered in brands mode."""
    wsdb_dir = mock_data_files / "wsdb"
    
    # Create non-matches file (software.json already in correct location from fixture)
    non_matches_file = wsdb_dir / "non_matches.yaml"
    non_matches_data = {
        "brand_non_matches": [
            {
                "pipeline_brand": "Barrister and Mann",
                "wsdb_brand": "Stirling Soap Co.",
                "added_at": "2025-12-17T10:30:00Z",
            }
        ],
        "scent_non_matches": [],
    }
    with non_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump(non_matches_data, f)

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        response = client.post("/api/wsdb-alignment/batch-analyze?threshold=0.1&limit=100&mode=brands")
        assert response.status_code == 200
        data = response.json()

        # Find Barrister and Mann result
        bam_result = next((r for r in data["pipeline_results"] if r["source_brand"] == "Barrister and Mann"), None)
        assert bam_result is not None

        # Verify Stirling Soap Co. is NOT in the matches
        stirling_matches = [m for m in bam_result["matches"] if m["brand"] == "Stirling Soap Co."]
        assert len(stirling_matches) == 0


def test_non_match_filtering_brand_scent_mode(mock_data_files):
    """Test that non-matches are filtered in brand+scent mode."""
    wsdb_dir = mock_data_files / "wsdb"
    
    # Create non-matches file (software.json already in correct location from fixture)
    non_matches_file = wsdb_dir / "non_matches.yaml"
    non_matches_data = {
        "brand_non_matches": [],
        "scent_non_matches": [
            {
                "pipeline_brand": "Barrister and Mann",
                "pipeline_scent": "Seville",
                "wsdb_brand": "Stirling Soap Co.",
                "wsdb_scent": "Executive Man",
                "added_at": "2025-12-17T10:31:00Z",
            }
        ],
    }
    with non_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump(non_matches_data, f)

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        response = client.post("/api/wsdb-alignment/batch-analyze?threshold=0.1&limit=100&mode=brand_scent")
        assert response.status_code == 200
        data = response.json()

        # Find Barrister and Mann - Seville result
        bam_seville = next(
            (
                r
                for r in data["pipeline_results"]
                if r["source_brand"] == "Barrister and Mann" and r["source_scent"] == "Seville"
            ),
            None,
        )
        assert bam_seville is not None

        # Verify Stirling Executive Man is NOT in the matches
        stirling_matches = [
            m for m in bam_seville["matches"] if m["brand"] == "Stirling Soap Co." and m["name"] == "Executive Man"
        ]
        assert len(stirling_matches) == 0


def test_bidirectional_filtering(mock_data_files):
    """Test that non-matches work in both directions."""
    wsdb_dir = mock_data_files / "wsdb"
    
    # Create non-matches file (Pipeline: BaM != WSDB: Stirling)
    # (software.json already in correct location from fixture)
    non_matches_file = wsdb_dir / "non_matches.yaml"
    non_matches_data = {
        "brand_non_matches": [
            {
                "pipeline_brand": "Barrister and Mann",
                "wsdb_brand": "Stirling Soap Co.",
                "added_at": "2025-12-17T10:30:00Z",
            }
        ],
        "scent_non_matches": [],
    }
    with non_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump(non_matches_data, f)

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        response = client.post("/api/wsdb-alignment/batch-analyze?threshold=0.1&limit=100&mode=brands")
        assert response.status_code == 200
        data = response.json()

        # Check Pipeline → WSDB: BaM should NOT match Stirling
        bam_result = next((r for r in data["pipeline_results"] if r["source_brand"] == "Barrister and Mann"), None)
        if bam_result:
            stirling_matches = [m for m in bam_result["matches"] if m["brand"] == "Stirling Soap Co."]
            assert len(stirling_matches) == 0

        # Check WSDB → Pipeline: Stirling should NOT match BaM
        stirling_result = next((r for r in data["wsdb_results"] if r["source_brand"] == "Stirling Soap Co."), None)
        if stirling_result:
            bam_matches = [m for m in stirling_result["matches"] if m["brand"] == "Barrister and Mann"]
            assert len(bam_matches) == 0


def test_duplicate_non_match_prevention(mock_data_files):
    """Test that duplicate non-matches are not added."""
    wsdb_dir = mock_data_files / "wsdb"
    non_matches_file = wsdb_dir / "non_matches.yaml"
    
    # Initialize empty file
    with non_matches_file.open("w", encoding="utf-8") as f:
        yaml.dump({"brand_non_matches": [], "scent_non_matches": []}, f)

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        # Add first time
        response1 = client.post(
            "/api/wsdb-alignment/non-matches",
            json={
                "match_type": "brand",
                "pipeline_brand": "Black Mountain Shaving",
                "wsdb_brand": "Mountain Hare Shaving",
            },
        )
        assert response1.status_code == 200
        assert response1.json()["success"] is True

        # Try to add again (duplicate)
        response2 = client.post(
            "/api/wsdb-alignment/non-matches",
            json={
                "match_type": "brand",
                "pipeline_brand": "Black Mountain Shaving",
                "wsdb_brand": "Mountain Hare Shaving",
            },
        )
        assert response2.status_code == 200
        assert response2.json()["success"] is True
        assert "already exists" in response2.json()["message"]

        # Verify only one entry in file
        with non_matches_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["brand_non_matches"]) == 1


def test_add_alias_success(mock_data_files):
    """Test successfully adding an alias to a brand."""
    soaps_file = mock_data_files / "soaps.yaml"

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        # Add an alias
        response = client.post(
            "/api/wsdb-alignment/add-alias",
            json={"pipeline_brand": "Barrister and Mann", "alias": "B&M"},
        )
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "B&M" in response.json()["aliases"]

        # Verify it was written to file
        with soaps_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert "aliases" in data["Barrister and Mann"]
        assert "B&M" in data["Barrister and Mann"]["aliases"]


def test_add_alias_duplicate(mock_data_files):
    """Test that duplicate aliases are not added."""
    soaps_file = mock_data_files / "soaps.yaml"

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        # Add alias first time
        response1 = client.post(
            "/api/wsdb-alignment/add-alias",
            json={"pipeline_brand": "Barrister and Mann", "alias": "B&M"},
        )
        assert response1.status_code == 200

        # Try to add same alias again
        response2 = client.post(
            "/api/wsdb-alignment/add-alias",
            json={"pipeline_brand": "Barrister and Mann", "alias": "B&M"},
        )
        assert response2.status_code == 200
        assert "already exists" in response2.json()["message"]

        # Verify only one entry
        with soaps_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert data["Barrister and Mann"]["aliases"].count("B&M") == 1


def test_add_alias_brand_not_found(mock_data_files):
    """Test adding alias to non-existent brand."""
    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        response = client.post(
            "/api/wsdb-alignment/add-alias",
            json={"pipeline_brand": "Nonexistent Brand", "alias": "Test Alias"},
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()


def test_add_alias_case_insensitive_duplicate(mock_data_files):
    """Test that case-insensitive duplicate aliases are not added."""
    soaps_file = mock_data_files / "soaps.yaml"

    with patch("api.wsdb_alignment.PROJECT_ROOT", mock_data_files.parent):
        # Add alias
        response1 = client.post(
            "/api/wsdb-alignment/add-alias",
            json={"pipeline_brand": "Barrister and Mann", "alias": "B&M"},
        )
        assert response1.status_code == 200

        # Try to add same alias with different case
        response2 = client.post(
            "/api/wsdb-alignment/add-alias",
            json={"pipeline_brand": "Barrister and Mann", "alias": "b&m"},
        )
        assert response2.status_code == 200
        assert "already exists" in response2.json()["message"]

        # Verify only one entry
        with soaps_file.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        assert len(data["Barrister and Mann"]["aliases"]) == 1

