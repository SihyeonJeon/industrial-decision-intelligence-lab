from __future__ import annotations

import pandas as pd
import pytest

from decision_lab.uncertainty import parse_int_list, summarize_lead_time_grid


def test_parse_int_list_rejects_invalid_values() -> None:
    for raw in ("", "1,0", "-1,2"):
        with pytest.raises(ValueError):
            parse_int_list(raw, "lead times")


def test_parse_int_list_sorts_and_deduplicates() -> None:
    assert parse_int_list("7,3,7", "lead times") == [3, 7]


def test_summarize_lead_time_grid_selects_robust_quantile() -> None:
    grid = pd.DataFrame(
        [
            {
                "lead_time_days": 5,
                "service_quantile": 0.90,
                "model_cost": 50.0,
                "model_service_level": 0.91,
                "cost_delta_pct": 0.20,
                "gate": "allow",
                "decision_gate": "pass",
            },
            {
                "lead_time_days": 7,
                "service_quantile": 0.90,
                "model_cost": 70.0,
                "model_service_level": 0.89,
                "cost_delta_pct": 0.10,
                "gate": "block",
                "decision_gate": "warn",
            },
            {
                "lead_time_days": 5,
                "service_quantile": 0.99,
                "model_cost": 80.0,
                "model_service_level": 0.94,
                "cost_delta_pct": 0.30,
                "gate": "allow",
                "decision_gate": "pass",
            },
            {
                "lead_time_days": 7,
                "service_quantile": 0.99,
                "model_cost": 100.0,
                "model_service_level": 0.92,
                "cost_delta_pct": 0.25,
                "gate": "allow",
                "decision_gate": "pass",
            },
        ]
    )

    summary = summarize_lead_time_grid(grid)

    assert summary["scenario_count"] == 4
    assert summary["pass_count"] == 3
    assert summary["robust_service_quantile"] == 0.99
    assert summary["robust_worst_model_service"] == 0.92
