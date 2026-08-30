from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.models import PredictionLog
from backend.app.db.session import get_db
from backend.app.features.basic import FEATURE_SCHEMA_VERSION, build_features
from backend.app.model.registry import model_registry
from backend.app.safety.conformal import conformal_engine
from backend.app.safety.evaluator import evaluate
from backend.app.weather.schemas import ForecastRequest
from backend.app.weather.service import weather_service

router = APIRouter(prefix="/v1", tags=["prediction"])


class PredictionResponse(BaseModel):
    location: str
    bust_probability: float | None = Field(
        default=None, description="Calibrated likelihood of forecast deviation (0.0 to 1.0)"
    )
    risk_level: str | None = Field(
        default=None, description="Categorical risk tier: LOW, MEDIUM, HIGH, CRITICAL"
    )
    trust_state: str = Field(
        ..., description="Validation status: SUPPORTED, DEGRADED, or ABSTAINED"
    )
    abstain: bool = Field(
        ..., description="Whether inference was safely withheld due to corrupt/OOD inputs"
    )
    novelty_score: float = Field(
        default=0.0, description="Mahalanobis novelty distance score"
    )
    conformal_lower: float | None = Field(
        default=None, description="Conformal 90% lower bound"
    )
    conformal_upper: float | None = Field(
        default=None, description="Conformal 90% upper bound"
    )
    reason_codes: list[str] = Field(
        default_factory=list, description="Diagnostic audit codes for safety decisions"
    )
    evidence: list[str] = Field(
        default_factory=list, description="Physical and statistical drivers of uncertainty"
    )
    model_version: str | None = None
    feature_schema_version: str | None = None
    data_version: str | None = None


class ActualObservationRequest(BaseModel):
    prediction_id: int
    actual_value: float
    bust_error_threshold: Optional[float] = Field(
        default=3.0,
        description="Error margin (°C or mm) beyond which a forecast is marked as a bust",
    )


@router.post("/predict", response_model=PredictionResponse)
async def predict(
    request: ForecastRequest, db: Session = Depends(get_db)
) -> PredictionResponse:
    if request.latitude is None or request.longitude is None:
        raise HTTPException(
            status_code=422, detail="latitude and longitude are required for V0.1"
        )

    # 1. Fetch ensemble forecast
    try:
        forecast = await weather_service.get_forecast(
            location=request.location,
            latitude=request.latitude,
            longitude=request.longitude,
            variable=request.variable,
            lead_hours=request.lead_hours,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch ensemble forecast across all providers: {str(exc)}",
        )

    # 2. Extract features
    features = build_features(forecast)

    # 3. Model inference
    active_scorer, _ = model_registry.get_active_model()
    result = active_scorer.predict_probability(features)

    # 4. Safety & Conformal Evaluation
    safety = evaluate(feature_values=features, probability=result.probability)
    interval = conformal_engine.compute_conformal_interval(
        forecast_mean=features.get("forecast_mean", 0.0),
        spread=features.get("forecast_spread", 1.0),
    )

    # 5. Persist audit log
    log_entry = PredictionLog(
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        variable=request.variable,
        lead_hours=request.lead_hours,
        forecast_mean=features.get("forecast_mean"),
        forecast_spread=features.get("forecast_spread"),
        member_count=int(features.get("member_count", 0)),
        bust_probability=None if safety.abstain else result.probability,
        risk_level=None if safety.abstain else result.risk_level,
        trust_state=safety.trust_state,
        abstain=safety.abstain,
        model_version=None if safety.abstain else result.model_version,
    )
    db.add(log_entry)
    db.commit()

    return PredictionResponse(
        location=request.location,
        bust_probability=None if safety.abstain else result.probability,
        risk_level=None if safety.abstain else result.risk_level,
        trust_state=safety.trust_state,
        abstain=safety.abstain,
        novelty_score=safety.novelty_score,
        conformal_lower=None if safety.abstain else interval.lower_bound,
        conformal_upper=None if safety.abstain else interval.upper_bound,
        reason_codes=safety.reason_codes,
        evidence=[] if safety.abstain else result.evidence,
        model_version=None if safety.abstain else result.model_version,
        feature_schema_version=None if safety.abstain else FEATURE_SCHEMA_VERSION,
        data_version=None if safety.abstain else forecast.data_version,
    )


@router.get("/models", tags=["model-registry"])
def list_registered_models():
    return {
        "active_version": model_registry._active_version,
        "models": list(model_registry._metadata.values()),
    }


@router.post("/actuals", tags=["evaluation"])
def log_actual_observation(
    payload: ActualObservationRequest, db: Session = Depends(get_db)
):
    record = db.query(PredictionLog).filter(PredictionLog.id == payload.prediction_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Prediction record not found")

    forecast_mean = record.forecast_mean or 0.0
    error = abs(payload.actual_value - forecast_mean)
    was_bust = error > payload.bust_error_threshold

    record.actual_value = payload.actual_value
    record.was_bust = was_bust
    record.verified_at = datetime.now(timezone.utc)
    db.commit()

    return {
        "status": "verified",
        "prediction_id": record.id,
        "forecast_mean": forecast_mean,
        "actual_value": payload.actual_value,
        "error": round(error, 3),
        "was_bust": was_bust,
    }


@router.get("/metrics", tags=["evaluation"])
def get_evaluation_metrics(db: Session = Depends(get_db)):
    verified = (
        db.query(PredictionLog)
        .filter(PredictionLog.verified_at.isnot(None))
        .all()
    )

    if not verified:
        return {
            "status": "insufficient_data",
            "verified_count": 0,
            "message": "No verified ground-truth observations logged yet.",
        }

    brier_sum = 0.0
    mae_sum = 0.0
    bust_count = 0

    for item in verified:
        p = item.bust_probability or 0.5
        o = 1.0 if item.was_bust else 0.0
        brier_sum += (p - o) ** 2

        if item.forecast_mean is not None and item.actual_value is not None:
            mae_sum += abs(item.forecast_mean - item.actual_value)

        if item.was_bust:
            bust_count += 1

    total = len(verified)
    return {
        "verified_count": total,
        "bust_rate": round(bust_count / total, 4),
        "brier_score": round(brier_sum / total, 4),
        "mean_absolute_error": round(mae_sum / total, 4),
    }


@router.get("/logs", tags=["prediction"])
def get_prediction_logs(limit: int = 10, db: Session = Depends(get_db)):
    return (
        db.query(PredictionLog)
        .order_by(PredictionLog.id.desc())
        .limit(limit)
        .all()
    )