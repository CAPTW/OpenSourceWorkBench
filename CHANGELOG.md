# Changelog

All notable OpenSolver Workbench changes are summarized here for release
review. OSW follows source-first release evidence; public tags are created only
by a dedicated release/tag gate.

## Unreleased

### v0.1.4-rc1 Public Prerelease And Live Optional Validation

- Published `v0.1.4-rc1` as a public prerelease with wheel, sdist, Windows
  portable ZIP, `SHA256SUMS.txt`, and `release_asset_manifest.json` assets.
- Recorded an installed-only live optional validation matrix for issues `#6`
  through `#11`. On this machine, Gmsh, GNU Octave, CalculiX `ccx`, OpenFOAM,
  CoolProp/Cantera, and PyVista/meshio were missing, so each target was
  classified as `skipped-missing` and remains open for a prepared validation
  environment.
- Added a prepared-machine plan for issues `#6` through `#11`, defining
  required packages/executables, future installed-only validation commands,
  pass/partial/keep-open criteria, and separate closure-gate requirements.
- Added a design-only FEASpec IR contract for future VFEA work, defining
  `FEASpecCandidate` versus approved FEASpec, explicit units, GeometryGraph,
  materials/sections, boundary conditions, loads, dimensions, assumptions,
  evidence/confidence, diagnostics, validation states, serialization examples,
  and CalculiX-first compatibility without implementing FEASpec/VFEA, VLM APIs,
  solver execution, mandatory Abaqus, topology optimization, or certification
  claims.
- Added canonical FEASpec JSON examples and six synthetic benchmark seed
  folders for future FEASpec model and validator work. The fixtures cover
  candidate, approved, and invalid diagnostic cases with placeholder source
  metadata and planned metrics only; no generated images, solver outputs, VLM
  runs, mandatory Abaqus, or certification claims are included.
- Added an experimental FEASpec Python model layer under
  `src/osw/experimental/feaspec/` that loads, basic-checks, and serializes the
  examples and benchmark seeds. The layer is structural only and does not add a
  production/full physics validator, full ProjectSchema persistence,
  ProjectSchema mutation, solver adapter/exporter, VLM API, credential
  handling, automatic solver execution, mandatory Abaqus, topology
  optimization, or certification claim.
- Added a design-only FEASpec validator contract covering pipeline phases,
  diagnostic schema, severity taxonomy, required diagnostic codes, approval
  rules, solver handoff gates, CalculiX-first compatibility, Abaqus
  optional/non-default handling, and benchmark readiness. The contract does not
  implement the production validator, full ProjectSchema persistence,
  ProjectSchema mutation, solver adapter/exporter, VLM API, credentials, or
  solver execution.
- Added an experimental FEASpec semantic validator report layer under
  `src/osw/experimental/feaspec/`, with structured severities, diagnostic
  categories, stable diagnostic codes, phase results, approval and solver
  handoff blockers, CalculiX-first field-level compatibility, Abaqus
  optional/non-default diagnostics, and benchmark readiness checks for existing
  examples and seed fixtures. It does not implement full physics validation,
  full ProjectSchema persistence, ProjectSchema mutation, solver
  adapters/exporters, VLM APIs, credentials, or solver execution.
- Added a design-only FEASpec to ProjectSchema bridge contract that requires an
  approved FEASpec and validator report with no blockers, maps reviewed fields
  to current ProjectSchema concepts where safe, preserves explicit units,
  provenance/evidence, confidence, diagnostics, and unmapped fields, and records
  ProjectSchema extension needs. It does not mutate ProjectSchema, generate
  solver exports, call VLM APIs, handle credentials, or execute solvers.
- Added an experimental FEASpec to ProjectSchema bridge plan layer under
  `src/osw/experimental/feaspec/`, with `plan_project_from_feaspec`,
  `explain_bridge_plan`, `FEASpecProjectBridgePlan`, bridge diagnostics,
  extension needs, unmapped fields, provenance preservation, and
  ProjectSchema-compatible draft dictionaries for approved examples. It blocks
  candidates and invalid fixtures and does not persist ProjectSchema files,
  mutate ProjectSchema, call SolverAdapter/exporter code, generate solver
  decks, call VLM APIs, handle credentials, or execute solvers.
- Added a design-only FEASpec to CalculiX case-planning contract that defines
  approved-FEASpec, validator, and bridge preconditions; a future case-plan
  object shape; mesh requirements; node/element/material/section/BC/load/step
  and output planning; `FC_*` diagnostics; and issue `#8` separation. It does
  not add a case generator, `.inp` writer, SolverAdapter/exporter call, live
  `ccx` validation, or solver execution.
- Added an experimental FEASpec to CalculiX case-plan model under
  `src/osw/experimental/feaspec/`, with `plan_calculix_case_from_feaspec`,
  `plan_calculix_case_from_bridge`, `explain_calculix_case_plan`,
  `FEASpecCalculiXCasePlan`, node/element/material/section/BC/load/step/output
  planning records, and `FC_*` diagnostics. It preserves approved bridge
  evidence, blocks candidates and validator/bridge blockers, marks examples
  without explicit mesh topology as `FC_MESH_REQUIRED`, keeps
  `ready_for_solver_execution` false, and does not write `.inp` files, call
  solver adapters/exporters, run `ccx`, mutate ProjectSchema, add VLM APIs, or
  execute solvers.
- Added a design-only FEASpec to CalculiX `.inp` writer contract that defines
  future writer preconditions, proposed render/write APIs, result objects,
  deterministic file-section ordering, provenance comments, `FW_*` diagnostics,
  golden fixture strategy, issue `#8` separation, and the no-run safety
  boundary. It does not implement a writer, generate `.inp` files, call
  SolverAdapter or runner code, mutate ProjectSchema, run CalculiX, add VLM
  APIs, or execute solvers.
