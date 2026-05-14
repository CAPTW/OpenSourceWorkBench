# Tutorial 06: Cantera Reactor

## Goal

Run a bounded 0D constant-volume reactor example and produce a species/time
table plus a temperature/time plot placeholder for the report.

This tutorial is not a combustion CFD solver or process simulator.

## Prerequisites

- Base OSW development install for plugin discovery and validation.
- Optional Cantera for real reactor integration:

  ```powershell
  python -m pip install -e .[thermo]
  ```

- A local Cantera mechanism such as `gri30.yaml`.

Cantera is optional. Importing OSW or discovering the plugin does not import
Cantera.

## Steps

1. Preview the case without running integration:

   ```python
   from osw.solvers.cantera.adapter import CanteraReactorPlugin

   plugin = CanteraReactorPlugin()
   preview = plugin.prepare_case(
       {
           "mechanism": "gri30.yaml",
           "temperature_k": 1000.0,
           "pressure_pa": 101325.0,
           "composition": {"CH4": 1.0, "O2": 2.0, "N2": 7.52},
           "end_time_s": 0.001,
           "time_step_s": 0.0001,
       }
   )
   print(preview)
   ```

2. If Cantera is installed and the preview is valid, run the bounded reactor
   explicitly:

   ```python
   from osw.solvers.cantera.adapter import CanteraReactorConfig

   result = plugin.run_reactor(
       CanteraReactorConfig(
           mechanism="gri30.yaml",
           temperature_k=1000.0,
           pressure_pa=101325.0,
           composition={"CH4": 1.0, "O2": 2.0, "N2": 7.52},
           end_time_s=0.001,
           time_step_s=0.0001,
       )
   )
   print(result.table.to_csv_text())
   print(result.plot_dataset_placeholder)
   ```

3. Add the table, plot placeholder, dependency status, mechanism name, and known
   limitations to the HTML report.

## Expected Output

- A table with `time_s`, `temperature_k`, `pressure_pa`, and selected species
  mole fractions.
- A temperature/time plot dataset placeholder.
- A friendly diagnostic if Cantera or the requested mechanism is unavailable.
- Validation errors for invalid pressure, temperature, time range, or
  composition.

## Troubleshooting

- `Cantera is not installed`: install the optional thermo stack or use the
  diagnostic as the tutorial result.
- Missing mechanism: verify that `gri30.yaml` is available to the local Cantera
  installation.
- Zero or negative composition entries are allowed only when the total
  composition remains positive.
- Keep time ranges small; this plugin is a 0D educational demo, not a CFD or
  process simulator workflow.
