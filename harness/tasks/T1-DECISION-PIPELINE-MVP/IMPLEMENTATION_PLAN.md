# T1 Decision Pipeline MVP

Status: in progress.

## Scope

Build a local CLI that:

- downloads or locates UCI Online Retail II;
- aggregates daily SKU demand;
- selects high-signal SKUs;
- builds lag/rolling/calendar features;
- trains a model forecast and seasonal-naive baseline;
- converts forecasts into base-stock inventory decisions;
- simulates inventory with lead time;
- writes JSON/CSV/PNG evidence.

## Non-Scope

- no production inventory recommendation;
- no dashboard;
- no long HTML evidence page;
- no external publishing;
- no public benchmark claim.

## Metrics

Forecast:

- WAPE;
- bias;
- number of evaluated SKU-days.

Decision:

- total cost;
- service level;
- stockout units;
- holding units;
- average inventory.

## Pass Condition

The MVP passes if a clean local run produces:

- `reports/decision_report.json`;
- `reports/sku_metrics.csv`;
- `reports/service_frontier.csv`;
- `reports/figures/policy_comparison.png`;
- `reports/figures/service_frontier.png`;
- tests passing.
