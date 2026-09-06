"""API endpoints for extract phase field overrides."""

from __future__ import annotations

import logging
import os
import sys
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from sotd.extract.override_manager import OverrideManager  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/extract-overrides", tags=["extract-overrides"])


def _override_file_path() -> Path:
    sotd_data_dir = os.environ.get("SOTD_DATA_DIR")
    if sotd_data_dir:
        return Path(sotd_data_dir) / "extract_overrides.yaml"
    return project_root / "data" / "extract_overrides.yaml"


class ExtractOverrideResponse(BaseModel):
    success: bool
    message: str
    month: str
    comment_id: str
    fields: Dict[str, str] = Field(default_factory=dict)


class ExtractOverrideUpdateRequest(BaseModel):
    """All four product keys; string upserts, null/empty deletes."""

    razor: Optional[str] = None
    blade: Optional[str] = None
    brush: Optional[str] = None
    soap: Optional[str] = None


@router.get("/{month}/{comment_id}", response_model=ExtractOverrideResponse)
async def get_extract_overrides(month: str, comment_id: str) -> ExtractOverrideResponse:
    """Get extract overrides for a comment."""
    try:
        manager = OverrideManager(_override_file_path())
        manager.load_overrides()
        fields = manager.get_comment_overrides(month, comment_id)
        return ExtractOverrideResponse(
            success=True,
            message="Extract overrides retrieved",
            month=month,
            comment_id=comment_id,
            fields=fields,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error getting extract overrides: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.put("/{month}/{comment_id}", response_model=ExtractOverrideResponse)
async def put_extract_overrides(
    month: str, comment_id: str, body: ExtractOverrideUpdateRequest
) -> ExtractOverrideResponse:
    """Upsert/delete extract overrides for a comment (YAML only; no pipeline run).

    Only fields present in the JSON body are applied. A string upserts; null or
    "" deletes that field. Omitted fields are left unchanged.
    """
    try:
        updates: Dict[str, Optional[str]] = {}
        for field in ("razor", "blade", "brush", "soap"):
            if field in body.model_fields_set:
                updates[field] = getattr(body, field)

        if not updates:
            raise HTTPException(
                status_code=400, detail="At least one of razor, blade, brush, soap must be provided"
            )

        manager = OverrideManager(_override_file_path())
        # Preserve fields not in this request
        manager.load_overrides()
        current = manager.get_comment_overrides(month, comment_id)
        merged: Dict[str, Optional[str]] = {
            "razor": current.get("razor"),
            "blade": current.get("blade"),
            "brush": current.get("brush"),
            "soap": current.get("soap"),
        }
        merged.update(updates)

        fields = manager.update_comment_overrides(month, comment_id, merged)
        return ExtractOverrideResponse(
            success=True,
            message=(
                "Extract overrides saved. Re-run extract→match→enrich with --force "
                f"for {month} to apply."
            ),
            month=month,
            comment_id=comment_id,
            fields=fields,
        )
    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    except Exception as e:
        logger.error("Error saving extract overrides: %s", e)
        raise HTTPException(status_code=500, detail=str(e)) from e
