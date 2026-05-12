---
name: qa-review
description: Run OSW QA and review scoring before checkpoint, amend, or merge decisions.
---

# QA Review

Use before reporting completion. Run available checks: `python
tools/qa/run_fast_qa.py`, scope drift, architecture boundaries, solver artifact
scan, `pytest tests/unit -q`, and `ruff check src tests`. Record skipped checks
with exact reasons.
