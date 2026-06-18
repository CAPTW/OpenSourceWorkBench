"""JSON I/O helpers for FEASpec human review records."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Any

from .human_review import FEASpecHumanReviewRecord
from .human_review_errors import FEASpecHumanReviewError


def parse_human_review_record_dict(data: Mapping[str, Any]) -> FEASpecHumanReviewRecord:
    """Parse a human review record mapping."""

    return FEASpecHumanReviewRecord.from_dict(data)


def human_review_record_from_dict(data: Mapping[str, Any]) -> FEASpecHumanReviewRecord:
    """Parse a human review record mapping."""

    return parse_human_review_record_dict(data)


def human_review_record_to_dict(record: FEASpecHumanReviewRecord) -> dict[str, Any]:
    """Serialize a human review record to a plain mapping."""

    return record.to_dict()


def load_human_review_record(path: str | Path) -> FEASpecHumanReviewRecord:
    """Load a JSON human review record from disk."""

    review_path = Path(path)
    _require_json_path(review_path)
    try:
        payload = json.loads(review_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        msg = f"Invalid human review record JSON: {review_path}"
        raise FEASpecHumanReviewError(msg) from exc
    if not isinstance(payload, Mapping):
        msg = "Human review record JSON must contain an object."
        raise FEASpecHumanReviewError(msg)
    return parse_human_review_record_dict(payload)


def dump_human_review_record(
    record: FEASpecHumanReviewRecord,
    path: str | Path,
    *,
    overwrite: bool = False,
) -> None:
    """Write a JSON human review record without implicit parent creation."""

    review_path = Path(path)
    _require_json_path(review_path)
    if not review_path.parent.exists():
        msg = f"Parent directory does not exist: {review_path.parent}"
        raise FEASpecHumanReviewError(msg)
    if review_path.exists() and not overwrite:
        msg = f"Human review record already exists: {review_path}"
        raise FEASpecHumanReviewError(msg)
    review_path.write_text(
        json.dumps(record.to_dict(), indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _require_json_path(path: Path) -> None:
    if path.suffix.lower() != ".json":
        msg = f"Human review records use JSON files only: {path}"
        raise FEASpecHumanReviewError(msg)
