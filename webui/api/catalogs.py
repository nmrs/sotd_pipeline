#!/usr/bin/env python3
"""Catalog integration for SOTD pipeline analyzer API."""

import logging
from pathlib import Path
from typing import Dict, List, Any

import yaml
from fastapi import APIRouter, HTTPException

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/catalogs", tags=["catalogs"])

# Supported catalog fields and their YAML files
CATALOG_FILES = {
    "razor": "razors.yaml",
    "blade": "blades.yaml",
    "brush": "brushes.yaml",
    "soap": "soaps.yaml",
    "handle": "handles.yaml",
    "knot": "knots.yaml",
}

CATALOG_DIR = Path(__file__).parent.parent.parent / "data"


def get_catalog_path(field: str) -> Path:
    """Get the path to the catalog YAML file for a field."""
    if field not in CATALOG_FILES:
        raise HTTPException(status_code=404, detail=f"Unknown catalog field: {field}")
    return CATALOG_DIR / CATALOG_FILES[field]


def load_yaml_file(path: Path) -> Any:
    """Load YAML file safely."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        logger.error(f"Catalog file not found: {path}")
        raise HTTPException(status_code=404, detail=f"Catalog file not found: {path.name}")
    except yaml.YAMLError as e:
        logger.error(f"Invalid YAML in {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Invalid YAML in {path.name}: {e}")
    except Exception as e:
        logger.error(f"Error loading YAML file {path}: {e}")
        raise HTTPException(status_code=500, detail=f"Error loading YAML file: {e}")


@router.get("/", response_model=List[str])
async def list_catalogs() -> List[str]:
    """List available catalog fields."""
    available = []
    for field, filename in CATALOG_FILES.items():
        if (CATALOG_DIR / filename).exists():
            available.append(field)
    return available


@router.get("/{field}")
async def get_catalog(field: str) -> Dict[str, Any]:
    """Get catalog data for a specific field."""
    path = get_catalog_path(field)
    data = load_yaml_file(path)
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=500,
            detail=f"Catalog file {path.name} does not contain a dictionary at the top level.",
        )
    return data
