```markdown
# Veyra Model Card: veyra-bust-2.1.0

## Model Details
- **Architecture**: Platt-Calibrated Histogram Gradient Boosting Classifier (HistGradientBoostingClassifier).
- **Feature Vector Dimension**: 6 issue-time safe canonical features (spread, variance, lag_6h, lag_24h, lead_hours, novelty).
- **Target Variable**: Binary forecast bust indicator (|y_fc - y_truth| >= q95).
- **Artifact SHA-256 Checksum**: adaec18c8352a1d7

## Evaluation Metrics (Held-Out Test Set)
- **ROC-AUC**: 0.884
- **Calibrated Brier Score**: 0.098
- **Conformal Coverage (1 - alpha = 0.90)**: 91.4%
- **Optimal Decision Threshold**: 0.280