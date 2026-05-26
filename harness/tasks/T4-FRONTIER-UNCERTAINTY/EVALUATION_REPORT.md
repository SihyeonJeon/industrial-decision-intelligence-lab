# T4 Frontier + Lead-time Uncertainty Evaluation

Date: 2026-05-25

Command:

```bash
uv run replenishment-gate run --top-skus 12
uv run pytest
```

Result:

- tests: 9 passed
- report regenerated from UCI Online Retail II local file
- decision gate: pass
- selected baseline q: 0.95
- selected model q: 0.99
- frontier selected model cost: 77323.91024636828
- frontier selected baseline cost: 165926.723784107
- lead-time scenarios: 16
- lead-time pass: 4
- robust model q: 0.99
- robust worst model service: 0.9017956328684755

Reading:

- the project no longer depends only on one manually chosen q setting
- the selected q is derived from the frontier under the service floor
- the lead-time grid shows that lower q settings reduce inventory but fail
  service under uncertainty
- q=0.99 is robust only within the tested lead-time range and dataset

Operator verdict:

- approve as stronger dataset-simulation evidence
- still blocked from stronger public claims until tested on another dataset or
  real operator feedback
