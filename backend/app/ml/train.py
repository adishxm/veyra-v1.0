import os
import json
import hashlib
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import brier_score_loss, roc_auc_score

# 1. Generate synthetic historical atmospheric NWP dataset
np.random.seed(42)
n_samples = 5000

# Features: [spread, temp_variance, pressure_trend, humidity_gradient, lead_hours, novelty_proxy]
X = np.random.randn(n_samples, 6)
X[:, 0] = np.abs(X[:, 0]) * 2.5   # Ensemble spread (°C)
X[:, 4] = np.random.choice([24, 48, 72, 120], n_samples) # Lead horizon

# Ground truth bust occurrence: high spread + high lead hours -> higher bust likelihood
logits = 0.8 * X[:, 0] + 0.015 * X[:, 4] + 0.5 * X[:, 1] - 2.2
probs = 1 / (1 + np.exp(-logits))
y = (np.random.rand(n_samples) < probs).astype(int)

# Train/Test Split
split = int(0.8 * n_samples)
X_train, X_test = X[:split], X[split:]
y_train, y_test = y[:split], y[split:]

# 2. Train Base Estimator & Calibrate Probabilities
base_model = LogisticRegression(C=1.0, random_state=42)
calibrated_clf = CalibratedClassifierCV(estimator=base_model, method="isotonic", cv=3)
calibrated_clf.fit(X_train, y_train)

# 3. Compute Held-Out Verification Metrics
test_probs = calibrated_clf.predict_proba(X_test)[:, 1]
brier = round(float(brier_score_loss(y_test, test_probs)), 4)
auc = round(float(roc_auc_score(y_test, test_probs)), 4)

# 4. Compute 90% Conformal Prediction Non-Conformity Quantile
residuals = np.abs(y_test - test_probs)
conformal_q = round(float(np.quantile(residuals, 0.90)), 4)

# 5. Serialize Artifact & Generate Checksum
artifact_dir = os.path.join(os.path.dirname(__file__), "artifacts")
model_path = os.path.join(artifact_dir, "veyra_model_v2_1_0.joblib")
joblib.dump(calibrated_clf, model_path)

hasher = hashlib.sha256()
with open(model_path, "rb") as f:
    hasher.update(f.read())
checksum = hasher.hexdigest()[:12]

metadata = {
    "model_id": "veyra-bust-2.1.0",
    "version": "2.1.0",
    "stage": "active",
    "algorithm": "calibrated-isotonic-ensemble",
    "feature_schema_version": "personal-veyra-features-v2",
    "checksum": checksum,
    "conformal_quantile_90": conformal_q,
    "metrics": {
        "brier_score": brier,
        "roc_auc": auc
    }
}

with open(os.path.join(artifact_dir, "model_metadata.json"), "w") as f:
    json.dump(metadata, f, indent=2)

print(f"Artifact created: {model_path}")
print(f"Checksum: {checksum} | Brier: {brier} | ROC-AUC: {auc} | Conformal Q90: {conformal_q}")