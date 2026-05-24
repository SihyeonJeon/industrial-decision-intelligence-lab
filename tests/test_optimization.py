from __future__ import annotations

import pandas as pd

from decision_lab.optimize import select_frontier_policy


def test_select_frontier_policy_uses_lowest_cost_feasible_row() -> None:
    frontier = pd.DataFrame(
        [
            {
                "service_quantile": 0.90,
                "policy": "baseline",
                "total_cost": 100.0,
                "service_level": 0.91,
                "stockout_units": 9.0,
                "average_inventory": 20.0,
            },
            {
                "service_quantile": 0.99,
                "policy": "baseline",
                "total_cost": 140.0,
                "service_level": 0.97,
                "stockout_units": 3.0,
                "average_inventory": 30.0,
            },
            {
                "service_quantile": 0.90,
                "policy": "model",
                "total_cost": 70.0,
                "service_level": 0.88,
                "stockout_units": 12.0,
                "average_inventory": 14.0,
            },
            {
                "service_quantile": 0.99,
                "policy": "model",
                "total_cost": 85.0,
                "service_level": 0.93,
                "stockout_units": 7.0,
                "average_inventory": 18.0,
            },
        ]
    )

    selected = select_frontier_policy(frontier, service_target=0.90)

    assert selected["baseline"]["service_quantile"] == 0.90
    assert selected["model"]["service_quantile"] == 0.99
    assert selected["recommended_policy"] == "model"
    assert selected["decision_gate"] == "pass"
