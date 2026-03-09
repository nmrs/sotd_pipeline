"""Validation router — endpoints for reviewing agent validation output.

Serves verified matches and catalog change proposals produced by the
match validation agent, and handles accept/reject actions from the WebUI.
"""

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .catalog_updater import CatalogUpdater
from .queue_manager import QueueManager

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Module-level state (configured at startup via configure())
# ---------------------------------------------------------------------------
_data_dir: Optional[Path] = None
_catalog_updater: Optional[CatalogUpdater] = None

VALID_FIELDS = {"razor", "blade", "brush", "soap"}
MONTH_RE = re.compile(r"^\d{4}-\d{2}$")


def configure(data_dir: Path) -> None:
    """Set the data directory. Called from main.py during startup."""
    global _data_dir, _catalog_updater
    _data_dir = Path(data_dir)
    _catalog_updater = CatalogUpdater(_data_dir)
    logger.info(f"Validation router configured with data_dir={_data_dir}")


def _get_data_dir() -> Path:
    if _data_dir is None:
        raise RuntimeError("Validation router not configured — call configure() first")
    return _data_dir


def _get_catalog_updater() -> CatalogUpdater:
    if _catalog_updater is None:
        raise RuntimeError("Validation router not configured — call configure() first")
    return _catalog_updater


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------
class AcceptProposalRequest(BaseModel):
    month: str = Field(..., description="Month in YYYY-MM format")
    proposal_index: int = Field(..., ge=0, description="Index of the proposal in the file")
    edited_proposal: Optional[Dict[str, Any]] = Field(
        default=None, description="Optionally edited proposal to apply instead of the original"
    )


class RejectProposalRequest(BaseModel):
    month: str = Field(..., description="Month in YYYY-MM format")
    proposal_index: int = Field(..., ge=0, description="Index of the proposal in the file")
    reason: Optional[str] = Field(default=None, description="Optional rejection reason")


class BulkApproveRequest(BaseModel):
    field: str = Field(..., description="Field type (razor, blade, brush, soap)")
    matches: List[Dict[str, Any]] = Field(
        ..., description="List of matches with original and matched data"
    )


class ActionResponse(BaseModel):
    success: bool
    message: str
    operation_id: Optional[str] = None
    status_url: Optional[str] = None


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------
router = APIRouter(prefix="/api/validation", tags=["validation"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _load_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_json(path: Path, data: Any) -> None:
    tmp = path.with_suffix(".tmp")
    try:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        tmp.replace(path)
    except Exception:
        if tmp.exists():
            tmp.unlink()
        raise


def _collect_months(data_dir: Path) -> List[str]:
    """Gather unique YYYY-MM values from verified/ and proposed/ directories."""
    months: set[str] = set()
    for subdir in ("verified", "proposed"):
        d = data_dir / subdir
        if d.is_dir():
            for f in d.glob("*.json"):
                stem = f.stem
                if MONTH_RE.match(stem):
                    months.add(stem)
    return sorted(months, reverse=True)


# ---------------------------------------------------------------------------
# GET endpoints
# ---------------------------------------------------------------------------
@router.get("/verified/{month}")
async def get_verified(month: str):
    """Load verified matches for a given month."""
    data_dir = _get_data_dir()
    path = data_dir / "verified" / f"{month}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Verified file not found for {month}")
    return _load_json(path)


@router.get("/proposed/{month}")
async def get_proposed(month: str):
    """Load proposed catalog changes for a given month."""
    data_dir = _get_data_dir()
    path = data_dir / "proposed" / f"{month}.json"
    if not path.exists():
        raise HTTPException(status_code=404, detail=f"Proposed file not found for {month}")
    return _load_json(path)


@router.get("/months")
async def get_months():
    """List months that have agent validation data."""
    data_dir = _get_data_dir()
    return {"months": _collect_months(data_dir)}


# ---------------------------------------------------------------------------
# POST endpoints
# ---------------------------------------------------------------------------
@router.post("/accept-proposal", response_model=ActionResponse)
async def accept_proposal(request: AcceptProposalRequest):
    """Accept a proposal — apply it to the catalog via CatalogUpdater."""
    data_dir = _get_data_dir()
    updater = _get_catalog_updater()

    # Load proposed file
    proposed_path = data_dir / "proposed" / f"{request.month}.json"
    if not proposed_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Proposed file not found for {request.month}"
        )

    proposals = _load_json(proposed_path)

    if request.proposal_index >= len(proposals):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid proposal_index {request.proposal_index} — file has {len(proposals)} proposals",
        )

    proposal = proposals[request.proposal_index]

    # Check if already actioned
    if proposal.get("_status") in ("accepted", "rejected"):
        raise HTTPException(
            status_code=409,
            detail=f"Proposal {request.proposal_index} is already {proposal['_status']}",
        )

    # Determine which proposal to apply
    apply_proposal = request.edited_proposal if request.edited_proposal is not None else proposal

    # Apply to catalog
    try:
        updater.apply_proposal(apply_proposal)
    except Exception as e:
        logger.error(f"Failed to apply proposal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to apply proposal: {e}")

    # Mark as accepted in the proposed file
    proposals[request.proposal_index]["_status"] = "accepted"
    proposals[request.proposal_index]["_accepted_at"] = datetime.now(timezone.utc).isoformat()
    _save_json(proposed_path, proposals)

    return ActionResponse(success=True, message="Proposal accepted and applied to catalog")


