"""Safe placeholder handling for CalculiX ``.frd`` artifacts."""

from __future__ import annotations

from pathlib import Path

from osw.core.artifacts import RunArtifact
from osw.core.diagnostics import DiagnosticReport

from .results import CalculiXParsedResults, CalculiXResultStatus

FRD_DEFERRED_MESSAGE = (
    "Full FRD field parsing is deferred. The artifact is available for future "
    "post-processing."
)


def parse_calculix_frd(path: str | Path) -> CalculiXParsedResults:
    """Detect FRD metadata without attempting full field parsing."""

    source = Path(path).expanduser()
    diagnostics = DiagnosticReport()
    if not source.exists():
        diagnostics.add_error(
            "calculix-frd-missing",
            f"CalculiX FRD artifact was not found: {source}",
            path=source,
        )
        return CalculiXParsedResults(
            frd_path=source,
            status=CalculiXResultStatus.MISSING_ARTIFACTS,
            diagnostics=diagnostics,
        )
    diagnostics.add_warning(
        "calculix-frd-parser-deferred",
        FRD_DEFERRED_MESSAGE,
        hint="Use the recorded FRD artifact with a future post-processing pipeline.",
        path=source,
    )
    return CalculiXParsedResults(
        frd_path=source,
        status=CalculiXResultStatus.UNSUPPORTED,
        artifacts=(
            RunArtifact(
                source,
                "frd_result",
                "CalculiX FRD result artifact.",
                format="frd",
                metadata={"parser": "deferred"},
            ),
        ),
        diagnostics=diagnostics,
        metadata={"frd_size_bytes": source.stat().st_size},
    )


__all__ = ["FRD_DEFERRED_MESSAGE", "parse_calculix_frd"]
