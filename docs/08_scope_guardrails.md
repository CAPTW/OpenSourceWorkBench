# Scope Guardrails

These guardrails define what OSW v0.1 may do, what it must not do, and when a
request should stop, park, or defer.

## In Scope

- PySide6 GUI shell and workflow previews.
- Plugin/add-in contracts for importers, solvers, scripts, post-processing, and
  reports.
- Planning-only optional solver manifest UX design that improves optional
  dependency discovery, plugin manifest guidance, and health messaging without
  installing, bundling, or executing external solvers.
- Design-only optional solver manifest UX contracts that define target stacks,
  health states, future CLI/GUI surfaces, plugin-provided manifest trust
  boundaries, and validation relationships without implementing schemas,
  discovery services, CLI commands, GUI panels, or solver execution.
- Experimental optional solver manifest schema/model records that stay
  declarative: typed manifest fields, JSON I/O helpers, structural diagnostics,
  and built-in stack records without discovery, health-check execution, CLI or
  GUI surfaces, dependency installation, or solver execution.
- Design-only optional solver discovery service contracts that define passive
  metadata inspection, future presence-check boundaries, active validation-gate
  separation, diagnostics, privacy redaction, cache freshness, CLI/GUI handoff,
  and plugin trust boundaries without implementing discovery or executing
  commands.
- Experimental passive optional solver discovery services that consume
  declarative manifests, use injectable resolvers, redact local paths and
  environment values by default, map passive evidence to missing, partially
  installed, discovered, or unknown states, and do not execute solver commands,
  import optional solver packages, install dependencies, mutate issues, or
  claim validation success.
- Experimental optional solver CLI preview commands that list built-in
  manifests, explain one stack, and show passive doctor evidence in text or
  JSON while redacting paths by default, never exposing environment values,
  and not installing dependencies, running smoke checks, executing solver
  commands, mutating issues, or claiming validation success.
- Design-only optional solver GUI health panel contracts that define future
  entry points, panel layout, stack cards, details, diagnostics, guidance,
  validation history, redaction/privacy behavior, user actions, accessibility,
  plugin trust labels, and pure view-model boundaries without implementing GUI
  source, view-model source, CLI behavior changes, plugin loading, active
  smoke validation, solver command execution, dependency installation, issue
  mutation, release mutation, or validation success claims.
- Experimental optional solver GUI health panel view-model records that remain
  pure Python and UI-agnostic: summary counts, stack cards, details,
  diagnostics, guidance, validation history, filters, and action states from
  supplied manifests and passive discovery reports, without PySide/Qt imports,
  GUI widgets, discovery execution, solver command execution, dependency
  installation, issue mutation, release mutation, or validation success claims.
- Experimental optional solver GUI health panel display source that consumes an
  already-built view-model and renders read-only PySide summary, card, details,
  diagnostics, guidance, validation-history, safety, and action-state sections,
  without GUI-initiated discovery, solver command execution, subprocess usage,
  install actions, issue closure actions, release mutation, or validation
  success claims.
- Experimental optional solver GUI export summary payloads that consume an
  already-built health panel view-model, render redacted JSON, Markdown, and
  plain text in memory, and analyze save paths without GUI widgets, file
  writes, clipboard integration, shell/browser actions, discovery execution,
  solver command execution, issue mutation, or validation success claims.
- Experimental optional solver GUI export summary action wiring that uses that
  payload layer, writes exactly one explicit `.json`, `.md`, or `.txt`
  redacted summary after path validation and overwrite confirmation, and still
  does not add clipboard integration, shell/browser actions, output-folder
  opening, discovery refresh, solver command execution, dependency
  installation, issue mutation, release mutation, or validation success claims.
- Design-only experimental optional solver GUI passive refresh planning that
  defines explicit user flow, injected runner boundaries, worker/threading
  policy, atomic view-model replacement, status/error display, privacy,
  export interaction, validation-gate separation, and future tests without
  mutating runtime source, GUI source, view-model source, CLI source, issues,
  releases, tags, assets, or validation status.
- Experimental optional solver GUI passive refresh view-model helpers that
  model refresh state, request/result metadata, action states, stale-result
  handling, success/failure/cancel apply results, atomic health panel
  view-model replacement, status/error text, and selected-stack/filter
  preservation over supplied passive reports without GUI source, worker source,
  discovery execution, solver command execution, dependency installation,
  issue mutation, release mutation, or validation success claims.
- Experimental optional solver GUI passive refresh action wiring that runs only
  after explicit user action, uses an injected runner or built-in passive
  discovery service, swaps the accepted health panel view-model atomically on
  success, preserves the prior view-model on failed/canceled/stale results, and
  keeps export bound to the accepted view-model without automatic startup
  refresh, background workers, active smoke validation, solver command
  execution, dependency installation, issue mutation, release mutation, or
  validation success claims.
- Experimental optional solver plugin manifest GUI display source that consumes
  an already-built plugin manifest GUI view-model and renders summary,
  accepted/rejected/conflict rows, diagnostics, trust/source labels, safety
  guidance, and disabled/future action states without file dialogs, file
  loading, plugin activation, package import, directory scan, network fetch,
  discovery execution, solver execution, dependency installation, issue
  mutation, release mutation, or validation success claims.
- Experimental optional solver plugin manifest explicit import GUI
  implementation that runs only after explicit user action, accepts one local
  `.json` file, delegates loading to the existing data-only loader, renders the
  OSW-EXP-076 explicit-import view-model, and keeps activation, plugin package
  import, directory scanning, network fetching, discovery execution, validation
  execution, solver execution, dependency installation, issue mutation, release
  mutation, bundled-solver claims, and certification claims out of scope.
- Experimental optional solver plugin manifest export-summary view-model records
  that remain pure Python and UI-agnostic: redacted header, section, source,
  candidate, acknowledgement, diagnostic, redaction/privacy, stale-source,
  conflict, unsafe-claim, evidence/history, limitation, non-action flag, and
  disabled/future action states over supplied records, without file export, file
  writes, export file creation, clipboard behavior, report attachment,
  reloadable bundles, runtime persistence behavior, settings files, runtime state
  files, schema files, ProjectSchema mutation, GUI behavior, CLI behavior, reload
  behavior, source behavior mutation, discovery execution, validation execution,
  solver execution, dependency installation, issue mutation, release mutation,
  tag mutation, asset mutation, version bump, validation claims, or certification
  claims.
- Experimental optional solver plugin manifest state-writer view-model records
  that remain pure Python, side-effect-free, and non-writing: storage options,
  write plans, schema/migration, redaction/privacy, acknowledgements, stale
  sources, conflicts/shared stacks, unsafe claims, evidence/history,
  atomicity/error plans, non-action flags, diagnostics, and disabled/future
  action states over supplied records, without writer implementation, file
  writes, directory creation, runtime state files, settings files, schema files,
  export/report files, reloadable bundles, ProjectSchema mutation, GUI behavior,
  CLI behavior, reload behavior, export behavior, clipboard/report/open-folder
  behavior, automatic activation, trust restoration, file mutation, dependency
  installation, dependency uninstall, solver uninstall, plugin package import,
  directory scan, network fetch, discovery execution, validation execution,
  solver execution, issue/release/tag/asset mutation, version bump, validation
  claims, or certification claims.
- Design-only optional solver plugin manifest export-summary GUI contracts that
  define future PySide review semantics over the OSW-EXP-097 export-summary
  view-model, including header, sections, source/provenance, candidate,
  acknowledgement, diagnostics, redaction/privacy, stale-source/re-preview,
  conflict/shared-stack, unsafe-claim, evidence/history, limitation, non-action
  flag, action-state, safety guidance, and `OSPMG_EXPORT_SUMMARY_GUI_*`
  diagnostic boundaries, without GUI implementation, file export, file writes,
  export file creation, report file creation, clipboard behavior, report
  attachment, open-output-folder behavior, reloadable bundle creation, runtime
  persistence behavior, settings files, runtime state files, schema files,
  ProjectSchema mutation, CLI behavior, reload behavior, source behavior
  mutation, automatic activation, trust restoration, file mutation, dependency
  installation, dependency uninstall, solver uninstall, plugin package import,
  directory scan, network fetch, discovery execution, validation execution,
  solver execution, issue/release/tag/asset mutation, version bump,
  validation-pass/fail claim, or certification claim.
- ProjectSchema, UnitSystem, MaterialDB, ResultDataset, and FigureDataset.
- Standard/exported CAD, CAE, CFD, chemistry, `.m`, and `.mat` workflows.
- meshio, Gmsh, PyVista, and Matplotlib integration points.
- Bounded educational demos for CalculiX, OpenFOAM templates, Cantera,
  CoolProp, and MATLAB/Octave figure preview.
- HTML reports, validation matrix, golden tests, and release checklist.
- Planning-only experimental VFEA scope documentation when it preserves human
  review, validation gates, and no automatic solver execution.
- Planning-only FEASpec IR design that records candidate data, explicit units,
  evidence, diagnostics, human approval, and future ProjectSchema/SolverAdapter
  boundaries without implementing solver behavior.
- FEASpec documentation examples and synthetic benchmark seed fixtures that
  remain JSON/text-only and do not include generated solver outputs.
- Experimental FEASpec Python models and structural basic checks that load and
  serialize documented fixtures without adding a production/full physics
  validator, full ProjectSchema persistence, ProjectSchema mutation, solver
  adapter, VLM provider, or solver execution.
- Design-only FEASpec validator contract documentation that defines future
  diagnostics, severity taxonomy, human-review gates, solver handoff blockers,
  CalculiX-first compatibility, Abaqus optional/non-default handling, and
  benchmark readiness without implementing runtime validator behavior.
- Experimental FEASpec semantic validator reports that validate documented
  model fields, examples, and benchmark readiness without mesh generation,
  numerical physics validation, full ProjectSchema persistence, ProjectSchema
  mutation, solver export, VLM integration, or solver execution.
- Design-only FEASpec to ProjectSchema bridge documentation that defines
  approved-spec preconditions, validator-report requirements, explicit-unit
  mapping, provenance/evidence preservation, bridge diagnostics, unmapped-field
  reporting, and ProjectSchema extension needs without full ProjectSchema
  persistence or schema mutation.
- Experimental FEASpec to ProjectSchema bridge plan layer that accepts only
  approved FEASpec, requires a validator report with no blockers, returns a
  draft plan with diagnostics, extension needs, unmapped fields, and a
  ProjectSchema-compatible dictionary, and still does not persist ProjectSchema,
  mutate ProjectSchema, call solver adapters/exporters, or execute solvers.
- Design-only FEASpec to CalculiX case planning that defines a future
  CalculiX-first case-plan object, mesh requirements, mapping diagnostics, and
  issue `#8` separation without implementing a case generator, `.inp` writer,
  SolverAdapter/exporter call, live `ccx` validation, or solver execution.
- Experimental FEASpec to CalculiX case-plan model that consumes only approved
  FEASpec bridge plans, returns serializable planning records and `FC_*`
  diagnostics, reports missing explicit mesh topology, and still does not write
  `.inp` files, call solver adapters/exporters, mutate ProjectSchema, run
  `ccx`, call VLM APIs, or execute solvers.
- Design-only FEASpec to CalculiX `.inp` writer documentation that defines
  future writer preconditions, `FW_*` diagnostics, deterministic section
  ordering, provenance comments, golden fixture strategy, and issue `#8`
  separation without implementing a writer, generating `.inp` files, calling
  solver adapters/runners, mutating ProjectSchema, or executing solvers.
