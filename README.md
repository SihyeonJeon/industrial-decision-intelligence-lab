# Industrial Decision Intelligence Lab

Retail transaction data to inventory policy simulation:

- aggregate SKU demand
- forecast short-horizon demand
- choose base-stock levels under lead time and service target
- simulate cost, stockouts, and service level
- compare a seasonal baseline against a model-informed policy

## Data

Default source: UCI Online Retail II.

The raw Excel file is not committed. Download it locally, then run the pipeline.

## Run

```bash
uv sync
uv run decision-lab fetch
uv run decision-lab run --top-skus 12
```

Outputs:

- `reports/decision_report.json`
- `reports/sku_metrics.csv`
- `reports/service_frontier.csv`
- `reports/figures/policy_comparison.png`
- `reports/figures/service_frontier.png`

## Result View

![Cost-service frontier](reports/figures/service_frontier.png)

## Current Result

UCI Online Retail II, top 12 SKUs, final 60-day simulation:

- model WAPE: `0.861` vs seasonal baseline `1.071`
- model policy cost: `77,323.91` vs baseline `174,450.85`
- service level: `0.928` vs baseline `0.957`
- service floor: `0.900`
- decision gate: `pass`
- frontier: model policy stays below baseline cost across tested service
  quantiles while exposing stockout/service trade-off

This is a dataset simulation, not production inventory advice.
