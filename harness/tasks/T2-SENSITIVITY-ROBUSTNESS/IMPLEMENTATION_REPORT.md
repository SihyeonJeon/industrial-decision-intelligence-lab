# T2 Implementation Report

Task: sensitivity and robustness layer.

Implemented:

- added cost-service sensitivity grid;
- added CLI controls for holding and stockout cost grids;
- exported `reports/sensitivity_grid.csv`;
- exported `reports/figures/sensitivity_grid.png`;
- recorded sensitivity summary in `reports/decision_report.json`;
- extended end-to-end test coverage for sensitivity outputs.

Default grid:

- service quantiles from `--frontier-quantiles`;
- holding costs: `0.02,0.04,0.08`;
- stockout costs: `2.0,4.0,8.0`.

Boundary:

- this is a scenario stress test, not an external benchmark;
- pass means cost improves while the model policy stays above the service floor;
- warning scenarios remain visible and are not filtered from the CSV.
