#!/usr/bin/env python3
"""Check local Markdown links without network access."""

from __future__ import annotations

import argparse
import fnmatch
import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote, urlsplit

from _common import repo_root

DEFAULT_INCLUDES = (
    "README.md",
    "CHANGELOG.md",
    "docs/**/*.md",
    "examples/**/*.md",
    "examples/**/README*.md",
)
DEFAULT_EXCLUDES = (
    ".git/**",
    ".venv/**",
    "venv/**",
    "__pycache__/**",
    "build/**",
    "dist/**",
    "wheelhouse/**",
    ".pytest_cache/**",
    ".mypy_cache/**",
    ".ruff_cache/**",
    "**/__pycache__/**",
    "**/constant/polyMesh/**",
    "**/processor*/**",
)

INLINE_LINK_RE = re.compile(
    r"(!?)\[([^\]\n]*)\]\(((?:\\.|[^()\\\n]|\([^()\n]*\))*)\)"
)
REFERENCE_LINK_RE = re.compile(r"^\s{0,3}\[([^\]\n]+)\]:\s*(.+?)\s*$")
REFERENCE_USAGE_RE = re.compile(r"(!?)\[([^\]\n]+)\]\[([^\]\n]*)\]")
AUTOLINK_RE = re.compile(r"<((?:https?://|mailto:|tel:)[^>\s]+)>", re.IGNORECASE)
HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*#*\s*$")
SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.-]*:")
WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
EXTERNAL_SCHEMES = {"http", "https", "mailto", "tel"}


@dataclass(frozen=True)
class MarkdownLink:
    source: Path
    line: int
    target: str
    kind: str


@dataclass(frozen=True)
class LinkFailure:
    source: Path
    line: int
    target: str
    reason: str


@dataclass(frozen=True)
class LinkCheckResult:
    checked_files: int
    local_links_checked: int
    external_links_skipped: int
    failures: tuple[LinkFailure, ...]


def _is_fence_start(line: str) -> str | None:
    stripped = line.lstrip()
    if stripped.startswith("```"):
        return "```"
    if stripped.startswith("~~~"):
        return "~~~"
    return None


def _target_token(raw_target: str) -> str:
    target = raw_target.strip()
    if not target:
        return ""
    if target.startswith("<"):
        closing = target.find(">")
        if closing >= 0:
            return target[1:closing].strip()
    return target.split()[0].strip()


def _normalize_reference_id(reference_id: str) -> str:
    return re.sub(r"\s+", " ", reference_id.strip()).lower()


def _markdown_content_lines(text: str) -> list[tuple[int, str]]:
    lines: list[tuple[int, str]] = []
    in_fence: str | None = None

    for line_number, line in enumerate(text.splitlines(), start=1):
        fence = _is_fence_start(line)
        if fence and in_fence is None:
            in_fence = fence
            continue
        if fence and in_fence == fence:
            in_fence = None
            continue
        if in_fence:
            continue
        lines.append((line_number, line))

    return lines


def extract_markdown_links(path: Path, text: str) -> list[MarkdownLink]:
    """Extract Markdown links outside fenced code blocks."""

    links: list[MarkdownLink] = []
    content_lines = _markdown_content_lines(text)
    reference_definitions: dict[str, str] = {}

    for _line_number, line in content_lines:
        reference_match = REFERENCE_LINK_RE.match(line)
        if not reference_match:
            continue
        reference_id = _normalize_reference_id(reference_match.group(1))
        if reference_id and reference_id not in reference_definitions:
            reference_definitions[reference_id] = _target_token(reference_match.group(2))

    for line_number, line in content_lines:
        occupied_spans: list[tuple[int, int]] = []
        for match in INLINE_LINK_RE.finditer(line):
            raw_target = _target_token(match.group(3))
            if raw_target:
                links.append(
                    MarkdownLink(
                        source=path,
                        line=line_number,
                        target=raw_target,
                        kind="image" if match.group(1) else "inline",
                    )
                )
                occupied_spans.append(match.span())

        reference_match = REFERENCE_LINK_RE.match(line)
        if reference_match:
            raw_target = _target_token(reference_match.group(2))
            if raw_target:
                links.append(
                    MarkdownLink(
                        source=path,
                        line=line_number,
                        target=raw_target,
                        kind="reference",
                    )
                )
                occupied_spans.append(reference_match.span())

        for match in REFERENCE_USAGE_RE.finditer(line):
            if any(start <= match.start() < end for start, end in occupied_spans):
                continue
            reference_id = _normalize_reference_id(match.group(3) or match.group(2))
            if not reference_id:
                continue
            raw_target = reference_definitions.get(reference_id)
            links.append(
                MarkdownLink(
                    source=path,
                    line=line_number,
                    target=raw_target or reference_id,
                    kind="reference-usage" if raw_target else "missing-reference",
                )
            )
            occupied_spans.append(match.span())

        for match in AUTOLINK_RE.finditer(line):
            if any(start <= match.start() < end for start, end in occupied_spans):
                continue
            links.append(
                MarkdownLink(
                    source=path,
                    line=line_number,
                    target=match.group(1),
                    kind="autolink",
                )
            )

    return links


