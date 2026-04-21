# Deployment & Readiness Check

This project now includes a root-level `vercel.json` for **multi-service deployment**:
- Python backend API served from `api/index.py` (ASGI app from `backend/app/main.py`)
- React frontend built from `frontend/package.json`

## 1) Deploy on Vercel

```bash
vercel
```

For production:

```bash
vercel --prod
```

## 2) Validate deployment

After deployment, verify:

- Frontend page loads at `https://<deployment-url>/`
- Health endpoint works at `https://<deployment-url>/api/health`
- API docs available at `https://<deployment-url>/api/docs`

## 3) Quick functional smoke checks

1. Upload CSV via `/api/docs` → `POST /v1/data/upload`
2. Copy `dataset_id`
3. Run in order:
   - `POST /v1/external/sync`
   - `POST /v1/features/build/{dataset_id}`
   - `POST /v1/forecast/run`
   - `POST /v1/optimize/staffing`
   - `POST /v1/optimize/inventory`
   - `POST /v1/optimize/pricing`
   - `POST /v1/report/generate`

If all endpoints return 200 and frontend renders results, the project is deployment-ready for iterative testing.
