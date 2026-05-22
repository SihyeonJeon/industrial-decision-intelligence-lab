project: industrial-decision-intelligence-lab
date: 2026-05-23
operator_verdict: APPROVE
implementation_status: APPROVE_FOR_IMPLEMENTATION
publication_status: BLOCKED

decision_domain:

- demand-to-inventory planning for online retail SKUs

dataset:

- UCI Online Retail II
- citation: Chen, D. (2012). Online Retail II [Dataset]. UCI Machine Learning
  Repository. https://doi.org/10.24432/C5CG6D
- license: Creative Commons Attribution 4.0 International
- raw data is not committed

evaluation_contract:

- compare seasonal naive demand forecast against model-informed forecast
- convert both forecasts into base-stock decisions
- simulate inventory under lead time
- primary metric: total simulated cost
- secondary metrics: service level, stockout units, holding units, forecast WAPE

public_boundary:

- do not claim production inventory readiness
- do not claim public benchmark status
- do not use model accuracy as the headline
- long visual HTML page needs human layout approval
