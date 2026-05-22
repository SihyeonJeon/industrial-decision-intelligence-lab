from __future__ import annotations

import pandas as pd

from decision_lab.simulate import SimulationConfig, simulate_policy


def test_higher_base_stock_reduces_stockout_in_short_simulation() -> None:
    dates = pd.date_range("2025-01-01", periods=12, freq="D")
    predictions = pd.DataFrame(
        {
            "sku": ["SKU001"] * len(dates),
            "date": dates,
            "actual": [8.0] * len(dates),
            "baseline_base_stock": [2.0] * len(dates),
            "model_base_stock": [16.0] * len(dates),
        }
    )
    config = SimulationConfig(lead_time_days=2, holding_cost_per_unit_day=0.01, stockout_cost_per_unit=5.0)

    _baseline_detail, baseline = simulate_policy(predictions, "baseline", config)
    _model_detail, model = simulate_policy(predictions, "model", config)

    assert model["stockout_units"] < baseline["stockout_units"]
    assert model["service_level"] > baseline["service_level"]
