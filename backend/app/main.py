import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api.prediction import router as prediction_router
from backend.app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


# Ensure tables exist immediately upon module load
init_db()

app = FastAPI(
    title="Veyra V1.0 Build",
    version="1.0.0",
    description="Forecast reliability intelligence with calibrated risk and safe abstention.",
    lifespan=lifespan,
)

# Enable CORS for frontend clients
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