- Added an experimental no-run FEASpec CalculiX `.inp` renderer under
  `src/osw/experimental/feaspec/`, with public render/write/explain APIs,
  `FW_*` diagnostics, deterministic section ordering, provenance and
  no-certification comments, and overwrite-guarded caller-path writes. Approved
  examples still block until explicit mesh topology exists, test file writes
  stay under pytest `tmp_path`, and the renderer does not run `ccx`, call
  SolverAdapter or runner code, mutate ProjectSchema, validate issue `#8`, add
  VLM APIs, or add tracked `.inp` fixtures.
- Added controlled no-run FEASpec CalculiX `.inp` golden text fixtures under
  `tests/fixtures/feaspec/calculix_golden/`, with README/manifest metadata,
  SHA-256 checks, normalized renderer comparisons for synthetic cantilever and
  truss cases, and QA allowlist coverage for arbitrary `.inp` rejection. These
  fixtures are not solver outputs, do not run `ccx`, do not validate issue
  `#8`, and do not claim engineering correctness or certification.
- Added an experimental no-run FEASpec CalculiX export bundle layer under
  `src/osw/experimental/feaspec/`, with `export_calculix_case`,
  `export_calculix_case_from_feaspec`, `export_calculix_case_from_bridge`, and
  `explain_calculix_export_result`. It writes only caller-directory `.inp`,
  manifest JSON, diagnostics JSON, and `README_RUN_FIRST.txt` bundles after
  renderer success, includes checksums and no-run metadata, blocks unsafe
  basenames and overwrite risks, keeps `ready_for_solver_execution` false, and
  does not run `ccx`, call SolverAdapter or runner code, mutate ProjectSchema,
  validate issue `#8`, add VLM APIs, or stage runtime export bundles.
- Added `feaspec-calculix-export-preview`, an experimental no-run CLI command
  that reads FEASpec JSON and reports validation, bridge, case-plan, render,
  planned-file, and diagnostic status in text or JSON. It supports strict
  blocked-preview exit code `2`, writes no files, creates no output
  directories, runs no `ccx`, calls no SolverAdapter or runner code, mutates no
  ProjectSchema, validates no issue `#8`, and stages no runtime export bundles.
- Added `feaspec-calculix-export-write`, an experimental no-run CLI command
  that requires an explicit output directory and writes local export bundles
  only through the no-run exporter API. It blocks missing mesh/topology examples,
  supports text and JSON output plus explicit `--create-dir`/`--overwrite`,
  writes only `.inp`, manifest JSON, diagnostics JSON, and README files on
  success, runs no `ccx`, calls no SolverAdapter or runner code, mutates no
  ProjectSchema, validates no issue `#8`, and stages no runtime export bundles.
- Added a design-only FEASpec CalculiX result import / run gate document for
  post-export sequencing. It keeps FEASpec human review, no-run export
  preview/write, installed-only run, result import, and ResultDataset/report
  summary as separate future gates; defines `FR_*` and `FI_*` diagnostics; and
  does not implement result import, run commands, SolverAdapter/runner or
  subprocess paths, ProjectSchema mutation, solver execution, live issue `#8`
  validation, or release mutation.
- Added an experimental FEASpec human review record model under
  `src/osw/experimental/feaspec/`, with JSON-serializable reviewer state,
  action, accepted warnings, diagnostic decisions, validator summary/hash,
  bridge/case/export summaries, acknowledgements, and solver-execution flags.
  It records `solver_execution_performed=false` and does not implement a GUI,
  CLI approval command, result import, run gate, SolverAdapter/runner path,
  ProjectSchema mutation, VLM API, credential handling, issue `#8`
  validation, or solver execution.
- Added `feaspec-human-review-create`, `feaspec-human-review-validate`, and
  `feaspec-human-review-summary` as experimental record-only CLI commands for
  FEASpec human-review JSON. They validate before writing, refuse implicit
  parent-directory creation, guard overwrite behavior, support text and JSON
  output, keep `solver_execution_performed=false`, and do not implement GUI,
  result import, run gate, SolverAdapter/runner/subprocess paths,
  ProjectSchema mutation, live issue `#8` validation, VLM APIs, dependency
  install, or solver execution.
- Added a design-only FEASpec human review GUI dialog contract that maps the
  human-review record model and CLI approval workflow into future dialog entry
  points, panels, warning acceptance, approval gating, record preview, save
  behavior, CLI/GUI consistency, and view-model planning. It does not implement
  GUI source, result import, run-gate behavior, SolverAdapter/runner/subprocess
  paths, ProjectSchema mutation, live issue `#8` validation, VLM APIs,
  dependency installation, or solver execution.
- Added an experimental pure Python FEASpec human review dialog view-model
  layer under `src/osw/experimental/feaspec/`. It computes dialog panels,
  diagnostic rows, warning acceptance rows, action availability and disabled
  reasons, record previews, and save-path plans for a future GUI while avoiding
  PySide/Qt imports, GUI source mutation, result import, run-gate behavior,
  SolverAdapter/runner/subprocess paths, exporter/renderer side effects,
  ProjectSchema mutation, live issue `#8` validation, VLM APIs, dependency
  installation, and solver execution.
- Added a read-only FEASpec human review GUI dialog under `src/osw/gui/dialogs/`
  that binds to the existing view-model. It renders source evidence,
  diagnostics, warning rows, disabled action reasons, safety copy, and record
  preview only. It adds no record save integration, file dialog, result import
  implementation, installed-only run gate implementation, SolverAdapter/runner
  or subprocess path, ProjectSchema mutation, live issue `#8` validation, VLM
  API, dependency installation or upgrade, release mutation, or solver
  execution.
