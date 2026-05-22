from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

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
        sensitivity_holding_costs="0.02,0.04",
        sensitivity_stockout_costs="2.0,4.0",
        synthetic=True,
    )

    payload = run_pipeline(args)

    assert payload["decision"]["recommended_policy"] in {"baseline", "model"}
    assert payload["decision"]["decision_gate"] in {"pass", "warn"}
    assert (tmp_path / "decision_report.json").exists()
    assert (tmp_path / "sku_metrics.csv").exists()
    assert (tmp_path / "service_frontier.csv").exists()
    assert (tmp_path / "sensitivity_grid.csv").exists()
    assert (tmp_path / "figures" / "policy_comparison.png").exists()
    assert (tmp_path / "figures" / "service_frontier.png").exists()
    assert (tmp_path / "figures" / "sensitivity_grid.png").exists()
    assert (tmp_path / "figures" / "sku_tradeoffs.png").exists()

    saved = json.loads((tmp_path / "decision_report.json").read_text())
    assert saved["scope_note"].startswith("UCI Online Retail II simulation")
    assert saved["sensitivity"]["scenario_count"] == 8
    assert saved["sensitivity"]["pass_count"] <= saved["sensitivity"]["scenario_count"]
    assert saved["sensitivity"]["pass_rate"] == (
        saved["sensitivity"]["pass_count"] / saved["sensitivity"]["scenario_count"]
    )
    assert saved["sku_diagnostics"]["sku_count"] == 4
    assert saved["sku_diagnostics"]["cost_improved_count"] <= 4
    assert saved["sku_diagnostics"]["service_floor_met_count"] <= 4

    sensitivity = pd.read_csv(tmp_path / "sensitivity_grid.csv")
    required_columns = {
        "service_quantile",
        "holding_cost",
        "stockout_cost",
        "cost_delta_pct",
        "service_floor_met",
        "cost_improved",
        "decision_gate",
        "recommended_policy",
    }
    assert required_columns.issubset(sensitivity.columns)

    passed = sensitivity[sensitivity["decision_gate"] == "pass"]
    assert (passed["service_floor_met"]).all()
    assert (passed["cost_improved"]).all()
    assert (sensitivity[sensitivity["recommended_policy"] == "model"]["decision_gate"] == "pass").all()

    sku_metrics = pd.read_csv(tmp_path / "sku_metrics.csv")
    sku_columns = {
        "cost_delta_pct",
        "service_delta",
        "model_wape_delta",
        "model_service_floor_met",
        "decision_flag",
    }
    assert sku_columns.issubset(sku_metrics.columns)
    accepted = sku_metrics[sku_metrics["decision_flag"] == "accept"]
    assert (accepted["cost_delta"] > 0).all()
    assert (accepted["model_service_floor_met"]).all()
