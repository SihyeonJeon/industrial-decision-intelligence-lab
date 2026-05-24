from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

from .optimize import select_frontier_policy
from .sensitivity import plot_sensitivity_grid
from .uncertainty import plot_lead_time_grid


def write_report(
    report_dir: Path,
    forecast_metrics: dict,
    decision_summaries: dict[str, dict[str, float]],
    sku_metrics: pd.DataFrame,
    service_target: float,
    frontier: pd.DataFrame | None = None,
    sensitivity_grid: pd.DataFrame | None = None,
    sensitivity_summary: dict | None = None,
    lead_time_grid: pd.DataFrame | None = None,
    lead_time_summary: dict | None = None,
) -> dict:
    report_dir.mkdir(parents=True, exist_ok=True)
    (report_dir / "figures").mkdir(exist_ok=True)

    baseline_cost = decision_summaries["baseline"]["total_cost"]
    model_cost = decision_summaries["model"]["total_cost"]
    cost_delta = baseline_cost - model_cost
    cost_delta_pct = cost_delta / max(baseline_cost, 1.0)
    model_service = decision_summaries["model"]["service_level"]
    baseline_service = decision_summaries["baseline"]["service_level"]
    service_floor_met = model_service >= service_target
    cost_improved = model_cost < baseline_cost
    recommended_policy = "model" if cost_improved and service_floor_met else "baseline"

    payload = {
        "project": "industrial-decision-intelligence-lab",
        "evidence_grade": "dataset_simulation",
        "claim_allowed": False,
        "scope_note": "UCI Online Retail II simulation, not production inventory advice",
        "forecast": forecast_metrics,
        "decision": {
            "baseline": decision_summaries["baseline"],
            "model": decision_summaries["model"],
            "cost_delta": float(cost_delta),
            "cost_delta_pct": float(cost_delta_pct),
            "service_target": float(service_target),
            "service_delta": float(model_service - baseline_service),
            "service_floor_met": bool(service_floor_met),
            "cost_improved": bool(cost_improved),
            "decision_gate": "pass" if recommended_policy == "model" else "warn",
            "recommended_policy": recommended_policy,
        },
        "frontier_selection": select_frontier_policy(frontier, service_target)
        if frontier is not None
        else {},
        "sensitivity": sensitivity_summary or {},
        "lead_time_uncertainty": lead_time_summary or {},
        "sku_diagnostics": summarize_sku_metrics(sku_metrics),
    }

    with (report_dir / "decision_report.json").open("w") as file:
        json.dump(payload, file, indent=2)

    sku_metrics.to_csv(report_dir / "sku_metrics.csv", index=False)
    plot_sku_tradeoffs(report_dir / "figures" / "sku_tradeoffs.png", sku_metrics, service_target)
    plot_policy_comparison(
        report_dir / "figures" / "policy_comparison.png",
        decision_summaries,
        service_target,
    )
    if frontier is not None:
        frontier.to_csv(report_dir / "service_frontier.csv", index=False)
        plot_service_frontier(report_dir / "figures" / "service_frontier.png", frontier)
    if sensitivity_grid is not None:
        sensitivity_grid.to_csv(report_dir / "sensitivity_grid.csv", index=False)
        plot_sensitivity_grid(report_dir / "figures" / "sensitivity_grid.png", sensitivity_grid)
    if lead_time_grid is not None:
        lead_time_grid.to_csv(report_dir / "lead_time_grid.csv", index=False)
        plot_lead_time_grid(report_dir / "figures" / "lead_time_grid.png", lead_time_grid)
    return payload


def build_sku_metrics(
    predictions: pd.DataFrame,
    detail: pd.DataFrame,
    service_target: float,
) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for sku, sku_predictions in predictions.groupby("sku"):
        actual_sum = max(float(sku_predictions["actual"].sum()), 1.0)
        row: dict[str, object] = {"sku": sku, "actual_units": actual_sum}
        for policy in ["baseline", "model"]:
            error = sku_predictions["actual"] - sku_predictions[f"{policy}_pred"]
            policy_detail = detail[(detail["sku"] == sku) & (detail["policy"] == policy)]
            row[f"{policy}_wape"] = float(error.abs().sum() / actual_sum)
            row[f"{policy}_bias"] = float(error.sum() / actual_sum)
            row[f"{policy}_cost"] = float(policy_detail["total_cost"].sum())
            row[f"{policy}_service_level"] = float(
                policy_detail["fulfilled"].sum() / max(policy_detail["actual"].sum(), 1.0)
            )
        row["cost_delta"] = row["baseline_cost"] - row["model_cost"]
        row["cost_delta_pct"] = row["cost_delta"] / max(float(row["baseline_cost"]), 1.0)
        row["service_delta"] = row["model_service_level"] - row["baseline_service_level"]
        row["model_wape_delta"] = row["model_wape"] - row["baseline_wape"]
        row["model_service_floor_met"] = row["model_service_level"] >= service_target
        row["decision_flag"] = classify_sku(row)
        rows.append(row)
    return pd.DataFrame(rows).sort_values("cost_delta", ascending=False)


