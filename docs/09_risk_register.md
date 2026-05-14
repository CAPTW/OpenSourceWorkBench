# Risk Register

| Risk | Impact | Mitigation | Fallback |
| --- | --- | --- | --- |
| Scope drift toward proprietary clone behavior | Confuses project identity and invites impossible expectations | Keep non-goals in README, North Star, guardrails, and review protocol | Remove or rewrite claims; park the feature behind a decision log |
| CAD import expectations | Pulls v0.1 into licensed, unstable, unsupported native formats | Accept only standard/exported STEP, IGES, STL, mesh, and similar formats | Document manual export workflow from commercial tools |
| External solver execution | Unsafe process control, unclear logs, and difficult failure recovery | Keep GUI to preparation, preview, validation, and result import; require future runner design | Provide case preparation and run instructions outside GUI |
| `.m` execution safety | Arbitrary scripts may mutate files, call shell commands, or depend on proprietary toolboxes | Preview `.m` and `.mat` content first; do not auto-run arbitrary `.m` code | Treat workflow as figure/data preview only until a sandboxed runner exists |
| GUI dependency burden | PySide6 can slow setup and block headless contributors | Keep GUI as an optional extra and keep CLI/unit tests GUI-free | Ship CLI and docs workflows while GUI extras are unavailable |
| Validation without golden evidence | Weak research credibility and over-trust in demo outputs | Add validation matrix rows, assumptions, limitations, and golden fixtures as demos mature | Mark workflow as preview-only until evidence exists |
| Simulink, `.slx`, or `.mlapp` expectations | Creates MATLAB product compatibility burden | Limit script support to preview-first `.m` and `.mat` workflows | Defer as post-v0.1 research topic with explicit non-goal note |
| Full OpenFOAM UI or solver coverage | Expands beyond a bounded educational demo | Keep only cavity/duct templates and documented limitations | Ship template preparation/reporting without broad case editor |
| Industrial certification claims | Legal and trust risk | Ban certification/compliance/production accuracy language in docs and UI | Replace with educational/research validation wording |
| Heavy dependencies blocking bootstrap | Slows contributors and CI | Keep PySide6, mesh, viz, thermo, and script stacks as optional extras | Allow doctor to report missing optional modules without failing |
| Solver runtime artifacts committed | Pollutes repo and hides reproducibility issues | Use `.gitignore`, preflight checks, and review gates | Remove artifacts from index and store curated fixtures under examples/tests |
| Report output overclaiming results | Users may trust unvalidated results | Reports must list assumptions, limitations, and validation status | Block release of report feature until warnings are present |
| Plugin API too broad too early | Locks weak abstractions into v0.1 | Start with narrow importer/solver/report contracts | Keep experimental plugin APIs internal until stable |
| Optional solver tools missing locally | Demos fail on contributor machines | Doctor command reports availability; tests stay network-free and solver-free | Provide fixture-only or template-only demo mode |
| Nonlinear contact/plasticity pressure | Pulls v0.1 into advanced nonlinear CAE validation | Mark as future research unless a later prompt explicitly defers it | Keep CalculiX v0.1 demo linear static only |
| Final license decision pending | Public release cannot make clear license and reuse terms | Treat license finalization as a P1 release blocker | Do not tag or announce public v0.1 until `LICENSE` and package metadata are finalized |
| Broad `pytest -q` collection mismatch | A single all-tests command can fail before running tests, despite CI-style split suites passing | Track as P2 test configuration cleanup; keep CI using explicit suite commands | Use `pytest -q --import-mode=importlib` or rename duplicate test modules in a focused PR |
| Docs link checker absent | Release docs rely on targeted local link checks instead of a reusable project command | Keep CI skip explicit and record manual/targeted checks | Add `tools/qa/check_docs_links.py` in a small QA tooling PR |

## Review Trigger Risks

Any review finding in these areas should block merge until fixed:

- native commercial CAD direct import;
- Simulink or `.mlapp` support;
- full OpenFOAM UI or full solver coverage;
- industrial certification or production CAE claims;
- GUI direct subprocess solver execution;
- committed runtime artifacts, secrets, or generated junk.
