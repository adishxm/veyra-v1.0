from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from backend.app.features.basic import FEATURE_SCHEMA_VERSION, build_features
from backend.app.model.baseline import BaselineReliabilityScorer
from backend.app.safety.evaluator import evaluate
from backend.app.weather.schemas import EnsembleForecast, ForecastRequest

router = APIRouter(prefix="/v1", tags=["prediction"])
scorer = BaselineReliabilityScorer()


class PredictionResponse(BaseModel):
    location: str
    bust_probability: float | None
    risk_level: str | None
    trust_state: str
    abstain: bool
    reason_codes: list[str]
    evidence: list[str]
    model_version: str | None
    feature_schema_version: str | None
    data_version: str | None


def risk_level(probability: float) -> str:
    if probability >= 0.67:
        return "HIGH"
    if probability >= 0.34:
        return "MEDIUM"
    return "LOW"


@router.post("/predict", response_model=PredictionResponse)
def predict(request: ForecastRequest) -> PredictionResponse:
    if request.latitude is None or request.longitude is None:
        raise HTTPException(status_code=422, detail="latitude and longitude are required for V0.1")

    now = datetime.now(timezone.utc)
    forecast = EnsembleForecast(
        location=request.location,
        latitude=request.latitude,
        longitude=request.longitude,
        variable=request.variable,
        issue_time=now,
        valid_time=now + timedelta(hours=request.lead_hours),
        lead_hours=request.lead_hours,
        values=[20.0, 21.0, 22.0, 24.0, 25.0],
        unit="provider-fixture",
        provider="development-fixture",
        data_version="fixture-v1",
    )
    features = build_features(forecast)
    result = scorer.predict_probability(features)
    safety = evaluate(feature_values=features, probability=result.probability)
    return PredictionResponse(
        location=request.location,
        bust_probability=None if safety.abstain else result.probability,
        risk_level=None if safety.abstain else risk_level(result.probability),
        trust_state=safety.trust_state,
        abstain=safety.abstain,
        reason_codes=safety.reason_codes,
        evidence=["ensemble_spread", "lead_time"],
        model_version=None if safety.abstain else result.model_version,
        feature_schema_version=None if safety.abstain else FEATURE_SCHEMA_VERSION,
        data_version=None if safety.abstain else forecast.data_version,
    )
