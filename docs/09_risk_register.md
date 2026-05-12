# Risk Register

| Risk | Impact | Mitigation | Fallback |
| --- | --- | --- | --- |
| Scope drift toward proprietary clone behavior | Confuses project identity and invites impossible expectations | Keep non-goals in README, North Star, and review protocol | Remove or rewrite claims; park the feature behind a decision log |
| Native commercial CAD requests | Pulls v0.1 into licensed, unstable, unsupported territory | Accept only standard/exported STEP, IGES, STL, mesh, and similar formats | Document manual export workflow from commercial tools |
| Simulink, `.slx`, or `.mlapp` expectations | Creates MATLAB product compatibility burden | Limit script support to preview-first `.m` and `.mat` workflows | Defer as post-v0.1 research topic with explicit non-goal note |
| Full OpenFOAM UI or solver coverage | Expands beyond a bounded educational demo | Keep only cavity/duct templates and documented limitations | Ship template preparation/reporting without broad case editor |
| Industrial certification claims | Legal and trust risk | Ban certification/compliance/production accuracy language in docs and UI | Replace with educational/research validation wording |
| GUI direct solver execution | Unsafe coupling and unclear failure recovery | Keep execution behind future backend/service boundary | Provide case preparation and run instructions outside GUI |
| Heavy dependencies blocking bootstrap | Slows contributors and CI | Keep PySide6, mesh, viz, thermo, and script stacks as optional extras | Allow doctor to report missing optional modules without failing |
| Solver runtime artifacts committed | Pollutes repo and hides reproducibility issues | Use `.gitignore`, preflight checks, and review gates | Remove artifacts from index and store curated fixtures under examples/tests |
| Validation without golden evidence | Weak research credibility | Add golden fixtures and validation matrix rows as demos mature | Mark workflow as preview-only until evidence exists |
| Report output overclaiming results | Users may trust unvalidated results | Reports must list assumptions, limitations, and validation status | Block release of report feature until warnings are present |
| Plugin API too broad too early | Locks weak abstractions into v0.1 | Start with narrow importer/solver/report contracts | Keep experimental plugin APIs internal until stable |
| Optional solver tools missing locally | Demos fail on contributor machines | Doctor command reports availability; tests stay network-free and solver-free | Provide fixture-only or template-only demo mode |

## Review Trigger Risks

Any review finding in these areas should block merge until fixed:

- native commercial CAD direct import;
- Simulink or `.mlapp` support;
- full OpenFOAM UI or full solver coverage;
- industrial certification or production CAE claims;
- GUI direct subprocess solver execution;
- committed runtime artifacts, secrets, or generated junk.
