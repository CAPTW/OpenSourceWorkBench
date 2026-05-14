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
| License metadata drift after finalization | Future edits could make `LICENSE`, pyproject metadata, README, release checklist, or plugin metadata disagree | Keep `GPL-3.0-or-later` recorded in the decision log, license/version plan, release checklist, and release metadata QA check | Block release/tag prompts until metadata is realigned |
| RC local tag gate bypass | A local RC tag could be created before QA, notices, or final checklist evidence are reviewed | Require OSW-AUTO-043 feature-branch QA, squash merge, post-merge pre-tag QA, annotated tag verification, and clean `develop` state | Do not push or announce; if an unpushed local tag is rejected later, use maintainer-approved local tag deletion only |
| Release metadata tag-mode mismatch | A QA checker can reject valid post-tag evidence if it only supports pre-tag metadata prompts | Keep `check_release_metadata.py` split between strict pre-tag mode and RC-aware expected annotated tag mode | Block push gates until the checker accepts only the intended local RC tag and still rejects final or unexpected tags |
| Stale RC tag after release-gate follow-up commit | A later QA-tooling commit can make an earlier local RC tag no longer represent current `develop` | Treat `v0.1.0-rc1` as local-only OSW-AUTO-043 evidence after OSW-AUTO-044A and treat `v0.1.0-rc2` as local-only OSW-AUTO-045/046 evidence after OSW-AUTO-047 advances `develop` | Do not push stale RC tags after follow-up commits; run a fresh RC3 tag gate for the next current RC |
| RC2 tag gate bypass | A current RC2 tag could be created before version metadata, release notes, QA, or rc1 preservation are verified | Require OSW-AUTO-045 version bump, feature-branch QA, squash merge, post-merge pre-tag QA, rc1 verification, and annotated rc2 verification | Do not create or push `v0.1.0-rc2` outside the focused RC2 gate; after OSW-AUTO-047, use a later RC3 gate if a current pushable RC is needed |
| Public tag push without approval | A local release-candidate tag could be treated as a public release before maintainer approval | Keep local tag creation separate from push approval and require explicit maintainer instruction before any `git push --tags` or tag push | Stop and keep the local tag unpushed until maintainer direction is explicit |
| Final tag gate bypass | The final `v0.1.0` tag could be created during the RC gate | Keep final tag creation blocked until a separate final release gate | Do not create or move `v0.1.0` in RC prompts |
| Third-party notices require maintainer review | Optional dependencies and plugin ecosystems may have redistribution obligations that are not fully captured in source docs | Maintain `docs/14_third_party_notices.md`, review notices before source/wheel release, and perform separate review before any binary distribution | Ship source-first artifacts and avoid bundled external solver binaries |
| External solver binaries accidentally bundled | Release artifacts could inherit unreviewed redistribution duties or platform-specific binary risk | Keep CalculiX, OpenFOAM, Gmsh, GNU Octave, and SU2 as user-installed optional runtime tools | Remove binaries from artifacts and document install-only handoff |
| Release artifacts staged by mistake | `dist/`, `build/`, `wheelhouse/`, logs, or generated solver outputs could enter a release commit | Run solver artifact and release metadata scans before merge and before any tag prompt | Stop release, remove artifacts from the index, and rerun QA before tagging |
| Broad `pytest -q` collection mismatch | A single all-tests command can fail before running tests if duplicate test basenames reappear | Rename colliding test modules and run `tools/qa/check_duplicate_test_basenames.py` in fast QA | Block future duplicate basenames before merge; use `pytest -q --import-mode=importlib` only as diagnostic evidence, not as the default fix |
| Docs link checker regression | Broken local Markdown links could enter release docs or examples | Run `tools/qa/check_docs_links.py` in fast and pre-merge QA; keep it local-only and exclude generated `.codex/reports/` evidence | Fix broken links narrowly or block release docs changes until links pass |

## Review Trigger Risks

Any review finding in these areas should block merge until fixed:

- native commercial CAD direct import;
- Simulink or `.mlapp` support;
- full OpenFOAM UI or full solver coverage;
- industrial certification or production CAE claims;
- GUI direct subprocess solver execution;
- committed runtime artifacts, secrets, or generated junk.
