from __future__ import annotations

import pandas as pd


def build_report(
    focus: str,
    forecast_df: pd.DataFrame,
    staffing_recs: list[dict],
    anomalies: list[dict],
) -> dict:
    orders_growth = 0.0
    if len(forecast_df) > 1:
        orders_growth = ((forecast_df["orders_count"].iloc[-1] - forecast_df["orders_count"].iloc[0]) /
                         max(forecast_df["orders_count"].iloc[0], 1e-6)) * 100

    major_anomalies = anomalies[:3]

    return {
        "executive_summary": (
            f"Forecast indicates {orders_growth:.1f}% order movement over forecast horizon. "
            f"Primary focus: {focus}."
        ),
        "detected_problems": [
            {
                "issue": f"{a['metric']} anomaly",
                "severity": "high" if abs(a["z_score"]) > 3.5 else "medium",
                "evidence": f"z={a['z_score']:.2f} at {a['timestamp']}",
            }
            for a in major_anomalies
        ],
        "forecast_insights": [
            {
                "metric": "orders_count",
                "horizon": f"{len(forecast_df)}h",
                "trend": f"{orders_growth:.1f}%",
            }
        ],
        "optimization_decisions": [
            {
                "type": "staffing",
                "action": (
                    f"Apply {len(staffing_recs)} hourly staffing recommendations with "
                    "capacity-constrained minimum staffing."
                ),
                "impact": "Reduced SLA breach risk during predicted peaks.",
            }
        ],
        "risk_opportunity_signals": [
            {
                "signal": "External event/weather placeholders active",
                "effect": "Plug live APIs to enable correction factors in production.",
            }
        ],
        "prioritized_action_plan": [
            {"priority": 1, "owner": "ops_manager", "deadline": "today", "action": "Review staffing deltas."},
            {"priority": 2, "owner": "procurement", "deadline": "today", "action": "Align inventory with demand trend."},
            {"priority": 3, "owner": "data_team", "deadline": "this_week", "action": "Connect live news/holiday/weather feeds."},
        ],
    }
