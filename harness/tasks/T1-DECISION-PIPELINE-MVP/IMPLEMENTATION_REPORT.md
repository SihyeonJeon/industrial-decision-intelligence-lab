# T1 Decision Pipeline MVP

Status: implemented.

Changed:

- added packaged CLI: `decision-lab`;
- added UCI Online Retail II fetcher;
- added transaction cleaning and daily SKU demand aggregation;
- added lag, rolling, and calendar features;
- added seasonal-naive baseline;
- added histogram gradient boosting demand forecast;
- added base-stock policy conversion;
- added inventory simulation under lead time;
- added JSON, CSV, and PNG evidence outputs;
- added cost-service frontier across service quantiles;
- added tests for feature leakage, simulation behavior, and synthetic end-to-end
  report generation.

Outputs from actual data run:

- `reports/decision_report.json`;
- `reports/sku_metrics.csv`;
- `reports/service_frontier.csv`;
- `reports/figures/policy_comparison.png`.
- `reports/figures/service_frontier.png`.

Verification:

- `uv sync` passed;
- `uv run pytest`: 3 passed;
- synthetic run passed;
- UCI Online Retail II run passed.

Public boundary:

- raw data excluded from git;
- result is dataset simulation only;
- not production inventory advice;
- not a public benchmark.
