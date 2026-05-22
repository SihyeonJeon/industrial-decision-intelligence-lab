# T2 Evaluation Report

Verdict: PASS with stronger boundary.

Why pass:

- the result is no longer a single favorable run;
- cost and service are tested across 36 scenario settings;
- only 9 scenarios pass, which keeps the claim conditional;
- warning scenarios expose where inventory savings break the service floor;
- the public README now points to sensitivity before stronger interpretation.

Important result:

- scenarios: `36`;
- pass: `9`;
- pass rate: `0.25`;
- median cost delta pct: `0.479`;
- model-policy count: `9`;
- reliable region: q=`0.99` under the current grid.

Residual risk:

- costs are scenario parameters;
- SKU selection remains top-volume only;
- no second external retail dataset yet;
- no deep forecasting comparison yet.

Next allowed work:

- SKU failure gallery;
- second dataset check;
- lightweight portfolio page update with the sensitivity figure;
- Colab notebook only if deep forecasting baselines are added.
