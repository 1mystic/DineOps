from __future__ import annotations

import numpy as np
import pandas as pd


def detect_anomalies(df: pd.DataFrame) -> list[dict]:
    ordered = df.sort_values("timestamp").copy()

    anomalies: list[dict] = []
    for metric in ["orders_count", "revenue", "prep_time", "delivery_time"]:
        vals = ordered[metric].to_numpy(dtype=float)
        mu = vals.mean()
        sigma = vals.std() + 1e-8
        z = (vals - mu) / sigma
        idx = np.where(np.abs(z) > 2.8)[0]
        for i in idx:
            anomalies.append(
                {
                    "timestamp": ordered.iloc[i]["timestamp"],
                    "metric": metric,
                    "value": float(vals[i]),
                    "z_score": float(z[i]),
                    "likely_cause": _likely_cause(metric),
                }
            )
    return sorted(anomalies, key=lambda a: abs(a["z_score"]), reverse=True)


def _likely_cause(metric: str) -> str:
    mapping = {
        "orders_count": "Demand shock (event/news/weather) or promotion effect",
        "revenue": "Pricing mix shift or discount leakage",
        "prep_time": "Kitchen bottleneck or staffing mismatch",
        "delivery_time": "Courier capacity/weather traffic disruption",
    }
    return mapping.get(metric, "Operational variance")
