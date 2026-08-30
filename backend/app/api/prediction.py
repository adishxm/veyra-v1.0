from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.features.basic import FEATURE_SCHEMA_VERSION, build_features
from backend.app.model.baseline import BaselineReliabilityScorer
from backend.app.safety.evaluator import evaluate
from backend.app.weather.schemas import EnsembleForecast, ForecastRequest

router = APIRouter(prefix="/v1", tags=["prediction"])
scorer = BaselineReliabilityScorer()


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
    reason_codes: list[str] = Field(
        default_factory=list, description="Diagnostic audit codes for safety decisions"
    )
    evidence: list[str] = Field(
        default_factory=list, description="Physical and statistical drivers of uncertainty"
    )
    model_version: str | None = None
    feature_schema_version: str | None = None
    data_version: str | None = None


@router.post("/predict", response_model=PredictionResponse)
def predict(request: ForecastRequest) -> PredictionResponse:
    if request.latitude is None or request.longitude is None:
        raise HTTPException(status_code=422, detail="latitude and longitude are required for V0.1")

    now = datetime.now(timezone.utc)

    # Synthetic ensemble fixture (will be wired to real NWP provider in next phase)
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

    # 1. Feature extraction
    features = build_features(forecast)

    # 2. Baseline inference & dynamic evidence attribution
    result = scorer.predict_probability(features)

    # 3. Safety guardrails & trust evaluation
    safety = evaluate(feature_values=features, probability=result.probability)

    # 4. Construct calibrated response with safety gating
    return PredictionResponse(
        location=request.location,
        bust_probability=None if safety.abstain else result.probability,
        risk_level=None if safety.abstain else result.risk_level,
        trust_state=safety.trust_state,
        abstain=safety.abstain,
        reason_codes=safety.reason_codes,
        evidence=[] if safety.abstain else result.evidence,
        model_version=None if safety.abstain else result.model_version,
        feature_schema_version=None if safety.abstain else FEATURE_SCHEMA_VERSION,
        data_version=None if safety.abstain else forecast.data_version,
    )