# CHM CoolProp / Cantera Binding

OSW-FUNC-018 adds bounded chemistry/property workflows for educational CHM
examples. The implementation is optional-dependency first: importing OSW,
`osw.solvers.coolprop`, or `osw.solvers.cantera` does not require CoolProp or
Cantera installed.

## CoolProp

CoolProp models live in `osw.solvers.coolprop.model`:

- `PropertyInputPair`
- `CoolPropPropertyRequest`
- `CoolPropSweepRequest`
- `CoolPropPropertyValue`
- `CoolPropPropertyResult`
- `CoolPropSweepResult`

`osw.solvers.coolprop.property_adapter` lazily imports `CoolProp.CoolProp` only
inside calculation calls. It supports simple T/P or P/T property points and
T/P sweeps using SI values. Missing CoolProp returns a
`dependency_missing` result with a diagnostic that asks the user to install the
CHM optional extra or CoolProp.

Supported v0.1 output names are density, viscosity, enthalpy, entropy, cp, and
thermal_conductivity. The adapter does not implement a unit conversion engine or
phase-envelope GUI.

## Cantera

Cantera models live in `osw.solvers.cantera.model`:

- `CanteraMixtureSpec`
- `CanteraReactorKind`
- `CanteraReactorRequest`
- `CanteraReactorResult`

`osw.solvers.cantera.reactor_adapter` lazily imports `cantera` only inside
reactor calls. The v0.1 adapter supports a bounded constant-volume 0D reactor
using Cantera `Solution`, `IdealGasReactor`, and `ReactorNet` when Cantera is
available. It collects time, temperature, pressure, and tracked species mole
fraction histories. Missing Cantera or missing mechanisms return friendly
diagnostics.

Cantera support is not reacting CFD, a combustion CFD solver, a detailed
mechanism editor, or a process simulator.

## ResultDataset Binding

CoolProp and Cantera results convert to `ResultDataset` records through:

- `coolprop_result_to_result_dataset`
- `coolprop_sweep_to_result_dataset`
- `cantera_result_to_result_dataset`

The result datasets include scalar summaries, table metadata, series metadata,
diagnostics, and optional dependency notes. The unified ResultViewer can display
CoolProp property values, CoolProp sweep series, Cantera time histories,
species histories, property tables, reactor tables, and warnings without
additional visualization dependencies.

Report generation consumes these datasets through existing
`ResultDataset.to_report_tables()` paths. The report generator does not import
CoolProp or Cantera and does not execute calculations.

## Plugin Metadata

Two built-in data-only manifests are available:

- `osw.coolprop`: `property_model`, optional dependency `CoolProp`
- `osw.cantera`: `solver_adapter`, optional dependency `cantera`

Plugin discovery and health checks operate on manifest data only. They do not
execute plugin code, property calculations, reactor calculations, subprocesses,
or external tools.

## GUI Binding

The frozen GUI shell is preserved. The main menu adds a bounded CHM menu:

- CoolProp Property Calculator...
- Cantera 0D Reactor...

The dialogs use existing theme tokens, display dependency diagnostics, and emit
ResultDataset records to MainWindow after successful or warning-level results.
They do not call subprocesses or external executables.

## CLI

CHM CLI commands:

```text
python -m osw.cli coolprop-check
python -m osw.cli coolprop-props --fluid Water --T 300 --P 101325
python -m osw.cli coolprop-sweep --fluid Water --sweep T --start 280 --stop 320 --count 5 --P 101325 --out artifacts/chm/water_sweep.json
python -m osw.cli cantera-check
python -m osw.cli cantera-reactor --mechanism gri30.yaml --composition "CH4:1,O2:2,N2:7.52" --T 1000 --P 101325 --end-time 0.001 --out artifacts/chm/reactor.json
python -m osw.cli chm-result-inspect PATH
```

`coolprop-check` and `cantera-check` report package availability only. Property
and reactor commands fail gracefully with dependency diagnostics when optional
packages are missing.

## Safety Limits

- CoolProp and Cantera are optional.
- CHM adapters do not call `ExternalCommandRunner`.
- CHM adapters do not call subprocesses.
- GUI dialogs do not call subprocesses.
- DWSIM, CAPE-OPEN, process flowsheets, Aspen/HYSYS clone behavior, reacting
  CFD, and industrial certification claims are out of scope.

