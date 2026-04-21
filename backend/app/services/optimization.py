from __future__ import annotations

import math

import pandas as pd


def staffing_optimize(
    forecast_df: pd.DataFrame,
    labor_cost_per_staff_hour: float,
    service_capacity_per_staff_hour: float,
    min_staff_per_shift: int,
) -> list[dict]:
    recommendations: list[dict] = []

    for _, row in forecast_df.iterrows():
        required = max(
            min_staff_per_shift,
            math.ceil(row["orders_count"] / max(service_capacity_per_staff_hour, 1e-6)),
        )
        recommended = required
        estimated_cost = recommended * labor_cost_per_staff_hour
        recommendations.append(
            {
                "timestamp": row["timestamp"],
                "required_staff": required,
                "recommended_staff": recommended,
                "projected_gap": 0,
                "estimated_cost": round(estimated_cost, 2),
            }
        )

    return recommendations


def inventory_optimize(df: pd.DataFrame, service_level: float, lead_time_days: int) -> list[dict]:
    grouped = df.groupby("item_category", dropna=False)["inventory_used"]
    z = 1.28 if service_level < 0.9 else 1.64

    recommendations: list[dict] = []
    for category, values in grouped:
        mean_usage = float(values.mean())
        std_usage = float(values.std(ddof=0) if len(values) > 1 else 0.0)

        expected = mean_usage * max(lead_time_days, 1)
        safety_stock = z * std_usage * (max(lead_time_days, 1) ** 0.5)
        reorder_qty = max(expected + safety_stock, 0.0)

        recommendations.append(
            {
                "item_category": str(category),
                "expected_daily_usage": round(mean_usage, 2),
                "safety_stock": round(safety_stock, 2),
                "reorder_quantity": round(reorder_qty, 2),
            }
        )

    return sorted(recommendations, key=lambda r: r["reorder_quantity"], reverse=True)


def pricing_optimize(df: pd.DataFrame, max_price_change_pct: float) -> list[dict]:
    grouped = df.groupby("item_category", dropna=False)
    recommendations: list[dict] = []

    for category, gdf in grouped:
        base_aov = float(gdf["avg_order_value"].mean())
        prep_penalty = float(gdf["prep_time"].mean()) / max(float(df["prep_time"].mean()), 1e-6)

        # simple elasticity proxy: if prep penalty is high, reduce upward pressure.
        elasticity_proxy = max(0.5, min(1.5, 1.2 - 0.25 * prep_penalty))
        multiplier = 1 + max_price_change_pct * (elasticity_proxy - 0.5)
        lift = (multiplier - 1.0) * elasticity_proxy * 100

        recommendations.append(
            {
                "item_category": str(category),
                "current_avg_order_value": round(base_aov, 2),
                "recommended_price_multiplier": round(multiplier, 4),
                "expected_revenue_lift_pct": round(lift, 2),
            }
        )

    return sorted(recommendations, key=lambda r: r["expected_revenue_lift_pct"], reverse=True)
