---
name: plugin-contract
description: Guide importer, solver, script, post-processing, and report plugin contract changes.
---

# Plugin Contract

Use when adding or reviewing plugin-facing behavior.

Require manifest fields: id, display name, version, type, entry point,
capabilities, optional extras, preview requirement, validation messages, and
limitations. Plugin import must avoid side effects, process launches, and heavy
dependency imports until the plugin is explicitly used.
