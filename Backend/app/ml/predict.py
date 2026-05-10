"""
Prediction service. Caches the joblib model in memory.
If no model exists yet, falls back to rule-based scoring thresholds.
"""
import os
from typing import Tuple

import joblib
import numpy as np

from app.config import settings

_model_cache = None


def load_model():
    global _model_cache
    if _model_cache is None:
        if not os.path.exists(settings.ML_MODEL_PATH):
            return None
        _model_cache = joblib.load(settings.ML_MODEL_PATH)
    return _model_cache


def reset_model_cache() -> None:
    global _model_cache
    _model_cache = None


def predict_level(
    accuracy: float, avg_difficulty: float, attempt_time: float
) -> Tuple[str, float]:
    model = load_model()

    if model is None:
        # Rule-based fallback (mirrors scoring thresholds)
        if accuracy < 50:
            return "Beginner", 0.5
        if accuracy < 80:
            return "Intermediate", 0.5
        return "Expert", 0.5

    X = np.array([[accuracy, avg_difficulty, attempt_time]])
    pred = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    return str(pred), float(np.max(proba))
