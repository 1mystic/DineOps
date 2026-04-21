# Backend

Run locally:

```bash
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

Core endpoints:
- `POST /v1/data/upload`
- `POST /v1/external/sync`
- `POST /v1/features/build/{dataset_id}`
- `POST /v1/forecast/run`
- `POST /v1/optimize/staffing`
- `POST /v1/optimize/inventory`
- `POST /v1/optimize/pricing`
- `POST /v1/anomalies/detect?dataset_id=...`
- `POST /v1/report/generate`

Run tests:

```bash
PYTHONPATH=backend pytest -q backend/tests
```
