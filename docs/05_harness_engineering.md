# Harness Engineering

The test harness starts with network-free unit tests. Integration, GUI, golden,
and validation tests have reserved directories but should only gain fixtures
when a concrete v0.1 workflow is implemented.

External solvers must not run in unit tests. Later integration tests may use
explicit opt-in markers and local fixture cases, but default CI should remain
fast and deterministic.
