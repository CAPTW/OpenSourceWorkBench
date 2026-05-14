# CoolProp Property Example

This example documents the bounded OSW v0.1 CoolProp workflow: a single
thermophysical property point and a small temperature sweep.

It is not a process flowsheet simulator.

## Property Point

Inputs use explicit SI units at the plugin boundary:

- `fluid`: `Water`
- `pressure_pa`: `101325`
- `temperature_k`: `300`
- `outputs`: `D`, `H`

The plugin calls CoolProp `PropsSI` only when a calculation is explicitly
requested. Importing OSW or discovering the plugin does not import CoolProp.

Expected reportable outputs:

- density `D` in `kg/m^3`
- specific enthalpy `H` in `J/kg`
- a table preview with `fluid`, `pressure_pa`, `temperature_k`, property name,
  value, and unit
- a plot dataset placeholder describing the property point

## Sweep Table

A minimal temperature sweep can hold pressure fixed and vary temperature:

```text
fluid = Water
pressure_pa = 101325
temperatures_k = 300, 310
outputs = D
```

The resulting table can be exported to CSV for report attachment or later
plotting.

## Optional Dependency

CoolProp is optional. If CoolProp is not installed, the plugin reports a
friendly missing dependency diagnostic instead of failing package import or
making CoolProp mandatory for OSW bootstrap tests.
