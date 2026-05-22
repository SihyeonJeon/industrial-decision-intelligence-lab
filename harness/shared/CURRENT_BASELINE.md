# Current Baseline

date: 2026-05-23

project: industrial-decision-intelligence-lab

status: local MVP complete, public release blocked

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
- q=0.99 is the current recommended setting because it passes the 0.90 service
  floor with the largest observed cost reduction in this grid.

## Boundary

- dataset simulation only
- no production inventory advice
- no public benchmark claim
- no long visual HTML page without human layout approval
