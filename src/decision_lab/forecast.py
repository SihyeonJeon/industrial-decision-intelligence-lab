from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.metrics import mean_absolute_error
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


@dataclass(frozen=True)
class ForecastConfig:
    validation_days: int = 45
    test_days: int = 60
    random_state: int = 7


NUMERIC_FEATURES = [
    "lag_1",
    "lag_7",
    "lag_14",
    "lag_28",
    "roll_mean_7",
    "roll_std_7",
    "roll_mean_14",
    "roll_std_14",
    "roll_mean_28",
    "roll_std_28",
    "day_of_week",
    "day_of_month",
    "month",
    "is_weekend",
    "trend",
]
CATEGORICAL_FEATURES = ["sku"]


def run_forecasts(frame: pd.DataFrame, config: ForecastConfig) -> dict[str, pd.DataFrame | dict]:
    max_date = frame["date"].max()
    test_start = max_date - pd.Timedelta(days=config.test_days - 1)
    validation_start = test_start - pd.Timedelta(days=config.validation_days)

    train_core = frame[frame["date"] < validation_start].copy()
    validation = frame[(frame["date"] >= validation_start) & (frame["date"] < test_start)].copy()
    train_full = frame[frame["date"] < test_start].copy()
    test = frame[frame["date"] >= test_start].copy()

    if train_core.empty or validation.empty or test.empty:
        raise ValueError("not enough history for train/validation/test split")

    validation = _predict_split(train_core, validation, config, "model_pred")
    test = _predict_split(train_full, test, config, "model_pred")

    validation["baseline_pred"] = _seasonal_naive(validation)
    test["baseline_pred"] = _seasonal_naive(test)

    prediction_cols = ["sku", "date", "demand", "baseline_pred", "model_pred"]
    predictions = test[prediction_cols].rename(columns={"demand": "actual"}).copy()
    validation_predictions = validation[prediction_cols].rename(columns={"demand": "actual"}).copy()

    metrics = {
        "split": {
            "train_rows": int(len(train_full)),
            "validation_rows": int(len(validation)),
            "test_rows": int(len(test)),
            "test_start": str(test_start.date()),
            "test_end": str(max_date.date()),
        },
        "baseline": forecast_metrics(predictions["actual"], predictions["baseline_pred"]),
        "model": forecast_metrics(predictions["actual"], predictions["model_pred"]),
    }

    return {
        "predictions": predictions,
        "validation_predictions": validation_predictions,
        "metrics": metrics,
    }


def forecast_metrics(actual: pd.Series, predicted: pd.Series) -> dict[str, float]:
    actual_arr = actual.to_numpy(dtype=float)
    pred_arr = predicted.to_numpy(dtype=float)
    denominator = max(float(np.abs(actual_arr).sum()), 1.0)
    error = actual_arr - pred_arr
    return {
        "mae": float(mean_absolute_error(actual_arr, pred_arr)),
        "wape": float(np.abs(error).sum() / denominator),
        "bias": float(error.sum() / denominator),
    }


def _predict_split(
    train: pd.DataFrame,
    target: pd.DataFrame,
    config: ForecastConfig,
    output_col: str,
) -> pd.DataFrame:
    model = _make_model(config)
    model.fit(train[NUMERIC_FEATURES + CATEGORICAL_FEATURES], train["demand"])
    predicted = model.predict(target[NUMERIC_FEATURES + CATEGORICAL_FEATURES])
    out = target.copy()
    out[output_col] = np.clip(predicted, 0.0, None)
    return out


def _make_model(config: ForecastConfig) -> Pipeline:
    preprocess = ColumnTransformer(
        transformers=[
            ("sku", OneHotEncoder(handle_unknown="ignore", sparse_output=False), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES),
        ]
    )
    regressor = HistGradientBoostingRegressor(
        loss="poisson",
        max_iter=220,
        learning_rate=0.055,
        max_leaf_nodes=24,
        min_samples_leaf=18,
        l2_regularization=0.02,
        random_state=config.random_state,
    )
    return Pipeline([("preprocess", preprocess), ("regressor", regressor)])


def _seasonal_naive(frame: pd.DataFrame) -> pd.Series:
    baseline = frame["lag_7"].where(frame["lag_7"].notna(), frame["roll_mean_28"])
    baseline = baseline.where(baseline.notna(), frame["roll_mean_7"])
    baseline = baseline.fillna(frame["demand"].median())
    return baseline.clip(lower=0.0)
