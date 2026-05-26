# replenishment-policy-gate

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Stop lower-cost replenishment policies from hiding stockout risk

Forecast error is not the decision. This repo takes daily SKU demand, compares
a seasonal baseline with a model forecast, converts both into base-stock reorder
levels, and gates the candidate policy against service-floor, lead-time, cost,
and SKU-level failure cases.

![Service frontier](reports/figures/service_frontier.png)

## What It Does

- builds daily SKU demand from transaction data
- compares a seasonal baseline against a model-informed forecast
- chooses base-stock levels under lead-time and service constraints
- simulates holding cost, stockout cost, service level, and order volume
- rejects low-service policies that save inventory but miss the service floor
- tests cost/service sensitivity across 36 scenarios
- tests lead-time uncertainty across 16 scenarios
- writes JSON, CSV, and figure outputs for review

## Current Result

UCI Online Retail II, top 50 SKUs, final 60-day simulation

| Check | Result |
| --- | ---: |
| model WAPE | 0.865 |
| seasonal baseline WAPE | 1.070 |
| model policy cost | 158,345.68 |
| baseline policy cost | 372,195.68 |
| model service level | 0.970 |
| service floor | 0.900 |
| frontier cost delta | 50.4% lower |
| final gate | `review` |
| robust quantile | q=0.99 |
| robust lead-time pass | 4 / 4 |
| blocked lead-time settings | 12 / 16 |
| blocked cost settings | 27 / 36 |
| SKU service floor pass | 48 / 50 |

The selected model policy passes the current service floor and lowers simulated
cost on this split. The gate does not treat that as a blanket approval:

- model q 0.84, 0.90, and 0.95 are blocked under lead-time checks
- robust q 0.99 passes 4 / 4 lead-time settings
- 12 / 16 lead-time and 27 / 36 cost settings are blocked
- 2 / 50 SKUs require baseline or SKU-level override review
- cost weights remain a deployment parameter, not a constant

Visual case page:
<https://sihyeonjeon.github.io/projects/replenishment-policy-gate/>

## Quick Start

```bash
git clone https://github.com/SihyeonJeon/replenishment-policy-gate
cd replenishment-policy-gate
uv sync
uv run replenishment-gate run --synthetic --report-dir /tmp/replenishment-gate-smoke
```

Run on the default public dataset:

```bash
uv run replenishment-gate fetch
uv run replenishment-gate run
```

The raw Excel file is not committed. `replenishment-gate fetch` downloads Online
Retail II from UCI into `data/raw/`; see [data/README.md](data/README.md).

## Outputs

```text
reports/
  decision_report.json
  failure_modes.csv
  sku_metrics.csv
  service_frontier.csv
  sensitivity_grid.csv
  lead_time_grid.csv
  figures/
    policy_comparison.png
    service_frontier.png
    sensitivity_grid.png
    lead_time_grid.png
    sku_tradeoffs.png
```

Useful files:

- [decision_report.json](reports/decision_report.json): summary metrics and
  decision gate
- [failure_modes.csv](reports/failure_modes.csv): named gate failures and
  actions
- [sku_metrics.csv](reports/sku_metrics.csv): SKU-level forecast and service
  diagnostics
- [service_frontier.csv](reports/service_frontier.csv): feasible policy grid
- [lead_time_grid.csv](reports/lead_time_grid.csv): lead-time robustness grid

## Test

```bash
uv run ruff check src tests
uv run pytest
```

CI also runs a synthetic smoke pipeline.

## Boundary

Dataset simulation only. Not production inventory advice, not a public
benchmark, and not a claim that the same policy transfers to another retailer
without local demand, lead-time, cost, and service calibration.
