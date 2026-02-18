"""
API for v2 brush-match operator review (Phase 2).

Endpoints:
- GET /brush-match/runs — list available run IDs
- GET /brush-match/queue — list entries needing review (by run_id, status, limit)
- GET /brush-match/entry/{entry_id} — get one entry (entry_id = base64url(norm))
- POST /brush-match/entry/{entry_id}/decision — accept/override and persist to correct_matches + gold
"""

import base64
import logging
import os
import sys
from pathlib import Path

# Add project root so brushmatch and sotd can be imported when running from webui/
_project_root = Path(__file__).resolve().parents[2]
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

from typing import Any, Optional  # noqa: E402

from fastapi import APIRouter, HTTPException  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/brush-match", tags=["brush-match", "v2"])


def _get_data_root() -> Path:
    """Data root (project data/ or SOTD_DATA_DIR)."""
    env = os.environ.get("SOTD_DATA_DIR")
    if env:
        return Path(env)
    return Path(__file__).resolve().parents[2] / "data"


def _runs_base() -> Path:
    return _get_data_root() / "brushmatch" / "runs"


def _gold_dir() -> Path:
    return _get_data_root() / "brushmatch" / "gold"


def _entry_id_encode(norm: str) -> str:
    """Encode normalized string as URL-safe path segment."""
    return base64.urlsafe_b64encode(norm.encode("utf-8")).decode("ascii").rstrip("=")


def _entry_id_decode(entry_id: str) -> str:
    """Decode entry_id back to normalized string."""
    pad = 4 - (len(entry_id) % 4)
    if pad != 4:
        entry_id += "=" * pad
    return base64.urlsafe_b64decode(entry_id.encode("ascii")).decode("utf-8")


# --- Response/request models ---


class RunInfo(BaseModel):
    run_id: str
    path: str


class QueueItem(BaseModel):
    entry_id: str
    raw: str
    norm: str
    decision_type: str


class QueueResponse(BaseModel):
    run_id: str
    status: str
    items: list[QueueItem]
    total: int


class DecisionAcceptRequest(BaseModel):
    """Payload for accepting a match (complete or composite)."""

    kind_override: Optional[str] = Field(None, description="complete|composite|unknown")
    span_override: Optional[list[int]] = Field(
        None, description="[knot_start, knot_end] token indices"
    )
    selection: dict[str, Any] = Field(
        ...,
        description="Either { brush: { brand, model } } or { handle: { brand, model }, knot: { brand, model } }",
    )


class DecisionResponse(BaseModel):
    success: bool
    message: str


# --- Endpoints ---


@router.get("/runs", response_model=list[RunInfo])
async def list_runs() -> list[RunInfo]:
    """List available v2 run IDs (from data/brushmatch/runs/)."""
    base = _runs_base()
    if not base.exists():
        return []
    out: list[RunInfo] = []
    for p in sorted(base.iterdir()):
        if p.is_dir() and (p / "entries.json").exists():
            out.append(RunInfo(run_id=p.name, path=str(p)))
    return out


@router.get("/queue", response_model=QueueResponse)
async def get_queue(
    run_id: str,
    status: str = "needs_review",
    limit: int = 100,
) -> QueueResponse:
    """List entries in the run that match the given status (e.g. needs_review)."""
    try:
        from brushmatch.persist import load_entries
    except ImportError:
        raise HTTPException(status_code=500, detail="brushmatch package not available")
    base = _runs_base()
    if not base.exists():
        return QueueResponse(run_id=run_id, status=status, items=[], total=0)
    entries = load_entries(run_id, runs_base=_runs_base())
    if not entries:
        return QueueResponse(run_id=run_id, status=status, items=[], total=0)
    items: list[QueueItem] = []
    for norm, data in entries.items():
        if not isinstance(data, dict):
            continue
        dec = data.get("decision") or {}
        if not isinstance(dec, dict):
            continue
        if dec.get("decision_type") != status:
            continue
        raw = data.get("raw") or norm
        items.append(
            QueueItem(
                entry_id=_entry_id_encode(norm),
                raw=raw,
                norm=norm,
                decision_type=status,
            )
        )
        if len(items) >= limit:
            break
    return QueueResponse(run_id=run_id, status=status, items=items, total=len(items))


