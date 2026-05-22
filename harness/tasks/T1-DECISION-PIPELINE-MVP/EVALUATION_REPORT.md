# T1 Evaluation Report

Verdict: PASS with boundary retained.

Why pass:

- the project links forecasting to a constrained inventory decision;
- the result is measured through cost and service level, not model score alone;
- the model-informed policy passes the service floor while reducing simulated
  cost;
- the report records service-level trade-off instead of hiding it;
- the frontier view exposes how cost and service move under multiple service
  quantiles;
- tests cover leakage, simulation directionality, and end-to-end output.

Important result:

- model WAPE improved from `1.071` to `0.861`;
- model policy cost improved from `174450.85` to `77323.91`;
- model service level was `0.928`, below baseline `0.957` but above the `0.900`
  service floor;
- therefore the decision gate is `pass`, not an unbounded model win.

Residual risk:

- demand aggregation is SKU-level only;
- returns/cancellations are removed, not modeled;
- lead time and costs are scenario parameters;
- no external validation beyond this dataset;
- no visual HTML evidence page yet.

Next allowed work:

- package polish and README tightening;
- GitHub repo initialization;
- GitHub Pages project entry after copy-boundary review;
- visual HTML evidence page only after human layout approval.
