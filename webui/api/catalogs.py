#!/usr/bin/env python3
"""Catalog integration for SOTD pipeline analyzer API."""

import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

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

# Support SOTD_DATA_DIR environment variable for containerized deployments
SOTD_DATA_DIR = os.environ.get("SOTD_DATA_DIR")
if SOTD_DATA_DIR:
    CATALOG_DIR = Path(SOTD_DATA_DIR)
else:
    # Fallback to relative path for development
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


@router.get("/")
async def list_catalogs() -> Dict[str, List[Dict[str, Any]]]:
    """List available catalog fields with metadata."""
    catalogs = []
    for field, filename in CATALOG_FILES.items():
        file_path = CATALOG_DIR / filename
        if file_path.exists():
            try:
                stat = file_path.stat()
                catalogs.append(
                    {
                        "name": field,
                        "path": str(file_path),
                        "size": stat.st_size,
                        "last_modified": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    }
                )
            except Exception as e:
                logger.error(f"Error getting stats for {file_path}: {e}")
                # Still include the catalog even if we can't get stats
                catalogs.append(
                    {
                        "name": field,
                        "path": str(file_path),
                        "size": 0,
                        "last_modified": "",
                    }
                )

    return {"catalogs": catalogs}


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