- Added explicit FEASpec human review GUI save integration for caller-provided
  JSON paths. The dialog validates the in-memory review record before writing,
  refuses unacknowledged overwrites, creates no parent directories, and writes
  exactly one human-review JSON record. It adds no file dialog, export bundle
  write, `.inp` write, result import implementation, installed-only run gate,
  SolverAdapter/runner/subprocess path, ProjectSchema mutation, live issue `#8`
  validation, VLM API, dependency installation or upgrade, release mutation, or
  solver execution.
- Added a design-only FEASpec human review GUI file-dialog contract for future
  review-record JSON path selection. The design covers entry points, default
  filename sanitization, JSON filters, directory policy, overwrite
  confirmation, path safety, save-plan integration, error handling, and future
  implementation tests without adding `QFileDialog` usage, GUI source mutation,
  export bundle writes, result import, run gates, SolverAdapter/runner paths,
  ProjectSchema mutation, live issue `#8` validation, VLM APIs, dependency
  changes, release mutation, or solver execution.
- Added FEASpec human review GUI file-dialog implementation for review-record
  JSON save-path selection only. The chooser is mockable in tests, uses a
  deterministic sanitized default filename and narrow JSON filter, treats
  cancel as no-op, requires overwrite confirmation, creates no parent
  directories, writes nothing until the existing save integration is triggered,
  and adds no export bundle write, `.inp` write, result import, run gate,
  SolverAdapter/runner/subprocess path, ProjectSchema mutation, live issue
  `#8` validation, VLM API, dependency installation or upgrade, release
  mutation, or solver execution.
- Added `feaspec-calculix-run-installed-only`, an experimental installed-only
  FEASpec CalculiX run gate for existing no-run export bundles. It defaults to
  dry-run, requires explicit `--execute`, `--confirm-run`, and
  `--acknowledge-readme` before invoking an already installed `ccx`, writes
  isolated runtime logs and `run_metadata.json`, and has fake-`ccx` tests for
  success, nonzero exit, timeout, missing executable, invalid bundle, and CLI
  behavior. It does not install solvers or dependencies, import results, call
  SolverAdapter or runner code, mutate ProjectSchema, validate or close issue
  `#8`, edit releases/assets/tags, add VLM APIs, bundle external solvers, or
  claim industrial certification.
- Added an experimental FEASpec CalculiX result import model under
  `src/osw/experimental/feaspec/`. It inspects explicit result directories,
  classifies run metadata, export manifests, diagnostics, stdout/stderr, and
  `.dat`/`.frd`/`.sta`/`.cvg` artifacts, preserves provenance, reports `FI_*`
  diagnostics, and builds an in-memory ResultDataset draft with artifact and
  field references. It does not parse numerical result content, write
  ResultDataset files, add a write-capable import CLI, execute CalculiX, call
  SolverAdapter or runner code, mutate ProjectSchema, validate or close issue
  `#8`, add VLM APIs, bundle external solvers, or claim industrial
  certification.
- Added `feaspec-calculix-result-import-preview`, an experimental preview-only
  CLI command for the FEASpec CalculiX result import model. It requires an
  explicit result directory, classifies existing artifacts, reports text or JSON
  diagnostics, exposes an in-memory ResultDataset draft with `writes_files=false`,
  and supports strict exit code `2` for blocked, unsupported, or future-parser
  cases. It does not parse numerical `.dat`/`.frd` content, write ResultDataset
  files, execute CalculiX, call SolverAdapter or runner code, mutate
  ProjectSchema, validate or close issue `#8`, add VLM APIs, bundle external
  solvers, or claim industrial certification.
- Added an experimental FEASpec CalculiX `.sta` / `.cvg` status scanner under
  `src/osw/experimental/feaspec/`. It classifies text-only progress,
  convergence-message, warning, error, completion, failure, informational, and
  unknown lines with bounded snippets and counts, enriches result-import
  previews with status summaries, and preserves metadata scanner hashes and
  limits. It does not parse numeric convergence values, parse `.dat`/`.frd`
  numerical content, write ResultDataset files, execute CalculiX, call
  SolverAdapter or runner code, mutate ProjectSchema, validate or close issue
  `#8`, add VLM APIs, bundle external solvers, or claim industrial
  certification.
- Added a design-only FEASpec CalculiX `.dat` minimal parser contract. It
  defines the future accepted header/scalar/table preview subset, rejected
  unknown or unitless content, safety limits, unit-handling rules, `FP_DAT_*`
  diagnostics, output model, ResultDataset preview mapping, and fixture
  strategy without adding `.dat` parser implementation, numerical extraction,
  ResultDataset writes, solver execution, SolverAdapter/runner paths,
  ProjectSchema mutation, issue `#8` validation, bundled solvers, or
  certification claims.
- Added an experimental FEASpec CalculiX `.dat` metadata section scanner under
  `src/osw/experimental/feaspec/`. It classifies direct `.dat` heading text,
  section spans, section kinds, unsupported/unknown sections, bounded snippets,
  and section counts, then enriches result-import previews with
  `dat_section_summary` metadata. It does not extract numeric values, extract
  table rows or columns, infer units, write ResultDataset files, execute
  CalculiX, call SolverAdapter or runner code, mutate ProjectSchema, validate
  or close issue `#8`, add VLM APIs, bundle external solvers, or claim
  industrial certification.
- Added an experimental FEASpec CalculiX `.dat` minimal parser under
  `src/osw/experimental/feaspec/`. It consumes section-scanner output and
  parses only explicit scalar candidates plus small delimited table candidates
  with explicit units or caller `unit_context`, preserving raw text, line
  provenance, diagnostics, and limitations. It enriches result-import previews
  in memory only and does not implement free-form `.dat` parsing, `.frd`
  parsing, unit inference, mesh/field reconstruction, ResultDataset writes,
  solver execution, SolverAdapter/runner calls, ProjectSchema mutation, issue
  `#8` validation, VLM APIs, bundled solvers, or certification claims.
