from __future__ import annotations

import math
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .optimize import PolicyConfig, add_base_stock_levels
from .simulate import SimulationConfig, simulate_policy
from .gate import classify_policy_gate, recommended_policy_for_gate


def parse_float_list(raw: str, name: str) -> list[float]:
    values = [float(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise ValueError(f"{name} must not be empty")
    invalid = [value for value in values if not math.isfinite(value) or value <= 0]
    if invalid:
        raise ValueError(f"{name} must contain positive finite values")
    return sorted(set(values))


def build_sensitivity_grid(
    predictions: pd.DataFrame,
    validation_predictions: pd.DataFrame,
    service_quantiles: list[float],
    holding_costs: list[float],
    stockout_costs: list[float],
    lead_time_days: int,
    service_target: float,
) -> pd.DataFrame:
    rows: list[dict[str, float | str | bool]] = []
    for service_quantile in service_quantiles:
        policy_predictions = add_base_stock_levels(
            predictions,
            validation_predictions,
            PolicyConfig(
                lead_time_days=lead_time_days,
                service_quantile=service_quantile,
            ),
        )
        for holding_cost in holding_costs:
            for stockout_cost in stockout_costs:
                config = SimulationConfig(
                    lead_time_days=lead_time_days,
                    holding_cost_per_unit_day=holding_cost,
                    stockout_cost_per_unit=stockout_cost,
                )
                _baseline_detail, baseline = simulate_policy(policy_predictions, "baseline", config)
                _model_detail, model = simulate_policy(policy_predictions, "model", config)

                baseline_cost = baseline["total_cost"]
                model_cost = model["total_cost"]
                cost_delta = baseline_cost - model_cost
                cost_delta_pct = cost_delta / max(baseline_cost, 1.0)
                service_floor_met = model["service_level"] >= service_target
                cost_improved = model_cost < baseline_cost
                gate = classify_policy_gate(service_floor_met, cost_improved)
                recommended_policy = recommended_policy_for_gate(gate)

                rows.append(
                    {
                        "service_quantile": service_quantile,
                        "holding_cost": holding_cost,
                        "stockout_cost": stockout_cost,
                        "cost_ratio": stockout_cost / holding_cost,
                        "baseline_cost": baseline_cost,
                        "model_cost": model_cost,
                        "cost_delta": cost_delta,
                        "cost_delta_pct": cost_delta_pct,
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


def summarize_sensitivity(grid: pd.DataFrame) -> dict[str, float | int]:
    total = max(len(grid), 1)
    passes = int((grid["decision_gate"] == "pass").sum())
    model_rows = grid[grid["recommended_policy"] == "model"]
    gate_counts = grid["gate"].value_counts().to_dict() if "gate" in grid.columns else {}
    return {
        "scenario_count": int(len(grid)),
        "pass_count": passes,
        "pass_rate": float(passes / total),
        "allow_count": int(gate_counts.get("allow", 0)),
        "review_count": int(gate_counts.get("review", 0)),
        "block_count": int(gate_counts.get("block", 0)),
        "median_cost_delta_pct": float(grid["cost_delta_pct"].median()),
        "min_cost_delta_pct": float(grid["cost_delta_pct"].min()),
        "max_cost_delta_pct": float(grid["cost_delta_pct"].max()),
        "median_model_service": float(grid["model_service_level"].median()),
        "min_model_service": float(grid["model_service_level"].min()),
        "model_policy_count": int(len(model_rows)),
    }


def plot_sensitivity_grid(path: Path, grid: pd.DataFrame) -> None:
    holding_costs = sorted(grid["holding_cost"].unique())
    fig, axes = plt.subplots(
        1,
        len(holding_costs),
        figsize=(3.0 * len(holding_costs) + 1.6, 4.8),
        sharey=True,
        layout="constrained",
    )
    if len(holding_costs) == 1:
        axes = [axes]

    vmin = float(grid["cost_delta_pct"].min())
    vmax = float(grid["cost_delta_pct"].max())
    scatter = None
    for axis, holding_cost in zip(axes, holding_costs, strict=True):
        subset = grid[grid["holding_cost"] == holding_cost]
        passed = subset["gate"] == "allow" if "gate" in subset.columns else subset["decision_gate"] == "pass"
        blocked = subset["gate"] == "block" if "gate" in subset.columns else ~passed
        review = ~(passed | blocked)

        scatter = axis.scatter(
            subset.loc[passed, "stockout_cost"],
            subset.loc[passed, "service_quantile"],
            c=subset.loc[passed, "cost_delta_pct"],
            cmap="Blues",
            vmin=vmin,
            vmax=vmax,
            s=92,
            edgecolor="#1f2937",
            linewidth=0.5,
            label="pass",
        )
        axis.scatter(
            subset.loc[blocked, "stockout_cost"],
            subset.loc[blocked, "service_quantile"],
            marker="x",
            c="#ef4444",
            s=74,
            label="block",
        )
        axis.scatter(
            subset.loc[review, "stockout_cost"],
            subset.loc[review, "service_quantile"],
            marker="^",
            c="#f59e0b",
            s=70,
            label="review",
        )
        axis.set_xscale("log")
        axis.set_xlabel("stockout cost")
        axis.set_title(f"holding {holding_cost:g}")
        axis.grid(True, alpha=0.25)

    axes[0].set_ylabel("service quantile")
    axes[-1].legend(loc="lower right")
    colorbar = fig.colorbar(scatter, ax=axes, fraction=0.046, pad=0.04)
    colorbar.set_label("cost delta pct")
    fig.savefig(path, dpi=160)
    plt.close(fig)
