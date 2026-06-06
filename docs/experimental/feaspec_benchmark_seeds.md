# FEASpec benchmark seeds

Status: documentation and synthetic seed fixtures only; no generated images,
VLM provider runs, solver runs, or benchmark scores exist yet.

The benchmark seeds live under `tests/fixtures/feaspec/benchmark_seeds/`.
They provide deterministic text prompts, source metadata, approved ground-truth
FEASpec-style JSON, and planned detection metrics for future FEASpec models and
validators.

## Seed Folder Layout

Each seed folder contains:

- `prompt.txt`
- `source_metadata.json`
- `ground_truth_feaspec.json`
- `expected_metrics.json`
- `README.md`

`source_metadata.json` uses `source_type: "synthetic_drawing_placeholder"` and
`image_file: null`. No image is generated in this gate.

## Included Cases

- `cantilever_001`
- `cantilever_002`
- `truss_001`
- `truss_002`
- `frame_001`
- `plate_with_hole_001`

## Metrics Planned

Each `expected_metrics.json` records:

- schema validity requirement;
- required validation state;
- node, edge, boundary-condition, load, material, and dimension counts;
- expected solver compatibility planning states;
- future detection metrics for node precision, node recall, connectivity F1,
  boundary-condition accuracy, load accuracy, and dimension accuracy.

These are planned metrics for future validators and provider benchmarks. They
are not VLM benchmark scores and are not evidence of solver accuracy.

## Future Drawing Generation

A later gate may create simple synthetic drawing images from these seeds. That
future work should keep the image generation deterministic, license-safe, and
small. Generated images should point back to the seed folder and must not
replace the ground-truth FEASpec file.

## Future Closure Criteria

A future benchmark gate can be considered complete only after:

- seed folder schemas are validated by implementation code;
- generated drawings, if any, are deterministic and reviewed;
- benchmark metrics are computed without external solver execution;
- failures distinguish invalid candidates from approved ground truth;
- docs avoid industrial certification, stable-production, and bundled-solver
  claims.

## Non-Goals

- No generated solver result.
- No VLM benchmark score.
- No VLM API integration.
- No provider credentials or API keys.
- No solver execution.
- No CalculiX input deck generation.
- No Abaqus exporter or mandatory Abaqus dependency.
- No topology optimization.
- No industrial certification.