@router.get("/entry/{entry_id}")
async def get_entry(entry_id: str) -> dict[str, Any]:
    """Get full entry by id (entry_id is base64url-encoded normalized string)."""
    try:
        norm = _entry_id_decode(entry_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid entry_id: {e}") from e
    # We don't know run_id from entry_id; caller must have it. Load from first run that contains it.
    base = _runs_base()
    if not base.exists():
        raise HTTPException(status_code=404, detail="No runs found")
    try:
        from brushmatch.persist import load_entries
    except ImportError:
        raise HTTPException(status_code=500, detail="brushmatch package not available")
    for run_path in sorted(base.iterdir(), reverse=True):
        if not run_path.is_dir():
            continue
        entries = load_entries(run_path.name, runs_base=base)
        if norm in entries:
            return {"run_id": run_path.name, "entry_id": entry_id, **entries[norm]}
    raise HTTPException(status_code=404, detail="Entry not found")


@router.post("/entry/{entry_id}/decision", response_model=DecisionResponse)
async def submit_decision(entry_id: str, body: DecisionAcceptRequest) -> DecisionResponse:
    """Accept match: write to correct_matches (v1 schema) and gold kind/segmentation."""
    try:
        norm = _entry_id_decode(entry_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid entry_id: {e}") from e
    data_root = _get_data_root()
    runs_base = data_root / "brushmatch" / "runs"
    try:
        from brushmatch.persist import load_entries, save_gold_kind, save_gold_segmentation
    except ImportError:
        raise HTTPException(status_code=500, detail="brushmatch package not available")
    # Load entry to get run_id and current kind/segmentation
    entries = {}
    run_id: Optional[str] = None
    for rp in sorted((runs_base).iterdir(), reverse=True):
        if not rp.is_dir():
            continue
        entries = load_entries(rp.name, runs_base=runs_base)
        if norm in entries:
            run_id = rp.name
            break
    if not run_id or norm not in entries:
        raise HTTPException(status_code=404, detail="Entry not found")
    entry_data = entries[norm]
    raw = entry_data.get("raw") or norm
    correct_matches_path = data_root / "correct_matches"
    gold_dir = _gold_dir()
    # Build match_data for CorrectMatchesManager (v1 schema)
    selection = body.selection
    if "brush" in selection:
        b = selection["brush"]
        match_data = {
            "original": raw,
            "matched": {"brand": b.get("brand"), "model": b.get("model")},
            "field": "brush",
        }
    elif "handle" in selection and "knot" in selection:
        h = selection["handle"]
        k = selection["knot"]
        match_data = {
            "original": raw,
            "matched": {
                "brand": None,
                "model": None,
                "handle": {"brand": h.get("brand"), "model": h.get("model")},
                "knot": {"brand": k.get("brand"), "model": k.get("model")},
            },
            "field": "brush",
        }
    else:
        raise HTTPException(
            status_code=400,
            detail="selection must contain 'brush' or both 'handle' and 'knot'",
        )
    from rich.console import Console

    from sotd.match.tools.managers.correct_matches_manager import CorrectMatchesManager

    console = Console()
    manager = CorrectMatchesManager(console, correct_matches_path)
    match_key = manager.create_match_key("brush", raw, match_data["matched"])
    manager.mark_match_as_correct(match_key, match_data)
    manager.save_correct_matches()
    # Gold labels (FR-33)
    kind_label = body.kind_override
    if not kind_label:
        kr = entry_data.get("kind_result") or {}
        kind_label = kr.get("kind_pred") or "unknown"
    save_gold_kind({norm: kind_label}, gold_dir)
    if body.span_override or (entry_data.get("segmentation_result") and kind_label == "composite"):
        seg = entry_data.get("segmentation_result") or {}
        knot_span = body.span_override or seg.get("knot_span") or [0, 0]
        handle_chunk = seg.get("handle_chunk") or ""
        knot_chunk = seg.get("knot_chunk") or ""
        save_gold_segmentation(
            {
                norm: {
                    "knot_span": knot_span,
                    "handle_chunk": handle_chunk,
                    "knot_chunk": knot_chunk,
                }
            },
            gold_dir,
        )
    logger.info("Brush match accepted: norm=%s, run_id=%s", norm[:50], run_id)
    return DecisionResponse(success=True, message="Accepted and saved to correct_matches and gold.")
