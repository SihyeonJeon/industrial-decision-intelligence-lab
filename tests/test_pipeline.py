from __future__ import annotations

import argparse
import json
from pathlib import Path

from decision_lab.cli import run_pipeline


def test_synthetic_pipeline_writes_report(tmp_path: Path) -> None:
    args = argparse.Namespace(
        raw_file=Path("missing.xlsx"),
        report_dir=tmp_path,
        top_skus=4,
        min_days=120,
        validation_days=35,
        test_days=45,
        lead_time_days=5,
        service_quantile=0.99,
        service_target=0.90,
        holding_cost=0.04,
        stockout_cost=4.0,
        frontier_quantiles="0.84,0.99",
        synthetic=True,
    )

    payload = run_pipeline(args)

    assert payload["decision"]["recommended_policy"] in {"baseline", "model"}
    assert payload["decision"]["decision_gate"] in {"pass", "warn"}
    assert (tmp_path / "decision_report.json").exists()
    assert (tmp_path / "sku_metrics.csv").exists()
    assert (tmp_path / "service_frontier.csv").exists()
    assert (tmp_path / "figures" / "policy_comparison.png").exists()
    assert (tmp_path / "figures" / "service_frontier.png").exists()

    saved = json.loads((tmp_path / "decision_report.json").read_text())
    assert saved["scope_note"].startswith("UCI Online Retail II simulation")
