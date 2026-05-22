from __future__ import annotations

from dataclasses import dataclass

import pandas as pd


@dataclass(frozen=True)
class SimulationConfig:
    lead_time_days: int = 7
    holding_cost_per_unit_day: float = 0.04
    stockout_cost_per_unit: float = 4.0
    order_cost: float = 0.0


def simulate_policy(
    predictions: pd.DataFrame,
    policy: str,
    config: SimulationConfig,
) -> tuple[pd.DataFrame, dict[str, float]]:
    base_col = f"{policy}_base_stock"
    rows: list[dict[str, object]] = []

    for sku, sku_frame in predictions.sort_values(["sku", "date"]).groupby("sku"):
        inventory = float(sku_frame[base_col].iloc[0])
        pipeline: dict[pd.Timestamp, float] = {}
        for record in sku_frame.itertuples(index=False):
            date = pd.Timestamp(record.date)
            demand = float(record.actual)
            base_stock = float(getattr(record, base_col))
            received = pipeline.pop(date, 0.0)
            inventory += received

            fulfilled = min(inventory, demand)
            stockout = max(demand - fulfilled, 0.0)
            inventory -= fulfilled

            on_order = sum(pipeline.values())
            order_quantity = max(base_stock - inventory - on_order, 0.0)
            if order_quantity > 0:
                arrival = date + pd.Timedelta(days=config.lead_time_days)
                pipeline[arrival] = pipeline.get(arrival, 0.0) + order_quantity

            holding_cost = inventory * config.holding_cost_per_unit_day
            stockout_cost = stockout * config.stockout_cost_per_unit
            order_cost = config.order_cost if order_quantity > 0 else 0.0

            rows.append(
                {
                    "sku": sku,
                    "date": date,
                    "policy": policy,
                    "actual": demand,
                    "base_stock": base_stock,
                    "received": received,
                    "fulfilled": fulfilled,
                    "stockout": stockout,
                    "ending_inventory": inventory,
                    "order_quantity": order_quantity,
                    "holding_cost": holding_cost,
                    "stockout_cost": stockout_cost,
                    "order_cost": order_cost,
                    "total_cost": holding_cost + stockout_cost + order_cost,
                }
            )

    detail = pd.DataFrame(rows)
    summary = summarize_simulation(detail)
    return detail, summary


def summarize_simulation(detail: pd.DataFrame) -> dict[str, float]:
    demand = max(float(detail["actual"].sum()), 1.0)
    return {
        "total_cost": float(detail["total_cost"].sum()),
        "service_level": float(detail["fulfilled"].sum() / demand),
        "stockout_units": float(detail["stockout"].sum()),
        "holding_units": float(detail["ending_inventory"].sum()),
        "average_inventory": float(detail["ending_inventory"].mean()),
        "order_units": float(detail["order_quantity"].sum()),
        "sku_count": int(detail["sku"].nunique()),
        "days": int(detail["date"].nunique()),
    }
