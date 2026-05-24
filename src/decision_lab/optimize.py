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


def select_frontier_policy(frontier: pd.DataFrame, service_target: float) -> dict[str, object]:
    selections = {
        "baseline": _select_policy_rows(frontier, "baseline", service_target),
        "model": _select_policy_rows(frontier, "model", service_target),
    }
    baseline = selections["baseline"]
    model = selections["model"]
    baseline_cost = float(baseline["total_cost"])
    model_cost = float(model["total_cost"])
    cost_delta = baseline_cost - model_cost
    model_feasible = bool(model["service_floor_met"])
    cost_improved = model_cost < baseline_cost
    recommended_policy = "model" if model_feasible and cost_improved else "baseline"
    return {
        "service_target": float(service_target),
        "baseline": baseline,
        "model": model,
        "cost_delta": float(cost_delta),
        "cost_delta_pct": float(cost_delta / max(baseline_cost, 1.0)),
        "service_delta": float(model["service_level"] - baseline["service_level"]),
        "decision_gate": "pass" if recommended_policy == "model" else "warn",
        "recommended_policy": recommended_policy,
    }


def _select_policy_rows(frontier: pd.DataFrame, policy: str, service_target: float) -> dict[str, object]:
    rows = frontier[frontier["policy"] == policy].copy()
    if rows.empty:
        raise ValueError(f"frontier has no rows for policy: {policy}")
    rows["service_floor_met"] = rows["service_level"] >= service_target
    feasible = rows[rows["service_floor_met"]]
    if feasible.empty:
        selected = rows.sort_values(["service_level", "total_cost"], ascending=[False, True]).iloc[0]
    else:
        selected = feasible.sort_values(["total_cost", "service_level"], ascending=[True, False]).iloc[0]
    return {
        "service_quantile": float(selected["service_quantile"]),
        "total_cost": float(selected["total_cost"]),
        "service_level": float(selected["service_level"]),
        "stockout_units": float(selected["stockout_units"]),
        "average_inventory": float(selected["average_inventory"]),
        "service_floor_met": bool(selected["service_floor_met"]),
        "feasible_count": int(rows["service_floor_met"].sum()),
    }
