"""
Train a RandomForest classifier on user performance.
Features: accuracy, avg_difficulty, attempt_time
Target:   competency_level (Beginner/Intermediate/Expert)
"""
import os
from typing import Optional

import joblib
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score
from sklearn.model_selection import train_test_split

from app.config import settings

FEATURES = ["accuracy", "avg_difficulty", "attempt_time"]
TARGET = "competency_level"


def train_model(dataset_path: Optional[str] = None) -> dict:
    path = dataset_path or settings.DATASET_PATH
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"Dataset not found at {path}. Generate it first via /api/ml/generate-dataset."
        )

    df = pd.read_csv(path).dropna(subset=FEATURES + [TARGET])
    if len(df) < 5:
        raise ValueError(
            f"Need at least 5 completed attempts to train (have {len(df)})."
        )

    X = df[FEATURES]
    y = df[TARGET]

    # Stratify only when feasible
    classes = y.value_counts()
    can_stratify = (classes.min() >= 2) and (len(classes) > 1)

    if len(df) >= 10:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y,
            test_size=0.2,
            random_state=42,
            stratify=y if can_stratify else None,
        )
    else:
        X_train = X_test = X
        y_train = y_test = y

    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=10,
        random_state=42,
    )
    model.fit(X_train, y_train)

    y_pred = model.predict(X_test)
    acc = accuracy_score(y_test, y_pred)

    os.makedirs(os.path.dirname(settings.ML_MODEL_PATH) or ".", exist_ok=True)
    joblib.dump(model, settings.ML_MODEL_PATH)

    return {
        "accuracy": round(float(acc), 4),
        "samples_total": int(len(df)),
        "samples_trained": int(len(X_train)),
        "model_path": settings.ML_MODEL_PATH,
        "classes": list(model.classes_),
        "features": FEATURES,
    }
