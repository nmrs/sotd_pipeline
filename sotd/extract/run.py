import json
from datetime import datetime, timezone
from typing import Any
from sotd.extract.comment import parse_comment


def run_extraction_for_month(month: str) -> dict[str, Any]:
    path = f"data/comments/{month}.json"
    try:
        with open(path, "r") as f:
            comments = json.load(f)["data"]
    except FileNotFoundError:
        return {
            "meta": {"month": month, "error": f"File not found: {path}"},
            "data": [],
            "skipped": [],
        }

    data = []
    skipped = []
    field_counts = {"razor": 0, "blade": 0, "brush": 0, "soap": 0}

    for comment in comments:
        extracted = parse_comment(comment)
        if extracted:
            data.append({**comment, "extracted": extracted})
            for field in extracted:
                field_counts[field] += 1
        else:
            skipped.append(comment)

    meta = {
        "month": month,
        "extracted_at": datetime.now(tz=timezone.utc).isoformat(),
        "comment_count": len(comments),
        "shave_count": len(data),
        "skipped_count": len(skipped),
        "field_coverage": field_counts,
    }

    return {"meta": meta, "data": data, "skipped": skipped}


# New function to save extraction result to disk
from pathlib import Path


def save_extraction_result(
    month: str, result: dict[str, Any], base_path: str = "data/extracted"
) -> None:
    out_path = Path(base_path) / f"{month}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)


import argparse


def main():
    parser = argparse.ArgumentParser(description="Extract SOTD shaves for a given month")
    parser.add_argument("--month", required=True, help="Month to extract in YYYY-MM format")
    parser.add_argument("--debug", action="store_true", help="Print debug output for skipped items")
    args = parser.parse_args()

    result = run_extraction_for_month(args.month)
    save_extraction_result(args.month, result)

    meta = result["meta"]
    print(
        f"[INFO] Extracted {meta.get('shave_count', 0)} shaves from {meta.get('comment_count', 0)} comments ({meta.get('month')})"
    )

    if args.debug:
        print(f"[DEBUG] Skipped count: {meta.get('skipped_count', 0)}")


if __name__ == "__main__":
    main()
