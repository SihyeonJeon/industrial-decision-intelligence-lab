from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd

from .data import DEFAULT_XLSX, fetch_online_retail_ii, load_transactions
from .features import (
    FeatureConfig,
    build_daily_demand,
    build_supervised_frame,
    make_synthetic_transactions,
)
from .forecast import ForecastConfig, run_forecasts
from .optimize import PolicyConfig, add_base_stock_levels
from .report import build_sku_metrics, write_report
from .sensitivity import build_sensitivity_grid, parse_float_list, summarize_sensitivity
from .simulate import SimulationConfig, simulate_policy
from .uncertainty import build_lead_time_grid, parse_int_list, summarize_lead_time_grid


def main() -> None:
    parser = argparse.ArgumentParser(prog="decision-lab")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("fetch", help="Download UCI Online Retail II into data/raw")

    run = subparsers.add_parser("run", help="Run forecast-to-inventory simulation")
    run.add_argument("--raw-file", type=Path, default=DEFAULT_XLSX)
    run.add_argument("--report-dir", type=Path, default=Path("reports"))
    run.add_argument("--top-skus", type=int, default=12)
    run.add_argument("--min-days", type=int, default=180)
    run.add_argument("--validation-days", type=int, default=45)
    run.add_argument("--test-days", type=int, default=60)
    run.add_argument("--lead-time-days", type=int, default=7)
    run.add_argument("--service-quantile", type=float, default=0.99)
    run.add_argument("--service-target", type=float, default=0.90)
    run.add_argument("--holding-cost", type=float, default=0.04)
    run.add_argument("--stockout-cost", type=float, default=4.0)
    run.add_argument("--frontier-quantiles", default="0.84,0.90,0.95,0.99")
    run.add_argument("--sensitivity-holding-costs", default="0.02,0.04,0.08")
    run.add_argument("--sensitivity-stockout-costs", default="2.0,4.0,8.0")
    run.add_argument("--uncertainty-lead-times", default="5,7,10,14")
    run.add_argument("--synthetic", action="store_true")

    args = parser.parse_args()
    if args.command == "fetch":
        path = fetch_online_retail_ii()
        print(path)
        return

    if args.command == "run":
        payload = run_pipeline(args)
        decision = payload["decision"]
        print(
            "gate={gate} recommended={policy} baseline_cost={baseline:.2f} "
            "model_cost={model:.2f} delta_pct={delta:.2%} model_service={service:.3f}".format(
                gate=decision["decision_gate"],
                policy=decision["recommended_policy"],
                baseline=decision["baseline"]["total_cost"],
                model=decision["model"]["total_cost"],
                delta=decision["cost_delta_pct"],
                service=decision["model"]["service_level"],
            )
        )


def run_pipeline(args: argparse.Namespace) -> dict:
    feature_config = FeatureConfig(top_skus=args.top_skus, min_days=args.min_days)
    forecast_config = ForecastConfig(
        validation_days=args.validation_days,
        test_days=args.test_days,
    )
    policy_config = PolicyConfig(
        lead_time_days=args.lead_time_days,
        service_quantile=args.service_quantile,
    )
    simulation_config = SimulationConfig(
        lead_time_days=args.lead_time_days,
        holding_cost_per_unit_day=args.holding_cost,
        stockout_cost_per_unit=args.stockout_cost,
    )

    if args.synthetic:
        transactions = make_synthetic_transactions(days=320, sku_count=max(args.top_skus, 4))
    else:
        transactions = load_transactions(args.raw_file)

    daily = build_daily_demand(transactions, feature_config)
    supervised = build_supervised_frame(daily, feature_config)
    forecast_result = run_forecasts(supervised, forecast_config)

    predictions = add_base_stock_levels(
        forecast_result["predictions"],
        forecast_result["validation_predictions"],
        policy_config,
    )

    baseline_detail, baseline_summary = simulate_policy(predictions, "baseline", simulation_config)
    model_detail, model_summary = simulate_policy(predictions, "model", simulation_config)
    detail = pd.concat([baseline_detail, model_detail], ignore_index=True)

    sku_metrics = build_sku_metrics(predictions, detail, args.service_target)
    frontier = build_frontier(
        forecast_result["predictions"],
        forecast_result["validation_predictions"],
        simulation_config,
        parse_quantiles(args.frontier_quantiles),
        args.lead_time_days,
    )
    sensitivity_grid = build_sensitivity_grid(
        forecast_result["predictions"],
        forecast_result["validation_predictions"],
        parse_quantiles(args.frontier_quantiles),
        parse_float_list(args.sensitivity_holding_costs, "sensitivity holding costs"),
        parse_float_list(args.sensitivity_stockout_costs, "sensitivity stockout costs"),
        args.lead_time_days,
        args.service_target,
    )
    lead_time_grid = build_lead_time_grid(
        forecast_result["predictions"],
        forecast_result["validation_predictions"],
        parse_quantiles(args.frontier_quantiles),
        parse_int_list(args.uncertainty_lead_times, "uncertainty lead times"),
        args.holding_cost,
        args.stockout_cost,
        args.service_target,
    )
    return write_report(
        args.report_dir,
        forecast_result["metrics"],
        {"baseline": baseline_summary, "model": model_summary},
        sku_metrics,
        args.service_target,
        frontier,
        sensitivity_grid,
        summarize_sensitivity(sensitivity_grid),
        lead_time_grid,
        summarize_lead_time_grid(lead_time_grid),
    )


def parse_quantiles(raw: str) -> list[float]:
    values = [float(part.strip()) for part in raw.split(",") if part.strip()]
    if not values:
        raise ValueError("frontier quantiles must not be empty")
    for value in values:
        if not 0.0 < value < 1.0:
            raise ValueError(f"frontier quantile out of range: {value}")
    return sorted(set(values))


def build_frontier(
    predictions: pd.DataFrame,
    validation_predictions: pd.DataFrame,
    simulation_config: SimulationConfig,
    quantiles: list[float],
    lead_time_days: int,
) -> pd.DataFrame:
    rows: list[dict[str, float | str]] = []
    for quantile in quantiles:
        policy_predictions = add_base_stock_levels(
            predictions,
            validation_predictions,
            PolicyConfig(
                lead_time_days=lead_time_days,
                service_quantile=quantile,
            ),
        )
        for policy in ["baseline", "model"]:
            _detail, summary = simulate_policy(policy_predictions, policy, simulation_config)
            rows.append(
                {
                    "service_quantile": quantile,
                    "policy": policy,
                    "total_cost": summary["total_cost"],
                    "service_level": summary["service_level"],
                    "stockout_units": summary["stockout_units"],
                    "average_inventory": summary["average_inventory"],
                }
            )
    return pd.DataFrame(rows)


if __name__ == "__main__":
    main()
