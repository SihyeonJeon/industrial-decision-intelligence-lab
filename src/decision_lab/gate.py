from __future__ import annotations

import pandas as pd


def classify_policy_gate(
    service_floor_met: bool,
    cost_improved: bool,
) -> str:
    if not service_floor_met:
        return "block"
    if not cost_improved:
        return "review"
    return "allow"


def classify_grid_gate(row: pd.Series) -> str:
    return classify_policy_gate(
        service_floor_met=bool(row["service_floor_met"]),
        cost_improved=bool(row["cost_improved"]),
    )


def recommended_policy_for_gate(gate: str) -> str:
    return "model" if gate == "allow" else "baseline"


def build_gate_summary(
    sensitivity_grid: pd.DataFrame | None,
    lead_time_grid: pd.DataFrame | None,
    sku_metrics: pd.DataFrame,
) -> dict[str, object]:
    sensitivity_counts = _gate_counts(sensitivity_grid)
    lead_time_counts = _gate_counts(lead_time_grid)
    sku_counts = _sku_gate_counts(sku_metrics)

    robust_quantile = None
    robust_lead_time_passes = 0
    robust_lead_time_total = 0
    if lead_time_grid is not None and not lead_time_grid.empty:
        candidate_rows = []
        for service_quantile, rows in lead_time_grid.groupby("service_quantile"):
            if bool((rows["gate"] == "allow").all()):
                candidate_rows.append(
                    {
                        "service_quantile": float(service_quantile),
                        "mean_model_cost": float(rows["model_cost"].mean()),
                        "worst_model_service": float(rows["model_service_level"].min()),
                        "passes": int((rows["gate"] == "allow").sum()),
                        "total": int(len(rows)),
                    }
                )
        if candidate_rows:
            selected = sorted(
                candidate_rows,
                key=lambda row: (row["mean_model_cost"], row["service_quantile"]),
            )[0]
            robust_quantile = selected["service_quantile"]
            robust_lead_time_passes = selected["passes"]
            robust_lead_time_total = selected["total"]

    if robust_quantile is None:
        final_gate = "review"
        final_action = "keep baseline until lead-time calibration produces an allowed model quantile"
    elif sku_counts["block"] > 0:
        final_gate = "review"
        final_action = "allow robust model quantile only with SKU-level overrides"
    else:
        final_gate = "allow"
        final_action = "allow robust model quantile"

    return {
        "gate_states": ["allow", "review", "block"],
        "final_gate": final_gate,
        "final_action": final_action,
        "robust_service_quantile": robust_quantile,
        "robust_lead_time_passes": robust_lead_time_passes,
        "robust_lead_time_total": robust_lead_time_total,
        "sensitivity_counts": sensitivity_counts,
        "lead_time_counts": lead_time_counts,
        "sku_counts": sku_counts,
    }


def _gate_counts(grid: pd.DataFrame | None) -> dict[str, int]:
    counts = {"allow": 0, "review": 0, "block": 0}
    if grid is None or grid.empty or "gate" not in grid.columns:
        return counts
    raw = grid["gate"].value_counts().to_dict()
    for gate in counts:
        counts[gate] = int(raw.get(gate, 0))
    return counts


def _sku_gate_counts(sku_metrics: pd.DataFrame) -> dict[str, int]:
    counts = {"allow": 0, "review": 0, "block": 0}
    if sku_metrics.empty:
        return counts
    for row in sku_metrics.itertuples(index=False):
        if not bool(row.model_service_floor_met):
            counts["block"] += 1
        elif float(row.cost_delta) <= 0:
            counts["review"] += 1
        else:
            counts["allow"] += 1
    return counts
