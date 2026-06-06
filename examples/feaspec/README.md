# FEASpec examples

These files are design-only examples for the experimental FEASpec IR. They are
not loaded by production code, not validated by a shipped FEASpec schema, and
not solver input decks.

Use these fixtures to understand the intended shape of future FEASpec data:

- `cantilever_beam_candidate.json`: untrusted draft with warnings.
- `cantilever_beam_approved.json`: human-reviewed educational benchmark.
- `truss_2d_candidate.json`: untrusted 2D truss draft.
- `truss_2d_approved.json`: human-reviewed 2D truss benchmark.
- `plate_with_hole_candidate.json`: candidate region/pressure example.
- `invalid_missing_units.json`: missing per-entity units diagnostic fixture.
- `invalid_unconnected_graph.json`: disconnected graph diagnostic fixture.
- `invalid_load_target.json`: invalid load target diagnostic fixture.

The examples preserve the FEASpec guardrails:

- FEASpec and VFEA are not implemented by these files.
- Solver execution is not performed or implied.
- VLM API integration, API keys, credentials, and provider configuration are
  absent.
- Abaqus is optional and non-default if mentioned.
- These examples do not claim industrial certification or production CAE
  accuracy.
