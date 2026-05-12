# Plugin Contract

OSW plugins are planned for importers, solver adapters, post-processing steps,
and report contributors. A plugin should declare:

- stable `id`, `name`, `version`, `domain`, `type`, and `license`;
- `input_formats` and `output_formats` for standard/exported data contracts;
- `requires` for mandatory import-time Python modules;
- `optional_requires` for optional stacks such as mesh, visualization, GUI, or
  chemistry integrations;
- `capabilities` such as `preview`, `validate`, `prepare_case`, `import_result`,
  `post_process`, or `render_report`.

v0.1 plugins must prefer preview-first behavior and structured validation
messages over direct mutation.

## v0.1 Plugin Types

The base contract defines these plugin families:

- `cad_importer`
- `mesh_importer`
- `mesh_generator`
- `solver_adapter`
- `script_importer`
- `property_model`
- `post_processor`
- `report`

Solver adapters may prepare cases and import results, but external execution
still belongs behind a future reviewed runner contract.

## Discovery

Discovery supports:

- local plugin directories containing `osw-plugin.json`, `osw-plugin.yaml`, or
  `*.manifest.json` / `*.manifest.yaml`;
- Python entry points in the `osw.plugins` group when packages are installed.

Discovery loads manifests only. It must not launch solver processes, mutate
projects, write output files, or import heavy optional dependencies merely to
list available plugins.
