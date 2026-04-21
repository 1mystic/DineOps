from __future__ import annotations

from fastapi import FastAPI, File, HTTPException, UploadFile

from app.schemas import (
    AnomalyResponse,
    ExternalSyncRequest,
    ExternalSyncResponse,
    FeatureBuildResponse,
    ForecastRequest,
    ForecastResponse,
    InventoryOptimizationRequest,
    InventoryOptimizationResponse,
    PricingOptimizationRequest,
    PricingOptimizationResponse,
    ReportRequest,
    ReportResponse,
    StaffingOptimizationRequest,
    StaffingOptimizationResponse,
    UploadResponse,
)
from app.services.anomalies import detect_anomalies
from app.services.external import sync_external_signals
from app.services.features import build_features, pca_like_projection
from app.services.forecasting import ensemble_forecast
from app.services.ingestion import parse_and_validate_csv
from app.services.optimization import inventory_optimize, pricing_optimize, staffing_optimize
from app.services.reporting import build_report
from app.store import store

app = FastAPI(title="DineOps Intelligence Platform", version="0.2.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/v1/data/upload", response_model=UploadResponse)
async def upload_data(file: UploadFile = File(...)) -> UploadResponse:
    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    contents = await file.read()
    try:
        artifact, report = parse_and_validate_csv(contents)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    store.put(artifact)
    return UploadResponse(dataset_id=artifact.dataset_id, row_count=len(artifact.cleaned), validation_report=report)


@app.post("/v1/external/sync", response_model=ExternalSyncResponse)
def external_sync(req: ExternalSyncRequest) -> ExternalSyncResponse:
    try:
        artifact = store.get(req.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    signals = sync_external_signals(req.start_date, req.end_date, req.location_id)
    artifact.metadata["external_signals"] = signals
    return ExternalSyncResponse(dataset_id=req.dataset_id, rows=len(signals), signals=signals)


@app.post("/v1/features/build/{dataset_id}", response_model=FeatureBuildResponse)
def build_dataset_features(dataset_id: str) -> FeatureBuildResponse:
    try:
        artifact = store.get(dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    external_signals = artifact.metadata.get("external_signals")
    features = build_features(artifact.cleaned, external_signals=external_signals)
    features = pca_like_projection(features)
    artifact.features = features

    return FeatureBuildResponse(
        dataset_id=dataset_id,
        feature_columns=list(features.columns),
        rows=len(features),
    )


@app.post("/v1/forecast/run", response_model=ForecastResponse)
def run_forecast(req: ForecastRequest) -> ForecastResponse:
    try:
        artifact = store.get(req.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    source_df = artifact.features if artifact.features is not None else artifact.cleaned
    forecast_df = ensemble_forecast(source_df, req.horizon)
    artifact.metadata["latest_forecast"] = forecast_df

    points = forecast_df.to_dict(orient="records")
    return ForecastResponse(dataset_id=req.dataset_id, model_weights=forecast_df.attrs["weights"], points=points)


@app.post("/v1/optimize/staffing", response_model=StaffingOptimizationResponse)
def optimize_staffing(req: StaffingOptimizationRequest) -> StaffingOptimizationResponse:
    try:
        artifact = store.get(req.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    forecast_df = artifact.metadata.get("latest_forecast")
    if forecast_df is None:
        forecast_df = ensemble_forecast(artifact.cleaned, horizon=24)
        artifact.metadata["latest_forecast"] = forecast_df

    recs = staffing_optimize(
        forecast_df=forecast_df,
        labor_cost_per_staff_hour=req.labor_cost_per_staff_hour,
        service_capacity_per_staff_hour=req.service_capacity_per_staff_hour,
        min_staff_per_shift=req.min_staff_per_shift,
    )
    artifact.metadata["staffing_recommendations"] = recs
    return StaffingOptimizationResponse(dataset_id=req.dataset_id, recommendations=recs)


@app.post("/v1/optimize/inventory", response_model=InventoryOptimizationResponse)
def optimize_inventory(req: InventoryOptimizationRequest) -> InventoryOptimizationResponse:
    try:
        artifact = store.get(req.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    source_df = artifact.features if artifact.features is not None else artifact.cleaned
    recs = inventory_optimize(source_df, req.service_level, req.lead_time_days)
    artifact.metadata["inventory_recommendations"] = recs
    return InventoryOptimizationResponse(dataset_id=req.dataset_id, recommendations=recs)


@app.post("/v1/optimize/pricing", response_model=PricingOptimizationResponse)
def optimize_pricing(req: PricingOptimizationRequest) -> PricingOptimizationResponse:
    try:
        artifact = store.get(req.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    source_df = artifact.features if artifact.features is not None else artifact.cleaned
    recs = pricing_optimize(source_df, req.max_price_change_pct)
    artifact.metadata["pricing_recommendations"] = recs
    return PricingOptimizationResponse(dataset_id=req.dataset_id, recommendations=recs)


@app.post("/v1/anomalies/detect", response_model=AnomalyResponse)
def anomalies(dataset_id: str) -> AnomalyResponse:
    try:
        artifact = store.get(dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    source_df = artifact.features if artifact.features is not None else artifact.cleaned
    results = detect_anomalies(source_df)
    artifact.metadata["anomalies"] = results
    return AnomalyResponse(dataset_id=dataset_id, anomalies=results)


@app.post("/v1/report/generate", response_model=ReportResponse)
def report(req: ReportRequest) -> ReportResponse:
    try:
        artifact = store.get(req.dataset_id)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail="Dataset not found") from exc

    forecast_df = artifact.metadata.get("latest_forecast")
    if forecast_df is None:
        forecast_df = ensemble_forecast(artifact.cleaned, horizon=24)

    staffing_recs = artifact.metadata.get("staffing_recommendations")
    if staffing_recs is None:
        staffing_recs = staffing_optimize(forecast_df, 22.0, 12.0, 2)

    anomaly_list = artifact.metadata.get("anomalies")
    if anomaly_list is None:
        anomaly_list = detect_anomalies(artifact.cleaned)

    payload = build_report(req.focus, forecast_df, staffing_recs, anomaly_list)
    return ReportResponse(**payload)
