# Cantera Reactor Example

This example documents the bounded OSW v0.1 Cantera workflow: a small 0D
constant-volume reactor with a species/time table and temperature/time plot
placeholder.

It is not a combustion CFD solver or process simulator.

## Inputs

All plugin boundary inputs use explicit SI units:

- `mechanism`: `gri30.yaml`
- `temperature_k`: `1000`
- `pressure_pa`: `101325`
- `composition`: `CH4:1.0, O2:2.0, N2:7.52`
- `end_time_s`: `0.001`
- `time_step_s`: `0.0001`

## Outputs

The result is reportable as:

- a species/time table with `time_s`, `temperature_k`, `pressure_pa`, and
  selected species mole fractions;
- a temperature/time plot dataset placeholder;
- dependency and mechanism diagnostics when Cantera or the requested mechanism
  is unavailable.

## Optional Dependency

Cantera is optional. Importing OSW or discovering this plugin does not import
Cantera. A reactor run imports Cantera only when explicitly requested and gives
a friendly diagnostic if the dependency or mechanism is missing.