- Added an experimental FEASpec CalculiX `.frd` block metadata scanner under
  `src/osw/experimental/feaspec/`. It classifies block labels, spans, block
  kinds, unsupported/unknown records, snippets, and deferred reference
  candidates; enriches result-import model and CLI preview summaries in memory;
  and preserves the design baseline. It does not parse numerical field values,
  reconstruct mesh, build visualization arrays, infer units, write
  ResultDataset files, execute solvers, call SolverAdapter/runner code, mutate
  ProjectSchema, validate issue `#8`, add VLM APIs, bundle solvers, or claim
  certification.
- Added an experimental FEASpec CalculiX ResultDataset draft mapping layer
  under `src/osw/experimental/feaspec/`. It maps result import artifacts,
  `.sta`/`.cvg` status summaries, bounded `.dat` scalar/table candidates,
  deferred `.frd` references, provenance, diagnostics, and limitations into a
  stable in-memory draft and exposes CLI preview counts. It does not persist or
  write ResultDataset files, parse additional `.frd` numerical field values,
  reconstruct meshes, infer units, execute solvers, call SolverAdapter/runner
  code, mutate ProjectSchema, validate issue `#8`, add VLM APIs, bundle
  solvers, or claim certification.
- Added a design-only FEASpec CalculiX ResultDataset write-flow contract. It
  defines the future output layout, schema/versioning, explicit path and
  overwrite policy, atomic-write strategy, artifact references,
  validation-before-write rules, CLI/GUI future design, and `FDW_*`
  diagnostics while adding no persistence implementation, file writes, `.frd`
  numerical parsing, mesh reconstruction, solver execution, SolverAdapter or
  runner integration, ProjectSchema mutation, issue `#8` validation, bundled
  solvers, or certification claims.
- Added an experimental FEASpec CalculiX ResultDataset write plan model under
  `src/osw/experimental/feaspec/`. It validates reviewed output-directory
  intent, path safety, planned standard files, future atomic write paths,
  artifact references, draft diagnostics, provenance, and limitations
  acknowledgement in memory only. It writes no files, creates no directories,
  copies no artifacts, performs no ResultDataset persistence, adds no
  write-capable import CLI/GUI, executes no solver, calls no SolverAdapter or
  runner code, mutates no ProjectSchema, validates no issue `#8`, adds no VLM
  APIs, bundles no solvers, and claims no certification.
- Added an experimental FEASpec CalculiX ResultDataset schema payload model
  under `src/osw/experimental/feaspec/`. It assembles deterministic in-memory
  ResultDataset, manifest, diagnostics, provenance, and review README payload
  records from the reviewed draft mapping and write plan. It writes no files,
  creates no directories, copies no artifacts, performs no ResultDataset
  persistence, adds no write-capable import CLI/GUI, executes no solver, calls
  no SolverAdapter or runner code, mutates no ProjectSchema, validates no issue
  `#8`, adds no VLM APIs, bundles no solvers, and claims no certification.
- Preserved the release boundaries: no dependency install, solver install,
  release mutation, asset upload, issue closure, bundled external solver,
  stable-production claim, industrial certification claim, or VFEA
  implementation claim.

### v0.1.4rc1 Candidate Metadata Aligned

Candidate package version: `0.1.4rc1`

- Aligned package, CLI, and release metadata for the `v0.1.4-rc1` prerelease
  candidate after the release-boundary decision selected the v0.1.4 line. No
  `v0.1.4-rc1` tag, release assets, or GitHub Release were created by this
  metadata gate.

### v0.1.3rc2 Maintenance Development Cycle Opened

Previous development package version: `0.1.3rc2.dev0`

- Added reusable release asset download smoke automation for Issue `#2`,
  covering `SHA256SUMS.txt`, `release_asset_manifest.json`, safe archive
  checks, and optional full wheel/sdist/portable ZIP smoke.
- Improved Windows portable ZIP user guidance for Issue `#4`, including
  unsigned/no MSI/no code-signing warnings, no bundled external solver wording,
  checksum verification, and future `README_RUN_FIRST.txt` template guidance.
- Added a read-only `Release asset smoke` GitHub Actions workflow for Issue
  `#2`: pull requests and `develop` pushes use offline release asset fixtures,
  while live GitHub release downloads are manual `workflow_dispatch` only.
- Made the offline release asset fixture byte-stable across CI checkouts so
  `release_asset_manifest.json` checksum verification is not changed by Git
  line-ending normalization.
- Documented the OSW-MAINT-002 duplicate-file quarantine review for Issue `#1`,
  retaining 19 divergent archived files under ignored artifacts with no restore,
  no permanent deletion, and no high-risk secrets found.
- Added v0.1.3rc2 maintenance issue closure triage for Issues `#1`, `#2`,
  `#4`, and `#5`, recording evidence-based completion decisions without
  release, asset, or tag mutation.
- Finalized the reusable post-public release checklist for Issue `#3`, covering
  the `v0.1.3-rc1` flow from metadata/tag gates through draft, asset upload,
  publish, post-public audit, docs polish, CI/manual smoke, and issue closure
  triage without stable-production, MSI, signing, or bundled-solver claims.
- Added remaining-open-issue triage for the v0.1.3rc2 cycle, recommending
  Issue `#13` onboarding examples/tutorials as the next practical public
  usability slice, Issue `#16` as a release-trust fallback, and live optional
  validation only on machines with the relevant tools installed.
- Improved onboarding examples and tutorials for Issue `#13`, adding a tutorial
  index, first CLI walkthrough, first GUI walkthrough, result dataset
  walkthrough, release asset smoke walkthrough, categorized examples, and
  optional dependency diagnostics for the `0.1.3rc2.dev0` maintenance line.
