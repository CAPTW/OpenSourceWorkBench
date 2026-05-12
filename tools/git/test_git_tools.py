"""Focused tests for OSW local Git safety helpers."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

THIS_DIR = Path(__file__).resolve().parent
if str(THIS_DIR) not in sys.path:
    sys.path.insert(0, str(THIS_DIR))

import create_worktree  # noqa: E402
import preflight_commit  # noqa: E402
import rescue_dirty_worktree  # noqa: E402


class PreflightPatternTests(unittest.TestCase):
    def test_secret_detection_flags_high_confidence_tokens(self) -> None:
        sample = (
            b"OPENAI_"
            b"API_KEY = "
            b'"sk-'
            b"1234567890abcdefghijklmnopqrstuvwxyz"
            b'"\n'
        )

        findings = preflight_commit.find_secret_findings("config.py", sample)

        self.assertTrue(any("OPENAI_API_KEY" in finding for finding in findings))

    def test_runtime_artifact_detector_blocks_solver_outputs_with_allowlist(self) -> None:
        self.assertTrue(preflight_commit.is_runtime_artifact("runs/case/processor0/U"))
        self.assertTrue(preflight_commit.is_runtime_artifact("cases/beam/results.frd"))
        self.assertFalse(preflight_commit.is_runtime_artifact("examples/beam/results.frd"))
        self.assertFalse(preflight_commit.is_runtime_artifact("tests/golden/results.frd"))


class WorktreePlanTests(unittest.TestCase):
    def test_worktree_plan_uses_osw_feature_prefix_and_safe_slug(self) -> None:
        plan = create_worktree.build_worktree_plan(
            "Linear Static Demo!",
            repo_root=Path("C:/repo/open-solver-workbench"),
            worktree_root=Path("C:/repo/_worktrees"),
            base_branch="develop",
            branch_prefix="feature/osw-",
        )

        self.assertEqual(plan.slug, "linear-static-demo")
        self.assertEqual(plan.branch_name, "feature/osw-linear-static-demo")
        self.assertEqual(plan.path, Path("C:/repo/_worktrees/linear-static-demo"))
        self.assertEqual(plan.base_branch, "develop")


class RescuePlanTests(unittest.TestCase):
    def test_rescue_paths_stay_inside_git_directory(self) -> None:
        paths = rescue_dirty_worktree.build_rescue_paths(
            repo_root=Path("C:/repo/open-solver-workbench"),
            timestamp="20260512-010203",
        )

        self.assertEqual(
            paths.directory,
            Path("C:/repo/open-solver-workbench/.git/osw-rescue/20260512-010203"),
        )
        self.assertEqual(paths.unstaged_patch.name, "unstaged.patch")
        self.assertEqual(paths.staged_patch.name, "staged.patch")
        self.assertEqual(paths.untracked_manifest.name, "untracked-files.txt")


if __name__ == "__main__":
    unittest.main()
