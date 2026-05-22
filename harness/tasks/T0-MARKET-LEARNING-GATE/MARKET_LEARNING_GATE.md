# T0 Market And Learning Gate

Status: approved by operator.

## Market Signal

The current signal is not "prediction model in isolation". Recent roles ask for
forecasting, optimization, simulation, measurable decision impact, and
stakeholder-readable recommendations.

Examples checked on 2026-05-23:

- Affirm quantitative modeling role: forecasting, headcount planning, linear
  programming, constrained scheduling, SQL/Python.
- Lyft optimization role: forecasting, ML, optimization, production decision
  systems, resource allocation, monitoring.
- Walmart last-mile role: demand/supply forecasting, capacity optimization,
  predictive simulation, cost/service trade-offs.

## Selected Domain

Demand-to-inventory planning for retail SKUs.

Reason:

- uses real transaction data;
- links forecasting to an operational decision;
- produces clear metrics without claiming production readiness;
- fits industrial engineering plus AI/data systems positioning.

## Learning Target

- time-series feature construction from transactions;
- baseline versus model forecasting;
- base-stock inventory policy;
- lead-time simulation;
- service-level and cost trade-offs.

## Dataset

UCI Online Retail II:

- two years of UK non-store online retail transactions;
- 1,067,371 instances;
- sequential/time-series/business characteristics;
- CC BY 4.0 license.

## Acceptance

- reproducible CLI;
- no notebook-only path;
- report includes forecast and decision metrics;
- at least one failure/trade-off is visible.
