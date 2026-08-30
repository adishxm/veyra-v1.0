import asyncio
from typing import List, Optional
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.app.db.models import PredictionLog
from backend.app.db.session import get_db, SessionLocal
from backend.app.features.basic import FEATURE_SCHEMA_VERSION, build_features
from backend.app.jobs.manager import job_manager
from backend.app.model.registry import model_registry
from backend.app.safety.conformal import conformal_engine
from backend.app.safety.evaluator import evaluate
from backend.app.weather.schemas import ForecastRequest
from backend.app.weather.service import weather_service

router = APIRouter(prefix="/v1", tags=["batch-and-jobs"])

class BatchForecastRequest(BaseModel):
    items: List[ForecastRequest] = Field(..., max_length=50)



class BatchItemResult(BaseModel):
    location: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    success: bool
    bust_probability: Optional[float] = None
    risk_level: Optional[str] = None
    trust_state: Optional[str] = None
    abstain: Optional[bool] = None
    novelty_score: Optional[float] = None
    conformal_lower: Optional[float] = None
    conformal_upper: Optional[float] = None
    error: Optional[str] = None


class BatchResponse(BaseModel):
    total_requested: int
    successful_count: int
    failed_count: int
    results: List[BatchItemResult]


async def _process_single_forecast(
    req: ForecastRequest, db: Session
) -> BatchItemResult:
    """Evaluate a single forecast with isolated exception catching."""
    if req.latitude is None or req.longitude is None:
        return BatchItemResult(
            location=req.location,
            success=False,
            error="Missing latitude or longitude coordinates.",
        )

    try:
        forecast = await weather_service.get_forecast(
            location=req.location,
            latitude=req.latitude,
            longitude=req.longitude,
            variable=req.variable,
            lead_hours=req.lead_hours,
        )
        features = build_features(forecast)
        active_scorer, _ = model_registry.get_active_model()
        result = active_scorer.predict_probability(features)
        safety = evaluate(feature_values=features, probability=result.probability)
        interval = conformal_engine.compute_conformal_interval(
            forecast_mean=features.get("forecast_mean", 0.0),
            spread=features.get("forecast_spread", 1.0),
        )

        log_entry = PredictionLog(
            location=req.location,
            latitude=req.latitude,
            longitude=req.longitude,
            variable=req.variable,
            lead_hours=req.lead_hours,
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

        return BatchItemResult(
            location=req.location,
            latitude=req.latitude,
            longitude=req.longitude,
            success=True,
            bust_probability=None if safety.abstain else result.probability,
            risk_level=None if safety.abstain else result.risk_level,
            trust_state=safety.trust_state,
            abstain=safety.abstain,
            novelty_score=safety.novelty_score,
            conformal_lower=None if safety.abstain else interval.lower_bound,
            conformal_upper=None if safety.abstain else interval.upper_bound,
        )
    except Exception as ex:
        return BatchItemResult(
            location=req.location,
            latitude=req.latitude,
            longitude=req.longitude,
            success=False,
            error=str(ex),
        )


@router.post("/predict/batch", response_model=BatchResponse)
async def predict_batch(
    payload: BatchForecastRequest, db: Session = Depends(get_db)
) -> BatchResponse:
    """Synchronous concurrent batch evaluation with failure isolation."""
    tasks = [_process_single_forecast(item, db) for item in payload.items]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for r in results if r.success)
    return BatchResponse(
        total_requested=len(payload.items),
        successful_count=success_count,
        failed_count=len(payload.items) - success_count,
        results=list(results),
    )


async def _run_background_batch(job_id: str, items: List[ForecastRequest]):
    db = SessionLocal()
    try:
        tasks = [_process_single_forecast(item, db) for item in items]
        results = await asyncio.gather(*tasks)
        dict_results = [r.model_dump() for r in results]
        job_manager.update_progress(job_id, dict_results)
    except Exception as ex:
        job_manager.fail_job(job_id, str(ex))
    finally:
        db.close()


@router.post("/jobs/predict")
async def create_prediction_job(
    payload: BatchForecastRequest, background_tasks: BackgroundTasks
):
    """Enqueues an asynchronous batch forecast job and returns a job_id for polling."""
    job = job_manager.create_job(total_items=len(payload.items))
    background_tasks.add_task(_run_background_batch, job.job_id, payload.items)
    return {
        "job_id": job.job_id,
        "status": job.status,
        "total_items": job.total_items,
        "created_at": job.created_at.isoformat(),
        "poll_url": f"/v1/jobs/{job.job_id}",
    }


@router.get("/jobs/{job_id}")
def get_job_status(job_id: str):
    """Retrieve execution state, progress, and completed batch outputs."""
    job = job_manager.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job ID not found.")
    return {
        "job_id": job.job_id,
        "status": job.status,
        "total_items": job.total_items,
        "completed_items": job.completed_items,
        "completed_at": job.completed_at.isoformat() if job.completed_at else None,
        "error": job.error,
        "results": job.results,
    }