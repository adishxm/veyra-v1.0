from fastapi import FastAPI

from backend.app.api.prediction import router as prediction_router

app = FastAPI(
    title="Veyra V3.0 Final Build",
    version="3.0.0-dev",
    description="Forecast reliability intelligence with calibrated risk and safe abstention.",
)

app.include_router(prediction_router)


@app.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "veyra-v3-personal",
        "version": "3.0.0-dev",
    }
