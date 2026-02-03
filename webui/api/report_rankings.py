#!/usr/bin/env python3
"""Report rankings API: placement over time for aggregation table rows."""

import logging
import os
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

# Add project root for sotd imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from sotd.report.load import load_aggregated_data  # noqa: E402
from sotd.report.table_generators.table_generator import TableGenerator  # noqa: E402

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/report-rankings", tags=["report-rankings"])


class MonthsResponse(BaseModel):
    """Available months with aggregated data."""

    months: List[str]


class TableInfo(BaseModel):
    """One aggregation table."""

    id: str
    label: str


class TablesResponse(BaseModel):
    """List of aggregation tables."""

    tables: List[TableInfo]


class ItemsResponse(BaseModel):
    """Item names for a table (row labels)."""

    items: List[str]


class SeriesPoint(BaseModel):
    """One month's rank/shaves for an item."""

    month: str
    rank: Optional[int] = None
    shaves: Optional[int] = None


class SeriesEntry(BaseModel):
    """Time series for one item."""

    item: str
    data: List[SeriesPoint]


class SeriesResponse(BaseModel):
    """Rank-over-time series for requested items."""

    months: List[str]
    series: List[SeriesEntry]


def _get_aggregated_dir() -> Path:
    """Return path to data/aggregated directory."""
    env_dir = os.environ.get("SOTD_DATA_DIR")
    if env_dir:
        return Path(env_dir) / "aggregated"
    return project_root / "data" / "aggregated"


def _humanize(key: str) -> str:
    """Convert snake_case key to title label (e.g. razor_manufacturers -> Razor manufacturers)."""
    return key.replace("_", " ").title()


def _get_available_months(aggregated_dir: Path) -> List[str]:
    """List month stems (YYYY-MM) from aggregated JSON files, sorted."""
    if not aggregated_dir.exists():
        return []
    months = []
    for f in aggregated_dir.glob("*.json"):
        if f.stem and f.stat().st_size > 0:
            # Validate YYYY-MM
            if re.match(r"^\d{4}-\d{2}$", f.stem):
                months.append(f.stem)
    months.sort()
    return months


def _get_tables_from_data(data: Dict[str, Any]) -> List[TableInfo]:
    """Build table list from aggregated data: every key whose value is a list of objects."""
    tables = []
    for key, value in data.items():
        if isinstance(value, list) and len(value) > 0 and isinstance(value[0], dict):
            tables.append(TableInfo(id=key, label=_humanize(key)))
    tables.sort(key=lambda t: t.label)
    return tables


def _identifier_column(row: Dict[str, Any]) -> Optional[str]:
    """Return the key in row that holds the item display name (case-insensitive match)."""
    skip = {"rank", "position", "shaves", "unique_users", "unique users"}
    for k, v in row.items():
        k_lower = k.lower().replace(" ", "_")
        if k_lower in skip or (isinstance(v, (int, float)) and k_lower != "rank"):
            continue
        if isinstance(v, str) and v.strip():
            return k
    return None


def _row_display_name(row: Dict[str, Any]) -> Optional[str]:
    """Get the display name for a row (for matching and items list)."""
    # Prefer "name" (any case)
    for key in ("name", "Name", "User", "user"):
        if key in row and isinstance(row[key], str):
            return row[key].strip() or None
    col = _identifier_column(row)
    if col and col in row:
        return str(row[col]).strip() or None
    return None


def _normalize_name(s: str) -> str:
    """Normalize for matching: lowercase, collapse whitespace."""
    return " ".join(s.lower().split())


@router.get("/months", response_model=MonthsResponse)
async def get_months() -> MonthsResponse:
    """List available months with aggregated data."""
    aggregated_dir = _get_aggregated_dir()
    months = _get_available_months(aggregated_dir)
    return MonthsResponse(months=months)


