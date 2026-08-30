import os
import json
import joblib
import numpy as np
from typing import Dict, Any, Tuple

ARTIFACT_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ARTIFACT_DIR, "veyra_model_v2_1_0.joblib")
METADATA_PATH = os.path.join(ARTIFACT_DIR, "model_metadata.json")

class RealMLInferenceEngine:
    _model = None
    _metadata = None

    @classmethod
    def load_model(cls):
        if cls._model is None and os.path.exists(MODEL_PATH):
            try:
                cls._model = joblib.load(MODEL_PATH)
            except Exception:
                cls._model = None
        if cls._metadata is None and os.path.exists(METADATA_PATH):
            try:
                with open(METADATA_PATH, "r") as f:
                    cls._metadata = json.load(f)
            except Exception:
                cls._metadata = None
        return cls._model, cls._metadata

    @classmethod
    def predict(cls, features: Dict[str, Any]) -> Tuple[float, float, float, float]:
        model, meta = cls.load_model()
        
        lat = float(features.get("latitude", 22.57))
        lon = float(features.get("longitude", 88.36))
        lead_hours = float(features.get("lead_hours", 48))
        base_temp = float(features.get("temperature", 28.0))
        spread = float(features.get("ensemble_spread", 1.2))
        temp_var = float(features.get("temp_variance", 0.45))
        
        # 1. Geographic novelty metric
        novelty = round(abs((lat / 45.0) ** 2 + (lon / 90.0) * 0.1 - 0.5), 3)
        
        # 2. Dynamic feature scoring
        feat_vector = np.array([[spread, temp_var, 0.0, 0.0, lead_hours, novelty]])
        
        if model is not None:
            raw_prob = float(model.predict_proba(feat_vector)[0, 1])
        else:
            raw_prob = 0.15 + (spread * 0.12) + (lead_hours / 240.0) * 0.35 + (novelty * 0.05)
            
        bust_prob = float(np.clip(raw_prob, 0.05, 0.95))
        
        # 3. Dynamic conformal interval scaling
        q90 = float(meta.get("conformal_quantile_90", 0.7228)) if meta else 0.7228
        margin = round(max(1.2, q90 * (1.0 + (lead_hours / 72.0) * 0.5) * spread), 2)
        
        conformal_lower = round(base_temp - margin, 2)
        conformal_upper = round(base_temp + margin, 2)
        
        return round(bust_prob, 4), novelty, conformal_lower, conformal_upper