- Experimental FEASpec CalculiX `.inp` renderer implementation that renders
  deterministic text only from writer-ready case plans, writes only to
  caller-provided paths with overwrite protection, and still does not run
  `ccx`, call SolverAdapter or runner code, mutate ProjectSchema, validate
  issue `#8`, add VLM APIs, or add tracked generated `.inp` fixtures.
- Controlled FEASpec CalculiX `.inp` golden text fixtures under
  `tests/fixtures/feaspec/calculix_golden/` that lock deterministic renderer
  output without running CalculiX, producing solver outputs, validating issue
  `#8`, or claiming engineering correctness.
- Experimental FEASpec CalculiX no-run export bundles that wrap successful
  renderer output into caller-provided directories with `.inp`, manifest JSON,
  diagnostics JSON, and README files while blocking unsafe basenames,
  preserving overwrite review, and still not running CalculiX, calling
  SolverAdapter or runner code, validating issue `#8`, or staging runtime
  export bundles.
- Experimental FEASpec CalculiX export preview CLI that reads FEASpec JSON,
  reports validation/bridge/case-plan/render diagnostics and planned bundle
  names, and still writes no files, creates no directories, runs no solver,
  calls no SolverAdapter or runner code, validates no issue `#8`, and stages no
  runtime export bundles.
- Experimental FEASpec CalculiX export write CLI that creates local no-run
  bundles only under explicit caller-provided output directories, blocks
  unsafe or unready inputs, writes only expected `.inp`, manifest, diagnostics,
  and README files, and still does not run CalculiX, call SolverAdapter or
  runner code, mutate ProjectSchema, validate issue `#8`, or stage runtime
  export bundles.
- Design-only FEASpec CalculiX result import / run gate planning that keeps
  export, human review, installed-only run, result import, and ResultDataset
  summary as separate future gates, defines `FR_*` and `FI_*` diagnostics, and
  does not implement result import, run commands, solver execution,
  SolverAdapter/runner/subprocess paths, ProjectSchema mutation, or issue `#8`
  closure.
- Experimental FEASpec CalculiX installed-only run gate behavior that validates
  existing no-run export bundles, defaults to dry-run, requires explicit
  execute, run confirmation, and README acknowledgement before a discovered
  `ccx` can be invoked, writes isolated runtime logs and metadata only under an
  explicit run directory, and still does not install solvers, import results,
  call SolverAdapter or broad runner code, mutate ProjectSchema, validate or
  close issue `#8`, edit releases/assets/tags, bundle external solvers, or
  claim certification.
- Experimental FEASpec CalculiX result import model and preview CLI behavior
  that inspects explicit result directories, classifies existing artifacts,
  reports `FI_*` diagnostics, and builds an in-memory ResultDataset draft with
  `writes_files=false`, while still avoiding broad numerical result parsing,
  ResultDataset persistence, solver execution, SolverAdapter/runner paths,
  ProjectSchema mutation, VLM APIs, issue `#8` closure, bundled solvers, and
  certification claims.
- Experimental FEASpec CalculiX `.sta` / `.cvg` status scanning that classifies
  text-only progress, convergence-message, warning, error, completion, failure,
  informational, and unknown lines with bounded snippets and counts, while
  still avoiding numeric convergence parsing, `.dat`/`.frd` numerical parsing,
  ResultDataset persistence, solver execution, SolverAdapter/runner paths,
  ProjectSchema mutation, live issue `#8` validation, bundled solvers, and
  certification claims.
- FEASpec CalculiX `.dat` minimal parser planning and bounded implementation
  that defines accepted known headings, explicit scalar/table preview
  candidates, unsupported content, safety limits, unit-handling rules,
  `FP_DAT_*` diagnostics, ResultDataset preview mapping, fixture strategy, and
  issue `#8` separation without implementing free-form `.dat` parsing, `.frd`
  parsing, unit inference, ResultDataset writes, solver execution,
  SolverAdapter/runner paths, ProjectSchema mutation, bundled solvers, or
  certification claims.
- Experimental FEASpec CalculiX `.dat` metadata section scanning that
  classifies heading text, line spans, section kinds, unsupported and unknown
  sections, bounded snippets, and counts while still avoiding numeric value
  extraction, table extraction, unit inference, ResultDataset writes, solver
  execution, SolverAdapter/runner paths, ProjectSchema mutation, live issue
  `#8` validation, bundled solvers, and certification claims.
- Experimental FEASpec CalculiX `.dat` minimal parsing that consumes section
  scanner output and parses only explicit scalar candidates plus small delimited
  table candidates with explicit units or caller `unit_context`, while still
  avoiding free-form `.dat` parsing, `.frd` numerical field parsing, unit inference,
  ResultDataset writes, solver execution, SolverAdapter/runner paths,
  ProjectSchema mutation, live issue `#8` validation, bundled solvers, and
  certification claims.
- FEASpec CalculiX `.frd` block metadata scanner that defines and implements
  only block-boundary metadata, field-reference candidates, mesh-reference
  candidates, unsupported diagnostics, `FP_FRD_*` codes, ResultDataset
  candidate-only mapping, and fixture strategy while still avoiding numerical
  field parsing, mesh reconstruction, visualization arrays, unit inference,
  ResultDataset writes, solver execution, SolverAdapter/runner paths,
  ProjectSchema mutation, live issue `#8` validation, bundled solvers, and
  certification claims.
- Experimental FEASpec CalculiX ResultDataset draft mapping that converts
  result-import artifacts, status summaries, bounded `.dat` scalar/table
  candidates, deferred `.frd` references, provenance, diagnostics, and
  limitations into an in-memory draft only while still avoiding ResultDataset
  persistence or writes, additional numerical parsing, mesh reconstruction,
  unit inference, solver execution, SolverAdapter/runner paths, ProjectSchema
  mutation, live issue `#8` validation, bundled solvers, and certification
  claims.
- Design-only FEASpec CalculiX ResultDataset write planning that defines future
  output layout, schema/versioning, explicit path and overwrite policy,
  atomic-write strategy, artifact references, validation-before-write rules,
  CLI/GUI future design, and `FDW_*` diagnostics while still avoiding
  ResultDataset persistence implementation, file writes, additional numerical
  parsing, mesh reconstruction, solver execution, SolverAdapter/runner paths,
  ProjectSchema mutation, live issue `#8` validation, bundled solvers, and
  certification claims.
- Experimental FEASpec CalculiX ResultDataset write planning model that
  validates explicit output-directory intent, path safety, planned standard
  files, future atomic write paths, artifact references, draft diagnostics,
  provenance, and limitations acknowledgement in memory only while still
  avoiding actual file writes, directory creation, artifact copying,
  ResultDataset persistence, write-capable CLI/GUI behavior, solver execution,
  SolverAdapter/runner paths, ProjectSchema mutation, live issue `#8`
  validation, bundled solvers, and certification claims.
- Experimental FEASpec CalculiX ResultDataset schema payload model that builds
  deterministic in-memory ResultDataset, manifest, diagnostics, provenance,
  and review README payload records from a reviewed draft mapping and write
  plan while still avoiding actual file writes, ResultDataset persistence,
  write-capable CLI/GUI behavior, atomic write implementation, artifact
  copying, solver execution, SolverAdapter/runner paths, ProjectSchema
  mutation, live issue `#8` validation, bundled solvers, and certification
  claims.
- Experimental FEASpec CalculiX ResultDataset library writer that consumes a
  validated write plan and schema payload, writes exactly the standard
  ResultDataset JSON, manifest, diagnostics, provenance, and review README
  files under explicit caller-reviewed output directories, and still avoids
  CLI/GUI behavior inside the writer, artifact copying, solver execution,
  SolverAdapter/runner paths, ProjectSchema mutation, live issue `#8`
  validation, bundled solvers, and certification claims.
- Historical FEASpec CalculiX result import write CLI planning that defined
  the `feaspec-calculix-result-import-write` review command, plan-only default
  behavior, explicit write mode, acknowledgements, text/JSON output, path
  policy, and safety boundary before implementation.
- Experimental FEASpec CalculiX result import write CLI behavior that defaults
  to plan-only review and writes standard ResultDataset review files only after
  explicit `--write`, output directory, limitations acknowledgement, and review
  acknowledgement while still avoiding artifact copying, solver execution,
  SolverAdapter/runner paths, ProjectSchema mutation, live issue `#8`
  validation, bundled solvers, and certification claims.
- Design-only FEASpec CalculiX result import write GUI planning that defines
  future preview entry points, panels, action states, disabled reasons,
  file-dialog policy, acknowledgements, and CLI/GUI consistency without adding
  GUI source, file dialogs, CLI behavior changes, solver execution, live issue
  `#8` validation, or certification claims.
- Experimental FEASpec CalculiX result write view-model behavior that computes
  UI-agnostic panels, rows, action states, disabled reasons,
  acknowledgements, preview records, and lexical save-path plans without
  importing PySide/Qt or GUI modules, opening file dialogs, invoking the
  writer, writing ResultDataset files, running solvers, importing
  SolverAdapter/runner/subprocess paths, mutating ProjectSchema, validating
  issue `#8`, or making certification claims.
- Experimental FEASpec CalculiX result write dialog behavior that renders the
  write view-model in a PySide6 dialog and may collect directory-only output
  selection and perform guarded ResultDataset persistence only through the
  existing library writer after enabled gates and explicit confirmation, while
  keeping artifact copying, CLI/library writer behavior changes, solver
  execution, SolverAdapter/runner paths, ProjectSchema mutation, live issue
  `#8` validation, bundled solvers, and certification claims out of scope.
- Design/planning-only FEASpec CalculiX result write GUI file-dialog behavior
  that defines future output-directory selection, default-directory policy,
  cancel no-op behavior, path validation, create-dir and overwrite
  acknowledgements, CLI/GUI consistency, and mocked implementation tests
  without adding QFileDialog implementation, GUI source changes, writer
  invocation, ResultDataset writes, solver execution, live issue `#8`
  validation, bundled solvers, or certification claims.
- Experimental FEASpec CalculiX result write GUI file-dialog behavior that
  uses directory-only output selection to update dialog-local selected-path
  display and save-plan analysis without invoking the writer, writing
  ResultDataset files, creating directories during selection, copying
  artifacts, changing CLI behavior, running solvers, validating issue `#8`,
  bundling solvers, or making certification claims.
- Experimental FEASpec CalculiX result write GUI writer integration behavior
  that enables write only after reviewed state and confirmation, delegates
  actual ResultDataset file writes to the existing library writer, writes only
  standard review files under the selected output directory, and still copies
  no original solver artifacts, opens no output-folder command, changes no CLI
  or library writer behavior, runs no solver, validates no issue `#8`, bundles
  no solvers, and makes no certification claims.
- Experimental FEASpec CalculiX result write GUI post-write polish behavior
  that formats writer status, written files, hashes, diagnostics, limitations,
  failure details, retry guidance, and copy-ready display text only. It still
  adds no OS clipboard integration, no open-output shell command, no artifact
  copying, no CLI/library writer behavior change, no solver execution, no
  issue `#8` validation, no bundled solvers, and no certification claims.
- FEASpec CalculiX result write GUI closure review that records the completed
  experimental review-file persistence slice without adding runtime source
  changes, parser changes, writer changes, solver execution, live issue `#8`
  validation, bundled solvers, or certification claims.
