from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .optimize import PolicyConfig, add_base_stock_levels
from .simulate import SimulationConfig, simulate_policy
from .gate import classify_policy_gate, recommended_policy_for_gate


def parse_int_list(raw: str, name: str) -> list[int]:
    values = [int(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise ValueError(f"{name} must not be empty")
    invalid = [value for value in values if not math.isfinite(value) or value <= 0]
    if invalid:
        raise ValueError(f"{name} must contain positive finite integers")
    return sorted(set(values))


def build_lead_time_grid(
    predictions: pd.DataFrame,
    validation_predictions: pd.DataFrame,
    service_quantiles: list[float],
    lead_time_days: list[int],
    holding_cost: float,
    stockout_cost: float,
    service_target: float,
) -> pd.DataFrame:
    rows: list[dict[str, float | int | str | bool]] = []
    for lead_time in lead_time_days:
        for service_quantile in service_quantiles:
            policy_predictions = add_base_stock_levels(
                predictions,
                validation_predictions,
                PolicyConfig(
                    lead_time_days=lead_time,
                    service_quantile=service_quantile,
                ),
            )
            config = SimulationConfig(
                lead_time_days=lead_time,
                holding_cost_per_unit_day=holding_cost,
                stockout_cost_per_unit=stockout_cost,
            )
            _baseline_detail, baseline = simulate_policy(policy_predictions, "baseline", config)
            _model_detail, model = simulate_policy(policy_predictions, "model", config)
            cost_delta = baseline["total_cost"] - model["total_cost"]
            service_floor_met = model["service_level"] >= service_target
            cost_improved = model["total_cost"] < baseline["total_cost"]
            gate = classify_policy_gate(service_floor_met, cost_improved)
            recommended_policy = recommended_policy_for_gate(gate)
            rows.append(
                {
                    "lead_time_days": int(lead_time),
                    "service_quantile": float(service_quantile),
                    "baseline_cost": baseline["total_cost"],
                    "model_cost": model["total_cost"],
                    "cost_delta": cost_delta,
                    "cost_delta_pct": cost_delta / max(baseline["total_cost"], 1.0),
                    "baseline_service_level": baseline["service_level"],
                    "model_service_level": model["service_level"],
                    "service_delta": model["service_level"] - baseline["service_level"],
                    "model_stockout_units": model["stockout_units"],
                    "model_average_inventory": model["average_inventory"],
                    "service_floor_met": service_floor_met,
                    "cost_improved": cost_improved,
                    "gate": gate,
                    "decision_gate": "pass" if gate == "allow" else "warn",
                    "recommended_policy": recommended_policy,
                }
            )
    return pd.DataFrame(rows)


def summarize_lead_time_grid(grid: pd.DataFrame) -> dict[str, float | int | None]:
    total = max(len(grid), 1)
    passes = int((grid["decision_gate"] == "pass").sum())
    gate_counts = grid["gate"].value_counts().to_dict() if "gate" in grid.columns else {}
    robust = _select_robust_quantile(grid)
    return {
        "scenario_count": int(len(grid)),
        "pass_count": passes,
        "pass_rate": float(passes / total),
        "allow_count": int(gate_counts.get("allow", 0)),
        "review_count": int(gate_counts.get("review", 0)),
        "block_count": int(gate_counts.get("block", 0)),
        "lead_time_min": int(grid["lead_time_days"].min()),
        "lead_time_max": int(grid["lead_time_days"].max()),
        "worst_model_service": float(grid["model_service_level"].min()),
        "median_cost_delta_pct": float(grid["cost_delta_pct"].median()),
        "robust_service_quantile": robust["service_quantile"],
        "robust_mean_model_cost": robust["mean_model_cost"],
        "robust_worst_model_service": robust["worst_model_service"],
    }


def plot_lead_time_grid(path: Path, grid: pd.DataFrame) -> None:
    fig, axis = plt.subplots(figsize=(7.0, 4.6), layout="constrained")
    passed = grid["gate"] == "allow" if "gate" in grid.columns else grid["decision_gate"] == "pass"
    blocked = grid["gate"] == "block" if "gate" in grid.columns else ~passed
    review = ~(passed | blocked)
    vmin = float(grid["cost_delta_pct"].min())
    vmax = float(grid["cost_delta_pct"].max())
    scatter = axis.scatter(
        grid.loc[passed, "lead_time_days"],
        grid.loc[passed, "service_quantile"],
        c=grid.loc[passed, "cost_delta_pct"],
        cmap="Blues",
        vmin=vmin,
        vmax=vmax,
        s=96,
        edgecolor="#1f2937",
        linewidth=0.5,
        label="pass",
    )
    axis.scatter(
        grid.loc[blocked, "lead_time_days"],
        grid.loc[blocked, "service_quantile"],
        marker="x",
        c="#ef4444",
        s=78,
        label="block",
    )
    axis.scatter(
        grid.loc[review, "lead_time_days"],
        grid.loc[review, "service_quantile"],
        marker="^",
        c="#f59e0b",
        s=72,
        label="review",
    )
    axis.set_xlabel("lead time days")
    axis.set_ylabel("service quantile")
    axis.set_title("lead-time uncertainty grid")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best")
    colorbar = fig.colorbar(scatter, ax=axis)
    colorbar.set_label("cost delta pct")
    fig.savefig(path, dpi=160)
    plt.close(fig)


def _select_robust_quantile(grid: pd.DataFrame) -> dict[str, float | None]:
    candidates = []
    for service_quantile, rows in grid.groupby("service_quantile"):
        gate_col = "gate" if "gate" in rows.columns else "decision_gate"
        allow_value = "allow" if gate_col == "gate" else "pass"
        if bool((rows[gate_col] == allow_value).all()):
            candidates.append(
                {
                    "service_quantile": float(service_quantile),
                    "mean_model_cost": float(rows["model_cost"].mean()),
                    "worst_model_service": float(rows["model_service_level"].min()),
                }
            )
    if not candidates:
        return {
            "service_quantile": None,
            "mean_model_cost": None,
            "worst_model_service": None,
        }
    return sorted(candidates, key=lambda item: (item["mean_model_cost"], item["service_quantile"]))[0]
