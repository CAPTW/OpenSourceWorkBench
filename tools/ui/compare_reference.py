"""Compare an OSW GUI screenshot against the reference image."""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ComparisonResult:
    """Structured result for visual comparison."""

    status: str
    return_code: int
    metrics: dict[str, Any] = field(default_factory=dict)
    message: str = ""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Compare an OpenSolver Workbench screenshot to the UI reference.",
    )
    parser.add_argument("--reference", required=True, type=Path)
    parser.add_argument("--candidate", required=True, type=Path)
    parser.add_argument("--out-json", type=Path)
    parser.add_argument("--out-diff", type=Path)
    parser.add_argument("--resize-candidate", action="store_true")
    parser.add_argument("--threshold", type=float, default=0.08)
    parser.add_argument("--quiet", action="store_true")
    return parser


def compare_images(
    *,
    reference: Path,
    candidate: Path,
    out_json: Path | None = None,
    out_diff: Path | None = None,
    resize_candidate: bool = False,
    threshold: float = 0.08,
) -> ComparisonResult:
    """Compare two images with optional Pillow-backed diff output."""

    pillow = _load_pillow()
    if pillow is None:
        result = ComparisonResult(
            status="pillow-unavailable",
            return_code=2,
            message="Pillow is not installed; image comparison was skipped.",
        )
        _write_json_if_requested(out_json, result)
        return result

    if not reference.exists() or not candidate.exists():
        result = ComparisonResult(
            status="missing-input",
            return_code=1,
            message=f"Missing image: reference={reference.exists()} candidate={candidate.exists()}",
        )
        _write_json_if_requested(out_json, result)
        return result

    Image = pillow["Image"]
    ImageChops = pillow["ImageChops"]
    ImageOps = pillow["ImageOps"]
    ImageStat = pillow["ImageStat"]

    ref_image = Image.open(reference).convert("RGB")
    candidate_image = Image.open(candidate).convert("RGB")
    reference_size = ref_image.size
    candidate_size = candidate_image.size
    status = "compared"
    return_code = 0
    message = ""

    if reference_size != candidate_size:
        if resize_candidate:
            candidate_image = candidate_image.resize(reference_size)
            status = "compared-resized"
            message = "Candidate was resized to reference dimensions for comparison."
        else:
            status = "size-mismatch"
            return_code = 1
            message = "Image sizes differ; pass --resize-candidate to compare resized images."

    compared_size = ref_image.size if ref_image.size == candidate_image.size else None
    metrics: dict[str, Any] = {
        "reference_size": list(reference_size),
        "candidate_size": list(candidate_size),
        "compared_size": list(compared_size) if compared_size else None,
        "threshold": threshold,
    }

    if compared_size:
        diff = ImageChops.difference(ref_image, candidate_image)
        stat = ImageStat.Stat(diff)
        mean_absolute_error = float(sum(stat.mean) / len(stat.mean))
        normalized = mean_absolute_error / 255.0
        max_channel_error = int(max(high for _low, high in stat.extrema))
        cutoff = max(0.0, min(1.0, threshold)) * 255.0
        if hasattr(diff, "get_flattened_data"):
            diff_pixels = diff.get_flattened_data()
        else:
            diff_pixels = diff.getdata()
        total_pixels = compared_size[0] * compared_size[1]
        over_threshold = sum(1 for pixel in diff_pixels if max(pixel) > cutoff)
        percent_over_threshold = over_threshold / total_pixels if total_pixels else 0.0
        metrics.update(
            {
                "mean_absolute_error": mean_absolute_error,
                "normalized_mean_absolute_error": normalized,
                "max_channel_error": max_channel_error,
                "percent_pixels_over_threshold": percent_over_threshold,
                "passed_threshold": normalized <= threshold,
            }
        )
        if out_diff is not None:
            out_diff.parent.mkdir(parents=True, exist_ok=True)
            ImageOps.grayscale(diff).point(lambda value: min(255, value * 4)).save(out_diff)

    result = ComparisonResult(
        status=status,
        return_code=return_code,
        metrics=metrics,
        message=message,
    )
    _write_json_if_requested(out_json, result)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    result = compare_images(
        reference=args.reference,
        candidate=args.candidate,
        out_json=args.out_json,
        out_diff=args.out_diff,
        resize_candidate=args.resize_candidate,
        threshold=args.threshold,
    )
    if not args.quiet:
        if result.message:
            print(result.message)
        print(json.dumps(_result_payload(result), indent=2))
    return result.return_code


def _load_pillow() -> dict[str, Any] | None:
    try:
        from PIL import Image, ImageChops, ImageOps, ImageStat
    except ModuleNotFoundError:
        return None
    return {
        "Image": Image,
        "ImageChops": ImageChops,
        "ImageOps": ImageOps,
        "ImageStat": ImageStat,
    }


def _write_json_if_requested(path: Path | None, result: ComparisonResult) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(_result_payload(result), indent=2), encoding="utf-8")


def _result_payload(result: ComparisonResult) -> dict[str, Any]:
    return {
        "status": result.status,
        "return_code": result.return_code,
        "message": result.message,
        "metrics": result.metrics,
    }


if __name__ == "__main__":
    sys.exit(main())
