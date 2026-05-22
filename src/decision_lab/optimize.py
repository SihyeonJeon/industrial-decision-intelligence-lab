from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class PolicyConfig:
    lead_time_days: int = 7
    service_quantile: float = 0.99
    min_base_stock: float = 1.0


def add_base_stock_levels(
    predictions: pd.DataFrame,
    validation_predictions: pd.DataFrame,
    config: PolicyConfig,
) -> pd.DataFrame:
    out = predictions.copy()
    for policy in ["baseline", "model"]:
        pred_col = f"{policy}_pred"
        residual_quantile = _positive_residual_quantile(
            validation_predictions,
            pred_col,
            config.service_quantile,
        )
        out[f"{policy}_base_stock"] = out.apply(
            lambda row: _base_stock(
                daily_forecast=float(row[pred_col]),
                residual_quantile=float(residual_quantile.get(row["sku"], 0.0)),
                config=config,
            ),
            axis=1,
        )
    return out


def _positive_residual_quantile(
    validation: pd.DataFrame,
    pred_col: str,
    quantile: float,
) -> dict[str, float]:
    work = validation[["sku", "actual", pred_col]].copy()
    work["positive_residual"] = np.clip(work["actual"] - work[pred_col], 0.0, None)
    values = work.groupby("sku")["positive_residual"].quantile(quantile)
    return {str(sku): float(value) for sku, value in values.items()}


def _base_stock(daily_forecast: float, residual_quantile: float, config: PolicyConfig) -> float:
    demand_during_lead = daily_forecast * config.lead_time_days
    safety_stock = residual_quantile * np.sqrt(config.lead_time_days)
    return max(config.min_base_stock, demand_during_lead + safety_stock)