- Optional solver plugin manifest reload GUI file-dialog design that defines a
  future explicit user-selected file bridge from GUI preview to the reload
  reader and reload view-model without turning that design into GUI file-dialog
  implementation, GUI source edit, CLI source edit, runtime source edit,
  file-reader source edit, reload view-model source edit, file dialog widget
  implementation, file opening behavior, runtime file reading, runtime state
  parsing, runtime reload acceptance, default reload path, background reload,
  directory scan, network fetch, plugin package import, CLI subprocess use,
  reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, ProjectSchema mutation, live discovery,
  passive refresh, validation execution, solver execution, dependency
  installation, dependency uninstall, solver uninstall, automatic activation,
  trust restoration, issue closure, release mutation, tag mutation, asset
  mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate.
- Optional solver plugin manifest reload GUI file-dialog implementation that
  adds only an explicit user-selected file preview wrapper around the reload
  reader and existing reload review panel. It must stay reader-first and
  review-only: no default reload path, background reload, directory scan,
  network fetch, plugin package import, CLI subprocess bridge, runtime reload
  acceptance, ProjectSchema mutation, live discovery, passive refresh,
  validation execution, solver execution, dependency install/uninstall,
  automatic activation, trust restoration, issue/release/tag/asset mutation,
  version bump, validation-pass or validation-fail evidence, bundled-solver
  claim, certification claim, reloadable bundle creation, export/report file
  creation, clipboard behavior, report attachment, or open-output-folder
  behavior.
- Optional solver plugin manifest reload acceptance design that defines only a
  future explicit reviewed-preview-to-session-state boundary. It must stay
  design-only: no reload acceptance implementation, runtime source edit, GUI
  source edit, CLI source edit, file-reader source edit, reload view-model
  source edit, acceptance button implementation, acceptance CLI command
  implementation, persistence write, ProjectSchema mutation, runtime reload
  acceptance, default reload path, background reload, directory scan, network
  fetch, plugin package import, CLI subprocess use, reloadable bundle creation,
  export/report file creation, clipboard/report/open-folder behavior, live
  discovery, passive refresh, validation execution, solver execution,
  dependency installation, dependency uninstall, solver uninstall, automatic
  activation, trust restoration, issue/release/tag/asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate.
- Optional solver plugin manifest reload acceptance view-model implementation
  that models supplied reload preview readiness, blockers, acknowledgements,
  diagnostics, accepted-for-session-review representation, future review
  requirements, non-action flags, and disabled/future actions. It must stay
  pure and side-effect-free: no runtime reload acceptance, source file IO,
  reader invocation, GUI behavior, CLI behavior, acceptance buttons, acceptance
  CLI commands, persistence write, ProjectSchema mutation, default reload path,
  background reload, directory scan, network fetch, plugin package import, CLI
  subprocess use, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration,
  issue/release/tag/asset mutation, version bump, validation-pass or
  validation-fail evidence, bundled-solver claim, or certification claim
  without a separate gate.
- Post-experimental ResultDataset scope review that summarizes completed
  FEASpec/CalculiX parser/import/write/GUI evidence, records skipped-missing
  live CalculiX validation, keeps issues `#6` through `#11` open, and routes
  future publish work to a separate release-boundary decision without runtime
  source changes, solver execution, issue mutation, release mutation, version
  bump, bundled solvers, or certification claims.
- Post-experimental release-boundary decision documentation that selects the
  next prerelease boundary from evidence while avoiding metadata alignment, tag
  creation, release edits, asset build/upload, issue mutation, solver
  execution, dependency install, bundled-solver claims, and certification
  claims.
- Experimental FEASpec human review record model that serializes reviewer
  state/action, accepted-warning reasons, diagnostic decisions, validator
  summary/hash, bridge/case/export summaries, acknowledgements, and
  solver-execution flags without implementing a GUI, result importer, run
  gate, SolverAdapter/runner path, ProjectSchema mutation, VLM API, or solver
  execution.
- Experimental FEASpec human review CLI record workflow that creates,
  validates, and summarizes review JSON records while writing only explicit
  review JSON files, preserving `solver_execution_performed=false`, and still
  without implementing GUI, result import, installed-only run gate,
  SolverAdapter or runner paths, ProjectSchema mutation, VLM API, live `ccx`
  validation, or solver execution.
- Design-only FEASpec human review GUI dialog planning that maps the review
  record model and CLI workflow into future entry points, panels, diagnostic
  presentation, warning acceptance, approval gating, record preview, save
  behavior, CLI/GUI consistency, and view-model planning without implementing
  GUI source, result import, installed-only run gate behavior, SolverAdapter or
  runner paths, ProjectSchema mutation, VLM API, dependency installation, live
  `ccx` validation, or solver execution.
- Experimental FEASpec human review GUI dialog view-model state/action layer
  that remains UI-agnostic and pure Python, computes panels, diagnostics,
  warning rows, action availability, record preview, and save-plan analysis,
  and still does not import PySide/Qt or GUI modules, implement result import
  or run gates, call SolverAdapter/runner/subprocess paths, mutate
  ProjectSchema, install dependencies, validate issue `#8`, or execute
  solvers.
- Design-only FEASpec human review GUI file-dialog planning that defines
  future path selection for one explicit review-record JSON save path while
  preserving the existing save integration, overwrite guard, parent-directory
  behavior, path safety, no export bundle write, no result import, no run gate,
  no SolverAdapter/runner/subprocess path, no ProjectSchema mutation, no VLM
  API, and no solver execution.

## Out of Scope

- Native SolidWorks, CATIA, NX, Creo, or other commercial CAD direct import.
- Simulink, `.slx`, or `.mlapp` support.
- Full OpenFOAM solver coverage or a full OpenFOAM UI.
- Full MATLAB proprietary toolbox compatibility.
- Industrial certification, compliance, accuracy, or production CAE claims.
- GUI direct subprocess solver execution.
- Proprietary solver automation that requires licensed commercial software.
- Automatic unreviewed solver execution from image or VLM output.
- ProjectSchema or SolverAdapter handoff from an unapproved FEASpec candidate.
- Mandatory Abaqus dependency, Abaqus exporter implementation, or commercial
  solver requirement in VFEA planning.
- Topology optimization implementation inside the initial VFEA scope.
- FEASpec examples or benchmark seeds presented as solver-validated results.
- Treating FEASpec model parsing or basic checks as proof of physical validity,
  solver readiness, or industrial certification.
- Treating FEASpec validator design documentation as a production validator,
  ProjectSchema bridge, solver exporter, VLM provider, or solver execution
  capability.
- Treating FEASpec semantic validator reports as proof of physical correctness,
  generated solver cases, ProjectSchema conversion, VLM interpretation, or
  permission for unreviewed solver execution.
- Treating FEASpec to ProjectSchema bridge design as a source bridge
  implementation, ProjectSchema migration, SolverAdapter/export path, VLM
  provider, or permission to execute solvers.
- Treating FEASpec bridge plan output as full ProjectSchema persistence,
  ProjectSchema schema mutation, solver export, SolverAdapter handoff, VLM
  provider output, or permission to execute solvers.
- Treating FEASpec to CalculiX case planning as a case generator, `.inp`
  writer, SolverAdapter/exporter implementation, live `ccx` validation, or
  permission to execute solvers.
- Treating FEASpec to CalculiX case-plan model output as a solver deck,
  `.inp` writer handoff, SolverAdapter/exporter implementation, ProjectSchema
  mutation, live `ccx` validation, or permission to execute solvers.
- Treating FEASpec to CalculiX `.inp` writer design as an implemented writer,
  generated deck fixture, SolverAdapter/exporter implementation, live `ccx`
  validation, ProjectSchema mutation, or permission to execute solvers.
- Treating the FEASpec CalculiX `.inp` renderer as a CalculiX exporter,
  SolverAdapter integration, runner integration, live `ccx` validation,
  ProjectSchema mutation, physical validation, or permission to execute
  solvers.
- Treating FEASpec CalculiX `.inp` golden fixtures as solver outputs, live
  `ccx` validation, engineering-correctness evidence, or permission to execute
  solvers.
- Treating FEASpec CalculiX no-run export bundles as SolverAdapter
  integration, runner integration, installed `ccx` validation, engineering
  correctness evidence, or permission to execute solvers.
- Treating FEASpec CalculiX export preview CLI output as generated export
  files, live `ccx` validation, engineering correctness evidence, or permission
  to execute solvers.
- Treating FEASpec CalculiX export write CLI output as live `ccx` validation,
  release asset generation, engineering correctness evidence, SolverAdapter or
  runner integration, ProjectSchema mutation, or permission to execute solvers.
- Treating FEASpec CalculiX result import / run gate design as implemented
  result import, implemented run commands, SolverAdapter or runner integration,
  subprocess use, live `ccx` validation, release mutation, or permission to
  execute solvers.
- Treating FEASpec CalculiX `.sta` / `.cvg` status scanning as numerical
  convergence parsing, `.dat`/`.frd` parser implementation, ResultDataset
  persistence, live `ccx` validation, SolverAdapter/runner integration,
  ProjectSchema mutation, engineering-correctness evidence, or permission to
  execute solvers.
- Treating FEASpec CalculiX `.dat` minimal parser design or implementation as
  free-form `.dat` parsing, `.frd` parsing, unit inference, ResultDataset
  persistence, live `ccx` validation, SolverAdapter/runner integration,
  ProjectSchema mutation, engineering-correctness evidence, bundled-solver
  evidence, certification, or permission to execute solvers.
- Treating FEASpec CalculiX ResultDataset draft mapping as ResultDataset
  persistence, CLI persistence behavior, additional `.frd` numerical
  parsing, mesh reconstruction, unit inference, live `ccx` validation,
  SolverAdapter/runner integration, ProjectSchema mutation,
  engineering-correctness evidence, bundled-solver evidence, certification, or
  permission to execute solvers.
- Treating FEASpec CalculiX ResultDataset write design as implemented
  persistence, an import-write CLI/GUI, actual file writes, atomic-write code,
  schema implementation, `.frd` numerical parsing, mesh reconstruction, live
  `ccx` validation, SolverAdapter/runner integration, ProjectSchema mutation,
  bundled-solver evidence, certification, or permission to execute solvers.
- Treating FEASpec CalculiX ResultDataset write plans as persisted
  ResultDataset files, CLI behavior inside the plan model, a GUI write/import
  command, actual file writes, directory creation, artifact copying,
  implemented atomic persistence, schema migration implementation, live `ccx`
  validation, SolverAdapter/runner integration, ProjectSchema mutation,
  bundled-solver evidence, certification, or permission to execute solvers.
- Treating FEASpec CalculiX ResultDataset schema payloads as persisted
  ResultDataset files, CLI behavior inside the schema model, a GUI write/import
  command, actual file writes, directory creation, artifact copying,
  implemented atomic persistence, live `ccx` validation, SolverAdapter/runner
  integration, ProjectSchema mutation, bundled-solver evidence, certification,
  or permission to execute solvers.
- Treating FEASpec CalculiX result import write CLI behavior as GUI write/import
  behavior, broad ResultDataset persistence, artifact-copying flow, solver
  execution path, SolverAdapter/runner integration, subprocess or external
  command invocation, ProjectSchema mutation, dependency install, live issue
  `#8` validation, release mutation, issue closure, certification,
  bundled-solver evidence, or permission to execute solvers.
- Treating the FEASpec CalculiX installed-only run gate as result import,
  SolverAdapter integration, broad runner integration, GUI direct execution,
  dependency or solver installation, bundled solver evidence, live issue `#8`
  closure, engineering-correctness evidence, certification, or permission to
  bypass explicit export-bundle, confirmation, README, timeout, and isolated
  run-directory checks.
