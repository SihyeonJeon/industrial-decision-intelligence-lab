# Current Baseline

date: 2026-05-23

project: industrial-decision-intelligence-lab

status: repo published, SKU diagnostics complete
current task: frontier selection and lead-time uncertainty complete

## Dataset

- UCI Online Retail II
- raw file: `data/raw/online_retail_II.xlsx`
- raw file is not committed
- source license: CC BY 4.0

## Run

```bash
uv run decision-lab run --top-skus 12 --min-days 180 --validation-days 45 --test-days 60 --lead-time-days 7
```

## Forecast Result

- test rows: 720
- test window: 2011-10-11 to 2011-12-09
- baseline WAPE: 1.071018491341356
- model WAPE: 0.8613691616541471
- baseline bias: -0.004931024361608453
- model bias: 0.09416660213477938

## Decision Result

- service target: 0.9
- baseline cost: 174450.85081518182
- model cost: 77323.91024636828
- cost delta: 97126.94056881354
- cost delta pct: 0.5567581935826302
- baseline service level: 0.957026080335884
- model service level: 0.9279571997216095
- service delta: -0.029068880614274484
- decision gate: pass
- recommended policy: model

## Frontier Result

Generated:

- `reports/service_frontier.csv`
- `reports/figures/service_frontier.png`

Tested service quantiles:

- 0.84
- 0.90
- 0.95
- 0.99

Reading:

- model policy has lower simulated cost across tested quantiles;
- model policy carries less inventory;
- model policy accepts higher stockout units than baseline;
- frontier selection compares only feasible rows under the 0.90 service floor;
- selected baseline row: q=0.95, cost 165926.723784107, service 0.912916871569834;
- selected model row: q=0.99, cost 77323.91024636828, service 0.9279571997216095;
- q=0.99 is the selected model setting because lower tested model quantiles
  miss the service floor.

## Sensitivity Result

Generated:

- `reports/sensitivity_grid.csv`
- `reports/figures/sensitivity_grid.png`

Grid:

- service quantiles: 0.84, 0.90, 0.95, 0.99
- holding costs: 0.02, 0.04, 0.08
- stockout costs: 2.0, 4.0, 8.0
- scenarios: 36
- pass: 9
- pass rate: 0.25
- median cost delta pct: 0.47890616004927944
- min cost delta pct: -0.07341699147623702
- max cost delta pct: 0.7117889990420658
- median model service: 0.8272164971578613

Reading:

- the model policy is not universally acceptable across the grid;
- q=0.99 is the only tested service region that passes the 0.90 floor;
- lower service quantiles reduce inventory but fail the current service gate;
- sensitivity output should be shown before any stronger public claim.

## Lead-time Uncertainty

Generated:

- `reports/lead_time_grid.csv`
- `reports/figures/lead_time_grid.png`

Grid:

- service quantiles: 0.84, 0.90, 0.95, 0.99
- lead times: 5, 7, 10, 14 days
- scenarios: 16
- pass: 4
- pass rate: 0.25
- worst model service: 0.7547105958001876
- robust service quantile: 0.99
- robust worst model service: 0.9017956328684755

Reading:

- lead-time uncertainty makes low q settings fail more clearly;
- q=0.99 is the only tested setting that passes every lead-time scenario;
- the model policy remains lower-cost than baseline in all tested lead-time
  rows, but only four rows meet both cost and service gates;
- this keeps the public claim narrow: dataset simulation under explicit
  lead-time assumptions.

## SKU Diagnostics

Generated:

- `reports/sku_metrics.csv`
- `reports/figures/sku_tradeoffs.png`

Result:

- SKU count: 12
- cost improved: 12
- service floor met: 11
- service risk: 1
- WAPE worse: 3
- largest service loss SKU: 22197
- largest service loss: -0.06444627589031715
- largest cost saving SKU: 84077
- largest cost saving: 35362.63076115469

Reading:

- aggregate pass does not imply every SKU is acceptable;
- SKU 84077 saves the most cost but fails the service floor;
- three SKUs have worse model WAPE even when decision cost improves;
- portfolio interpretation should lead with the decision chain and visible
  failure modes, not with model score alone.

## Boundary

- dataset simulation only
- no production inventory advice
- no public benchmark claim
- no long visual HTML page without human layout approval
