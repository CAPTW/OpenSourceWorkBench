"""Local-only optional solver prepared-machine validation command.

The command checks prerequisite presence through PATH/module metadata only. It
does not install dependencies, execute solvers, run project workloads, fetch
network data, mutate ProjectSchema, mutate issues or releases, or claim
certification.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import shutil
import sys
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import Enum
from pathlib import Path
from typing import Any

OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND = (
    "optional-solver-prepared-machine-validation"
)

_SUBCOMMANDS = (
    "explain",
    "prerequisites",
    "preflight",
    "plan",
    "run",
    "diagnostics",
    "evidence",
    "safety",
)

_EVIDENCE_JSON_FILENAME = (
    "optional_solver_prepared_machine_validation_evidence.json"
)
_EVIDENCE_MARKDOWN_FILENAME = (
    "optional_solver_prepared_machine_validation_evidence.md"
)

_SECRET_MARKERS = (
    "secret",
    "token",
    "api_key",
    "apikey",
    "password",
    "passwd",
    "bearer",
    "credential",
    "private_key",
    "access_key",
)

_NON_ACTIONS = (
    "No dependency installation is performed.",
    "No solver installation is performed.",
    "No solver execution is performed.",
    "No arbitrary user project workloads are run.",
    "No live discovery scans arbitrary locations.",
    "No network/provider/OAuth/MCP behavior is performed.",
    "No ProjectSchema mutation is performed.",
    "No ProjectSchema evidence is created.",
    "No issue, release, tag, or asset mutation is performed.",
    "No package version metadata is changed.",
    "No validation-pass or validation-fail overclaim is made.",
    "No issue closure is claimed.",
    "No bundled solver support is claimed.",
    "No certification or production readiness is claimed.",
)

_LIMITATIONS = (
    "Prerequisite presence is setup evidence only.",
    "Missing prerequisites park prepared-machine validation.",
    "Skipped-missing entries are separate from pass.",
    "Exit code 0 is command completion only and is not certification.",
    "Evidence is local operator evidence, not a release asset.",
    "Prepared-machine validation still requires a later retry on the target environment.",
)

_SAFETY_GUIDANCE = (
    "Run this command only on a machine intentionally prepared by the operator.",
    "Review preflight and plan output before using run.",
    "Use --write-evidence and --evidence-dir only for local evidence directories.",
    "GitHub state verified 2026-07-14: Issues #6 through #11 are closed with "
    "bounded, issue-specific evidence; revalidation or reopening requires a "
    "separate explicit gate.",
    "Keep release, tag, asset, and version changes in separate release gates.",
    "Treat skipped-missing as parked setup state, not as validation success.",
)


class PreparedMachineValidationStatus(Enum):
    """Top-level command status."""

    COMPLETE = "complete"
    PARKED = "parked"
    BLOCKED = "blocked"
    ERROR = "error"


@dataclass(frozen=True)
class PreparedMachineValidationPrerequisite:
    """A prerequisite catalog row and its optional evaluated state."""

    identifier: str
    display_name: str
    kind: str
    detection_method: str
    executable_names: tuple[str, ...] = ()
    python_modules: tuple[str, ...] = ()
    required: bool = True
    require_all_names: bool = True
    status: str = "not_evaluated"
    found_names: tuple[str, ...] = ()
    missing_names: tuple[str, ...] = ()
    skipped_missing: bool = False
    note: str = ""

    def to_mapping(self) -> dict[str, object]:
        return {
            "detection_method": self.detection_method,
            "display_name": self.display_name,
            "executable_names": list(self.executable_names),
            "found_names": list(self.found_names),
            "identifier": self.identifier,
            "kind": self.kind,
            "missing_names": list(self.missing_names),
            "note": self.note,
            "python_modules": list(self.python_modules),
            "required": self.required,
            "skipped_missing": self.skipped_missing,
            "status": self.status,
        }


@dataclass(frozen=True)
class PreparedMachineValidationRequest:
    """Parsed command request."""

    subcommand: str
    json_output: bool = False
    evaluate: bool = False
    diagnostics_only: bool = False
    safety_only: bool = False
    prepared_machine: bool = False
    acknowledge_optional_solver_validation: bool = False
    confirm_local_only: bool = False
    write_evidence: bool = False
    evidence_dir: str = ""
    allow_missing: bool = False
    git_sha: str = ""


@dataclass(frozen=True)
class PreparedMachineValidationEvidence:
    """Local evidence write result."""

    json_path_display: str
    markdown_path_display: str
    written: bool

    def to_mapping(self) -> dict[str, object]:
        return {
            "json_path": self.json_path_display,
            "markdown_path": self.markdown_path_display,
            "written": self.written,
        }


@dataclass(frozen=True)
class PreparedMachineValidationResult:
    """Deterministic command result."""

    command: str
    subcommand: str
    status: PreparedMachineValidationStatus
    exit_code: int
    prerequisites: tuple[PreparedMachineValidationPrerequisite, ...]
    diagnostics: tuple[str, ...]
    evidence: PreparedMachineValidationEvidence
    git_sha: str = ""
    plan: tuple[Mapping[str, object], ...] = ()

    @property
    def missing_prerequisites(self) -> tuple[str, ...]:
        return tuple(
            row.identifier
            for row in self.prerequisites
            if row.required and row.status in {"missing", "partial"}
        )

    @property
    def skipped_missing(self) -> tuple[str, ...]:
        return tuple(
            row.identifier
            for row in self.prerequisites
            if row.skipped_missing
        )


def build_prerequisite_catalog() -> tuple[PreparedMachineValidationPrerequisite, ...]:
    """Return the stable prerequisite catalog."""

    return (
        PreparedMachineValidationPrerequisite(
            identifier="gmsh_executable",
            display_name="gmsh executable",
            kind="executable",
            detection_method="shutil.which('gmsh')",
            executable_names=("gmsh",),
            note="Required for prepared Gmsh validation readiness.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="python_gmsh",
            display_name="Python gmsh",
            kind="python_module",
            detection_method="importlib.util.find_spec('gmsh')",
            python_modules=("gmsh",),
            note="Required for prepared Gmsh Python API readiness.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="octave_executable",
            display_name="octave executable",
            kind="executable",
            detection_method="shutil.which('octave') or shutil.which('octave-cli')",
            executable_names=("octave", "octave-cli"),
            require_all_names=False,
            note="GNU Octave command presence; no script execution is performed.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="ccx_executable",
            display_name="ccx executable",
            kind="executable",
            detection_method="shutil.which('ccx')",
            executable_names=("ccx",),
            note="CalculiX command presence; no solver job is run.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="openfoam_commands",
            display_name="OpenFOAM commands",
            kind="executable_group",
            detection_method=(
                "shutil.which for foamVersion, blockMesh, and simpleFoam"
            ),
            executable_names=("foamVersion", "blockMesh", "simpleFoam"),
            note="OpenFOAM shell command presence; no case is created or run.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="python_meshio",
            display_name="Python meshio",
            kind="python_module",
            detection_method="importlib.util.find_spec('meshio')",
            python_modules=("meshio",),
            note="Optional mesh package readiness.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="python_pyvista",
            display_name="Python pyvista",
            kind="python_module",
            detection_method="importlib.util.find_spec('pyvista')",
            python_modules=("pyvista",),
            note="Optional visualization package readiness.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="python_vtk",
            display_name="Python vtk",
            kind="python_module",
            detection_method="importlib.util.find_spec('vtk')",
            python_modules=("vtk",),
            note="VTK package readiness for PyVista-backed checks.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="python_coolprop",
            display_name="Python CoolProp",
            kind="python_module",
            detection_method="importlib.util.find_spec('CoolProp')",
            python_modules=("CoolProp",),
            note="Optional thermophysical package readiness.",
        ),
        PreparedMachineValidationPrerequisite(
            identifier="python_cantera",
            display_name="Python cantera",
            kind="python_module",
            detection_method="importlib.util.find_spec('cantera')",
            python_modules=("cantera",),
            note="Optional chemistry package readiness.",
        ),
    )


def evaluate_prerequisites(
    catalog: Sequence[PreparedMachineValidationPrerequisite] | None = None,
) -> tuple[PreparedMachineValidationPrerequisite, ...]:
    """Evaluate prerequisites without importing optional packages or running tools."""

    rows = catalog or build_prerequisite_catalog()
    return tuple(_evaluate_prerequisite(row) for row in rows)


def build_plan(
    prerequisites: Sequence[PreparedMachineValidationPrerequisite] | None = None,
) -> tuple[Mapping[str, object], ...]:
    """Return the deterministic run plan."""

    rows = prerequisites or build_prerequisite_catalog()
    return (
        {
            "action": "explain_workflow",
            "mutation": False,
            "solver_execution": False,
            "summary": "Explain local prepared-machine validation boundaries.",
        },
        {
            "action": "check_prerequisites",
            "mutation": False,
            "solver_execution": False,
            "summary": "Evaluate executable and Python module presence only.",
        },
        {
            "action": "classify_readiness",
            "mutation": False,
            "solver_execution": False,
            "summary": "Classify missing prerequisites as parked/skipped-missing.",
        },
        {
            "action": "write_local_evidence_when_explicit",
            "mutation": "explicit_local_files_only",
            "solver_execution": False,
            "summary": "Write JSON and Markdown evidence only with explicit evidence flags.",
        },
        {
            "action": "preserve_boundaries",
            "mutation": False,
            "solver_execution": False,
            "summary": (
                "Do not mutate ProjectSchema, issues, releases, tags, assets, "
                "or version metadata."
            ),
        },
        {
            "action": "catalog_size",
            "mutation": False,
            "solver_execution": False,
            "summary": f"{len(tuple(rows))} prerequisite rows are in scope.",
        },
    )


def build_safety_guidance() -> tuple[str, ...]:
    """Return stable safety guidance."""

    return _SAFETY_GUIDANCE


def build_evidence_payload(
    result: PreparedMachineValidationResult,
) -> dict[str, object]:
    """Build deterministic JSON-compatible local evidence."""

    return {
        "command": result.command,
        "command_line": (
            f"python -m osw.cli {OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND} "
            f"{result.subcommand}"
        ),
        "diagnostics": list(result.diagnostics),
        "evidence": result.evidence.to_mapping(),
        "exit_code": result.exit_code,
        "exit_semantics": _exit_semantics(result.exit_code),
        "git_sha": result.git_sha or "not_supplied",
        "limitations": list(_LIMITATIONS),
        "missing_prerequisites": list(result.missing_prerequisites),
        "non_actions": list(_NON_ACTIONS),
        "plan": [dict(row) for row in result.plan],
        "prerequisites": [row.to_mapping() for row in result.prerequisites],
        "project_schema_boundary": "no ProjectSchema mutation or evidence",
        "release_asset": False,
        "safety_guidance": list(_SAFETY_GUIDANCE),
        "skipped_missing": list(result.skipped_missing),
        "status": result.status.value,
        "subcommand": result.subcommand,
        "timestamp_utc": "not_recorded_for_deterministic_local_evidence",
    }


def render_jsonable_mapping(
    result: PreparedMachineValidationResult,
) -> dict[str, object]:
    """Render a deterministic JSON-compatible command mapping."""

    return build_evidence_payload(result)


def render_text(result: PreparedMachineValidationResult) -> str:
    """Render stable text output."""

    lines = [
        "Optional Solver Prepared-Machine Validation",
        f"command: {result.command}",
        f"subcommand: {result.subcommand}",
        f"status: {result.status.value}",
        f"exit_code: {result.exit_code}",
        f"git_sha: {result.git_sha or 'not supplied'}",
        (
            "command family: python -m osw.cli "
            f"{OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND} ..."
        ),
    ]

    if result.subcommand == "explain":
        lines.extend(
            [
                "Explanation:",
                "- This command is explicit, local-only, and operator-invoked.",
                (
                    "- It separates explain, prerequisites, preflight, plan, run, "
                    "diagnostics, evidence, and safety."
                ),
                "- It detects prerequisites without installing anything.",
                "- It does not execute solvers or user project workloads.",
                "- It does not claim certification.",
            ]
        )
    if result.plan:
        lines.append("Plan:")
        for row in result.plan:
            lines.append(
                "- "
                f"{row.get('action')}: {row.get('summary')} "
                f"(mutation={row.get('mutation')}, "
                f"solver_execution={row.get('solver_execution')})"
            )

    lines.append("Prerequisites:")
    for row in result.prerequisites:
        missing = ", ".join(row.missing_names) if row.missing_names else "none"
        found = ", ".join(row.found_names) if row.found_names else "none"
        lines.append(
            "- "
            f"{row.identifier}: {row.status}; "
            f"display={row.display_name}; kind={row.kind}; "
            f"method={row.detection_method}; found={found}; missing={missing}; "
            f"skipped_missing={row.skipped_missing}"
        )

    lines.append("Missing prerequisites:")
    if result.missing_prerequisites:
        lines.extend(f"- {item}" for item in result.missing_prerequisites)
    else:
        lines.append("- none")

    lines.append("Skipped-missing:")
    if result.skipped_missing:
        lines.extend(f"- {item}" for item in result.skipped_missing)
    else:
        lines.append("- none")

    lines.append("Diagnostics:")
    if result.diagnostics:
        lines.extend(f"- {item}" for item in result.diagnostics)
    else:
        lines.append("- none")

    lines.append("Evidence paths:")
    if result.evidence.written:
        lines.append(f"- {result.evidence.json_path_display}")
        lines.append(f"- {result.evidence.markdown_path_display}")
    else:
        lines.append("- none")

    lines.append("Non-actions:")
    lines.extend(f"- {item}" for item in _NON_ACTIONS)

    lines.append("Limitations:")
    lines.extend(f"- {item}" for item in _LIMITATIONS)

    lines.append("Exit-code policy:")
    for row in _exit_code_policy_rows():
        lines.append(f"- {row['code']}: {row['meaning']}")
    lines.append("- exit code 0 is not certification.")
    lines.append("- exit code 0 is not issue closure.")
    lines.append("- exit code 0 is not release mutation.")
    lines.append("- exit code 0 is not bundled solver support.")

    lines.append("Safety guidance:")
    lines.extend(f"- {item}" for item in _SAFETY_GUIDANCE)
    return "\n".join(lines)


def add_optional_solver_prepared_machine_validation_parser(
    subparsers: Any,
) -> argparse.ArgumentParser:
    """Register the prepared-machine validation command family."""

    parser = subparsers.add_parser(
        OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND,
        help="Run local-only optional solver prepared-machine validation checks.",
        description=(
            "Explain, preflight, plan, and run a local-only prepared-machine "
            "validation envelope. The command checks local prerequisites "
            "without installing dependencies or executing solvers."
        ),
    )
    _add_arguments(parser)
    return parser


def run_optional_solver_prepared_machine_validation_cli(
    args: argparse.Namespace,
) -> int:
    """Run the prepared-machine validation command from the main dispatcher."""

    request = PreparedMachineValidationRequest(
        subcommand=args.validation_command,
        json_output=bool(args.json),
        evaluate=bool(args.evaluate),
        diagnostics_only=bool(args.diagnostics_only),
        safety_only=bool(args.safety_only),
        prepared_machine=bool(args.prepared_machine),
        acknowledge_optional_solver_validation=bool(
            args.acknowledge_optional_solver_validation
        ),
        confirm_local_only=bool(args.confirm_local_only),
        write_evidence=bool(args.write_evidence),
        evidence_dir=str(args.evidence_dir or ""),
        allow_missing=bool(args.allow_missing),
        git_sha=str(args.git_sha or ""),
    )
    result = _build_result(request)
    _emit_result(result, request)
    return result.exit_code


def main(argv: Sequence[str] | None = None) -> int:
    """Standalone module entry point for focused tests."""

    parser = argparse.ArgumentParser(
        prog=OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND,
        description="Local-only optional solver prepared-machine validation command.",
    )
    _add_arguments(parser)
    args = parser.parse_args(argv)
    return run_optional_solver_prepared_machine_validation_cli(args)


def _add_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "validation_command",
        choices=_SUBCOMMANDS,
        help="Prepared-machine validation operation to perform.",
    )
    parser.add_argument("--json", action="store_true", help="Emit deterministic JSON.")
    parser.add_argument(
        "--diagnostics-only",
        action="store_true",
        help="Render diagnostics-focused output.",
    )
    parser.add_argument(
        "--safety-only",
        action="store_true",
        help="Render safety-focused output.",
    )
    parser.add_argument(
        "--evaluate",
        action="store_true",
        help="Evaluate local prerequisites for the prerequisites/evidence command.",
    )
    parser.add_argument(
        "--prepared-machine",
        action="store_true",
        help="Acknowledge that this is an intentionally prepared local machine.",
    )
    parser.add_argument(
        "--acknowledge-optional-solver-validation",
        action="store_true",
        help="Acknowledge optional solver validation boundaries.",
    )
    parser.add_argument(
        "--confirm-local-only",
        action="store_true",
        help="Confirm the command must remain local-only and non-mutating.",
    )
    parser.add_argument(
        "--write-evidence",
        action="store_true",
        help="Write local JSON/Markdown evidence when the subcommand permits it.",
    )
    parser.add_argument(
        "--evidence-dir",
        default="",
        help="Existing local directory for explicit evidence writes.",
    )
    parser.add_argument(
        "--allow-missing",
        action="store_true",
        help="Render missing prerequisites as skipped-missing only, never pass.",
    )
    parser.add_argument(
        "--git-sha",
        default="",
        help="Optional caller-supplied git SHA for evidence output.",
    )


def _build_result(
    request: PreparedMachineValidationRequest,
) -> PreparedMachineValidationResult:
    diagnostics: list[str] = []
    evaluate = _should_evaluate(request)
    prerequisites = (
        evaluate_prerequisites()
        if evaluate
        else build_prerequisite_catalog()
    )
    plan = build_plan(prerequisites) if request.subcommand in {"plan", "run"} else ()
    status = PreparedMachineValidationStatus.COMPLETE
    exit_code = 0

    if request.subcommand == "run":
        missing_acknowledgements = _missing_run_acknowledgements(request)
        if missing_acknowledgements:
            status = PreparedMachineValidationStatus.BLOCKED
            exit_code = 2
            diagnostics.extend(missing_acknowledgements)
        elif _has_missing_prerequisites(prerequisites):
            status = PreparedMachineValidationStatus.PARKED
            exit_code = 2
            diagnostics.append(
                "Prepared-machine validation is parked because required prerequisites are missing."
            )
        else:
            diagnostics.append(
                "Local prepared-machine preflight envelope completed; no solver execution occurred."
            )
    elif request.subcommand == "preflight":
        if _has_missing_prerequisites(prerequisites):
            status = PreparedMachineValidationStatus.PARKED
            exit_code = 2
            diagnostics.append(
                "Preflight parked: required prerequisites are missing or partially available."
            )
        else:
            diagnostics.append("Preflight completed: required prerequisites are present.")
    elif request.subcommand == "diagnostics":
        diagnostics.extend(
            (
                "Diagnostics render local readiness boundaries only.",
                "No ProjectSchema, issue, release, tag, asset, or solver mutation is performed.",
            )
        )
    elif request.subcommand == "evidence":
        diagnostics.append(
            "Evidence policy rendered; evidence writes require --write-evidence and --evidence-dir."
        )
    elif request.subcommand == "safety":
        diagnostics.append("Safety boundaries rendered.")
    elif request.subcommand == "prerequisites" and evaluate:
        diagnostics.append(
            "Prerequisites evaluated locally using PATH/module metadata only."
        )

    result = PreparedMachineValidationResult(
        command=OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND,
        subcommand=request.subcommand,
        status=status,
        exit_code=exit_code,
        prerequisites=prerequisites,
        diagnostics=tuple(diagnostics),
        evidence=PreparedMachineValidationEvidence("", "", False),
        git_sha=_redact_if_secret_like(request.git_sha),
        plan=plan,
    )
    return _maybe_write_evidence(result, request)


def _evaluate_prerequisite(
    row: PreparedMachineValidationPrerequisite,
) -> PreparedMachineValidationPrerequisite:
    if row.kind in {"executable", "executable_group"}:
        found = tuple(
            name for name in row.executable_names if shutil.which(name) is not None
        )
        if row.require_all_names:
            missing = tuple(name for name in row.executable_names if name not in found)
            status = "present" if not missing else ("partial" if found else "missing")
        else:
            missing = () if found else row.executable_names
            status = "present" if found else "missing"
        return replace(
            row,
            status=status,
            found_names=found,
            missing_names=missing,
            skipped_missing=status in {"missing", "partial"},
        )

    found_modules = tuple(
        name for name in row.python_modules if importlib.util.find_spec(name) is not None
    )
    missing_modules = tuple(name for name in row.python_modules if name not in found_modules)
    status = "present" if not missing_modules else "missing"
    return replace(
        row,
        status=status,
        found_names=found_modules,
        missing_names=missing_modules,
        skipped_missing=status == "missing",
    )


def _should_evaluate(request: PreparedMachineValidationRequest) -> bool:
    return request.subcommand in {"preflight", "run"} or (
        request.subcommand in {"prerequisites", "evidence"}
        and (request.evaluate or request.write_evidence)
    )


def _missing_run_acknowledgements(
    request: PreparedMachineValidationRequest,
) -> tuple[str, ...]:
    missing: list[str] = []
    if not request.prepared_machine:
        missing.append("Missing required --prepared-machine acknowledgement.")
    if not request.acknowledge_optional_solver_validation:
        missing.append(
            "Missing required --acknowledge-optional-solver-validation acknowledgement."
        )
    if not request.confirm_local_only:
        missing.append("Missing required --confirm-local-only confirmation.")
    return tuple(missing)


def _has_missing_prerequisites(
    prerequisites: Sequence[PreparedMachineValidationPrerequisite],
) -> bool:
    return any(
        row.required and row.status in {"missing", "partial", "not_evaluated"}
        for row in prerequisites
    )


def _maybe_write_evidence(
    result: PreparedMachineValidationResult,
    request: PreparedMachineValidationRequest,
) -> PreparedMachineValidationResult:
    if not request.write_evidence:
        return result

    if request.subcommand == "run" and result.status == PreparedMachineValidationStatus.BLOCKED:
        return result

    if request.subcommand not in {"preflight", "run", "evidence"}:
        return replace(
            result,
            status=PreparedMachineValidationStatus.BLOCKED,
            exit_code=4,
            diagnostics=(
                *result.diagnostics,
                "Evidence writing is not permitted for this subcommand.",
            ),
        )

    evidence_dir, error_code, diagnostic = _validate_evidence_dir(request.evidence_dir)
    if evidence_dir is None:
        return replace(
            result,
            status=PreparedMachineValidationStatus.BLOCKED,
            exit_code=error_code,
            diagnostics=(*result.diagnostics, diagnostic),
        )

    evidence = PreparedMachineValidationEvidence(
        json_path_display=_EVIDENCE_JSON_FILENAME,
        markdown_path_display=_EVIDENCE_MARKDOWN_FILENAME,
        written=True,
    )
    written_result = replace(
        result,
        evidence=evidence,
        diagnostics=(
            *result.diagnostics,
            "Local JSON/Markdown evidence written under the caller-supplied directory.",
        ),
    )
    try:
        (evidence_dir / _EVIDENCE_JSON_FILENAME).write_text(
            json.dumps(render_jsonable_mapping(written_result), indent=2, sort_keys=True)
            + "\n",
            encoding="utf-8",
        )
        (evidence_dir / _EVIDENCE_MARKDOWN_FILENAME).write_text(
            render_text(written_result) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        return replace(
            result,
            status=PreparedMachineValidationStatus.ERROR,
            exit_code=1,
            diagnostics=(
                *result.diagnostics,
                f"Evidence write failed: {_redact_if_secret_like(str(exc))}",
            ),
        )
    return written_result


def _validate_evidence_dir(value: str) -> tuple[Path | None, int, str]:
    text = str(value or "").strip()
    if not text:
        return None, 5, "--write-evidence requires explicit --evidence-dir."
    if "://" in text:
        return None, 4, "Evidence directory must be a local filesystem path."
    path = Path(text)
    if not path.exists():
        return None, 5, "Evidence directory must already exist."
    if not path.is_dir():
        return None, 5, "Evidence path must be an existing directory."
    if any(part in {".git", ".github"} for part in path.parts):
        return None, 4, "Evidence directory must not be a Git metadata or workflow path."
    return path, 0, ""


def _emit_result(
    result: PreparedMachineValidationResult,
    request: PreparedMachineValidationRequest,
) -> None:
    stream = sys.stderr if result.exit_code else sys.stdout
    if request.json_output:
        print(
            json.dumps(render_jsonable_mapping(result), indent=2, sort_keys=True),
            file=stream,
        )
    else:
        print(_select_text(render_text(result), request), file=stream)


def _select_text(text: str, request: PreparedMachineValidationRequest) -> str:
    if not (request.diagnostics_only or request.safety_only):
        return text
    lines = text.splitlines()
    selected: list[str] = [
        line
        for line in lines
        if line.startswith(("Optional Solver", "command:", "subcommand:", "status:", "exit_code:"))
    ]
    heading = "Diagnostics:" if request.diagnostics_only else "Safety guidance:"
    in_section = False
    for line in lines:
        if line == heading:
            in_section = True
            selected.append(line)
            continue
        if in_section and line and not line.startswith("- "):
            break
        if in_section:
            selected.append(line)
    return "\n".join(selected)


def _exit_code_policy_rows() -> tuple[dict[str, object], ...]:
    return (
        {"code": 0, "meaning": "command completed; not certification"},
        {"code": 1, "meaning": "internal error"},
        {"code": 2, "meaning": "prerequisites missing, parked, or acknowledgement missing"},
        {"code": 3, "meaning": "validation checks failed"},
        {"code": 4, "meaning": "unsafe request or forbidden mutation attempt"},
        {"code": 5, "meaning": "ambiguous configuration"},
    )


def _exit_semantics(exit_code: int) -> dict[str, object]:
    return {
        "bundled_solver_support": False,
        "certification": False,
        "code": exit_code,
        "issue_closure": False,
        "meaning": next(
            (
                str(row["meaning"])
                for row in _exit_code_policy_rows()
                if row["code"] == exit_code
            ),
            "unknown",
        ),
        "project_schema_mutation": False,
        "release_mutation": False,
        "validation_failure_claim": False,
        "validation_success_claim": False,
    }


def _redact_if_secret_like(value: object) -> str:
    text = str(value or "")
    if not text:
        return ""
    lowered = text.lower()
    if any(marker in lowered for marker in _SECRET_MARKERS):
        return "<redacted-secret-like-value>"
    return text


__all__ = [
    "OPTIONAL_SOLVER_PREPARED_MACHINE_VALIDATION_COMMAND",
    "PreparedMachineValidationEvidence",
    "PreparedMachineValidationPrerequisite",
    "PreparedMachineValidationRequest",
    "PreparedMachineValidationResult",
    "PreparedMachineValidationStatus",
    "add_optional_solver_prepared_machine_validation_parser",
    "build_evidence_payload",
    "build_plan",
    "build_prerequisite_catalog",
    "build_safety_guidance",
    "evaluate_prerequisites",
    "main",
    "render_jsonable_mapping",
    "render_text",
    "run_optional_solver_prepared_machine_validation_cli",
]