- Treating the FEASpec human review record model as a GUI implementation,
  result importer, run gate, SolverAdapter or runner integration,
  ProjectSchema mutation, VLM provider, credential surface, live `ccx`
  validation, or permission to execute solvers.
- Treating the FEASpec human review CLI workflow as a GUI implementation,
  result importer, installed-only run gate, SolverAdapter or runner
  integration, subprocess path, ProjectSchema mutation, VLM provider,
  credential surface, live `ccx` validation, export-bundle writer, or
  permission to execute solvers.
- Treating the FEASpec human review GUI dialog design as GUI source, result
  import implementation, installed-only run gate behavior, SolverAdapter or
  runner integration, subprocess path, ProjectSchema mutation, VLM provider,
  credential surface, live `ccx` validation, dependency installation, or
  permission to execute solvers.
- Treating the FEASpec human review GUI dialog view-model as GUI source,
  PySide/Qt widget behavior, result import implementation, installed-only run
  gate behavior, SolverAdapter or runner integration, subprocess path,
  ProjectSchema mutation, VLM provider, credential surface, live `ccx`
  validation, dependency installation, file-writing behavior, or permission to
  execute solvers.
- Treating the FEASpec human review GUI file-dialog design as implemented
  `QFileDialog` behavior, GUI source mutation, result import implementation,
  run gate behavior, SolverAdapter or runner integration, subprocess path,
  ProjectSchema mutation, VLM provider, credential surface, live `ccx`
  validation, dependency installation, file-writing behavior beyond the
  existing explicit JSON save integration, or permission to execute solvers.

## Scope Drift Definition

Scope drift is any change that:

- turns a bounded demo into broad solver/product coverage;
- implies OSW is a MATLAB, ANSYS, Simulink, or commercial CAD replacement;
- adds direct GUI execution of external solvers before backend safety exists;
- adds automatic unreviewed solver execution from image or VLM output;
- treats an unapproved FEASpec candidate as solver-ready;
- turns FEASpec basic checks into solver execution, solver export, or physical
  validation without a separate gate;
- turns FEASpec validator design into runtime validation, ProjectSchema
  persistence, solver export, or solver execution without a separate gate;
- turns FEASpec semantic validation into mesh generation, numerical physics
  validation, full ProjectSchema persistence, ProjectSchema mutation, solver
  export, VLM API integration, or solver execution without a separate gate;
- turns FEASpec bridge design into ProjectSchema mutation, source conversion
  behavior, solver adapter/export behavior, VLM API integration, or solver
  execution without a separate gate;
- turns FEASpec bridge plan behavior into full ProjectSchema persistence,
  ProjectSchema schema mutation, solver deck generation, solver
  adapter/export behavior, VLM API integration, or solver execution without a
  separate gate;
- turns FEASpec to CalculiX case planning into case generation, `.inp` writing,
  SolverAdapter/export behavior, live `ccx` validation, dependency install, or
  solver execution without a separate gate;
- turns FEASpec to CalculiX case-plan model output into solver deck writing,
  solver adapter/export behavior, live `ccx` validation, ProjectSchema
  mutation, dependency install, or solver execution without a separate gate;
- turns FEASpec to CalculiX `.inp` writer design into writer implementation,
  generated `.inp` fixtures, solver adapter/export behavior, live `ccx`
  validation, dependency install, or solver execution without a separate gate;
- turns the FEASpec CalculiX `.inp` renderer into SolverAdapter/exporter
  behavior, runner behavior, live `ccx` validation, dependency install,
  generated tracked `.inp` fixtures, ProjectSchema mutation, or solver
  execution without a separate gate;
- turns FEASpec CalculiX golden `.inp` fixtures into solver outputs, live
  validation evidence, physical validation, runner behavior, dependency
  install, or solver execution without a separate gate;
- turns the FEASpec CalculiX no-run exporter into SolverAdapter integration,
  runner behavior, live `ccx` validation, dependency install, automatic solver
  execution, release asset generation, or ProjectSchema mutation without a
  separate gate;
- turns the FEASpec CalculiX export preview CLI into file-writing export
  behavior, output directory creation, SolverAdapter integration, runner
  behavior, live `ccx` validation, dependency install, automatic solver
  execution, or ProjectSchema mutation without a separate gate;
- turns the FEASpec CalculiX export write CLI into CalculiX execution,
  SolverAdapter integration, runner behavior, live `ccx` validation,
  dependency install, automatic solver execution, ProjectSchema mutation,
  release asset generation, or hidden file writes outside explicit
  caller-provided output directories without a separate gate;
- turns the FEASpec CalculiX result import / run gate design into result import
  implementation, run command implementation, SolverAdapter integration,
  runner behavior, subprocess or external command invocation, live `ccx`
  validation, dependency install, ProjectSchema mutation, release mutation, or
  issue closure without a separate gate;
- turns the FEASpec CalculiX installed-only run gate into result import,
  SolverAdapter integration, broad runner behavior, GUI direct execution,
  dependency install, bundled-solver evidence, live issue `#8` closure,
  ProjectSchema mutation, release mutation, hidden execution, or execution
  without explicit run authorization and isolated runtime artifacts;
- turns the FEASpec CalculiX `.dat` minimal parser into free-form parser
  behavior, `.frd` parsing, unit inference, ResultDataset persistence,
  SolverAdapter/runner integration, subprocess or external command invocation,
  ProjectSchema mutation, dependency install, live
  issue `#8` validation, release mutation, issue closure, certification, or
  solver execution without a separate gate;
- turns the FEASpec CalculiX `.frd` block scanner design into `.frd` parser
  implementation, numerical field parsing, mesh reconstruction, unit inference,
  ResultDataset persistence, SolverAdapter/runner integration, subprocess or
  external command invocation, ProjectSchema mutation, dependency install,
  live issue `#8` validation, release mutation, issue closure, certification,
  or solver execution without a separate gate;
- turns the FEASpec CalculiX ResultDataset draft mapping into ResultDataset
  persistence or writes, additional numerical parsing, `.frd` field-value
  parsing, mesh reconstruction, unit inference, SolverAdapter/runner
  integration, subprocess or external command invocation, ProjectSchema
  mutation, dependency install, live issue `#8` validation, release mutation,
  issue closure, certification, or solver execution without a separate gate;
- turns the FEASpec CalculiX ResultDataset write design into ResultDataset
  persistence implementation, file writes, write-capable CLI or GUI behavior,
  atomic-write code, schema implementation, `.frd` numerical field parsing,
  mesh reconstruction, SolverAdapter/runner integration, subprocess or external
  command invocation, ProjectSchema mutation, dependency install, live issue
  `#8` validation, release mutation, issue closure, certification, or solver
  execution without a separate gate;
- turns the FEASpec CalculiX ResultDataset write plan into actual
  ResultDataset persistence, file writes, directory creation, artifact copying,
  write-capable CLI or GUI behavior, schema migration implementation,
  `.frd` numerical field parsing, mesh reconstruction, SolverAdapter/runner
  integration, subprocess or external command invocation, ProjectSchema
  mutation, dependency install, live issue `#8` validation, release mutation,
  issue closure, certification, or solver execution without a separate gate;
- turns the FEASpec CalculiX ResultDataset schema payload model into actual
  ResultDataset persistence, file writes, directory creation, artifact copying,
  write-capable CLI or GUI behavior, atomic write implementation, `.frd`
  numerical field parsing, mesh reconstruction, SolverAdapter/runner
  integration, subprocess or external command invocation, ProjectSchema
  mutation, dependency install, live issue `#8` validation, release mutation,
  issue closure, certification, or solver execution without a separate gate;
- turns the FEASpec CalculiX ResultDataset library writer into an import-write
  CLI or GUI command, artifact-copying implementation, solver execution path,
  numerical `.frd` parser, mesh reconstruction path, SolverAdapter/runner
  integration, subprocess or external command invocation, ProjectSchema
  mutation, dependency install, live issue `#8` validation, release mutation,
  issue closure, certification, or bundled-solver claim without a separate gate;
- turns the FEASpec CalculiX result import write CLI into GUI write/import
  behavior, broad ResultDataset persistence, artifact copying, solver execution
  path, SolverAdapter/runner integration, subprocess or external command
  invocation, ProjectSchema mutation, dependency install, live issue `#8`
  validation, release mutation, issue closure, certification, or
  bundled-solver claim without a separate gate;
- turns the FEASpec CalculiX result import write GUI design into GUI source,
  file-dialog implementation, hidden ResultDataset writes, artifact copying,
  solver execution path, SolverAdapter/runner integration, subprocess or
  external command invocation, ProjectSchema mutation, dependency install, live
  issue `#8` validation, release mutation, issue closure, certification, or
  bundled-solver claim without a separate gate;
- turns the FEASpec CalculiX result write view-model into a GUI dialog,
  file-dialog implementation, writer invocation path, ResultDataset write,
  artifact copying, solver execution path, SolverAdapter/runner integration,
  subprocess or external command invocation, ProjectSchema mutation,
  dependency install, live issue `#8` validation, release mutation, issue
  closure, certification, or bundled-solver claim without a separate gate;
- turns the FEASpec CalculiX result write GUI file-dialog planning into
  QFileDialog implementation, GUI source mutation, active GUI file writes,
  writer invocation, directory creation during selection, artifact copying,
  solver execution path, SolverAdapter/runner integration, subprocess or
  external command invocation, ProjectSchema mutation, dependency install,
  live issue `#8` validation, release mutation, issue closure, certification,
  or bundled-solver claim without a separate gate;
- turns the FEASpec CalculiX result write GUI file-dialog implementation into
  active GUI file writes, writer invocation, directory creation during
  selection, artifact copying, solver execution path, SolverAdapter/runner
  integration, subprocess or external command invocation, ProjectSchema
  mutation, dependency install, live issue `#8` validation, release mutation,
  issue closure, certification, or bundled-solver claim without a separate
  gate;
- turns the FEASpec CalculiX result write GUI writer-integration design into
  GUI source mutation, view-model source mutation, active GUI file writes,
  actual writer invocation, CLI behavior change, library writer behavior
  change, artifact copying, solver execution path, SolverAdapter/runner
  integration, subprocess or external command invocation, ProjectSchema
  mutation, dependency install, live issue `#8` validation, release mutation,
  issue closure, certification, or bundled-solver claim without a separate
  gate;
- turns the FEASpec human review record model into GUI approval workflow, run
  gate behavior, result import behavior, SolverAdapter/runner integration,
  subprocess or external command invocation, live `ccx` validation,
  ProjectSchema mutation, VLM API integration, credential handling, dependency
  install, or solver execution without a separate gate;
- turns the FEASpec human review CLI workflow into GUI approval behavior,
  no-run export writing, result import behavior, run gate behavior,
  SolverAdapter/runner integration, subprocess or external command invocation,
  live `ccx` validation, ProjectSchema mutation, VLM API integration,
  credential handling, dependency install, issue closure, or solver execution
  without a separate gate;
- turns the FEASpec human review GUI dialog design into GUI source,
  result import behavior, run gate behavior, SolverAdapter/runner integration,
  subprocess or external command invocation, live `ccx` validation,
  ProjectSchema mutation, VLM API integration, credential handling, dependency
  install, issue closure, or solver execution without a separate gate;
