import os
import json
import joblib
import math
import numpy as np
from typing import Dict, Any, Tuple
from backend.app.ml.conformal_ood_engine import ConformalOODSentinel

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "veyra_model_v2_1_0.joblib")
METADATA_PATH = os.path.join(ARTIFACT_DIR, "model_metadata.json")

class RealMLInferenceEngine:
    _artifact = None
    _metadata = None

    @classmethod
    def load_model(cls):
        if cls._artifact is None and os.path.exists(MODEL_PATH):
            try:
                cls._artifact = joblib.load(MODEL_PATH)
            except Exception:
                cls._artifact = None
        if cls._metadata is None and os.path.exists(METADATA_PATH):
            try:
                with open(METADATA_PATH, "r") as f:
                    cls._metadata = json.load(f)
            except Exception:
                cls._metadata = None
        return cls._artifact, cls._metadata

    @classmethod
    def predict(cls, features: Dict[str, Any]) -> Tuple[float, float, float, float, str, str]:
        artifact, _ = cls.load_model()

        lat = float(features.get("latitude", 22.57))
        lon = float(features.get("longitude", 88.36))
        lead_hours = float(features.get("lead_hours", 48))
        target_temp = float(features.get("temperature", 28.0))
        spread = float(features.get("ensemble_spread", 1.2))
        temp_var = float(features.get("temp_variance", 0.45))

        if any(math.isnan(v) or math.isinf(v) for v in [lat, lon, lead_hours, target_temp, spread, temp_var]):
            raise ValueError("Non-finite numeric values encountered in inference features")

        novelty = ConformalOODSentinel.compute_mahalanobis_novelty(target_temp, spread, temp_var, lead_hours)
        feat_vector = np.array([[spread, temp_var, 0.0, 0.0, lead_hours, novelty]])

        if artifact is not None and isinstance(artifact, dict) and "classifier" in artifact:
            raw_p = artifact["classifier"].predict_proba(feat_vector)[:, 1].reshape(-1, 1)
            raw_score = float(artifact["calibrator"].predict_proba(raw_p)[0, 1])
        else:
            raw_score = 0.10 + (spread * 0.12) + (lead_hours / 240.0) * 0.25

        return ConformalOODSentinel.evaluate(features, raw_score)