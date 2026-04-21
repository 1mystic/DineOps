from __future__ import annotations

from datetime import date, timedelta


def sync_external_signals(start_date: date, end_date: date, location_id: str) -> list[dict]:
    # Deterministic placeholders to keep the pipeline stable for local testing.
    rows: list[dict] = []
    current = start_date
    while current <= end_date:
        weekday = current.weekday()
        holiday_flag = 1 if weekday in (5, 6) else 0

        # pseudo-weather and sentiment signals.
        weather_index = round(0.3 + (weekday / 10.0), 3)
        if location_id.endswith("N"):
            weather_index = round(weather_index + 0.08, 3)

        news_sentiment = round(-0.2 + weekday * 0.07, 3)
        rows.append(
            {
                "date": current,
                "holiday_flag": holiday_flag,
                "weather_index": weather_index,
                "news_sentiment": news_sentiment,
            }
        )
        current += timedelta(days=1)

    return rows
