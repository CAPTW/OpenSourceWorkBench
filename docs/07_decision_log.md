# Decision Log

| Date | Decision | Rationale |
| --- | --- | --- |
| 2026-05-12 | Use `src/osw` package layout | Keeps imports explicit and packaging clean. |
| 2026-05-12 | Keep heavy dependencies as optional extras | Allows bootstrap tests without GUI or solver stacks. |
| 2026-05-12 | Disable GUI direct solver execution for v0.1 | Preserves preview-first safety and clearer backend boundaries. |

Add new decisions when architecture, dependency, or scope policy changes.