def _replace_markdown_link(match: re.Match[str]) -> str:
    return match.group(1)


def github_heading_slug(heading: str) -> str:
    """Return a GitHub-style heading anchor slug."""

    text = re.sub(r"!\[([^\]]*)\]\([^)]+\)", _replace_markdown_link, heading)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", _replace_markdown_link, text)
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("`", "")
    text = re.sub(r"[*_~]", "", text)
    text = text.strip().lower()
    text = "".join(char for char in text if char.isalnum() or char.isspace() or char == "-")
    return re.sub(r"\s+", "-", text).strip("-")


def markdown_anchors(path: Path) -> set[str]:
    anchors: set[str] = set()
    counts: dict[str, int] = {}
    in_fence: str | None = None

    for line in path.read_text(encoding="utf-8").splitlines():
        fence = _is_fence_start(line)
        if fence and in_fence is None:
            in_fence = fence
            continue
        if fence and in_fence == fence:
            in_fence = None
            continue
        if in_fence:
            continue

        match = HEADING_RE.match(line)
        if not match:
            continue
        base = github_heading_slug(match.group(2))
        count = counts.get(base, 0)
        counts[base] = count + 1
        anchors.add(base if count == 0 else f"{base}-{count}")

    return anchors


def _is_excluded(path: Path, *, root: Path, excludes: tuple[str, ...]) -> bool:
    relative = path.relative_to(root).as_posix()
    return any(fnmatch.fnmatch(relative, pattern) for pattern in excludes)


def discover_markdown_files(
    root: Path,
    *,
    includes: tuple[str, ...] = DEFAULT_INCLUDES,
    excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
) -> list[Path]:
    files: set[Path] = set()
    for pattern in includes:
        for path in root.glob(pattern):
            if path.is_file() and path.suffix.lower() == ".md":
                files.add(path)
    return sorted(path for path in files if not _is_excluded(path, root=root, excludes=excludes))


def _is_windows_absolute(target: str) -> bool:
    return bool(WINDOWS_ABSOLUTE_RE.match(target)) or target.startswith("\\\\")


def _is_repo_relative(path: Path, *, root: Path) -> bool:
    try:
        path.relative_to(root)
    except ValueError:
        return False
    return True


def _split_local_target(target: str) -> tuple[str, str]:
    if "#" not in target:
        return target, ""
    path_part, anchor = target.split("#", 1)
    return path_part, unquote(anchor).strip().lower()


def _failure(link: MarkdownLink, reason: str) -> LinkFailure:
    return LinkFailure(link.source, link.line, link.target, reason)


def validate_link(
    link: MarkdownLink,
    *,
    root: Path,
    strict_external: bool = False,
    allow_absolute_local: bool = False,
    allow_outside_repo: bool = False,
) -> tuple[str, LinkFailure | None]:
    """Validate one link and return its classification plus optional failure."""

    target = link.target.strip()
    if not target or target == "#":
        return "ignored", None
    if link.kind == "missing-reference":
        return "local", _failure(link, f"reference link definition not found: {target}")

    if _is_windows_absolute(target):
        if not allow_absolute_local:
            return "local", _failure(link, "absolute local paths are not allowed")
    else:
        parsed = urlsplit(target)
        scheme = parsed.scheme.lower()
        if scheme in EXTERNAL_SCHEMES:
            if strict_external:
                return "external", _failure(link, f"external {scheme} links are strict failures")
            return "external", None
        if scheme:
            return "local", _failure(link, f"unsupported link scheme: {scheme}")

    path_part, anchor = _split_local_target(target)
    if not path_part and not anchor:
        return "ignored", None

    if path_part.startswith("/") or path_part.startswith("\\"):
        if not allow_absolute_local:
            return "local", _failure(link, "absolute local paths are not allowed")

    if path_part:
        decoded_path = unquote(path_part).replace("\\", "/")
        candidate = (link.source.parent / decoded_path).resolve(strict=False)
    else:
        candidate = link.source.resolve(strict=False)

    root_resolved = root.resolve(strict=False)
    if not allow_outside_repo and not _is_repo_relative(candidate, root=root_resolved):
        return "local", _failure(link, "local link escapes the repository root")

    if path_part and not candidate.exists():
        return "local", _failure(link, "local target does not exist")

    if anchor:
        if candidate.is_dir():
            return "local", _failure(link, "directory links cannot have Markdown anchors")
        if candidate.suffix.lower() != ".md":
            return "local", _failure(link, "anchor target is not a Markdown file")
        anchors = markdown_anchors(candidate)
        if anchor not in anchors:
            return "local", _failure(link, f"Markdown anchor not found: #{anchor}")

    return "local", None


