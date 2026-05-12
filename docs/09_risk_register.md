# Risk Register

| Risk | Impact | Mitigation |
| --- | --- | --- |
| Scope drift toward proprietary clone behavior | Confuses project identity | Keep non-goals in README and reviews. |
| Heavy dependencies blocking bootstrap | Slows contributors | Keep extras optional and tests light. |
| Solver runtime artifacts committed | Pollutes repo and tests | Use `.gitignore` and Git preflight. |
| GUI executing solvers directly | Unsafe workflow coupling | Enforce backend boundary in architecture reviews. |
| Validation without golden evidence | Weak research credibility | Add golden fixtures as demos mature. |