- Recorded onboarding closure evidence for Issue `#13`, including first-run CLI
  smoke results, public docs QA coverage, and preserved prerelease/no
  bundled-solver limitations.
- Documented the code signing and installer strategy for Issue `#16`, covering
  current unsigned portable ZIP status, checksum/manifest limits, GitHub
  artifact attestation distinction, Authenticode signing options, MSI/MSIX/Store
  tradeoffs, and no-secret signing rules.
- Added remaining-open-issue triage after release-trust closure, recommending
  Issue `#12` v0.1.4 planning as the next gate, Issue `#15` Plugin Manager UX as
  the fallback implementation slice, and live optional validation / full-smoke
  workflow dispatch as deferred unless suitable environments or maintainer
  request are available.
- Added v0.1.4 feature selection planning for Issue `#12`, recommending a
  workflow/product-polish feature line with Issue `#15` Plugin Manager
  UX/install receipts as the first implementation candidate, Issue `#14`
  ResultViewer/FieldViewer workflow as the second candidate, Issue `#17` VFEA
  scope as planning-only, and Issues `#6`-`#11` live validation deferred until
  suitable environments are available.
- Locked v0.1.4 scope to Issue `#15` Plugin Manager UX/install receipts as the
  first implementation slice, keeping remote plugin store, dependency
  auto-install, plugin signing, marketplace behavior, plugin code execution
  during install, and GUI solver execution out of scope.
- Improved Plugin Manager UX for Issue `#15`, adding clearer managed install
  receipt summaries, quarantine/rejection records, diagnostics/safety
  messaging, managed-root uninstall eligibility, and CLI wording consistency
  without adding remote store, dependency auto-install, plugin signing,
  marketplace behavior, or plugin code execution during install.
- Recorded Plugin Manager UX closure evidence for Issue `#15`, preserving the
  local-only install, manifest-only validation, managed-root uninstall, no
  remote store, no dependency auto-install, no signing, and no marketplace
  boundaries.
- Recorded v0.1.4 planning closure evidence for Issue `#12` after feature
  selection, scope lock, Issue `#15` implementation, and Issue `#15` closure
  evidence landed on `develop`; Issue `#14` remains the next feature candidate,
  Issue `#17` remains experimental/deferred, and Issues `#6`-`#11` remain
  environment-dependent live validation.
- Improved ResultViewer / FieldViewer workflow for Issue `#14`, adding clearer
  catalog summaries, dataset details, plot/table/field/report handoff hints,
  field artifact summaries, diagnostics, PyVista optional/fallback state, and
  summary-first limitations without adding solver execution, script execution,
  full FRD/OpenFOAM field parsing, or mandatory PyVista.
- Recorded ResultViewer / FieldViewer closure evidence for Issue `#14`,
  preserving the no solver execution, no script execution, no external command
  execution, optional PyVista, and no full FRD/OpenFOAM field parser boundaries.
- Added v0.1.4 remaining scope review after Issue `#14` and Issue `#15`
  closure, selecting Issue `#17` VFEA experimental scope definition as the next
  planning-only slice while keeping Issues `#6`-`#11` live optional validation
  environment-dependent and deferred.
- Defined the experimental VFEA scope for Issue `#17`, documenting FEASpec
  candidate/validator/human-review/benchmark requirements, CalculiX-first
  planning, optional/non-default Abaqus export planning only, and explicit
  non-goals against automatic unreviewed solver execution, VLM API integration,
  topology optimization implementation, and certification claims.
- Recorded VFEA scope closure evidence for Issue `#17`, preserving the
  planning-only status, human-review requirement, no automatic solver execution,
  no mandatory Abaqus, no credentials, no topology optimization implementation,
  no certification, and no native commercial CAD import boundaries.
- Added a v0.1.4 completion review, recording that Issues `#12`, `#15`, `#14`,
  and `#17` complete the planned workflow/product-polish and VFEA scope line
  while Issues `#6`-`#11` remain live optional validation and no version, tag,
  release, or asset mutation is performed.
- Added a release-boundary decision recommending `v0.1.4-rc1` as the cleaner
  next prerelease boundary if maintainers choose release prep, while preserving
  active metadata `0.1.3rc2.dev0` until a later metadata-alignment gate.
- Recorded a `v0.1.3rc2` maintenance revalidation baseline covering release
  integrity, workflow safety, asset smoke evidence, known warnings, and next
  maintenance choices.
- Opened the `v0.1.3rc2` maintenance development cycle after the public
  `v0.1.3-rc1` prerelease and attached release assets.
- Carried forward the local validation documentation commit with PySide6/Pillow
  evidence and the missing optional solver/science backend matrix.
- Kept `v0.1.3-rc1` as the current public prerelease tag; no `v0.1.3-rc2` tag
  was created by this development-cycle gate.

### Patch v0.1.3rc1 Release Candidate Tag Published

Release-candidate package version: `0.1.3rc1`

Release-candidate tag: `v0.1.3-rc1`

- OSW-RELEASE-003 aligns source package metadata to `0.1.3rc1` after
  OSW-RELEASE-002 preserved historical local tags through `v0.1.2` and repaired
  the default editable import path for this checkout.
- OSW-RELEASE-005 created the local annotated `v0.1.3-rc1` tag, OSW-RELEASE-008
  pushed only that tag to `origin`, and OSW-RELEASE-009 verified that the remote
  tag peels to `a6e8d3a8211e02359841d10e1947e16ab847b132`.
- The existing `v0.1.2` final tag remains historical source-release evidence at
  `c39f21372ef837f096aa0d430cced82adc6f3485` and must not be moved,
  recreated, retargeted, deleted, or reused as the current `develop` line.