def check_docs_links(
    root: Path,
    *,
    includes: tuple[str, ...] = DEFAULT_INCLUDES,
    excludes: tuple[str, ...] = DEFAULT_EXCLUDES,
    strict_external: bool = False,
    allow_absolute_local: bool = False,
    allow_outside_repo: bool = False,
) -> LinkCheckResult:
    failures: list[LinkFailure] = []
    local_links_checked = 0
    external_links_skipped = 0
    files = discover_markdown_files(root, includes=includes, excludes=excludes)

    for path in files:
        for link in extract_markdown_links(path, path.read_text(encoding="utf-8")):
            classification, failure = validate_link(
                link,
                root=root,
                strict_external=strict_external,
                allow_absolute_local=allow_absolute_local,
                allow_outside_repo=allow_outside_repo,
            )
            if classification == "local":
                local_links_checked += 1
            elif classification == "external":
                external_links_skipped += 1
            if failure:
                failures.append(failure)

    return LinkCheckResult(
        checked_files=len(files),
        local_links_checked=local_links_checked,
        external_links_skipped=external_links_skipped,
        failures=tuple(failures),
    )


def result_as_dict(result: LinkCheckResult, *, root: Path) -> dict[str, object]:
    return {
        "checked_files": result.checked_files,
        "local_links_checked": result.local_links_checked,
        "external_links_skipped": result.external_links_skipped,
        "failures": [
            {
                "source": failure.source.relative_to(root).as_posix(),
                "line": failure.line,
                "target": failure.target,
                "reason": failure.reason,
            }
            for failure in result.failures
        ],
    }


def format_result(result: LinkCheckResult, *, root: Path) -> str:
    lines = [
        f"[info] Markdown files checked: {result.checked_files}",
        f"[info] Local links checked: {result.local_links_checked}",
        f"[info] External links skipped: {result.external_links_skipped}",
    ]
    if result.failures:
        lines.append("[fail] Broken Markdown links found:")
        for failure in result.failures:
            source = failure.source.relative_to(root).as_posix()
            lines.append(
                f"  - {source}:{failure.line}: {failure.target} ({failure.reason})"
            )
    else:
        lines.append("[ok] Markdown local links are valid.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=None, help="repository root")
    parser.add_argument("--include", action="append", default=[], help="Markdown glob to include")
    parser.add_argument("--exclude", action="append", default=[], help="glob to exclude")
    parser.add_argument(
        "--allow-external",
        action="store_true",
        help="allow external links without fetching them (default behavior)",
    )
    parser.add_argument(
        "--strict-external",
        action="store_true",
        help="treat external links as failures without fetching them",
    )
    parser.add_argument(
        "--allow-absolute-local",
        action="store_true",
        help="allow absolute local paths",
    )
    parser.add_argument(
        "--allow-outside-repo",
        action="store_true",
        help="allow local links outside the repository root",
    )
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON")
    parser.add_argument("--verbose", action="store_true", help="accepted for CLI symmetry")
    args = parser.parse_args()

    root = (args.root or repo_root()).resolve()
    includes = tuple(args.include) if args.include else DEFAULT_INCLUDES
    excludes = (*DEFAULT_EXCLUDES, *args.exclude)
    result = check_docs_links(
        root,
        includes=includes,
        excludes=excludes,
        strict_external=args.strict_external,
        allow_absolute_local=args.allow_absolute_local,
        allow_outside_repo=args.allow_outside_repo,
    )
    if args.json:
        print(json.dumps(result_as_dict(result, root=root), indent=2, sort_keys=True))
    else:
        print(format_result(result, root=root))
    return 1 if result.failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
