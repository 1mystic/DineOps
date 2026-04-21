from __future__ import annotations

from datetime import timedelta

import numpy as np
import pandas as pd


def _sarima_like_baseline(series: pd.Series, horizon: int) -> np.ndarray:
    recent = series.tail(min(len(series), 24))
    return np.full(horizon, float(recent.mean()))


def _additive_like(series: pd.Series, timestamps: pd.Series, horizon: int) -> np.ndarray:
    df = pd.DataFrame({"y": series.values, "h": timestamps.dt.hour.values})
    hour_avg = df.groupby("h")["y"].mean().to_dict()
    base = float(series.tail(24).mean())
    out = []
    start = timestamps.iloc[-1]
    for i in range(1, horizon + 1):
        ts = start + timedelta(hours=i)
        out.append(hour_avg.get(ts.hour, base))
    return np.array(out)


def _deep_like(series: pd.Series, horizon: int) -> np.ndarray:
    y = series.values.astype(float)
    if len(y) < 3:
        return np.full(horizon, float(np.mean(y)))
    trend = (y[-1] - y[-3]) / 2.0
    return np.array([max(y[-1] + trend * i, 0.0) for i in range(1, horizon + 1)])


def ensemble_forecast(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    ordered = df.sort_values("timestamp")
    y_orders = ordered["orders_count"]
    y_revenue = ordered["revenue"]
    timestamps = pd.to_datetime(ordered["timestamp"], utc=True)

    weights = {"sarima": 0.35, "additive": 0.30, "temporal": 0.35}

    f1_o = _sarima_like_baseline(y_orders, horizon)
    f2_o = _additive_like(y_orders, timestamps, horizon)
    f3_o = _deep_like(y_orders, horizon)

    f1_r = _sarima_like_baseline(y_revenue, horizon)
    f2_r = _additive_like(y_revenue, timestamps, horizon)
    f3_r = _deep_like(y_revenue, horizon)

    orders_forecast = weights["sarima"] * f1_o + weights["additive"] * f2_o + weights["temporal"] * f3_o
    revenue_forecast = weights["sarima"] * f1_r + weights["additive"] * f2_r + weights["temporal"] * f3_r

    last_ts = timestamps.iloc[-1]
    rows = []
    for i in range(1, horizon + 1):
        rows.append(
            {
                "timestamp": last_ts + timedelta(hours=i),
                "orders_count": float(max(orders_forecast[i - 1], 0.0)),
                "revenue": float(max(revenue_forecast[i - 1], 0.0)),
            }
        )

    result = pd.DataFrame(rows)
    result.attrs["weights"] = weights
    return result