def classify_sku(row: dict[str, object]) -> str:
    cost_improved = float(row["cost_delta"]) > 0
    service_floor_met = bool(row["model_service_floor_met"])
    if cost_improved and service_floor_met:
        return "accept"
    if cost_improved and not service_floor_met:
        return "service_risk"
    if not cost_improved and service_floor_met:
        return "cost_risk"
    return "review"


def summarize_sku_metrics(sku_metrics: pd.DataFrame) -> dict[str, object]:
    if sku_metrics.empty:
        return {
            "sku_count": 0,
            "cost_improved_count": 0,
            "service_floor_met_count": 0,
            "service_risk_count": 0,
            "wape_worse_count": 0,
        }

    largest_service_loss = sku_metrics.sort_values("service_delta").iloc[0]
    largest_cost_saving = sku_metrics.sort_values("cost_delta", ascending=False).iloc[0]
    return {
        "sku_count": int(len(sku_metrics)),
        "cost_improved_count": int((sku_metrics["cost_delta"] > 0).sum()),
        "service_floor_met_count": int(sku_metrics["model_service_floor_met"].sum()),
        "service_risk_count": int((sku_metrics["decision_flag"] == "service_risk").sum()),
        "wape_worse_count": int((sku_metrics["model_wape_delta"] > 0).sum()),
        "largest_service_loss_sku": str(largest_service_loss["sku"]),
        "largest_service_loss": float(largest_service_loss["service_delta"]),
        "largest_cost_saving_sku": str(largest_cost_saving["sku"]),
        "largest_cost_saving": float(largest_cost_saving["cost_delta"]),
    }


def plot_sku_tradeoffs(path: Path, sku_metrics: pd.DataFrame, service_target: float) -> None:
    fig, axis = plt.subplots(figsize=(7.4, 4.8))
    colors = {
        "accept": "#2563eb",
        "service_risk": "#ef4444",
        "cost_risk": "#f59e0b",
        "review": "#6b7280",
    }
    for flag, rows in sku_metrics.groupby("decision_flag"):
        axis.scatter(
            rows["cost_delta_pct"],
            rows["service_delta"],
            s=70,
            color=colors.get(flag, "#6b7280"),
            alpha=0.88,
            edgecolor="#111827",
            linewidth=0.35,
            label=flag,
        )

    label_rows = sku_metrics.reindex(
        sku_metrics["service_delta"].abs().sort_values(ascending=False).head(4).index
    )
    for row in label_rows.itertuples(index=False):
        axis.annotate(
            str(row.sku),
            (row.cost_delta_pct, row.service_delta),
            textcoords="offset points",
            xytext=(5, 4),
            fontsize=8,
        )

    axis.axhline(0, color="#111827", linewidth=0.9, alpha=0.5)
    axis.axvline(0, color="#111827", linewidth=0.9, alpha=0.5)
    axis.set_xlabel("cost delta pct")
    axis.set_ylabel("service delta")
    axis.set_title(f"SKU tradeoffs at service floor {service_target:.2f}")
    axis.grid(True, alpha=0.25)
    axis.legend(loc="best", fontsize=8)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_policy_comparison(
    path: Path,
    decision_summaries: dict[str, dict[str, float]],
    service_target: float,
) -> None:
    labels = ["total_cost", "service_level", "stockout_units", "average_inventory"]
    fig, axes = plt.subplots(2, 2, figsize=(8.5, 6.0))
    for axis, metric in zip(axes.ravel(), labels, strict=True):
        values = [decision_summaries["baseline"][metric], decision_summaries["model"][metric]]
        axis.bar(["baseline", "model"], values, color=["#8a8f98", "#2563eb"])
        axis.set_title(metric.replace("_", " "))
        axis.tick_params(axis="x", rotation=20)
        if metric == "service_level":
            axis.set_ylim(0.0, 1.05)
            axis.axhline(service_target, color="#ef4444", linestyle="--", linewidth=1.2)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


def plot_service_frontier(path: Path, frontier: pd.DataFrame) -> None:
    fig, axis = plt.subplots(figsize=(6.8, 4.4))
    for policy, rows in frontier.groupby("policy"):
        rows = rows.sort_values("service_level")
        color = "#2563eb" if policy == "model" else "#8a8f98"
        axis.plot(
            rows["service_level"],
            rows["total_cost"],
            marker="o",
            linewidth=2,
            label=policy,
            color=color,
        )
        for row in rows.itertuples(index=False):
            axis.annotate(
                f"q={row.service_quantile:.2f}",
                (row.service_level, row.total_cost),
                textcoords="offset points",
                xytext=(5, 5),
                fontsize=8,
            )
    axis.set_xlabel("service level")
    axis.set_ylabel("total cost")
    axis.set_title("cost-service frontier")
    axis.grid(True, alpha=0.25)
    axis.legend()
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)
