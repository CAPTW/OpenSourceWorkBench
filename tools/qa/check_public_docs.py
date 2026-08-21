"""Validate public-facing documentation for release scope and local links."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
README = REPO_ROOT / "README.md"
QUICKSTART = REPO_ROOT / "docs" / "quickstart.md"
DOCS_EXAMPLES = REPO_ROOT / "docs" / "examples.md"
EXAMPLES_README = REPO_ROOT / "examples" / "README.md"
KNOWN_LIMITATIONS = REPO_ROOT / "docs" / "release" / "known_limitations_v0_1.md"
TUTORIAL_INDEX = REPO_ROOT / "docs" / "tutorials" / "README.md"
FIRST_CLI = REPO_ROOT / "docs" / "tutorials" / "first_cli_walkthrough.md"
FIRST_GUI = REPO_ROOT / "docs" / "tutorials" / "first_gui_walkthrough.md"
RESULT_DATASET = REPO_ROOT / "docs" / "tutorials" / "result_dataset_walkthrough.md"
RELEASE_ASSET_SMOKE = (
    REPO_ROOT / "docs" / "tutorials" / "release_asset_smoke_walkthrough.md"
)
CODE_SIGNING_STRATEGY = (
    REPO_ROOT / "docs" / "release" / "code_signing_installer_strategy.md"
)

REQUIRED_PATHS = (
    README,
    QUICKSTART,
    DOCS_EXAMPLES,
    EXAMPLES_README,
    KNOWN_LIMITATIONS,
    TUTORIAL_INDEX,
    FIRST_CLI,
    FIRST_GUI,
    RESULT_DATASET,
    RELEASE_ASSET_SMOKE,
    CODE_SIGNING_STRATEGY,
    REPO_ROOT / "docs" / "assets" / "screenshots" / "osw_dark.png",
    REPO_ROOT / "docs" / "assets" / "screenshots" / "osw_light.png",
    REPO_ROOT / "docs" / "assets" / "screenshots" / "osw_system.png",
)

README_REQUIRED_PHRASES = (
    "educational/research open-source Engineering Solver & Script Workbench",
    "What Works In v0.1.3rc1",
    "Quickstart",
    "Screenshots",
    "Examples",
    "Try It In 10 Minutes",
    "Optional Dependencies",
    "Known Limitations",
    "Release Status",
    "v0.1.4-rc1",
    "public GitHub Release prerelease",
    "post-public-release roadmap",
)

LIMITATION_PHRASES = (
    "No industrial certification",
    "No native SolidWorks, CATIA, NX, Creo",
    "No Simulink",
    "No full OpenFOAM",
    "No plugin signing",
)

TUTORIAL_CURRENT_RELEASE_COPY = (
    "OSW package metadata is currently `0.1.5rc2`, and the current public GitHub "
    "prerelease is `v0.1.5-rc1`. OSW is intended for educational and research "
    "workflows, not stable-production, industrial, or regulated engineering use; "
    "it is not a MATLAB, ANSYS, or Simulink clone or a commercial CAD replacement."
)
EXAMPLES_CURRENT_RELEASE_COPY = (
    "These examples are small source-tree workflows for the current `develop` "
    "line. Package metadata is `0.1.5rc2`, and `v0.1.5-rc1` is the current public "
    "prerelease. They are intended for inspection and teaching, not production "
    "or regulated engineering use."
)
RELEASE_ASSET_LIMITATION = (
    "- The current public `v0.1.5-rc1` GitHub prerelease has five attached Release "
    "assets: a wheel, an sdist, an unsigned Windows portable ZIP, "
    "`SHA256SUMS.txt`, and `release_asset_manifest.json`. GitHub's automatic "
    "source archives are separate from that five-asset count. Release-asset "
    "`quick` and `full-static` verification establish only their stated identity "
    "and static-consistency result, report `release_readiness=false`, and do not "
    "establish installability, launch behavior, runtime correctness, engineering "
    "correctness, regulated-use suitability, or publication readiness. No MSI, "
    "code signing, Python package-index publication, bundled-solver distribution, "
    "stable-production status, broader engineering assurance, or future packaging "
    "format is claimed; those remain separately gated."
)
SIGNING_CURRENT_AUTHORITY_NOTE = (
    "Current-authority note: this page began as the post-`v0.1.3-rc1` strategy "
    "record. The current public prerelease is `v0.1.5-rc1`. The "
    "checksum/signing/installer distinctions and the current unsigned portable "
    "ZIP, no-MSI, no-code-signing, and no-bundled-solver limitations remain "
    "applicable; version-specific v0.1.3rc2/v0.1.4 recommendations below are "
    "retained as historical planning, not current roadmap authority."
)
CURRENT_AUTHORITY_PHRASES = (
    (TUTORIAL_INDEX, TUTORIAL_CURRENT_RELEASE_COPY),
    (EXAMPLES_README, EXAMPLES_CURRENT_RELEASE_COPY),
    (KNOWN_LIMITATIONS, RELEASE_ASSET_LIMITATION),
    (CODE_SIGNING_STRATEGY, SIGNING_CURRENT_AUTHORITY_NOTE),
)

UNSUPPORTED_CLAIMS = (
    "industrial-" + "certi" + "fied CAE product",
    "production " + "CAE replacement",
    "MAT" + "LAB replacement",
    "AN" + "SYS replacement",
    "Simu" + "link compatible",
    "native Solid" + "Works import",
)

MARKDOWN_LINK_RE = re.compile(r"!?\[[^\]]+\]\(([^)]+)\)")


def check_public_docs() -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_PATHS:
        if not path.exists():
            errors.append(f"Missing required public docs path: {path.relative_to(REPO_ROOT)}")

    if README.exists():
        readme = README.read_text(encoding="utf-8")
        for phrase in README_REQUIRED_PHRASES:
            if not _contains_phrase(readme, phrase):
                errors.append(f"README missing required phrase: {phrase}")
        for claim in UNSUPPORTED_CLAIMS:
            if claim in readme:
                errors.append(f"README contains unsupported claim: {claim}")

    if KNOWN_LIMITATIONS.exists():
        limitations = KNOWN_LIMITATIONS.read_text(encoding="utf-8")
        for phrase in LIMITATION_PHRASES:
            if not _contains_phrase(limitations, phrase):
                errors.append(f"Known limitations missing phrase: {phrase}")

    for path, phrase in CURRENT_AUTHORITY_PHRASES:
        if path.exists() and not _contains_phrase(path.read_text(encoding="utf-8"), phrase):
            errors.append(
                f"{path.relative_to(REPO_ROOT)} missing current-authority phrase: {phrase}"
            )

    for markdown_path in (
        README,
        QUICKSTART,
        DOCS_EXAMPLES,
        EXAMPLES_README,
        TUTORIAL_INDEX,
        FIRST_CLI,
        FIRST_GUI,
        RESULT_DATASET,
        RELEASE_ASSET_SMOKE,
        CODE_SIGNING_STRATEGY,
    ):
        if markdown_path.exists():
            errors.extend(_missing_local_links(markdown_path))
    return errors


def _missing_local_links(markdown_path: Path) -> list[str]:
    errors: list[str] = []
    text = markdown_path.read_text(encoding="utf-8")
    for match in MARKDOWN_LINK_RE.finditer(text):
        target = match.group(1).strip()
        if _is_external_or_anchor(target):
            continue
        link_path = target.split("#", 1)[0]
        if not link_path:
            continue
        resolved = (markdown_path.parent / link_path).resolve()
        if not resolved.exists():
            errors.append(
                f"{markdown_path.relative_to(REPO_ROOT)} has missing link target: {target}"
            )
    return errors


def _is_external_or_anchor(target: str) -> bool:
    return (
        target.startswith("#")
        or "://" in target
        or target.startswith("mailto:")
        or target.startswith("tel:")
    )


def _contains_phrase(text: str, phrase: str) -> bool:
    return " ".join(phrase.split()) in " ".join(text.split())


def main() -> int:
    errors = check_public_docs()
    if errors:
        for error in errors:
            print(f"[error] {error}", file=sys.stderr)
        return 1
    print("[ok] Public repository docs are present and scoped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