- No branch push, all-tags push, force push, GitHub Release, package artifact,
  binary installer, or public announcement was created by the v0.1.3rc1
  tag-only gates.

## 0.1.2 - GitHub Source Release Published

### Patch v0.1.2 Source Release

Final package version: `0.1.2`

Published final tag: `v0.1.2`

- OSW-AUTO-072 prepared final `0.1.2` package metadata after the local
  `v0.1.2-rc1` candidate and OSW-AUTO-071 triage reported no P0/P1 blockers.
- OSW-AUTO-073 created the local annotated `v0.1.2` tag, and OSW-AUTO-077
  pushed only `refs/heads/develop:refs/heads/develop` and
  `refs/tags/v0.1.2:refs/tags/v0.1.2` to GitHub.
- Remote `develop` and `v0.1.2^{}` both resolve to
  `c39f21372ef837f096aa0d430cced82adc6f3485`; the remote annotated tag object
  verified by OSW-AUTO-077 is `353a87897c842ee01aaae18abc4d69f330406e09`.
- Local `v0.1.2-rc1` remains annotated evidence at
  `28b30c1f79d4c62d160629e96fc1fcefa2382ebe` and was not pushed by
  OSW-AUTO-077.
- The local `v0.1.1` final tag remains historical local-only evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197` and must not be published as
  current after the OSW-AUTO-067 GUI workflow fix.
- GUI workflow evidence remains based on OSW-AUTO-068 and OSW-AUTO-070: import
  creates visible project items, Project Tree and Properties update,
  Run/Generate uses `WorkbenchWorkflowSession`, and table/report state reflects
  imported project data and diagnostics.
- Known limitations remain P2/P3: optional external solver executables and
  live runs are environment-specific, manual desktop CUA depth is limited,
  Cantera 3.2 emits a deprecation warning, external URL freshness is outside the
  local docs checker, and packaging smoke is separate.
- Release artifacts, a GitHub Release page, binary installers, and public
  announcement text were not created by the source publish gate.

### Patch v0.1.2rc1 Release Candidate

- OSW-AUTO-070 prepares package metadata for `0.1.2rc1` and the local
  annotated `v0.1.2-rc1` release-candidate gate after OSW-AUTO-068 verified
  the GUI workflow fix with no P0/P1 blockers.
- The local `v0.1.1` final tag remains historical evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197` and must not be published as
  current after the post-tag GUI workflow fix.
- `v0.1.2-rc1` is local-only unless a later explicit maintainer push gate
  approves it. Final `0.1.2` / `v0.1.2`, release artifacts, public push, and
  announcement remain blocked.

### GUI Workflow Glue

- OSW-AUTO-067 improves the GUI-native Import -> Configure/Inspect ->
  Run/Generate -> Result/Table -> Report path after OSW-AUTO-066 classified the
  interactive GUI workflow as `PASS_WITH_LIMITATIONS`.
- GUI imports can now add visible project items for supported mesh, standard
  geometry, `.m`, and `.mat` preview paths; selection updates the properties
  panel and table/plot/mesh preview state where data is available.
- GUI Run/Generate routes through a workflow service that prepares bounded
  case/template outputs or records optional dependency diagnostics without
  direct GUI solver subprocess execution.
- GUI report export now includes current imported/project state, result tables,
  mesh metadata, figure placeholders, and diagnostics when available.
- The local annotated `v0.1.1` tag remains preserved release evidence at
  `7b232f5003fcc8eb207846570499ffb3442d3197`. After this post-release workflow
  fix merges, `develop` is ahead of `v0.1.1`; public publish remains blocked
  pending a new release/version decision.

## 0.1.1 - Final Metadata Prepared

Final package version: `0.1.1`

Planned final local tag: `v0.1.1`

Final v0.1.1 metadata is prepared after the patch RC1 recovery path passed local
QA and source-install validation. The final `v0.1.1` tag is not created by this
release-prep update; it remains pending a dedicated local tag gate. No public tag
push, release artifact build, external solver binary bundle, remote push gate, or
public announcement is created by this update.

### Release Evidence

- Historical local `v0.1.0` evidence remains preserved at
  `da8728adf679314442755ed781c1dd57d1c6ed27` and must not be published as the
  current release.
- Local annotated `v0.1.1-rc1` evidence remains preserved at
  `da1a2c9e2d27674dc4bb85a2800138170c4c4dec`; it was not pushed.
- OSW-AUTO-061A was a docs/readiness cleanup only. The maintainer accepted that
  docs-only post-RC delta for this final-prep path.
- OSW-AUTO-057 fixed the isolated source-run blockers found after the local
  `v0.1.0` tag was created, including Ruff UP042 enum issues and subprocess
  PATH stabilization for QA tests.
- OSW-AUTO-058 verified a fresh source-install retest with no P0/P1 blockers.
- OSW-AUTO-060 verified `0.1.1rc1` source-install validation with ruff,
  default/importlib pytest, fast QA, pre-merge QA, docs link checking, and
  duplicate basename checking.

### Known Limitations

- Optional external solver executables remain environment-specific and are not
  bundled by default.
- GUI live interaction depth remains environment-specific; source-install
  validation records dependency and offscreen/QA evidence, not a full manual GUI
  UAT.
- External URL freshness remains out of scope for the local-only docs checker.
- Public push remains blocked until an explicit maintainer gate.

## 0.1.1rc1 - Patch Release Candidate

Release candidate package version: `0.1.1rc1`

Local release-candidate tag: `v0.1.1-rc1`

This patch release candidate follows the source-install recovery path selected
in OSW-AUTO-059. The existing local annotated `v0.1.0` tag remains historical
local-only evidence at `da8728adf679314442755ed781c1dd57d1c6ed27` and must not
be published as the current release. `v0.1.1-rc1` is local-only unless a later
explicit maintainer push gate approves the exact tag.