@router.post("/reject-proposal", response_model=ActionResponse)
async def reject_proposal(request: RejectProposalRequest):
    """Reject a proposal — record to rejections file and mark in proposed file."""
    data_dir = _get_data_dir()

    # Load proposed file
    proposed_path = data_dir / "proposed" / f"{request.month}.json"
    if not proposed_path.exists():
        raise HTTPException(
            status_code=404, detail=f"Proposed file not found for {request.month}"
        )

    proposals = _load_json(proposed_path)

    if request.proposal_index >= len(proposals):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid proposal_index {request.proposal_index} — file has {len(proposals)} proposals",
        )

    proposal = proposals[request.proposal_index]

    # Check if already actioned
    if proposal.get("_status") in ("accepted", "rejected"):
        raise HTTPException(
            status_code=409,
            detail=f"Proposal {request.proposal_index} is already {proposal['_status']}",
        )

    now = datetime.now(timezone.utc).isoformat()

    # Append to rejections file
    rejections_path = data_dir / "validation" / "rejections.json"
    rejections_path.parent.mkdir(parents=True, exist_ok=True)

    if rejections_path.exists():
        rejections = _load_json(rejections_path)
    else:
        rejections = []

    rejection_record = {
        "month": request.month,
        "proposal_index": request.proposal_index,
        "proposal": proposal,
        "reason": request.reason,
        "rejected_at": now,
    }
    rejections.append(rejection_record)
    _save_json(rejections_path, rejections)

    # Mark as rejected in the proposed file
    proposals[request.proposal_index]["_status"] = "rejected"
    proposals[request.proposal_index]["_rejected_at"] = now
    _save_json(proposed_path, proposals)

    return ActionResponse(success=True, message="Proposal rejected")


@router.post("/bulk-approve", response_model=ActionResponse)
async def bulk_approve(request: BulkApproveRequest):
    """Bulk approve verified matches — delegates to QueueManager for correct_matches writes."""
    if request.field not in VALID_FIELDS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid field '{request.field}'. Must be one of: {', '.join(sorted(VALID_FIELDS))}",
        )

    if not request.matches:
        raise HTTPException(status_code=400, detail="No matches provided")

    data_dir = _get_data_dir()

    correct_matches_path = data_dir / "correct_matches"
    queue_manager = QueueManager(correct_matches_path)

    try:
        operation_id = queue_manager.add_operation(
            "mark_correct", request.field, request.matches
        )
        status_url = f"/api/analysis/operation-status/{operation_id}"

        return ActionResponse(
            success=True,
            message="Bulk approve operation queued",
            operation_id=operation_id,
            status_url=status_url,
        )
    except Exception as e:
        logger.error(f"Failed to queue bulk-approve operation: {e}", exc_info=True)
        raise HTTPException(
            status_code=500, detail=f"Failed to queue operation: {e}"
        )
