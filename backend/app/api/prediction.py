from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.models import PredictionLog
from backend.app.db.session import get_db
from backend.app.features.basic import FEATURE_SCHEMA_VERSION, build_features
from backend.app.model.baseline import BaselineReliabilityScorer
from backend.app.safety.evaluator import evaluate
from backend.app.weather.client import fetch_ensemble_forecast
from backend.app.weather.schemas import ForecastRequest

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
async def predict(
    request: ForecastRequest, db: Session = Depends(get_db)
) -> PredictionResponse:
    if request.latitude is None or request.longitude is None:
        raise HTTPException(status_code=422, detail="latitude and longitude are required for V0.1")

    # 1. Fetch live multi-member ensemble NWP forecast data
    try:
        forecast = await fetch_ensemble_forecast(
            location=request.location,
            latitude=request.latitude,
            longitude=request.longitude,
            variable=request.variable,
            lead_hours=request.lead_hours,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Failed to fetch live ensemble forecast upstream: {str(exc)}",
        )

    # 2. Extract statistical and distributional features
    features = build_features(forecast)

    # 3. Model inference and dynamic evidence attribution
    result = scorer.predict_probability(features)

    # 4. Safety guardrails and trust evaluation
    safety = evaluate(feature_values=features, probability=result.probability)

    # 5. Persist prediction audit log to database
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

    # 6. Return response
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


@router.get("/logs", tags=["prediction"])
def get_prediction_logs(limit: int = 10, db: Session = Depends(get_db)):
    """Retrieve the most recent prediction audit records."""
    logs = (
        db.query(PredictionLog)
        .order_by(PredictionLog.id.desc())
        .limit(limit)
        .all()
    )
    return logs