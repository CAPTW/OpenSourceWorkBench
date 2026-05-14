from __future__ import annotations

import json
import sys
from pathlib import Path

TOOLS_QA = Path(__file__).resolve().parents[2] / "tools" / "qa"
if str(TOOLS_QA) not in sys.path:
    sys.path.insert(0, str(TOOLS_QA))

from check_docs_links import (  # noqa: E402
    check_docs_links,
    format_result,
    result_as_dict,
)


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _check(root: Path):
    return check_docs_links(root, includes=("README.md", "docs/**/*.md"))


def test_valid_relative_file_link_passes(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Doc](docs/page.md)\n")
    _write(tmp_path / "docs" / "page.md", "# Page\n")

    result = _check(tmp_path)

    assert result.failures == ()
    assert result.local_links_checked == 1


def test_missing_relative_file_link_fails_with_file_and_line(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "\n[Missing](docs/missing.md)\n")

    result = _check(tmp_path)
    message = format_result(result, root=tmp_path)

    assert result.failures
    assert "README.md:2" in message
    assert "docs/missing.md" in message
    assert "local target does not exist" in message


def test_valid_same_file_anchor_passes(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Main Heading\n\n[Jump](#main-heading)\n")

    assert _check(tmp_path).failures == ()


def test_missing_same_file_anchor_fails(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "# Main Heading\n\n[Jump](#missing-heading)\n")

    result = _check(tmp_path)

    assert result.failures
    assert "Markdown anchor not found" in result.failures[0].reason


def test_valid_file_plus_anchor_passes(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Doc](docs/page.md#details)\n")
    _write(tmp_path / "docs" / "page.md", "# Details\n")

    assert _check(tmp_path).failures == ()


def test_missing_file_plus_anchor_fails(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Doc](docs/page.md#missing)\n")
    _write(tmp_path / "docs" / "page.md", "# Details\n")

    result = _check(tmp_path)

    assert result.failures
    assert "#missing" in result.failures[0].reason


def test_links_and_raw_urls_inside_fenced_code_blocks_are_ignored(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        """# Readme

```
[Broken](docs/missing.md)
<https://example.invalid>
```
""",
    )

    result = _check(tmp_path)

    assert result.failures == ()
    assert result.local_links_checked == 0
    assert result.external_links_skipped == 0


def test_external_links_are_skipped_by_default(tmp_path: Path) -> None:
    _write(
        tmp_path / "README.md",
        "[Web](https://example.com)\n<http://example.com>\n<mailto:test@example.com>\n",
    )

    result = _check(tmp_path)

    assert result.failures == ()
    assert result.external_links_skipped == 3


def test_unsupported_scheme_fails(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[FTP](ftp://example.com/file)\n")

    result = _check(tmp_path)

    assert result.failures
    assert "unsupported link scheme" in result.failures[0].reason


def test_image_links_are_checked(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "![Plot](docs/plot.png)\n")
    _write(tmp_path / "docs" / "plot.png", "png")

    assert _check(tmp_path).failures == ()


def test_reference_style_link_definitions_are_checked(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[doc]: docs/page.md\n")
    _write(tmp_path / "docs" / "page.md", "# Page\n")

    assert _check(tmp_path).failures == ()


def test_reference_style_link_usage_is_checked(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Doc][doc]\n\n[doc]: docs/page.md\n")
    _write(tmp_path / "docs" / "page.md", "# Page\n")

    assert _check(tmp_path).failures == ()


def test_undefined_reference_style_link_usage_fails(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Doc][missing]\n")

    result = _check(tmp_path)
    message = format_result(result, root=tmp_path)

    assert result.failures
    assert "README.md:1" in message
    assert "reference link definition not found: missing" in message


def test_url_encoded_local_path_is_handled(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Encoded](docs/my%20file.md)\n")
    _write(tmp_path / "docs" / "my file.md", "# Encoded\n")

    assert _check(tmp_path).failures == ()


def test_inline_local_path_with_balanced_parentheses_passes(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Draft](docs/page_(draft).md)\n")
    _write(tmp_path / "docs" / "page_(draft).md", "# Draft\n")

    assert _check(tmp_path).failures == ()


def test_path_traversal_outside_repo_fails(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Outside](../outside.md)\n")

    result = _check(tmp_path)

    assert result.failures
    assert "escapes the repository root" in result.failures[0].reason


def test_windows_style_absolute_path_does_not_crash(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Windows](C:\\Temp\\doc.md)\n")

    result = _check(tmp_path)

    assert result.failures
    assert "absolute local paths" in result.failures[0].reason


def test_json_output_payload_is_serializable(tmp_path: Path) -> None:
    _write(tmp_path / "README.md", "[Missing](docs/missing.md)\n")

    payload = result_as_dict(_check(tmp_path), root=tmp_path)

    assert json.loads(json.dumps(payload))["failures"][0]["line"] == 1
