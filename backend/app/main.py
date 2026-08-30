import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.prediction import router as prediction_router
from backend.app.db.session import init_db
from backend.app.model.baseline import BaselineReliabilityScorer
from backend.app.model.ml_scorer import CalibratedMLScorer
from backend.app.model.registry import model_registry


def setup_model_registry():
    # 1. Register Active ML Model
    ml_model = CalibratedMLScorer(version="2.1.0-ml-prod")
    model_registry.register(
        version="2.1.0",
        model_instance=ml_model,
        stage="active",
        algorithm="calibrated-logistic-ensemble",
        metrics={"brier_score": 0.098, "roc_auc": 0.884},
    )

    # 2. Register Baseline Model as Rollback Safeguard
    baseline_model = BaselineReliabilityScorer()
    model_registry.register(
        version="1.0.0-baseline",
        model_instance=baseline_model,
        stage="rollback",
        algorithm="monotonic-development-heuristic",
        metrics={"brier_score": 0.185, "roc_auc": 0.742},
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    setup_model_registry()
    yield


# Immediate initialization for module imports and test suites
init_db()
setup_model_registry()

app = FastAPI(
    title="Veyra V1.0 Build",
    version="1.0.0",
    description="Forecast reliability intelligence with calibrated risk and safe abstention.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prediction_router)


@app.get("/", tags=["system"])
def root() -> dict[str, str]:
    return {
        "status": "online",
        "service": "veyra-v1-personal",
        "docs": "/docs",
    }


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": os.getenv("APP_NAME", "veyra-v1-personal"),
        "version": os.getenv("APP_VERSION", "1.0.0"),
    }