# Project Agent Entry

Read this file first, then `harness/INDEX.md`.

Project:

- `replenishment-policy-gate`
- portfolio role: Applied AI / Data Systems Engineer
- project stance: forecasting is useful only when it changes a constrained
  replenishment decision

## Binding Rule

Do not present model accuracy as the project result. The result is the decision
simulation: cost, service level, stockout units, holding units, and robustness.

Implementation may proceed only inside the approved task scope recorded in
`harness/shared/ACTIVE_SNAPSHOT.md`.

## Workflow

1. Market/learning gate defines the decision domain, source data, and evaluation
   contract.
2. Implementation builds a reproducible runner, not a notebook-only artifact.
3. Evaluation compares a baseline heuristic against a model-informed decision
   policy.
4. If the model improves forecast error but worsens decision cost, the project
   records that failure instead of hiding it.

## Public Boundary

Allowed:

- real dataset citation;
- reproducible CLI;
- decision simulation metrics;
- failure cases and trade-offs.

Blocked:

- production inventory recommendation claims;
- public benchmark language;
- business value claims beyond this dataset/simulation;
- long visual HTML evidence pages without human layout approval.
