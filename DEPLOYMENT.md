# Deployment & Readiness Check

This project now uses **Vercel Experimental Services** via root `vercel.json`:
- `frontend` service:
  - entrypoint: `frontend`
  - route prefix: `/`
  - framework: `vite`
- `backend` service:
  - entrypoint: `backend`
  - route prefix: `/_/backend`

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
- Health endpoint works at `https://<deployment-url>/_/backend/health`
- API docs available at `https://<deployment-url>/_/backend/docs`

## 3) Quick functional smoke checks

1. Upload CSV via `/_/backend/docs` → `POST /v1/data/upload`
2. Copy `dataset_id`
3. Run in order:
   - `POST /v1/external/sync`
   - `POST /v1/features/build/{dataset_id}`
   - `POST /v1/forecast/run`
   - `POST /v1/optimize/staffing`
   - `POST /v1/optimize/inventory`
   - `POST /v1/optimize/pricing`
   - `POST /v1/anomalies/detect?dataset_id=...`
   - `POST /v1/report/generate`

If all endpoints return 200 and frontend renders results, the project is deployment-ready for iterative testing.