No final `v0.1.1` tag, public tag push, release artifact build, external solver
binary bundle, remote push gate, or public announcement is created by this
release-candidate prep.

### Fixed Blocker Summary

- OSW-AUTO-057 fixed the isolated source-run blockers found after the local
  `v0.1.0` tag was created, including Ruff UP042 enum issues and subprocess
  PATH stabilization for QA tests.
- OSW-AUTO-058 verified a fresh source-install retest with ruff, default
  pytest, importlib pytest, fast QA, pre-merge QA, docs link checking, duplicate
  basename checking, and GUI offscreen launch passing with no P0/P1 blockers.
- OSW-AUTO-060 updates package metadata and release checks for the
  `0.1.1rc1` patch candidate without moving or publishing historical tags.

### Known Limitations

- Optional external solver executables remain environment-specific and are not
  bundled by default.
- GUI live interaction depth remains environment-specific even though offscreen
  launch smoke passed in source-install retest.
- External URL freshness remains out of scope for the local-only docs checker.
- Final `v0.1.1` remains blocked until a later final release gate.
- Public push remains blocked until an explicit maintainer gate.

## 0.1.0 - Final Metadata Prepared

Final package version: `0.1.0`

Planned final local tag: `v0.1.0`

Final v0.1.0 metadata is prepared after local RC3 UAT passed with no P0 or P1
blockers. The final `v0.1.0` tag is not created by this release-prep update; it
remains pending a dedicated local tag gate. No public tag push, release artifact
build, external solver binary bundle, remote push gate, or public announcement is
created by this update.

Local annotated `v0.1.0-rc1`, `v0.1.0-rc2`, and `v0.1.0-rc3` remain historical
local release evidence. RC3 points to
`dc7df75c53f0a4acb0a1ccf33d97c01ffdde4b16`, the last release-candidate commit
before this final metadata-prep change.

### Highlights

- PySide6 desktop GUI shell architecture remains optional behind the `gui`
  extra, with CLI diagnostics when PySide6 is unavailable.
- Plugin/add-in architecture covers importers, solvers, scripts,
  post-processing, and reports without executing plugin code during manifest
  validation.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset define
  the core v0.1 data contracts.
- Standard/exported CAD and mesh import policy remains explicit; commercial
  native CAD direct import is out of scope.
- meshio, Gmsh, PyVista, and Matplotlib workflows are optional integration
  surfaces with missing-dependency diagnostics.
- CalculiX linear static demo coverage includes input deck generation, optional
  runner diagnostics, result parsing, golden fixtures, and validation helpers.
- OpenFOAM cavity and duct template demos remain bounded educational templates,
  not a full OpenFOAM UI.
- Cantera and CoolProp basic demos cover small chemistry/property workflows with
  explicit SI-unit data and optional dependency behavior.
- MATLAB/Octave `.m` and `.mat` workflows remain preview-first; importing a
  script does not auto-run code.
- FigureDataset, ResultDataset, and HTML report workflows include assumptions,
  warnings, validation notes, figures, result tables, and known limitations.
- Validation, golden tests, docs link checking, duplicate test basename
  prevention, scope checks, architecture checks, and solver artifact scans are
  part of the release QA harness.

### RC3 Local UAT Summary

- OSW-AUTO-052 local UAT passed with no P0 or P1 blockers.
- Automated QA passed: release metadata, docs link checker, duplicate basename
  checker, scope drift, architecture boundaries, solver artifact scan, fast QA,
  pre-merge QA, ruff, required pytest suites, and default `pytest -q`.
- Demo smoke results: CAD import and HTML report passed; mesh import, Gmsh,
  CalculiX, OpenFOAM, Cantera/CoolProp, and MATLAB/Octave workflows passed with
  optional dependency missing where local optional stacks were unavailable.
- PySide6 was missing in the local UAT environment, so GUI help and friendly
  missing-extra diagnostics passed, but live GUI interaction was skipped.
- Live external solver runs were not performed because local solver executables
  and optional stacks were missing; this is treated as environment-specific and
  non-blocking for the base v0.1 source workflow.

### Known Limitations

- Simulink, `.slx`, and `.mlapp` workflows are not supported.
- Native commercial CAD direct import is not supported; use standard/exported
  formats such as STEP, STL, OBJ, IGES, BREP, or mesh formats.
- OSW is not a MATLAB clone, full ANSYS clone, full OpenFOAM UI, industrial
  certified CAE product, or substitute for expert engineering judgment.
- External solver executables and heavy optional Python stacks are not bundled
  by default and remain local environment responsibilities.
- External URL freshness is intentionally out of scope for the local-only docs
  link checker.

## 0.1.0rc3 - Draft

Release candidate package version: `0.1.0rc3`

Planned local release-candidate tag: `v0.1.0-rc3`

RC3 is the current local release-candidate target for `develop` after the
post-RC2 hardening work in OSW-AUTO-047 and OSW-AUTO-048. Local annotated
`v0.1.0-rc1` remains historical evidence at
`29c5c8bec8df30c7f7be72fc9be5e5409794968e`; local annotated `v0.1.0-rc2`
remains historical evidence at
`684dc6138d4257564bbcdd176a9d5ed311a7316d` and is no longer current
`develop` after OSW-AUTO-047/048. Neither prior RC tag should be pushed as the
current RC.

No public tag push, final `v0.1.0` tag, release artifact build, external solver
binary bundle, remote push gate, or public announcement is created by this
release-notes update.

### Highlights

- Package and CLI version metadata move from `0.1.0rc2` to `0.1.0rc3`.
- Release metadata QA accepts prior local rc1 and rc2 evidence while validating
  an expected annotated rc3 tag after the local tag gate.
