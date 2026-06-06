# v0.1.4 Plugin Manager UX closure evidence

Related issue: `#15 Improve Plugin Manager UX and install receipts`

## Repo State

- Review start HEAD: `25af8dbc165d92663b3c8ac24bd97629ce158fe2`
- Closure evidence commit: recorded by the `OSW-FEAT-002` gate after this
  document is committed.
- Public release: `v0.1.3-rc1`
- Public release tag target: `a6e8d3a8211e02359841d10e1947e16ab847b132`
- Active development version: `0.1.3rc2.dev0`
- Feature commit: `25af8dbc165d92663b3c8ac24bd97629ce158fe2`

OpenSolver Workbench remains educational/research software. It is not a stable
production CAE platform, an industrial-certified solver product, a MATLAB,
Simulink, ANSYS, Abaqus, or commercial CAD clone, or a bundled-solver
distribution.

## Evidence Summary

### Receipt UX

- The Plugin Manager table exposes source kind, install status, managed-root
  status, receipt presence, and diagnostic counts.
- The Receipt tab shows a selected managed plugin's ID, source kind/path,
  installed path, recorded file count, timestamp, manifest path, uninstall
  eligibility, and raw receipt JSON.
- Unmanaged discovered plugins, built-ins, and entry-point rows get explicit
  no-receipt messaging.

### Quarantine UX

- The Quarantine tab shows the rejected/quarantined install count.
- Latest records include timestamp, source kind/path, quarantine path when a
  ZIP copy was retained, reason, diagnostics, and raw record JSON.
- Missing or corrupt receipt/quarantine registries produce diagnostics instead
  of hidden success.

### Diagnostics And Safety Messaging

- The Safety tab documents local folder/ZIP install only.
- It states no plugin code execution during install, discovery, or health
  display.
- It states no remote or network install, no dependency auto-install, and no
  plugin signing, marketplace, or catalog behavior.
- It records duplicate ID, traversal, absolute-path, symlink, unsafe archive,
  and local link-escape rejection boundaries.

### Uninstall And Managed Root UX

- Uninstall eligibility is visible in the table/details.
- Non-managed rows disable uninstall.
- GUI uninstall remains routed through `PluginInstallManager.uninstall_plugin`;
  the dialog does not directly delete plugin directories.
- Installer summary logic refuses uninstall eligibility for receipt paths
  outside the managed install root.

### CLI Consistency

- `plugins-installed` output uses managed receipt and managed-root wording.
- `plugins-quarantine-list` output includes quarantine count, managed root,
  source kind, quarantine path, and rejection reason.
- `plugins-uninstall` output states managed-root receipt-owned removal.

### Docs And Tests

- `docs/33_plugin_install_hardening.md` documents Plugin Manager UX, receipts,
  quarantine records, and managed-root uninstall safety.
- `docs/tutorials/first_gui_walkthrough.md` includes a Plugin Manager
  receipt/quarantine inspection flow.
- `docs/04_validation_matrix.md`, `docs/10_release_checklist.md`,
  `docs/roadmap/v0_1_4.md`, `docs/roadmap/v0_1_4_scope_lock.md`, and
  `CHANGELOG.md` record the #15 implementation evidence.
- Focused receipt/quarantine unit coverage is in
  `tests/unit/test_plugin_manager_ux_receipts.py`.
- GUI coverage is in `tests/gui/test_plugin_manager_dialog.py`.

## Security Invariants

- No plugin code execution during install or discovery.
- No network plugin install.
- No dependency auto-install.
- No plugin signing, marketplace, remote catalog, or Store behavior.
- Managed-root uninstall only.
- Traversal, absolute-path, symlink/junction, unsafe archive, duplicate ID, and
  unmanaged uninstall protections remain in the installer and tests.
- Plugin install remains manifest-only validation.

## Tests And Checks

Closure QA for this evidence gate reruns:

- focused plugin install tests
- plugin install security tests
- plugin quarantine tests
- plugin manager UX receipt tests
- Plugin Manager GUI tests
- CLI surface and QA-tool tests
- full unit suite
- full GUI suite
- Ruff
- release, scope, architecture, docs link, solver artifact, public docs, JSON,
  diff, and status checks

## Decision

Issue `#15` is eligible for closure if the OSW-FEAT-002 focused and broad QA
commands pass, the public release/tag verification remains intact, and Issue
`#12` is left open.

## Remaining Limitations

- Remote plugin store remains out of scope.
- Plugin signing remains out of scope.
- Dependency auto-install remains out of scope.
- Marketplace/catalog behavior remains out of scope.
- Network plugin install remains out of scope.
- The public release remains a prerelease.
- The Windows portable ZIP remains unsigned, with no MSI/MSIX/code signing.
- External solvers remain optional and are not bundled.

## Next Recommendation

- `#14 ResultViewer / FieldViewer workflow`, or
- `OSW-PLAN-004_ISSUE_12_SCOPE_LOCK_CLOSURE` if maintainers want to close the
  planning issue after accepting the first v0.1.4 implementation slice.
