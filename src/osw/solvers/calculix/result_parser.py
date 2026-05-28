"""CalculiX result artifact parser and ResultDataset bridge."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport
from osw.core.result_dataset import ResultDataset, ResultSummaryValue
from osw.solvers.log_parser import GenericLogParser

from .dat_parser import parse_calculix_dat
from .frd_parser import parse_calculix_frd
from .results import (
    CalculiXParsedResults,
    CalculiXResultStatus,
    CalculiXStatusSummary,
    merge_parsed_results,
)
from .runner import CalculiXRunResult
from .sta_parser import parse_calculix_sta


class CalculixResultParserError(ValueError):
    """Compatibility exception for callers that need an explicit parser error."""


class CalculixFrdParserUnavailable(NotImplementedError):
    """Compatibility exception for the deferred full FRD parser."""


def parse_calculix_results(
    *,
    dat_path: str | Path | None = None,
    frd_path: str | Path | None = None,
    sta_path: str | Path | None = None,
    log_text: str = "",
    artifacts: tuple[RunArtifact, ...] = (),
    source_run_id: str = "",
    job_name: str = "",
) -> CalculiXParsedResults:
    """Parse available CalculiX artifacts without executing ``ccx``."""

    parsed: list[CalculiXParsedResults] = []
    if dat_path is not None:
        parsed.append(parse_calculix_dat(dat_path))
    if sta_path is not None:
        status_summary = parse_calculix_sta(sta_path)
        diagnostics = DiagnosticReport()
        _status_summary_diagnostics(status_summary, diagnostics, Path(sta_path))
        parsed.append(
            CalculiXParsedResults(
                sta_path=Path(sta_path),
                status=CalculiXResultStatus.PARSED
                if status_summary.increments or status_summary.completed is not None
                else CalculiXResultStatus.PARTIAL,
                status_summary=status_summary,
                artifacts=(
                    RunArtifact(
                        Path(sta_path),
                        "status",
                        "CalculiX status artifact.",
                        format="sta",
                    ),
                ),
                diagnostics=diagnostics,
            )
        )
    if frd_path is not None:
        parsed.append(parse_calculix_frd(frd_path))
    if log_text:
        parsed.append(_parse_log_text(log_text))

    if not parsed:
        diagnostics = DiagnosticReport()
        diagnostics.add_error(
            "calculix-result-artifacts-missing",
            "No CalculiX DAT, STA, FRD, or log artifact was provided.",
            hint=(
                "Provide a CalculiX case directory, a run result JSON, "
                "or a specific artifact path."
            ),
        )
        return CalculiXParsedResults(
            source_run_id=source_run_id,
            job_name=job_name,
            status=CalculiXResultStatus.MISSING_ARTIFACTS,
            artifacts=artifacts,
            diagnostics=diagnostics,
        )

    merged = merge_parsed_results(
        *parsed,
        source_run_id=source_run_id,
        job_name=job_name,
        metadata={"parser": "calculix-result-summary"},
    )
    if not artifacts:
        return merged
    metadata = {**merged.metadata, "external_artifact_count": len(artifacts)}
    return replace(
        merged,
        artifacts=_dedupe_artifacts((*merged.artifacts, *artifacts)),
        metadata=metadata,
    )


def parse_calculix_case_directory(path: str | Path) -> CalculiXParsedResults:
    """Parse the first matching CalculiX result artifacts in a case directory."""

    case_dir = Path(path).expanduser()
    diagnostics = DiagnosticReport()
    if not case_dir.exists() or not case_dir.is_dir():
        diagnostics.add_error(
            "calculix-case-directory-missing",
            f"CalculiX case directory was not found: {case_dir}",
            path=case_dir,
        )
        return CalculiXParsedResults(
            status=CalculiXResultStatus.MISSING_ARTIFACTS,
            diagnostics=diagnostics,
            metadata={"case_dir": str(case_dir)},
        )

    sta_path = _first_match(case_dir, "*.sta")
    frd_path = _first_match(case_dir, "*.frd")
    dat_path = _matching_dat(case_dir, sta_path=sta_path, frd_path=frd_path)
    log_text = _case_log_text(case_dir)
    artifacts = tuple(
        RunArtifact(item, _role_for_suffix(item.suffix), "CalculiX result artifact.")
        for item in sorted(case_dir.glob("*"))
        if item.is_file() and item.suffix.lower() in {".dat", ".sta", ".frd", ".log"}
    )
    result = parse_calculix_results(
        dat_path=dat_path,
        sta_path=sta_path,
        frd_path=frd_path,
        log_text=log_text,
        artifacts=artifacts,
        job_name=_job_name_from_paths(dat_path, sta_path, frd_path, case_dir),
    )
    result.metadata.setdefault("case_dir", str(case_dir))
    if dat_path is None and sta_path is None and frd_path is None and not log_text:
        result.diagnostics.add_error(
            "calculix-result-artifacts-missing",
            f"No CalculiX result artifacts were found in: {case_dir}",
            path=case_dir,
        )
    return result


def parse_calculix_run_artifacts(run_result: CalculiXRunResult) -> CalculiXParsedResults:
    """Parse artifacts recorded by ``CalculiXRunResult``."""

    dat_path = _artifact_path(run_result.artifacts, ".dat", roles={"dat_result"})
    sta_path = _artifact_path(run_result.artifacts, ".sta", roles={"status"})
    frd_path = _artifact_path(run_result.artifacts, ".frd", roles={"frd_result"})
    log_text = str(getattr(run_result, "combined_log", "") or "")
    result = parse_calculix_results(
        dat_path=dat_path,
        sta_path=sta_path,
        frd_path=frd_path,
        log_text=log_text,
        artifacts=tuple(run_result.artifacts),
        source_run_id=str(getattr(run_result, "run_id", "")),
        job_name=str(getattr(run_result, "job_name", "")),
    )
    result.metadata.setdefault("case_dir", str(getattr(run_result, "case_dir", "")))
    run_status = str(getattr(getattr(run_result, "status", ""), "value", ""))
    result.metadata.setdefault("run_status", run_status)
    return result


def result_dataset_from_calculix_run(run_result: CalculiXRunResult) -> ResultDataset:
    """Parse a run result and bridge it into a ResultDataset summary."""

    return calculix_results_to_result_dataset(parse_calculix_run_artifacts(run_result))


def calculix_results_to_result_dataset(parsed: CalculiXParsedResults) -> ResultDataset:
    """Convert parsed CalculiX summaries into a lightweight ResultDataset."""

    summaries: list[ResultSummaryValue] = []
    if (
        parsed.displacement_summary is not None
        and parsed.displacement_summary.max_magnitude is not None
    ):
        summaries.append(
            ResultSummaryValue(
                "max_displacement",
                parsed.displacement_summary.max_magnitude,
                parsed.displacement_summary.unit,
                "calculix.dat",
            )
        )
    if parsed.stress_summary is not None and parsed.stress_summary.max_von_mises is not None:
        summaries.append(
            ResultSummaryValue(
                "max_von_mises_stress",
                parsed.stress_summary.max_von_mises,
                parsed.stress_summary.unit,
                "calculix.dat",
            )
        )
    source = str(parsed.dat_path or parsed.frd_path or parsed.sta_path or "")
    warnings = tuple(message.message for message in parsed.diagnostics.warnings())
    return ResultDataset(
        dataset_id=parsed.job_name or Path(source).stem or "calculix-results",
        source=source,
        solver="CalculiX",
        analysis_type="linear_static",
        summaries=tuple(summaries),
        warnings=warnings,
        metadata={
            "status": parsed.status.value,
            "source_run_id": parsed.source_run_id,
            "artifacts": [artifact.to_dict() for artifact in parsed.artifacts],
            "diagnostics": parsed.diagnostics.to_dict(),
            **dict(parsed.metadata),
        },
    )


def _parse_log_text(text: str) -> CalculiXParsedResults:
    events = tuple(GenericLogParser().parse(text))
    diagnostics = DiagnosticReport()
    for event in events:
        if event.severity.value == "warning":
            diagnostics.add_warning(
                "log-warning-detected",
                event.message,
                metadata={"line_no": event.line_no},
            )
        elif event.severity.value == "error":
            diagnostics.add_error(
                "log-error-detected",
                event.message,
                metadata={"line_no": event.line_no},
            )
    return CalculiXParsedResults(
        status=CalculiXResultStatus.PARTIAL,
        log_events=events,
        diagnostics=diagnostics,
        metadata={"log_events": len(events)},
    )


def _status_summary_diagnostics(
    summary: CalculiXStatusSummary,
    diagnostics: DiagnosticReport,
    path: Path,
) -> None:
    for warning in summary.warnings:
        diagnostics.add_warning("calculix-sta-warning", warning, path=path)
    for error in summary.errors:
        diagnostics.add_error("calculix-sta-error", error, path=path)


def _first_match(root: Path, pattern: str) -> Path | None:
    matches = sorted(root.glob(pattern))
    return matches[0] if matches else None


def _matching_dat(root: Path, *, sta_path: Path | None, frd_path: Path | None) -> Path | None:
    dat_matches = sorted(root.glob("*.dat"))
    if not dat_matches:
        return None
    preferred_stems = [path.stem for path in (sta_path, frd_path) if path is not None]
    for stem in preferred_stems:
        for path in dat_matches:
            if path.stem == stem:
                return path
    return dat_matches[0]


def _case_log_text(root: Path) -> str:
    parts: list[str] = []
    for pattern in ("*.log", "stdout.txt", "stderr.txt"):
        for path in sorted(root.glob(pattern)):
            try:
                parts.append(path.read_text(encoding="utf-8", errors="replace"))
            except OSError:
                continue
    return "\n".join(part for part in parts if part)


def _artifact_path(
    artifacts: tuple[RunArtifact, ...],
    suffix: str,
    *,
    roles: set[str],
) -> Path | None:
    for artifact in artifacts:
        path = Path(artifact.path)
        if artifact.role in roles or path.suffix.casefold() == suffix.casefold():
            return path
    return None


def _role_for_suffix(suffix: str) -> str:
    return {
        ".dat": "dat_result",
        ".sta": "status",
        ".frd": "frd_result",
        ".log": "log",
    }.get(suffix.lower(), "unknown")


def _job_name_from_paths(
    dat_path: Path | None,
    sta_path: Path | None,
    frd_path: Path | None,
    case_dir: Path,
) -> str:
    for path in (dat_path, sta_path, frd_path):
        if path is not None:
            return path.stem
    return case_dir.name


def _dedupe_artifacts(artifacts: tuple[RunArtifact, ...]) -> tuple[RunArtifact, ...]:
    seen: set[tuple[str, str]] = set()
    unique: list[RunArtifact] = []
    for artifact in artifacts:
        key = (str(artifact.path), artifact.role)
        if key in seen:
            continue
        seen.add(key)
        unique.append(artifact)
    return tuple(unique)


__all__ = [
    "CalculixFrdParserUnavailable",
    "CalculixResultParserError",
    "calculix_results_to_result_dataset",
    "parse_calculix_case_directory",
    "parse_calculix_dat",
    "parse_calculix_results",
    "parse_calculix_run_artifacts",
    "result_dataset_from_calculix_run",
]