- turns the FEASpec human review GUI dialog view-model into GUI source,
  PySide/Qt widget behavior, result import behavior, run gate behavior,
  SolverAdapter/runner integration, subprocess or external command invocation,
  file-writing behavior, live `ccx` validation, ProjectSchema mutation, VLM API
  integration, credential handling, dependency install, issue closure, or
  solver execution without a separate gate;
- turns the FEASpec human review GUI dialog implementation into record save
  integration, file dialogs, result import behavior, installed-only run gate
  behavior, SolverAdapter/runner integration, subprocess or external command
  invocation, file-writing behavior, live `ccx` validation, ProjectSchema
  mutation, VLM API integration, credential handling, dependency install, issue
  closure, or solver execution without a separate gate;
- turns the FEASpec human review GUI save integration into file dialogs, export
  bundle writes, `.inp` writes, result import behavior, installed-only run gate
  behavior, SolverAdapter/runner integration, subprocess or external command
  invocation, live `ccx` validation, ProjectSchema mutation, VLM API
  integration, credential handling, dependency install, issue closure, or
  solver execution without a separate gate;
- turns the FEASpec human review GUI file-dialog design into `QFileDialog`
  implementation, GUI source mutation, hidden parent-directory creation,
  export bundle writes, result import behavior, installed-only run gate
  behavior, SolverAdapter/runner integration, subprocess or external command
  invocation, live `ccx` validation, ProjectSchema mutation, VLM API
  integration, credential handling, dependency install, issue closure, or
  solver execution without a separate gate;
- turns the FEASpec human review GUI file-dialog implementation into export
  bundle writing, `.inp` writing, result import behavior, installed-only run
  gate behavior, SolverAdapter/runner integration, subprocess or external
  command invocation, live `ccx` validation, ProjectSchema mutation, VLM API
  integration, credential handling, dependency install, issue closure, or
  solver execution without a separate gate;
- turns the optional solver GUI export summary design into export source,
  file dialogs, clipboard integration, shell/browser actions, discovery
  execution, solver execution, dependency installation, issue mutation, release
  mutation, validation-pass evidence, issue-closure evidence, bundled-solver
  claims, or certification claims without a separate implementation gate;
- turns the optional solver GUI export summary view-model into GUI export
  wiring, file dialogs, file writes, clipboard integration, shell/browser
  actions, discovery execution, solver execution, dependency installation,
  issue mutation, release mutation, validation-pass evidence, issue-closure
  evidence, bundled-solver claims, or certification claims without a separate
  implementation gate;
- turns the optional solver GUI export summary implementation into clipboard
  integration, open-output-folder or shell/browser actions, discovery refresh,
  solver execution, dependency installation, implicit parent-directory
  creation, multi-file or sidecar export, environment-value export by default,
  issue mutation, release mutation, validation-pass evidence, issue-closure
  evidence, bundled-solver claims, or certification claims without a separate
  gate;
- turns the optional solver GUI discovery refresh design into runtime source,
  GUI source, view-model source, CLI source, startup refresh, widget-owned
  discovery calls, background worker source, active validation, solver
  execution, dependency installation, issue mutation, release mutation,
  environment-value display, validation-pass evidence, issue-closure evidence,
  bundled-solver claims, or certification claims without a separate
  implementation gate;
- turns the optional solver GUI discovery refresh view-model into GUI wiring,
  background workers, threading, discovery service invocation, startup refresh,
  active validation, solver execution, dependency installation, file writes,
  issue mutation, release mutation, environment-value display, validation-pass
  evidence, issue-closure evidence, bundled-solver claims, or certification
  claims without a separate implementation gate;
- turns the optional solver GUI discovery refresh implementation into automatic
  startup refresh, background workers, threading, active smoke validation,
  solver execution, external solver command execution, dependency installation,
  plugin loading, issue mutation, release mutation, environment-value display,
  validation-pass evidence, issue-closure evidence, bundled-solver claims, or
  certification claims without a separate gate;
- turns the optional solver plugin manifest loading design into runtime loader
  source, filesystem plugin scanning, network marketplace behavior, plugin code
  execution, trusted-by-default third-party manifests, solver execution,
  dependency installation, issue mutation, release mutation, environment-value
  display, validation-pass evidence, issue-closure evidence, bundled-solver
  claims, or certification claims without a separate implementation gate;
- turns the optional solver plugin manifest loader model into plugin package
  discovery, directory scanning, network fetching, CLI/GUI behavior changes,
  trusted-by-default third-party manifests, solver execution, dependency
  installation, issue mutation, release mutation, environment-value display,
  validation-pass evidence, issue-closure evidence, bundled-solver claims, or
  certification claims without a separate gate;
- turns the optional solver plugin manifest CLI preview into plugin package
  discovery, directory scanning, network fetching, GUI behavior, trusted-by-
  default third-party manifests, discovery execution, solver execution,
  dependency installation, issue mutation, release mutation, environment-value
  display, validation-pass evidence, issue-closure evidence, bundled-solver
  claims, or certification claims without a separate gate;
- turns the optional solver plugin manifest GUI design into runtime source,
  GUI source, view-model source, file dialogs, plugin activation, plugin
  package loading, directory scanning, network fetching, trusted-by-default
  third-party manifests, discovery execution, solver execution, dependency
  installation, issue mutation, release mutation, environment-value display,
  validation-pass evidence, issue-closure evidence, bundled-solver claims, or
  certification claims without a separate gate;
- turns the optional solver plugin manifest GUI view-model into PySide/Qt
  source, file dialogs, file loading, JSON parsing, plugin activation, plugin
  package loading, directory scanning, network fetching, trusted-by-default
  third-party manifests, discovery execution, solver execution, dependency
  installation, issue mutation, release mutation, environment-value display,
  validation-pass evidence, issue-closure evidence, bundled-solver claims, or
  certification claims without a separate gate;
- turns the optional solver plugin manifest GUI implementation into file
  dialogs, file loading from widgets, plugin activation, plugin package import,
  directory scanning, network fetching, trusted-by-default third-party
  manifests, discovery execution, solver execution, dependency installation,
  issue mutation, release mutation, environment-value display, validation-pass
  evidence, issue-closure evidence, bundled-solver claims, or certification
  claims without a separate gate;
- turns the optional solver plugin manifest explicit import GUI design into
  implemented file dialogs, QFileDialog behavior, GUI file loading, JSON parsing
  from GUI source, plugin activation, plugin package import, directory scanning,
  network fetching, trusted-by-default third-party manifests, discovery
  execution, validation-pass evidence, solver execution, dependency
  installation, issue closure, release mutation, bundled-solver claims, or
  certification claims without a separate implementation and activation gate;
- turns the optional solver plugin manifest explicit import GUI view-model into
  file dialog implementation, GUI widget implementation, file loading, JSON
  parsing from paths, plugin activation, plugin package import, directory
  scanning, network fetching, trusted-by-default third-party manifests,
  discovery execution, validation-pass evidence, solver execution, dependency
  installation, issue closure, release mutation, bundled-solver claims, or
  certification claims without a separate implementation and activation gate;
- turns the optional solver plugin manifest explicit import GUI implementation
  into plugin activation, plugin package import, directory scanning, network
  fetching, trusted-by-default third-party manifests, automatic discovery
  execution, validation-pass evidence, solver execution, dependency
  installation, issue closure, release mutation, bundled-solver claims, or
  certification claims without a separate gate;
- turns the optional solver plugin manifest activation design into activation
  implementation, trusted-by-default third-party manifests, plugin package
  import, directory scanning, network fetching, automatic discovery execution,
  validation-pass evidence, solver execution, dependency installation, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  bundled-solver claims, or certification claims without a separate
  implementation gate;
- turns the optional solver plugin manifest activation view-model into activation
  persistence, GUI activation behavior, CLI activation behavior,
  trusted-by-default third-party manifests, plugin package import, directory
  scanning, network fetching, automatic discovery execution, validation-pass
  evidence, solver execution, dependency installation, issue closure, release
  mutation, tag mutation, asset mutation, version bump, bundled-solver claims, or
  certification claims without a separate implementation gate;
- turns the optional solver plugin manifest activation GUI into activation
  persistence, trusted-by-default third-party manifests, plugin package import,
  directory scanning, network fetching, automatic discovery execution,
  validation-pass evidence, solver execution, dependency installation, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  bundled-solver claims, or certification claims without a separate
  implementation gate;
- turns the optional solver plugin manifest deactivation design into
  deactivation implementation, deactivation persistence, GUI deactivation
  behavior, CLI deactivation behavior, file deletion, dependency uninstall,
  solver uninstall, trusted-by-default third-party manifests, plugin package
  import, directory scanning, network fetching, automatic discovery execution,
  validation-pass or validation-fail evidence, solver execution, issue closure,
  release mutation, tag mutation, asset mutation, version bump, bundled-solver
  claims, or certification claims without a separate implementation gate;
- turns the optional solver plugin manifest discovery-refresh integration design
  into runtime discovery integration, passive discovery behavior change,
  activation persistence, deactivation persistence, trusted-by-default
  third-party manifests, plugin package import, directory scanning, network
  fetching, automatic discovery execution, validation-pass evidence, solver
  execution, dependency installation, issue closure, release mutation, tag
  mutation, asset mutation, version bump, bundled-solver claims, or certification
  claims without a separate implementation gate;
- turns the optional solver plugin manifest discovery-refresh view-model into
  runtime discovery integration, passive discovery behavior change, GUI behavior,
  CLI behavior, activation persistence, deactivation persistence,
  trusted-by-default third-party manifests, plugin package import, directory
  scanning, network fetching, automatic discovery execution, validation-pass
  evidence, solver execution, dependency installation, issue closure, release
  mutation, tag mutation, asset mutation, version bump, bundled-solver claims, or
  certification claims without a separate implementation gate;
- turns the optional solver plugin manifest discovery-refresh GUI into runtime
  discovery integration, passive discovery behavior change, activation
  persistence, deactivation persistence, CLI behavior, trusted-by-default
  third-party manifests, plugin package import, directory scanning, network
  fetching, automatic discovery execution, validation-pass evidence, solver
  execution, dependency installation, issue closure, release mutation, tag
  mutation, asset mutation, version bump, bundled-solver claims, or certification
  claims without a separate implementation gate;
- turns the optional solver plugin manifest deactivation view-model into runtime
  deactivation behavior, deactivation persistence, GUI deactivation behavior, CLI
  deactivation behavior, file deletion, dependency uninstall, solver uninstall,
  activation/deactivation source mutation, trusted-by-default third-party
  manifests, plugin package import, directory scanning, network fetching,
  automatic discovery execution, validation-pass or validation-fail evidence,
  solver execution, issue closure, release mutation, tag mutation, asset
  mutation, version bump, bundled-solver claims, or certification claims without a
  separate implementation gate;
- turns the optional solver plugin manifest deactivation GUI into runtime
  deactivation behavior, deactivation persistence, file deletion, dependency
  uninstall, solver uninstall, activation/deactivation source mutation, CLI
  behavior, trusted-by-default third-party manifests, plugin package import,
  directory scanning, network fetching, automatic discovery execution,
  validation-pass or validation-fail evidence, solver execution, issue closure,
  release mutation, tag mutation, asset mutation, version bump, bundled-solver
  claims, or certification claims without a separate implementation gate;
- turns the optional solver plugin manifest reactivation design into reactivation
  implementation, reactivation persistence, GUI reactivation behavior, CLI
  reactivation behavior, automatic activation, trust restoration,
  trusted-by-default third-party manifests, file restoration, file rewrite, file
  deletion, dependency installation, dependency uninstall, solver uninstall,
  plugin package import, directory scanning, network fetching, automatic discovery
  execution, validation-pass or validation-fail evidence, solver execution, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  bundled-solver claims, or certification claims without a separate implementation
  gate;
