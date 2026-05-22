from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class FeatureConfig:
    top_skus: int = 12
    min_days: int = 180
    lags: tuple[int, ...] = (1, 7, 14, 28)
    rolling_windows: tuple[int, ...] = (7, 14, 28)


def build_daily_demand(transactions: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    daily = (
        transactions.groupby(["stock_code", "date"], as_index=False)["quantity"]
        .sum()
        .rename(columns={"stock_code": "sku", "quantity": "demand"})
    )

    sku_rank = (
        daily.groupby("sku")
        .agg(total_demand=("demand", "sum"), active_days=("date", "nunique"))
        .query("active_days >= @config.min_days")
        .sort_values(["total_demand", "active_days"], ascending=False)
        .head(config.top_skus)
        .index
    )

    if sku_rank.empty:
        raise ValueError("no SKU satisfied the minimum history requirement")

    selected = daily[daily["sku"].isin(sku_rank)].copy()
    start = selected["date"].min()
    end = selected["date"].max()
    calendar = pd.MultiIndex.from_product(
        [list(sku_rank), pd.date_range(start, end, freq="D")],
        names=["sku", "date"],
    )

    dense = (
        selected.set_index(["sku", "date"])
        .reindex(calendar, fill_value=0.0)
        .reset_index()
        .sort_values(["sku", "date"])
        .reset_index(drop=True)
    )
    dense["demand"] = dense["demand"].astype(float)
    return dense


def build_supervised_frame(daily: pd.DataFrame, config: FeatureConfig) -> pd.DataFrame:
    frame = daily.sort_values(["sku", "date"]).copy()
    grouped = frame.groupby("sku", group_keys=False)

    for lag in config.lags:
        frame[f"lag_{lag}"] = grouped["demand"].shift(lag)

    for window in config.rolling_windows:
        frame[f"roll_mean_{window}"] = grouped["demand"].shift(1).rolling(window).mean()
        frame[f"roll_std_{window}"] = grouped["demand"].shift(1).rolling(window).std()

    frame["day_of_week"] = frame["date"].dt.dayofweek
    frame["day_of_month"] = frame["date"].dt.day
    frame["month"] = frame["date"].dt.month
    frame["is_weekend"] = frame["day_of_week"].isin([5, 6]).astype(int)
    frame["trend"] = grouped.cumcount()

    feature_cols = [col for col in frame.columns if col.startswith(("lag_", "roll_"))]
    frame[feature_cols] = frame[feature_cols].replace([np.inf, -np.inf], np.nan)
    frame = frame.dropna(subset=feature_cols).reset_index(drop=True)
    return frame


def make_synthetic_transactions(days: int = 260, sku_count: int = 4) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    start = pd.Timestamp("2024-01-01")
    rng = np.random.default_rng(7)
    for sku_idx in range(sku_count):
        sku = f"SKU{sku_idx + 1:03d}"
        base = 8 + sku_idx * 3
        for day in range(days):
            date = start + pd.Timedelta(days=day)
            seasonal = 4 * np.sin(day / 7 * 2 * np.pi) + 2 * np.sin(day / 30 * 2 * np.pi)
            promo = 14 if day % (43 + sku_idx) in {0, 1, 2} else 0
            demand = max(0, round(base + seasonal + promo + rng.normal(0, 2)))
            if demand == 0:
                continue
            rows.append(
                {
                    "invoice": f"SYN{sku_idx:02d}{day:04d}",
                    "stock_code": sku,
                    "date": date,
                    "quantity": float(demand),
                    "unit_price": 2.5 + sku_idx,
                    "revenue": float(demand) * (2.5 + sku_idx),
                }
            )
    return pd.DataFrame(rows)
