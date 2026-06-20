# Live CalculiX run-gate validation for v0.1.4-rc1

## Status

`skipped-missing`

CalculiX `ccx` was not discovered on this machine, so no installed-only
CalculiX run gate was executed.

## Release context

- Public prerelease: `v0.1.4-rc1`
- Release URL: https://github.com/CAPTW/OpenSourceWorkBench/releases/tag/v0.1.4-rc1
- Release tag target: `f1683b441ab308fd65318ef6de3f1282549946a1`
- Version: `0.1.4rc1`
- Pre-validation develop HEAD: `7ac74bae2ba192319fdd635b58b965312ad8ebc3`
- Develop validation commit: the OSW-VALID-004 docs commit that adds this
  evidence on `develop`

## Environment discovery

Discovery was installed-only and PATH-based.

| Check | Result |
| --- | --- |
| `where.exe ccx` | exit code `1`; `ccx` missing |
| `shutil.which("ccx")` | `None` |
| Version/help probe | not run because `ccx` was missing |

No dependency installation or solver installation was attempted.

## Validation scope

This gate covers the installed-only FEASpec CalculiX run gate for issue `#8`.
It does not cover parser feature work, ResultDataset GUI/CLI review-file
persistence, release asset validation, or engineering certification.

The scope explicitly preserves:

- no dependency install;
- no solver install;
- no bundled solver claim;
- no release mutation;
- no tag mutation;
- no asset upload;
- no issue closure.

## Run evidence

| Item | Value |
| --- | --- |
| Command surface used | `where.exe ccx`; Python `shutil.which("ccx")`; CLI run-gate help in QA |
| Run gate executed | no |
| Output directory | `artifacts/validation/live_optional/OSW-VALID-004/` |
| Timeout | not applicable because no run occurred |
| stdout path | not applicable |
| stderr path | not applicable |
| run metadata path | not applicable |
| environment discovery path | `artifacts/validation/live_optional/OSW-VALID-004/environment_discovery.json` |
| summary path | `artifacts/validation/live_optional/OSW-VALID-004/live_calculix_validation_summary.json` |
| command log path | `artifacts/validation/live_optional/OSW-VALID-004/command_log.txt` |

The artifact directory is ignored runtime evidence and must not be staged.

## Result

Classification: `skipped-missing`

Reason: CalculiX `ccx` was not discovered on PATH. The installed-only run gate
requires an existing `ccx` executable and this validation gate does not install
solvers.

This result is not a pass, not a fail, and not a certification claim.

## Relationship to issue #8

Issue `#8` remains open. This validation gate records skipped-missing evidence
only. A later closure gate may be considered only after `ccx` is present and
the installed-only run gate records passing evidence.

## Safety boundaries

- no solver installation;
- no dependency installation;
- no solver execution;
- no runtime artifact staging;
- no release/tag/asset mutation;
- no issue closure;
- no bundled solver claim;
- no industrial certification claim.

## Next action

Rerun on a prepared machine with `ccx` already installed on PATH, or continue
with `OSW-PLAN-007_POST_EXP_RESULTDATASET_SCOPE_REVIEW`.

The follow-up
[Post-experimental ResultDataset scope review](../roadmap/post_exp_resultdataset_scope_review.md)
keeps this result classified as `skipped-missing`, keeps issue `#8` open, and
separates prepared-machine validation from future release-boundary decisions.