- turns the optional solver plugin manifest reactivation view-model into runtime
  reactivation behavior, reactivation persistence, GUI reactivation behavior, CLI
  reactivation behavior, automatic activation, trust restoration, file
  restore/rewrite/delete, dependency installation, dependency uninstall, solver
  uninstall, activation/deactivation/reactivation source mutation,
  trusted-by-default third-party manifests, plugin package import, directory
  scanning, network fetching, automatic discovery execution, validation-pass or
  validation-fail evidence, solver execution, issue closure, release mutation, tag
  mutation, asset mutation, version bump, bundled-solver claims, or certification
  claims without a separate implementation gate;
- turns the optional solver plugin manifest reactivation GUI into runtime
  reactivation behavior, reactivation persistence, automatic activation, trust
  restoration, file restore/rewrite/delete, dependency installation, dependency
  uninstall, solver uninstall, activation/deactivation/reactivation source
  mutation, CLI behavior, trusted-by-default third-party manifests, plugin package
  import, directory scanning, network fetching, automatic discovery execution,
  validation-pass or validation-fail evidence, solver execution, issue closure,
  release mutation, tag mutation, asset mutation, version bump, bundled-solver
  claims, or certification claims without a separate implementation gate;
- turns the optional solver plugin manifest state persistence design into
  persistence implementation, settings file creation, project schema mutation, GUI
  persistence behavior, CLI persistence behavior, automatic activation, trust
  restoration, file restore/rewrite/delete, dependency installation, dependency
  uninstall, solver uninstall, activation/deactivation/reactivation/discovery
  source mutation, trusted-by-default third-party manifests, plugin package import,
  directory scanning, network fetching, automatic discovery execution,
  validation-pass or validation-fail evidence, solver execution, issue closure,
  release mutation, tag mutation, asset mutation, version bump, bundled-solver
  claims, or certification claims without a separate implementation gate;
- turns the optional solver plugin manifest persistence view-model into runtime
  persistence behavior, file writes, settings file creation, ProjectSchema
  mutation, GUI persistence behavior, CLI persistence behavior, reload behavior,
  export behavior, automatic activation, trust restoration, file
  restore/rewrite/delete, dependency installation, dependency uninstall, solver
  uninstall, activation/deactivation/reactivation/discovery-refresh source
  mutation, trusted-by-default third-party manifests, plugin package import,
  directory scanning, network fetching, automatic discovery execution,
  validation-pass or validation-fail evidence, solver execution, issue closure,
  release mutation, tag mutation, asset mutation, version bump, bundled-solver
  claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest persistence schema model into runtime
  persistence behavior, file writes, schema file creation, settings file creation,
  runtime state file creation, ProjectSchema mutation, GUI persistence behavior,
  CLI persistence behavior, reload behavior, export behavior, automatic activation,
  trust restoration, file restore/rewrite/delete, dependency installation,
  dependency uninstall, solver uninstall,
  activation/deactivation/reactivation/discovery-refresh source mutation,
  trusted-by-default third-party manifests, plugin package import, directory
  scanning, network fetching, automatic discovery execution, validation-pass or
  validation-fail evidence, solver execution, issue closure, release mutation, tag
  mutation, asset mutation, version bump, bundled-solver claim, or certification
  claim without a separate gate;
- turns the optional solver plugin manifest persistence GUI design into GUI
  implementation, runtime persistence behavior, file writes, settings file
  creation, runtime state file creation, schema file creation, ProjectSchema
  mutation, file dialog or save dialog behavior, reload behavior, export
  behavior, clipboard behavior, open-output-folder behavior, CLI behavior,
  automatic activation, trust restoration, file restore/rewrite/delete,
  dependency installation, dependency uninstall, solver uninstall,
  activation/deactivation/reactivation/discovery-refresh source mutation,
  trusted-by-default third-party manifests, plugin package import, directory
  scanning, network fetching, automatic discovery execution, validation-pass or
  validation-fail evidence, solver execution, issue closure, release mutation, tag
  mutation, asset mutation, version bump, bundled-solver claim, or certification
  claim without a separate gate;
- turns the optional solver plugin manifest persistence GUI implementation into
  runtime persistence behavior, file writes, settings file creation, runtime
  state file creation, schema file creation, ProjectSchema mutation, file dialog
  or save dialog behavior, reload behavior, export behavior, clipboard behavior,
  open-output-folder behavior, CLI behavior, automatic activation, trust
  restoration, file restore/rewrite/delete, dependency installation, dependency
  uninstall, solver uninstall,
  activation/deactivation/reactivation/discovery-refresh source mutation,
  persistence view-model or schema-model behavior mutation, trusted-by-default
  third-party manifests, plugin package import, directory scanning, network
  fetching, automatic discovery execution, validation-pass or validation-fail
  evidence, solver execution, issue closure, release mutation, tag mutation,
  asset mutation, version bump, bundled-solver claim, or certification claim
  without a separate gate;
- turns the optional solver plugin manifest persistence CLI design into CLI
  implementation, runtime persistence behavior, file writes, settings file
  creation, runtime state file creation, schema file creation, ProjectSchema
  mutation, save/load/reload behavior, export behavior, clipboard behavior,
  open-output-folder behavior, GUI behavior, automatic activation, trust
  restoration, file restore/rewrite/delete, dependency installation, dependency
  uninstall, solver uninstall,
  activation/deactivation/reactivation/discovery-refresh source mutation,
  persistence view-model or schema-model behavior mutation, trusted-by-default
  third-party manifests, plugin package import, directory scanning, network
  fetching, automatic discovery execution, validation-pass or validation-fail
  evidence, solver execution, issue closure, release mutation, tag mutation,
  asset mutation, version bump, bundled-solver claim, or certification claim
  without a separate gate;
- turns the optional solver plugin manifest state export-summary design into
  export implementation, file writes, export file creation, reloadable bundle
  creation, clipboard behavior, open-output-folder behavior, persistence
  implementation, settings file creation, project schema mutation, GUI export
  behavior, CLI export behavior, automatic activation, trust restoration, file
  restore/rewrite/delete, dependency installation, dependency uninstall, solver
  uninstall, activation/deactivation/reactivation/discovery source mutation,
  trusted-by-default third-party manifests, plugin package import, directory
  scanning, network fetching, automatic discovery execution, validation-pass or
  validation-fail evidence, solver execution, issue closure, release mutation, tag
  mutation, asset mutation, version bump, bundled-solver claims, or certification
  claims without a separate implementation gate;
- turns the optional solver plugin manifest export-summary view-model into file
  export, file writes, export file creation, clipboard behavior, report
  attachment, reloadable bundle creation, runtime persistence behavior, settings
  file creation, runtime state file creation, schema file creation, ProjectSchema
  mutation, GUI behavior, CLI behavior, reload behavior, automatic activation,
  trust restoration, file restore/rewrite/delete, dependency installation,
  dependency uninstall, solver uninstall,
  activation/deactivation/reactivation/discovery-refresh/persistence source
  mutation, trusted-by-default third-party manifests, plugin package import,
  directory scanning, network fetching, automatic discovery execution,
  validation-pass or validation-fail evidence, solver execution, issue closure,
  release mutation, tag mutation, asset mutation, version bump, bundled-solver
  claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest export-summary GUI design into GUI
  implementation, file export, file writes, export file creation, report file
  creation, clipboard behavior, report attachment, open-output-folder behavior,
  reloadable bundle creation, runtime persistence behavior, settings file
  creation, runtime state file creation, schema file creation, ProjectSchema
  mutation, CLI behavior, reload behavior, automatic activation, trust
  restoration, file restore/rewrite/delete, dependency installation, dependency
  uninstall, solver uninstall, plugin package import, directory scanning,
  network fetching, automatic discovery execution, validation-pass or
  validation-fail evidence, solver execution, issue closure, release mutation,
  tag mutation, asset mutation, version bump, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest export-summary GUI into file export,
  file writes, export file creation, report file creation, clipboard behavior,
  report attachment, open-output-folder behavior, reloadable bundle creation,
  runtime persistence behavior, settings file creation, runtime state file
  creation, schema file creation, ProjectSchema mutation, CLI behavior, reload
  behavior, automatic activation, trust restoration, file restore/rewrite/delete,
  dependency installation, dependency uninstall, solver uninstall, plugin package
  import, directory scanning, network fetching, automatic discovery execution,
  validation-pass or validation-fail evidence, solver execution, issue closure,
  release mutation, tag mutation, asset mutation, version bump, bundled-solver
  claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest state writer design into writer
  implementation, file writes, runtime state file creation, settings file
  creation, schema file creation, export file creation, report file creation,
  reloadable bundle creation, ProjectSchema mutation, GUI behavior, CLI behavior,
  reload behavior, export behavior, clipboard behavior, report attachment,
  open-output-folder behavior, file dialog or save dialog behavior, automatic
  activation, trust restoration, file restore/rewrite/delete, dependency
  installation, dependency uninstall, solver uninstall, plugin package import,
  directory scanning, network fetching, automatic discovery execution,
  validation-pass or validation-fail evidence, solver execution, issue closure,
  release mutation, tag mutation, asset mutation, version bump, bundled-solver
  claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest state-writer view-model into writer
  implementation, file writes, directory creation, runtime state file creation,
  settings file creation, schema file creation, export file creation, report file
  creation, reloadable bundle creation, ProjectSchema mutation, GUI behavior,
  CLI behavior, reload behavior, export behavior, clipboard behavior, report
  attachment, open-output-folder behavior, automatic activation, trust
  restoration, file restore/rewrite/delete, dependency installation, dependency
  uninstall, solver uninstall, plugin package import, directory scanning,
  network fetching, automatic discovery execution, validation-pass or
  validation-fail evidence, solver execution, issue closure, release mutation,
  tag mutation, asset mutation, version bump, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest state-writer implementation into a
  default app/project/user settings path, unrequested background writes,
  directory creation, settings file creation, schema file creation, export or
  report output, reloadable bundle creation, ProjectSchema mutation, GUI
  controls, CLI commands, reload behavior, export/report/clipboard behavior,
  open-output-folder behavior, automatic activation, trust restoration,
  dependency installation, dependency uninstall, solver uninstall, plugin package
  import, directory scanning, network fetching, discovery execution, validation
  execution, solver execution, issue closure, release mutation, tag mutation,
  asset mutation, version bump, bundled-solver claim, validation-pass or
  validation-fail evidence, or certification claim without a separate gate;
- turns the optional solver plugin manifest persistence CLI implementation into
  live plugin discovery, passive refresh, plugin package import, directory scan,
  network fetch, default write paths, unrequested/background writes, settings
  file creation, schema file creation, export/report file creation, reloadable
  bundle creation, ProjectSchema mutation, GUI behavior, reload behavior,
  report/clipboard/open-folder behavior, automatic activation, trust
  restoration, dependency installation, dependency uninstall, solver uninstall,
  validation execution, solver execution, issue closure, release mutation, tag
  mutation, asset mutation, version bump, bundled-solver claim, validation-pass
  or validation-fail evidence, or certification claim without a separate gate;
