from __future__ import annotations

import io

from fastapi.testclient import TestClient

from app.main import app

CSV = """timestamp,orders_count,revenue,avg_order_value,item_category,inventory_used,staff_count,prep_time,delivery_time,location_id
2026-04-01T10:00:00Z,100,1200,12,entree,80,7,14,32,LOC-1
2026-04-01T11:00:00Z,110,1320,12,entree,86,8,13,30,LOC-1
2026-04-01T12:00:00Z,120,1500,12.5,beverage,95,9,12,28,LOC-1
2026-04-01T13:00:00Z,130,1660,12.8,beverage,98,10,11,27,LOC-1
"""


def upload_dataset(client: TestClient) -> str:
    files = {"file": ("sample.csv", io.BytesIO(CSV.encode("utf-8")), "text/csv")}
    res = client.post("/v1/data/upload", files=files)
    assert res.status_code == 200, res.text
    return res.json()["dataset_id"]


def test_end_to_end_pipeline() -> None:
    client = TestClient(app)
    dataset_id = upload_dataset(client)

    sync_payload = {
        "dataset_id": dataset_id,
        "location_id": "LOC-1",
        "start_date": "2026-04-01",
        "end_date": "2026-04-03",
    }
    sync_res = client.post("/v1/external/sync", json=sync_payload)
    assert sync_res.status_code == 200, sync_res.text
    assert sync_res.json()["rows"] == 3

    features_res = client.post(f"/v1/features/build/{dataset_id}")
    assert features_res.status_code == 200, features_res.text
    assert "event_correction" in features_res.json()["feature_columns"]

    forecast_res = client.post("/v1/forecast/run", json={"dataset_id": dataset_id, "horizon": 6})
    assert forecast_res.status_code == 200, forecast_res.text
    assert len(forecast_res.json()["points"]) == 6

    staffing_res = client.post("/v1/optimize/staffing", json={"dataset_id": dataset_id})
    assert staffing_res.status_code == 200, staffing_res.text
    assert len(staffing_res.json()["recommendations"]) >= 1

    inventory_res = client.post("/v1/optimize/inventory", json={"dataset_id": dataset_id})
    assert inventory_res.status_code == 200, inventory_res.text
    assert len(inventory_res.json()["recommendations"]) == 2

    pricing_res = client.post("/v1/optimize/pricing", json={"dataset_id": dataset_id})
    assert pricing_res.status_code == 200, pricing_res.text
    assert len(pricing_res.json()["recommendations"]) == 2

    anomaly_res = client.post(f"/v1/anomalies/detect?dataset_id={dataset_id}")
    assert anomaly_res.status_code == 200, anomaly_res.text

    report_res = client.post("/v1/report/generate", json={"dataset_id": dataset_id, "focus": "operations"})
    assert report_res.status_code == 200, report_res.text
    assert "executive_summary" in report_res.json()
