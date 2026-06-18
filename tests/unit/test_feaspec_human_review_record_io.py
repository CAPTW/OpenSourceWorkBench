from __future__ import annotations

import json
from pathlib import Path

import pytest

from osw.experimental.feaspec import (
    FEASpecHumanReviewError,
    create_human_review_record,
    dump_human_review_record,
    human_review_record_from_dict,
    human_review_record_to_dict,
    load_human_review_record,
    parse_human_review_record_dict,
)


def _record():
    return create_human_review_record(
        source_feaspec_id="cantilever-approved",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="approve_no_run_export",
        validator_report_summary={"has_blockers": False, "has_errors": False},
        validator_report_hash="sha256:validator",
        bridge_summary={"status": "ready"},
        case_plan_summary={"status": "ready_for_writer"},
        export_preview_summary={"status": "ready"},
    )


def test_parse_aliases_round_trip_dict() -> None:
    record = _record()
    payload = human_review_record_to_dict(record)

    assert parse_human_review_record_dict(payload).to_dict() == payload
    assert human_review_record_from_dict(payload).to_dict() == payload


def test_record_round_trips_through_json_file(tmp_path: Path) -> None:
    record = _record()
    output = tmp_path / "review.json"

    dump_human_review_record(record, output)
    loaded = load_human_review_record(output)

    assert loaded.to_dict() == record.to_dict()


def test_dump_refuses_overwrite_by_default(tmp_path: Path) -> None:
    record = _record()
    output = tmp_path / "review.json"
    dump_human_review_record(record, output)

    with pytest.raises(FEASpecHumanReviewError):
        dump_human_review_record(record, output)


def test_dump_overwrites_only_with_overwrite_true(tmp_path: Path) -> None:
    record = _record()
    output = tmp_path / "review.json"
    dump_human_review_record(record, output)
    changed = create_human_review_record(
        source_feaspec_id="truss-approved",
        reviewer="reviewer",
        reviewed_at="2026-06-18T00:00:00Z",
        action="reject",
        validator_report_summary={"has_blockers": False, "has_errors": False},
        validator_report_hash="sha256:other",
    )

    dump_human_review_record(changed, output, overwrite=True)

    assert load_human_review_record(output).source_feaspec_id == "truss-approved"


def test_dump_does_not_create_parent_dirs_implicitly(tmp_path: Path) -> None:
    record = _record()

    with pytest.raises(FEASpecHumanReviewError):
        dump_human_review_record(record, tmp_path / "missing" / "review.json")


def test_load_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(FEASpecHumanReviewError):
        load_human_review_record(path)


def test_json_only_paths_are_required(tmp_path: Path) -> None:
    record = _record()

    with pytest.raises(FEASpecHumanReviewError):
        dump_human_review_record(record, tmp_path / "review.txt")
    with pytest.raises(FEASpecHumanReviewError):
        load_human_review_record(tmp_path / "review.txt")


def test_dumped_payload_is_plain_json_object(tmp_path: Path) -> None:
    output = tmp_path / "review.json"
    dump_human_review_record(_record(), output)

    payload = json.loads(output.read_text(encoding="utf-8"))

    assert isinstance(payload, dict)
    assert payload["source_feaspec_id"] == "cantilever-approved"
