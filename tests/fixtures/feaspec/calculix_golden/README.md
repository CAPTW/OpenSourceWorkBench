# FEASpec CalculiX golden INP fixtures

These are no-run golden text fixtures for the experimental FEASpec CalculiX
INP renderer. They are not solver outputs, were not produced by running
CalculiX, and are used only to lock deterministic renderer text.
They were not produced by running CalculiX.

The fixtures are not evidence of engineering correctness, are not validation
results, and are not industrial certification. Live `ccx` validation remains
issue #8 and is separate from these fixtures.

The fixture files are intentionally small:

- `cantilever_minimal.inp`
- `truss_minimal.inp`

They contain deterministic header comments and CalculiX input-card text only.
They do not contain local machine paths, timestamps, solver logs, `.frd`,
`.dat`, `.sta`, `.cvg`, `.12d`, `.out`, or `.err` output content.
