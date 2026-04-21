from __future__ import annotations

import numpy as np
import pandas as pd

NUMERIC_FOR_SCALING = [
    "orders_count",
    "revenue",
    "avg_order_value",
    "inventory_used",
    "staff_count",
    "prep_time",
    "delivery_time",
]


def build_features(df: pd.DataFrame, external_signals: list[dict] | None = None) -> pd.DataFrame:
    out = df.copy()
    out["timestamp"] = pd.to_datetime(out["timestamp"], utc=True)

    out["hour"] = out["timestamp"].dt.hour
    out["weekday"] = out["timestamp"].dt.weekday
    out["month"] = out["timestamp"].dt.month
    out["date"] = out["timestamp"].dt.date
    out["is_weekend"] = (out["weekday"] >= 5).astype(int)

    out = out.sort_values(["location_id", "timestamp"]).reset_index(drop=True)
    out["orders_lag_1"] = out.groupby("location_id")["orders_count"].shift(1)
    out["orders_roll_24"] = (
        out.groupby("location_id")["orders_count"].transform(lambda s: s.rolling(24, min_periods=1).mean())
    )
    out["orders_lag_1"] = out["orders_lag_1"].fillna(out["orders_count"].median())

    # External signals join.
    if external_signals:
        ext = pd.DataFrame(external_signals)
        ext["date"] = pd.to_datetime(ext["date"]).dt.date
        out = out.merge(ext, on="date", how="left")
    else:
        out["holiday_flag"] = 0
        out["news_sentiment"] = 0.0
        out["weather_index"] = 0.0

    out["holiday_flag"] = out["holiday_flag"].fillna(0).astype(int)
    out["news_sentiment"] = out["news_sentiment"].fillna(0.0)
    out["weather_index"] = out["weather_index"].fillna(0.0)

    # Event-aware correction index.
    out["event_correction"] = 1 + 0.08 * out["news_sentiment"] + 0.06 * out["holiday_flag"] + 0.04 * out["weather_index"]

    # Linear algebra: z-score standardization.
    for col in NUMERIC_FOR_SCALING:
        mu = out[col].mean()
        sigma = out[col].std(ddof=0) + 1e-8
        out[f"{col}_z"] = (out[col] - mu) / sigma

    return out


def pca_like_projection(feature_df: pd.DataFrame, k: int = 3) -> pd.DataFrame:
    cols = [c for c in feature_df.columns if c.endswith("_z")]
    if not cols:
        return feature_df

    x = feature_df[cols].to_numpy(dtype=float)
    x_centered = x - np.mean(x, axis=0, keepdims=True)
    u, s, _ = np.linalg.svd(x_centered, full_matrices=False)
    kk = max(1, min(k, u.shape[1]))
    z = u[:, :kk] * s[:kk]
    for i in range(kk):
        feature_df[f"pc_{i+1}"] = z[:, i]
    return feature_df
