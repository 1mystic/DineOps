from __future__ import annotations

from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    dataset_id: str
    row_count: int
    validation_report: dict


class ExternalSyncRequest(BaseModel):
    dataset_id: str
    start_date: date
    end_date: date
    location_id: str


class ExternalSignalDay(BaseModel):
    date: date
    holiday_flag: int
    weather_index: float
    news_sentiment: float


class ExternalSyncResponse(BaseModel):
    dataset_id: str
    rows: int
    signals: list[ExternalSignalDay]


class FeatureBuildResponse(BaseModel):
    dataset_id: str
    feature_columns: list[str]
    rows: int


class ForecastRequest(BaseModel):
    dataset_id: str
    horizon: int = Field(default=24, ge=1, le=24 * 14)


class ForecastPoint(BaseModel):
    timestamp: datetime
    orders_count: float
    revenue: float


class ForecastResponse(BaseModel):
    dataset_id: str
    model_weights: dict[str, float]
    points: list[ForecastPoint]


class StaffingOptimizationRequest(BaseModel):
    dataset_id: str
    labor_cost_per_staff_hour: float = Field(default=22.0, gt=0)
    service_capacity_per_staff_hour: float = Field(default=12.0, gt=0)
    min_staff_per_shift: int = Field(default=2, ge=0)


class StaffingRecommendation(BaseModel):
    timestamp: datetime
    required_staff: int
    recommended_staff: int
    projected_gap: int
    estimated_cost: float


class StaffingOptimizationResponse(BaseModel):
    dataset_id: str
    recommendations: list[StaffingRecommendation]


class InventoryOptimizationRequest(BaseModel):
    dataset_id: str
    service_level: float = Field(default=0.9, gt=0.5, lt=0.999)
    lead_time_days: int = Field(default=2, ge=0, le=14)


class InventoryRecommendation(BaseModel):
    item_category: str
    expected_daily_usage: float
    safety_stock: float
    reorder_quantity: float


class InventoryOptimizationResponse(BaseModel):
    dataset_id: str
    recommendations: list[InventoryRecommendation]


class PricingOptimizationRequest(BaseModel):
    dataset_id: str
    max_price_change_pct: float = Field(default=0.08, gt=0, le=0.25)


class PricingRecommendation(BaseModel):
    item_category: str
    current_avg_order_value: float
    recommended_price_multiplier: float
    expected_revenue_lift_pct: float


class PricingOptimizationResponse(BaseModel):
    dataset_id: str
    recommendations: list[PricingRecommendation]


class AnomalyResponse(BaseModel):
    dataset_id: str
    anomalies: list[dict]


class ReportRequest(BaseModel):
    dataset_id: str
    focus: Literal["operations", "staffing", "inventory", "pricing"] = "operations"


class ReportResponse(BaseModel):
    executive_summary: str
    detected_problems: list[dict]
    forecast_insights: list[dict]
    optimization_decisions: list[dict]
    risk_opportunity_signals: list[dict]
    prioritized_action_plan: list[dict]
