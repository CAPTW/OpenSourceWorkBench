# OSW-AUTO-032 Known Limitations Review

## Initial Review

Decision: minor amend required.

Score: 88/100.

Checkpoint: `39c5755`.

Findings:

- High: the self-check report summarized non-goal topics without enough
  negative-scope context, so `check_scope_drift.py` failed on the report file.
  The public README, release checklist, and known limitations page were already
  scope-safe.

Required fix:

- Reword the self-check report so it explicitly says OSW v0.1 does not make
  industrial certification claims, does not replace expert engineering
  judgment, does not support commercial native CAD direct import, does not
  support Simulink or `.mlapp`, and does not support full MATLAB proprietary
  toolbox compatibility.

## Amend Review

Decision: merge possible.

Score: 100/100.

Checkpoint: `39c5755`.

Amend commit: `c1bc44d`.

Required fixes: complete.

Evidence:

- `docs/known_limitations.md` exists and states v0.1 boundaries directly.
- README links the known limitations page.
- Release checklist references the known limitations page.
- No `src/**` files changed.
- The limitations page covers expert judgment, optional dependencies, external
  solver dependency behavior, OpenFOAM template boundaries, CFD/CAE validation
  boundaries, report limitations, and `.m` execution security.
- The limitations page uses non-goal language for unsupported commercial native
  CAD direct import, unsupported Simulink and `.mlapp`, unsupported full MATLAB
  proprietary toolbox compatibility, and unsupported broad solver/product
  claims.

## QA Evidence

- `python tools\qa\check_scope_drift.py --base develop`: passed.
- `python tools\qa\check_scope_drift.py`: passed.
- `python tools\qa\run_fast_qa.py`: passed.
- `pytest tests\unit -q`: `187 passed, 3 skipped`.
- `ruff check src tests`: passed.
- `python tools\qa\check_architecture_boundaries.py`: passed.
- `python tools\qa\check_no_solver_artifacts_committed.py --base develop`:
  passed.
- `python tools\qa\check_changed_files_scope.py --base develop --allow README.md --allow docs/10_release_checklist.md --allow docs/known_limitations.md --allow .codex/reports/self_check/OSW-AUTO-032_KNOWN_LIMITATIONS.md --forbid "src/**"`:
  passed.
- Local markdown link check: passed.

## Category Score

- Architecture Compliance: 18/18.
- Test Coverage / Regression Safety: 18/18.
- User Workflow Quality: 12/12.
- Numerical / Validation Safety: 12/12.
- Error Handling / Robustness: 10/10.
- Security / Script Safety: 10/10.
- Documentation: 5/5.
- Scope Discipline: 5/5.
- Git / Local Environment Safety: 10/10.

## Decision

Proceed to merge gate using amend branch
`amend/osw-p9-3-known-limitations-review-01`.

No hard blockers remain. No generated solver artifacts or secrets were detected.
