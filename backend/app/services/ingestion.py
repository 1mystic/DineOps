from __future__ import annotations

import io
import uuid

import numpy as np
import pandas as pd

from app.store import DatasetArtifact

REQUIRED_COLUMNS = [
    "timestamp",
    "orders_count",
    "revenue",
    "avg_order_value",
    "item_category",
    "inventory_used",
    "staff_count",
    "prep_time",
    "delivery_time",
    "location_id",
]

OPTIONAL_COLUMNS = ["customer_segment"]

NUMERIC_COLUMNS = [
    "orders_count",
    "revenue",
    "avg_order_value",
    "inventory_used",
    "staff_count",
    "prep_time",
    "delivery_time",
]


def parse_and_validate_csv(contents: bytes) -> tuple[DatasetArtifact, dict]:
    df = pd.read_csv(io.BytesIO(contents))
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True, errors="coerce")
    if df["timestamp"].isna().any():
        raise ValueError("Invalid timestamp values detected")

    for col in NUMERIC_COLUMNS:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Statistical imputation: median by location and hour, fallback global median.
    df["hour"] = df["timestamp"].dt.hour
    imputation_report = {}
    for col in NUMERIC_COLUMNS:
        null_before = int(df[col].isna().sum())
        by_group = df.groupby(["location_id", "hour"])[col].transform(
            lambda s: s.fillna(s.median())
        )
        df[col] = by_group
        df[col] = df[col].fillna(df[col].median())
        null_after = int(df[col].isna().sum())
        imputation_report[col] = {"null_before": null_before, "null_after": null_after}

    df = df.drop(columns=["hour"])
    df = df.sort_values(["location_id", "timestamp"]).reset_index(drop=True)

    # Basic bounds.
    df["revenue"] = np.maximum(df["revenue"], 0)
    df["prep_time"] = np.maximum(df["prep_time"], 0)
    df["delivery_time"] = np.maximum(df["delivery_time"], 0)

    dataset_id = str(uuid.uuid4())
    artifact = DatasetArtifact(dataset_id=dataset_id, raw=df.copy(), cleaned=df)

    report = {
        "required_columns": REQUIRED_COLUMNS,
        "optional_columns": OPTIONAL_COLUMNS,
        "rows": len(df),
        "imputation": imputation_report,
    }
    return artifact, report
