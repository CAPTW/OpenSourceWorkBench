# Codex Hooks

This directory documents local hook wiring for Codex harness runs. The hooks are
examples; they do not grant permission to push, delete branches, delete
worktrees, or run destructive Git commands.

Recommended local order:

1. `pre_prompt_scope_guard.py`
2. `pre_edit_arch_boundary.py`
3. `post_edit_fast_checks.py`
4. `pre_merge_quality_gate.py`
5. `stop_task_summary.py`

All hooks should be treated as local advisory automation unless a prompt
explicitly requires a failing hook to block the task.
