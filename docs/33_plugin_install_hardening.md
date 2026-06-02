# Plugin Install Hardening

OpenSolver Workbench (OSW) employs a highly secure, manifest-first local plugin installation flow for v0.1.

This document describes the security model, safety validation gates, install receipts tracking, quarantine handling, safe uninstallation policy, and troubleshooting resources.

## Security Model & Safe Extraction

### Static Manifest-Only Validation
To prevent code execution exploits during installation and discovery, OSW enforces manifest-only validation:
- **No Python Import**: Manifests (`manifest.json`, `osw-plugin.json`, `manifest.yaml`) are parsed statically as JSON or YAML. No plugin Python modules are imported or executed.
- **No Solver Execution**: Optional external solver dependencies are diagnosed statically using `shutil.which` or registry checking without executing any solver binaries.
- **No Network / Subprocess Calls**: The installer operates 100% locally and isolated from network or direct shell subprocesses.

### Sandbox & Zip Safety Check
Before a ZIP archive is extracted:
1. **Aggressive Path Traversal Rejection**: Rejects any entry containing `../`, mixed slashes/backslashes (`..\`), absolute paths (such as `/tmp/...` or `C:\...`), and drive-letter / UNC formats (`\\server\share`).
2. **Symlink Escape Guard**: Pre-scans zip member attributes to reject any symbolic links, protecting against link-escape vulnerabilities.
3. **Zip Bomb Prevention**: Restricts extraction to a maximum file count limit ($\le 200$) and a maximum uncompressed size limit ($\le 10$ MB).
4. **Cache & Pycache Exclusion**: Skips extraction of `.pyc`, `.pyo`, and `__pycache__` directories automatically.
5. **Sandboxed Staging**: Performs ZIP extraction into a sandboxed OS temporary directory first, only migrating validated folders to the managed root.

---

## Receipts Registry

Every successful local installation writes a receipt record to `receipts.json` under the managed install root (`~/.osw/plugins` by default):

```json
{
  "plugin_id": "demo.plugin",
  "name": "Demo Plugin",
  "version": "0.1.0",
  "source_kind": "local_zip",
  "source_path": "/path/to/demo.zip",
  "installed_path": "/user/home/.osw/plugins/plugin_ZGVtby5wbHVnaW4",
  "manifest_path": "/user/home/.osw/plugins/plugin_ZGVtby5wbHVnaW4/osw-plugin.json",
  "sha256": "abcdef1234567890...",
  "installed_at": "2026-06-02T08:30:00.000Z",
  "status": "installed",
  "diagnostics": []
}
```

This tracking ensures all active plugins are easily audited, discovered, and cleanly removed.

---

## Quarantine & Rejection Policy

If a plugin fails static manifest validation, contains path traversal indicators, or triggers zip bomb constraints, it is rejected:
- **Rejection Log**: Failure logs are recorded in `quarantine_records.json`.
- **Isolation Directory**: Optional copies of the failed directory or ZIP file are isolated inside a dedicated `quarantine/` subfolder in the managed root to prevent accidental inclusion.
- **No State Mutation**: No registry entries are generated, and the system state remains untouched.

---

## Safe Uninstall

OSW permits clean uninstallation only for managed installed plugins:
1. **Safety Boundary Constraint**: The uninstall path is strictly validated to ensure it lies entirely within the managed `install_root`.
2. **Rejection of Core/Built-in Deletion**: Built-in plugins or Python entry-point plugins do not have installation receipts and cannot be uninstalled.
3. **Registry Cleanup**: Removes the plugin's folder and deletes its receipt entry from `receipts.json`.

---

## CLI Reference

Use the following CLI commands to manage and audit local plugins without PySide6 or graphical dependencies:

### Install a Plugin Folder
```bash
python -m osw.cli plugins-install-folder /path/to/plugin_folder --allow-replace
```

### Install a ZIP Archive
```bash
python -m osw.cli plugins-install-zip /path/to/plugin.zip
```

### List Installed Plugin Receipts
```bash
python -m osw.cli plugins-installed --json
```

### List Quarantined/Rejected Installations
```bash
python -m osw.cli plugins-quarantine-list
```

### Uninstall a Plugin
```bash
python -m osw.cli plugins-uninstall <PLUGIN_ID>
```

---

## Troubleshooting

### Missing Manifest
- **Message**: `No OSW plugin manifest found in ...`
- **Solution**: Ensure your plugin directory has a valid `manifest.json` or `osw-plugin.json` at the top level.

### Duplicate Plugin ID
- **Message**: `Duplicate plugin id: <ID>`
- **Solution**: Set `--allow-replace` in CLI or check "Allow Replace" in tests if you intend to overwrite the existing version.

### Safe ZIP Traversal Rejection
- **Message**: `Plugin zip entry would write outside the install staging folder`
- **Solution**: Remove any parent traversal (`../`), backslashes, absolute, or symlink components from your archive builder.
