from __future__ import annotations

import pandas as pd

from decision_lab.features import FeatureConfig, build_daily_demand, build_supervised_frame


def test_supervised_lags_do_not_include_current_day() -> None:
    transactions = pd.DataFrame(
        {
            "invoice": [f"I{i}" for i in range(40)],
            "stock_code": ["SKU001"] * 40,
            "date": pd.date_range("2025-01-01", periods=40, freq="D"),
            "quantity": [float(i) for i in range(40)],
            "unit_price": [1.0] * 40,
            "revenue": [1.0] * 40,
        }
    )
    config = FeatureConfig(top_skus=1, min_days=30)
    daily = build_daily_demand(transactions, config)
    supervised = build_supervised_frame(daily, config)

    row = supervised.iloc[0]
    source = daily[(daily["sku"] == row["sku"]) & (daily["date"] == row["date"])]
    previous = daily[(daily["sku"] == row["sku"]) & (daily["date"] == row["date"] - pd.Timedelta(days=1))]

    assert row["demand"] == float(source["demand"].iloc[0])
    assert row["lag_1"] == float(previous["demand"].iloc[0])
    assert row["lag_1"] != row["demand"]
