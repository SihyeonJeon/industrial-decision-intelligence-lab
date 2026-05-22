# T3 Implementation Report

Task: SKU-level failure diagnostics.

Implemented:

- added SKU cost delta pct;
- added SKU service delta;
- added SKU model WAPE delta;
- added SKU service-floor flag;
- added SKU decision flag: `accept`, `service_risk`, `cost_risk`, `review`;
- added `sku_diagnostics` summary to `reports/decision_report.json`;
- added `reports/figures/sku_tradeoffs.png`;
- extended tests for SKU diagnostic semantics.

Boundary:

- SKU flags are diagnostic labels for this simulation;
- labels are not production replenishment recommendations;
- visible service-risk rows must remain in the output.