- turns the optional solver plugin manifest export-summary CLI design into CLI
  implementation, export file creation, report file creation, reloadable bundle
  creation, clipboard behavior, report attachment, open-output-folder behavior,
  GUI behavior, reload behavior, ProjectSchema mutation, live discovery,
  passive refresh, plugin package import, directory scan, network fetch,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, issue closure, release mutation, tag mutation,
  asset mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest export-summary CLI implementation
  into export file creation, report file creation, reloadable bundle creation,
  clipboard behavior, report attachment, open-output-folder behavior, GUI
  behavior, reload behavior, ProjectSchema mutation, live discovery, passive
  refresh, plugin package import, directory scan, network fetch, validation
  execution, solver execution, dependency installation, dependency uninstall,
  solver uninstall, issue closure, release mutation, tag mutation, asset
  mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload design into reload
  implementation, runtime file reading, runtime state parsing, default reload
  path, background reload, reloadable bundle creation, GUI behavior, CLI
  behavior, ProjectSchema mutation, live discovery, passive refresh, plugin
  package import, directory scan, network fetch, validation execution, solver
  execution, dependency installation, dependency uninstall, solver uninstall,
  automatic activation, trust restoration, issue closure, release mutation, tag
  mutation, asset mutation, version bump, validation-pass or validation-fail
  evidence, bundled-solver claim, or certification claim without a separate
  gate;
- turns the optional solver plugin manifest reload view-model implementation
  into file reader/parser implementation, runtime file reading, default reload
  path, background reload, reloadable bundle creation, GUI behavior, CLI
  behavior, ProjectSchema mutation, live discovery, passive refresh, plugin
  package import, directory scan, network fetch, validation execution, solver
  execution, dependency installation, dependency uninstall, solver uninstall,
  automatic activation, trust restoration, issue closure, release mutation, tag
  mutation, asset mutation, version bump, validation-pass or validation-fail
  evidence, bundled-solver claim, or certification claim without a separate
  gate;
- turns the optional solver plugin manifest reload GUI design into reload GUI
  implementation, GUI source edit, file dialog behavior, file reader/parser
  implementation, runtime file reading, runtime state parsing, default reload
  path, background reload, reloadable bundle creation, export/report file
  creation, clipboard/report/open-folder behavior, CLI behavior, ProjectSchema
  mutation, live discovery, passive refresh, plugin package import, directory
  scan, network fetch, validation execution, solver execution, dependency
  installation, dependency uninstall, solver uninstall, automatic activation,
  trust restoration, issue closure, release mutation, tag mutation, asset
  mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload GUI implementation into file
  dialog behavior, file reader/parser implementation, runtime file reading,
  runtime state parsing, default reload path, background reload, reloadable
  bundle creation, export/report file creation, clipboard/report/open-folder
  behavior, CLI behavior, ProjectSchema mutation, live discovery, passive
  refresh, plugin package import, directory scan, network fetch, validation
  execution, solver execution, dependency installation, dependency uninstall,
  solver uninstall, automatic activation, trust restoration, issue closure,
  release mutation, tag mutation, asset mutation, version bump, validation-pass
  or validation-fail evidence, bundled-solver claim, or certification claim
  without a separate gate;
- extends the optional solver plugin manifest reload CLI implementation beyond
  stdout-first review-only output into file reader/parser implementation,
  runtime file reading, runtime state parsing, runtime reload behavior, default
  reload path, background reload, reload acceptance, reloadable bundle
  creation, export/report file creation, clipboard/report/open-folder behavior,
  GUI behavior, ProjectSchema mutation, live discovery, passive refresh, plugin
  package import, directory scan, network fetch, validation execution, solver
  execution, dependency installation, dependency uninstall, solver uninstall,
  automatic activation, trust restoration, issue closure, release mutation, tag
  mutation, asset mutation, version bump, validation-pass or validation-fail
  evidence, bundled-solver claim, or certification claim without a separate
  gate;
- turns the optional solver plugin manifest reload file reader design into file
  reader implementation, parser implementation, runtime file reading, runtime
  state parsing, source edit, CLI source edit, GUI source edit, default reload
  path, background reload, directory scan, network fetch, plugin package import,
  runtime reload, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, ProjectSchema mutation, live discovery,
  passive refresh, validation execution, solver execution, dependency
  installation, dependency uninstall, solver uninstall, automatic activation,
  trust restoration, issue closure, release mutation, tag mutation, asset
  mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload file reader implementation into
  a default reload path, background reload, directory scan, network fetch, plugin
  package import, runtime reload acceptance, CLI explicit-path wiring, GUI file
  dialog behavior, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, ProjectSchema mutation, live discovery,
  passive refresh, validation execution, solver execution, dependency installation,
  dependency uninstall, solver uninstall, automatic activation, trust restoration,
  issue closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest reload CLI explicit-path design into
  CLI explicit-path implementation, CLI source edit, runtime source edit,
  file-reader source edit, GUI source edit, path argument implementation, runtime
  file reading, runtime state parsing, runtime reload acceptance, default reload
  path, background reload, directory scan, network fetch, plugin package import,
  GUI file dialog, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, ProjectSchema mutation, live discovery,
  passive refresh, validation execution, solver execution, dependency
  installation, dependency uninstall, solver uninstall, automatic activation,
  trust restoration, issue closure, release mutation, tag mutation, asset
  mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload CLI explicit-path
  implementation into a default reload path, background reload, directory scan,
  network fetch, plugin package import, GUI file dialog behavior, runtime reload
  acceptance, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, ProjectSchema mutation, live discovery,
  passive refresh, validation execution, solver execution, dependency
  installation, dependency uninstall, solver uninstall, automatic activation,
  trust restoration, issue closure, release mutation, tag mutation, asset
  mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance design into reload
  acceptance implementation, runtime source edit, GUI source edit, CLI source
  edit, file-reader source edit, reload view-model source edit, acceptance
  button implementation, acceptance CLI command implementation, persistence
  write, ProjectSchema mutation, runtime reload acceptance, default reload path,
  background reload, directory scan, network fetch, plugin package import, CLI
  subprocess use, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance view-model
  implementation into runtime reload acceptance, source file IO, reader
  invocation, GUI behavior, CLI behavior, acceptance button implementation,
  acceptance CLI command implementation, persistence write, ProjectSchema
  mutation, default reload path, background reload, directory scan, network
  fetch, plugin package import, CLI subprocess use, reloadable bundle creation,
  export/report file creation, clipboard/report/open-folder behavior, live
  discovery, passive refresh, validation execution, solver execution,
  dependency installation, dependency uninstall, solver uninstall, automatic
  activation, trust restoration, issue closure, release mutation, tag mutation,
  asset mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance GUI design into
  reload acceptance GUI implementation, GUI source edit, runtime source edit,
  CLI source edit, file-reader source edit, reload view-model source edit, reload
  acceptance view-model source edit, acceptance button implementation,
  acceptance callback implementation, acceptance CLI command implementation,
  persistence write, ProjectSchema mutation, runtime reload acceptance, default
  reload path, background reload, directory scan, network fetch, plugin package
  import, CLI subprocess use, reloadable bundle creation, export/report file
  creation, clipboard/report/open-folder behavior, live discovery, passive
  refresh, validation execution, solver execution, dependency installation,
  dependency uninstall, solver uninstall, automatic activation, trust
  restoration, issue closure, release mutation, tag mutation, asset mutation,
  version bump, validation-pass or validation-fail evidence, bundled-solver
  claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance GUI implementation
  into acceptance buttons, acceptance callbacks, runtime reload acceptance, file
  IO, reader invocation, CLI bridge, GUI file-dialog behavior, persistence
  write, ProjectSchema mutation, default reload path, background reload,
  directory scan, network fetch, plugin package import, reloadable bundle
  creation, export/report file creation, clipboard/report/open-folder behavior,
  live discovery, passive refresh, validation execution, solver execution,
  dependency installation, dependency uninstall, solver uninstall, automatic
  activation, trust restoration, issue closure, release mutation, tag mutation,
  asset mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance CLI design into
  reload acceptance CLI implementation, CLI source edit, GUI source edit,
  runtime source edit, file-reader source edit, reload view-model source edit,
  reload acceptance view-model source edit, acceptance CLI command
  implementation, acceptance flag implementation, acceptance callback
  implementation, runtime reload acceptance, file IO, reader invocation, GUI
  behavior, GUI subprocess use, persistence write, ProjectSchema mutation,
  default reload path, background reload, directory scan, network fetch, plugin
  package import, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance CLI implementation
  into runtime reload acceptance, active acceptance mutation, file IO, file
  reading, file parsing, reader invocation, GUI call, GUI subprocess use,
  persistence write, ProjectSchema mutation, default reload path, background
  reload, directory scan, network fetch, plugin package import, reloadable
  bundle creation, export/report file creation, clipboard/report/open-folder
  behavior, live discovery, passive refresh, validation execution, solver
  execution, dependency installation, dependency uninstall, solver uninstall,
  automatic activation, trust restoration, issue closure, release mutation, tag
  mutation, asset mutation, version bump, validation-pass or validation-fail
  evidence, bundled-solver claim, or certification claim without a separate
  gate;
- turns the optional solver plugin manifest reload acceptance persistence design
  into persistence implementation, source edit, CLI source edit, GUI source edit,
  runtime source edit, state-writer source edit, file-reader source edit, reload
  view-model source edit, reload acceptance view-model source edit, persistence
  write, checked-in state file, ProjectSchema mutation, runtime reload
  acceptance, active acceptance mutation, file IO, file reading, file parsing,
  reader invocation, CLI/GUI call, subprocess use, default reload path,
  background reload, directory scan, network fetch, plugin package import,
  reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence
  view-model into a persistence writer implementation, file IO, file reading,
  file parsing, writer invocation, reader invocation, CLI behavior, GUI
  behavior, subprocess use, checked-in state file, ProjectSchema mutation,
  runtime reload acceptance, active acceptance mutation, default reload path,
  background reload, directory scan, network fetch, plugin package import,
  reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence
  writer into runtime reload acceptance, active acceptance mutation,
  ProjectSchema mutation, default reload path, background write, directory scan,
  network fetch, plugin package import, input file reader/parser, reload
  file-reader invocation, CLI behavior, GUI behavior, subprocess use,
  reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence CLI
  design into CLI implementation, CLI source edit, source edit, writer
  invocation, file write, file reading, file parsing, input state file reading
  or parsing, reload file-reader invocation, OSW-EXP-102 state-writer
  invocation, GUI behavior, GUI subprocess use, runtime reload acceptance,
  active acceptance mutation, ProjectSchema mutation, default reload path,
  background write, directory scan, network fetch, plugin package import,
  reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- reload acceptance persistence CLI implementation drift is any change that
  turns dry-run-only review/write-plan output into an actual write or runtime
  acceptance surface;
