# Tutorial 07: CoolProp Property Table

## Goal

Calculate a bounded thermophysical property point and a small temperature sweep
with explicit SI units for reportable chemistry/property data.

This tutorial is not a process flowsheet simulator.

## Prerequisites

- Base OSW development install for plugin discovery and validation.
- Optional CoolProp for real property calculations:

  ```powershell
  python -m pip install -e .[thermo]
  ```

CoolProp is optional. Importing OSW or discovering the plugin does not import
CoolProp.

## Steps

1. Define a property point with explicit SI inputs:

   ```python
   from osw.solvers.coolprop.property_plugin import (
       CoolPropPropertyPlugin,
       CoolPropStateInput,
   )

   plugin = CoolPropPropertyPlugin()
   state = CoolPropStateInput(
       fluid="Water",
       pressure_pa=101325.0,
       temperature_k=300.0,
       outputs=("D", "H"),
   )
   result = plugin.calculate_state(state)
   print(result.table.to_csv_text())
   ```

2. Build a small sweep table:

   ```python
   table = plugin.sweep_table(
       fluid="Water",
       pressure_pa=101325.0,
       temperatures_k=(300.0, 310.0),
       outputs=("D",),
   )
   print(table.to_csv_text())
   ```

3. Export the table to CSV when it is accepted for report attachment.
4. Add the property point, sweep table, units, optional dependency status, and
   limitations to the HTML report.

## Expected Output

- A table with `fluid`, `pressure_pa`, `temperature_k`, property key, value,
  and unit.
- CSV output for the point or sweep table.
- A plot dataset placeholder for later plotting/report integration.
- A friendly diagnostic if CoolProp is unavailable.

## Troubleshooting

- `CoolProp is not installed`: install the optional thermo stack or record the
  diagnostic as the tutorial output.
- Unknown fluid or property names are reported by CoolProp; use simple examples
  such as `Water`, `D`, or `H` first.
- Non-positive pressure or temperature is rejected before calculation.
- This tutorial is a property calculator and sweep table, not a process
  simulation workflow.
