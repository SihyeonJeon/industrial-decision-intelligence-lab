# T4 Frontier + Lead-time Uncertainty Implementation

Date: 2026-05-25

Scope:

- add frontier-based policy selection
- add lead-time uncertainty grid
- keep output as reproducible CSV, JSON, and figure artifacts

Implemented:

- `select_frontier_policy`
  - selects the lowest-cost row that meets the service floor
  - returns baseline/model selected q, cost, service, stockout, inventory
  - records pass/warn gate without production claims
- `build_lead_time_grid`
  - tests service quantiles across multiple lead-time values
  - reuses the same forecast and base-stock simulation contract
  - records cost delta, service floor, and recommended policy per row
- `summarize_lead_time_grid`
  - reports pass rate, worst model service, and robust q
  - robust q means all tested lead-time rows pass both cost and service gates
- report outputs
  - `reports/lead_time_grid.csv`
  - `reports/figures/lead_time_grid.png`
  - `decision_report.json.frontier_selection`
  - `decision_report.json.lead_time_uncertainty`

Boundary:

- dataset simulation only
- no production inventory advice
- no public benchmark wording