- turns the optional solver plugin manifest reload acceptance persistence CLI
  implementation into actual CLI writes, writer calls with `dry_run=False`,
  input state-file reading or parsing, reload file-reader invocation,
  OSW-EXP-102 state-writer invocation, GUI behavior, GUI subprocess use,
  runtime reload acceptance, active acceptance mutation, ProjectSchema mutation,
  default target path selection, background write, directory scan, network
  fetch, plugin package import, reloadable bundle creation, export/report file
  creation, clipboard/report/open-folder behavior, live discovery, passive
  refresh, validation execution, solver execution, dependency installation,
  dependency uninstall, solver uninstall, automatic activation, trust
  restoration, issue closure, release mutation, tag mutation, asset mutation,
  version bump, validation-pass or validation-fail evidence, bundled-solver
  claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence GUI
  review design into GUI implementation, GUI source edit, source edit, writer
  invocation, file write, input state-file reading or parsing, reload
  file-reader invocation, OSW-EXP-102 state-writer invocation, CLI behavior,
  subprocess use, runtime reload acceptance, active acceptance mutation,
  ProjectSchema mutation, default target path, background write, directory
  scan, network fetch, plugin package import, reloadable bundle creation,
  export/report file creation, clipboard/report/open-folder behavior, live
  discovery, passive refresh, validation execution, solver execution,
  dependency installation, dependency uninstall, solver uninstall, automatic
  activation, trust restoration, issue closure, release mutation, tag mutation,
  asset mutation, version bump, validation-pass or validation-fail evidence,
  bundled-solver claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence GUI
  review implementation into writer invocation, file write, input state-file
  reading or parsing, reload file-reader invocation, OSW-EXP-102 state-writer
  invocation, CLI behavior, CLI subprocess use, subprocess use, runtime reload
  acceptance, active acceptance mutation, ProjectSchema mutation, default
  target path, background write, directory scan, network fetch, plugin package
  import, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence GUI
  write design into GUI write implementation, GUI source edit, source edit,
  writer invocation, file write, input state-file reading or parsing, reload
  file-reader invocation, OSW-EXP-102 state-writer invocation, CLI behavior,
  CLI subprocess use, subprocess use, runtime reload acceptance, active
  acceptance mutation, ProjectSchema mutation, default target path, background
  write, directory scan, network fetch, plugin package import, reloadable
  bundle creation, export/report file creation, clipboard/report/open-folder
  behavior, live discovery, passive refresh, validation execution, solver
  execution, dependency installation, dependency uninstall, solver uninstall,
  automatic activation, trust restoration, issue closure, release mutation, tag
  mutation, asset mutation, version bump, validation-pass or validation-fail
  evidence, bundled-solver claim, or certification claim without a separate
  gate;
- turns the optional solver plugin manifest reload acceptance persistence GUI
  write implementation into runtime reload acceptance, active acceptance
  mutation, ProjectSchema mutation, default target path, background write,
  directory scan, network fetch, plugin package import, input state-file
  reading or parsing, reload file-reader invocation, OSW-EXP-102 state-writer
  invocation, CLI behavior, CLI subprocess use, subprocess use, reloadable
  bundle creation, export/report file creation, clipboard/report/open-folder
  behavior, live discovery, passive refresh, validation execution, solver
  execution, dependency installation, dependency uninstall, solver uninstall,
  automatic activation, trust restoration, issue closure, release mutation, tag
  mutation, asset mutation, version bump, validation-pass or validation-fail
  evidence, bundled-solver claim, or certification claim without a separate
  gate;
- turns the optional solver plugin manifest reload acceptance persistence CLI
  write design into CLI write implementation, CLI source edit, source edit,
  writer invocation, file write, file reading, file parsing, input state-file
  reading or parsing, reload file-reader invocation, OSW-EXP-102 state-writer
  invocation, GUI behavior, GUI subprocess use, subprocess use, runtime reload
  acceptance, active acceptance mutation, ProjectSchema mutation, default
  target path, background write, directory scan, network fetch, plugin package
  import, reloadable bundle creation, export/report file creation,
  clipboard/report/open-folder behavior, live discovery, passive refresh,
  validation execution, solver execution, dependency installation, dependency
  uninstall, solver uninstall, automatic activation, trust restoration, issue
  closure, release mutation, tag mutation, asset mutation, version bump,
  validation-pass or validation-fail evidence, bundled-solver claim, or
  certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence CLI
  write implementation into runtime reload acceptance, active acceptance
  mutation, ProjectSchema mutation, default target path, background write,
  directory scan, network fetch, plugin package import, input state-file
  reading or parsing, reload file-reader invocation, OSW-EXP-102 state-writer
  invocation, GUI behavior, GUI subprocess use, subprocess use, reloadable
  bundle creation, export/report file creation, clipboard/report/open-folder
  behavior, live discovery, passive refresh, validation execution, solver
  execution, dependency installation, dependency uninstall, solver uninstall,
  automatic activation, trust restoration, issue closure, release mutation, tag
  mutation, asset mutation, version bump, validation-pass or validation-fail
  evidence, bundled-solver claim, or certification claim without a separate
  gate;
- turns the optional solver plugin manifest reload acceptance persistence
  summary audit design into summary audit implementation, CLI source edit, GUI
  source edit, source edit, writer invocation, file write, file reading or
  parsing, input state-file reading or parsing, reload file-reader invocation,
  OSW-EXP-102 state-writer invocation, CLI behavior, GUI behavior, subprocess
  use, runtime reload acceptance, active acceptance mutation, ProjectSchema
  mutation, default target path, background write, directory scan, network
  fetch, plugin package import, reloadable bundle creation, export/report file
  creation, clipboard/report/open-folder behavior, live discovery, passive
  refresh, validation execution, solver execution, dependency installation,
  dependency uninstall, solver uninstall, automatic activation, trust
  restoration, issue closure, release mutation, tag mutation, asset mutation,
  version bump, validation-pass or validation-fail evidence, bundled-solver
  claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence
  summary audit implementation into file read/write, input state-file parsing,
  writer invocation, reload file-reader invocation, OSW-EXP-102 state-writer
  invocation, CLI/GUI calls, subprocess use, runtime reload acceptance, active
  acceptance mutation, ProjectSchema mutation, default target path, background
  write, directory scan, network fetch, plugin package import, reloadable
  bundle creation, export/report file creation, clipboard/report/open-folder
  behavior, live discovery, passive refresh, validation execution, solver
  execution, dependency installation, dependency uninstall, solver uninstall,
  automatic activation, trust restoration, issue closure, release mutation, tag
  mutation, asset mutation, version bump, validation-pass or validation-fail
  evidence, bundled-solver claim, or certification claim without a separate
  gate;
- turns the optional solver plugin manifest reload acceptance persistence
  ProjectSchema boundary design into ProjectSchema implementation,
  ProjectSchema source edit, ProjectSchema test edit, ProjectSchema mutation,
  ProjectSchema field addition, ProjectSchema migration, ProjectSchema
  validation evidence, source edit, CLI source edit, GUI source edit, writer
  invocation, file read/write, input state-file reading or parsing, reload
  file-reader invocation, OSW-EXP-102 state-writer invocation, CLI/GUI
  behavior, subprocess use, runtime reload acceptance, active acceptance
  mutation, default target path, background write, directory scan, network
  fetch, plugin package import, reloadable bundle creation, export/report file
  creation, clipboard/report/open-folder behavior, live discovery, passive
  refresh, validation execution, solver execution, dependency installation,
  dependency uninstall, solver uninstall, automatic activation, trust
  restoration, issue closure, release mutation, tag mutation, asset mutation,
  version bump, validation-pass or validation-fail evidence, bundled-solver
  claim, or certification claim without a separate gate;
- turns the optional solver plugin manifest reload acceptance persistence
  ProjectSchema boundary implementation into ProjectSchema source edit,
  ProjectSchema test edit, ProjectSchema mutation, ProjectSchema field
  addition, ProjectSchema migration, ProjectSchema validation evidence, file
  read/write, input state-file reading or parsing, writer invocation, reload
  file-reader invocation, OSW-EXP-102 state-writer invocation, CLI/GUI
  behavior, subprocess use, runtime reload acceptance, active acceptance
  mutation, default target path, background write, directory scan, network
  fetch, plugin package import, reloadable bundle creation, export/report file
  creation, clipboard/report/open-folder behavior, live discovery, passive
  refresh, validation execution, solver execution, dependency installation,
  dependency uninstall, solver uninstall, automatic activation, trust
  restoration, issue closure, release mutation, tag mutation, asset mutation,
  version bump, validation-pass or validation-fail evidence, bundled-solver
  claim, or certification claim without a separate gate;
- turns prepared-machine prerequisite documentation into dependency
  installation, solver installation, solver execution, live validation,
  ProjectSchema mutation, ProjectSchema evidence creation, issue/release/tag/
  asset mutation, certification claim, validation success/failure claim,
  validation command implementation, runtime source edit, CLI source edit, GUI
  source edit, optional-solver source edit, solver source edit, plugin
  discovery edit, or checked-in runtime/report/export/reloadable-bundle
  artifact;
- turns prepared-machine validation command design into command
  implementation, source edit, CLI source edit, dependency installation,
  solver installation, solver execution, live validation, ProjectSchema
  mutation or evidence creation, issue/release/tag/asset mutation, validation
  success/failure claim, issue closure claim, bundled solver support claim, or
  certification claim without a separate implementation or validation gate;
- turns a post-experimental ResultDataset scope review into runtime source
  changes, solver execution, issue closure, release mutation, tag or asset
  work, version metadata changes, or a claim that skipped-missing validation is
  passing evidence;
- turns a post-experimental release-boundary decision into metadata alignment,
  version bumping, tag creation, release editing, asset build/upload, issue
  mutation, solver execution, or a claim that selected-target artifacts already
  exist;
- turns v0.1.5-rc1 metadata alignment into tag creation, release
  create/edit/publish, asset build/upload, issue mutation, solver execution,
  dependency installation, or a claim that target release artifacts already
  exist;
- makes Abaqus or another commercial solver mandatory;
- makes heavy dependencies mandatory for bootstrap or unit tests;
- accepts proprietary native formats instead of standard/exported formats;
- adds user-facing claims that exceed validation evidence.
- adds nonlinear contact/plasticity as in-scope work instead of future research;
- changes file IO, parser, or runner behavior without focused tests.

## Stop / Park / Defer Criteria

Use this table before implementing any ambiguous request.

| Decision | Criteria | Required action |
| --- | --- | --- |
| Stop | Secrets, destructive Git operations, industrial certification claims, GUI direct solver subprocess execution, native commercial CAD direct import, Simulink or `.mlapp`, full ANSYS clone, or full OpenFOAM UI. | Do not implement. Write a blocker or scope report. |
| Park | Useful idea, but architecture is missing or risk is high: generalized solver execution, remote jobs, broad OpenFOAM case management, native CAD research, or advanced runner design. | Add a decision/risk note and create a future Task Card. |
| Defer | Plausible after v0.1 but not needed for the eight demos: richer materials, more formats, GUI polish, parallel execution, nonlinear contact/plasticity, or advanced MATLAB compatibility. | Mark post-v0.1 and keep current diff focused. |
| Proceed | Directly supports one of the eight demos and can show Import -> Configure -> Run -> Result -> Report without violating non-goals. | Implement within the Task Card and add evidence. |

## Success Path Criteria

For any v0.1 workflow, the acceptable path is:

1. Import: input is standard/exported or a local template.
2. Configure: units, materials, case options, and assumptions are visible.
3. Run: execution is absent, fixture-backed, prepared, or bounded by the demo
   contract.
4. Result: outputs map into ResultDataset and FigureDataset concepts.
5. Report: HTML report records inputs, assumptions, validation, and limitations.

If a proposed feature cannot satisfy this path without expanding scope, it does
not enter v0.1.

## Required Review Questions

- Which v0.1 demo does this change unblock?
- Is any optional dependency made mandatory for bootstrap or unit tests?
- Does any user-facing text overclaim solver coverage, validation, or
  certification?
- Can the workflow be inspected before mutation or execution?
- Are generated artifacts, solver outputs, and reports either ignored or curated
  as fixtures?

## Automated Guard

Use `python tools/qa/check_scope_drift.py` to scan changed files and
`python tools/qa/check_scope_drift.py --text "<claim>"` to check a proposed
claim before editing documentation or UI text.