- Default `pytest -q` collection remains fixed by OSW-AUTO-047 through unique
  test basenames and duplicate-basename QA.
- Documentation link checking is implemented by OSW-AUTO-048 and remains
  local-only/no-network by default. External URL freshness is intentionally out
  of scope for that checker.

### Known Limitations

- OSW v0.1 remains educational and research oriented, with unchanged
  out-of-scope boundaries recorded in `docs/known_limitations.md`.
- Optional external solvers and tools are not bundled by default.
- Final `v0.1.0`, public tag push, release artifacts, and public announcement
  remain blocked until separate maintainer-controlled gates.

## 0.1.0rc2 - Draft

Release candidate package version: `0.1.0rc2`

Planned release-candidate tag: `v0.1.0-rc2`

RC2 supersedes the local-only rc1 tag as the current `develop` release
candidate. The existing local `v0.1.0-rc1` tag remains historical evidence for
OSW-AUTO-043 and must not be pushed as the current RC after OSW-AUTO-044A/045.

No public tag push, final `v0.1.0` tag, release artifact build, external solver
binary bundle, or public announcement is created by this release-notes update.

### Highlights

- Package and CLI version metadata move from `0.1.0rc1` to `0.1.0rc2`.
- Release metadata QA now supports strict pre-tag checks, prior local RC
  evidence, and current RC tag validation without mutating tags.
- RC2 keeps the v0.1 feature scope from rc1: PySide6 GUI shell,
  plugin/add-in architecture, ProjectSchema / UnitSystem / MaterialDB,
  standard CAD/Mesh import policy, meshio/Gmsh/PyVista surfaces, CalculiX
  linear static demo, OpenFOAM cavity/duct templates, Cantera/CoolProp demos,
  MATLAB/Octave preview-first workflow, FigureDataset / ResultDataset / report
  flow, validation/golden/QA harness.

### Known Limitations

- OSW v0.1 remains educational and research oriented, with unchanged
  out-of-scope boundaries recorded in `docs/known_limitations.md`.
- Optional external solvers and tools are not bundled by default.
- Default `pytest -q` duplicate basename collection behavior remains a P2
  follow-up if still present; split suites and importlib-mode collection remain
  release evidence.
- `tools/qa/check_docs_links.py` remains a P2 follow-up if still absent.

## 0.1.0rc1 - Draft

Release candidate package version: `0.1.0rc1`

Planned release-candidate tag: `v0.1.0-rc1`

No Git tag is created by the release-notes step.

### Highlights

- PySide6 GUI shell with preview-oriented workflows.
- Plugin/add-in architecture for importers, solvers, script workflows,
  post-processing, and reports.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset
  contracts.
- Standard/exported CAD and mesh import policy; no native commercial CAD direct
  import claim.
- meshio, Gmsh, and PyVista pipeline surfaces with optional dependency
  diagnostics.
- CalculiX linear static cantilever demo with input deck generation, optional
  runner diagnostics, result summaries, and validation helper.
- OpenFOAM cavity and duct template demos; no full OpenFOAM UI or broad solver
  coverage claim.
- Cantera and CoolProp basic chemistry/property demos with optional dependency
  diagnostics.
- MATLAB/Octave `.m` and `.mat` preview-first workflow; script execution remains
  explicit and user-triggered.
- FigureDataset, ResultDataset, and HTML report workflow with assumptions,
  warnings, validation notes, and known limitations.
- Validation matrix, golden tests, physical sanity checks, and local QA harness
  for release readiness review.
- Plugin install, manifest validation, and health reporting surfaces designed to
  avoid executing plugin code during manifest validation.

### Known Limitations

- OSW v0.1 is educational and research oriented; it is not industrial
  certified and does not replace expert engineering judgment.
- Simulink, `.slx`, and `.mlapp` workflows are not supported.
- Commercial native CAD direct import is not supported. Use standard/exported
  formats such as STEP, STL, OBJ, IGES, or mesh formats.
- OSW is not a MATLAB clone, ANSYS clone, commercial CAD replacement, process
  simulator, or full OpenFOAM UI.
- OpenFOAM support is limited to bounded cavity and duct templates.
- Optional external solvers and tools such as CalculiX, OpenFOAM tools, Gmsh,
  GNU Octave, and SU2 are not bundled by default.
- Optional Python stacks such as PySide6, meshio, PyVista, Cantera, CoolProp,
  SciPy, and hdf5storage may be absent in base environments and should produce
  diagnostics or skips rather than hidden success.
- The broad default `pytest -q` command has a P2 follow-up for duplicate test
  module basename collection behavior if still present; CI-style split suites
  and importlib-mode collection are the current release evidence path.
- `tools/qa/check_docs_links.py` remains a P2 follow-up if still absent; docs
  link checking is recorded as a placeholder skip.

### QA Evidence Summary

- Pre-merge QA: `python tools/qa/run_pre_merge_qa.py` is part of the release
  evidence path when available.
- Fast QA: `python tools/qa/run_fast_qa.py` checks CLI version, doctor output,
  unit tests, lint, scope, architecture, and artifact scans.
- Unit, integration, golden, and validation suites are documented in
  `docs/10_release_checklist.md`.
- Optional external solver smoke checks remain environment-specific and are not
  required for base release-candidate metadata.

### Release Discipline

- Repository source license: `GPL-3.0-or-later`.
- The `LICENSE` file contains canonical GNU GPL version 3 text; the "or later"
  grant is recorded in project metadata and release documentation.
- Third-party dependency and optional solver notices are tracked in
  `docs/14_third_party_notices.md`.
- Source and wheel artifacts may be prepared only after the dedicated release/tag
  gate passes. External solver binaries are not bundled by default.