@router.get("/tables", response_model=TablesResponse)
async def get_tables() -> TablesResponse:
    """List all aggregation tables from the latest available month."""
    aggregated_dir = _get_aggregated_dir()
    months = _get_available_months(aggregated_dir)
    if not months:
        return TablesResponse(tables=[])

    latest = months[-1]
    file_path = aggregated_dir / f"{latest}.json"
    if not file_path.exists():
        return TablesResponse(tables=[])

    try:
        _, data = load_aggregated_data(file_path, debug=False)
        tables = _get_tables_from_data(data)
        return TablesResponse(tables=tables)
    except Exception as e:
        logger.warning(f"Failed to load aggregated data for tables: {e}")
        raise HTTPException(status_code=500, detail=str(e)) from e


@router.get("/items", response_model=ItemsResponse)
async def get_items(
    table: str = Query(..., description="Table id (snake_case)"),
    month: Optional[str] = Query(None, description="Month YYYY-MM; default latest"),
) -> ItemsResponse:
    """List item names (row labels) for a table, from a given month."""
    aggregated_dir = _get_aggregated_dir()
    months = _get_available_months(aggregated_dir)
    if not months:
        return ItemsResponse(items=[])

    use_month = month if month and month in months else months[-1]
    file_path = aggregated_dir / f"{use_month}.json"
    if not file_path.exists():
        return ItemsResponse(items=[])

    try:
        _, data = load_aggregated_data(file_path, debug=False)
        generator = TableGenerator(data, comparison_data={}, current_month=use_month)
        # TableGenerator accepts kebab or snake; data keys are snake_case
        table_name = table.replace("_", "-") if "_" in table else table
        rows = generator.get_structured_table_data(table_name, deltas=False)
    except Exception as e:
        logger.warning(f"Failed to get items for table {table}: {e}")
        raise HTTPException(status_code=400, detail=str(e)) from e

    names: List[str] = []
    seen: set = set()
    for row in rows:
        name = _row_display_name(row)
        if name and _normalize_name(name) not in seen:
            seen.add(_normalize_name(name))
            names.append(name)
    return ItemsResponse(items=names)


@router.get("/series", response_model=SeriesResponse)
async def get_series(
    table: str = Query(..., description="Table id (snake_case or kebab-case)"),
    items: str = Query(..., description="Comma-separated item names to track (URL-encoded)"),
) -> SeriesResponse:
    """Get rank and shaves over time for the given table and items."""
    aggregated_dir = _get_aggregated_dir()
    months = _get_available_months(aggregated_dir)
    if not months:
        return SeriesResponse(months=[], series=[])

    item_list = [unquote(s).strip() for s in items.split(",") if s.strip()]
    if not item_list:
        raise HTTPException(status_code=400, detail="At least one item is required")

    table_name = table.replace("_", "-") if "_" in table else table
    wanted = {_normalize_name(i): i for i in item_list}  # normalized -> original

    series_by_item: Dict[str, List[Dict[str, Any]]] = {orig: [] for orig in item_list}
    valid_months: List[str] = []

    for month_str in months:
        file_path = aggregated_dir / f"{month_str}.json"
        if not file_path.exists():
            continue
        try:
            _, data = load_aggregated_data(file_path, debug=False)
            generator = TableGenerator(data, comparison_data={}, current_month=month_str)
            rows = generator.get_structured_table_data(table_name, deltas=False)
        except Exception as e:
            logger.debug(f"Skip month {month_str}: {e}")
            continue

        valid_months.append(month_str)
        by_name: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            name = _row_display_name(row)
            if name:
                by_name[_normalize_name(name)] = row

        for norm, orig in wanted.items():
            row = by_name.get(norm)
            rank = row.get("rank", row.get("Rank")) if row else None
            shaves = row.get("shaves", row.get("Shaves")) if row else None
            if rank is not None and isinstance(rank, str):
                try:
                    rank = int(rank.replace("=", "").strip())
                except ValueError:
                    rank = None
            series_by_item[orig].append({"month": month_str, "rank": rank, "shaves": shaves})

    # Build response: ensure every item has an entry for every valid month (null if missing)
    series_entries = [
        SeriesEntry(
            item=item,
            data=[
                SeriesPoint(month=p["month"], rank=p["rank"], shaves=p.get("shaves"))
                for p in series_by_item[item]
            ],
        )
        for item in item_list
    ]
    return SeriesResponse(months=valid_months, series=series_entries)
