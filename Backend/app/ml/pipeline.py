"""
Data pipeline: read completed attempts from PostgreSQL → write CSV dataset.
"""
import os
from typing import Optional

import pandas as pd
from sqlalchemy.orm import Session

from app.config import settings
from app.models import TestAttempt


def export_dataset(db: Session, output_path: Optional[str] = None) -> Optional[str]:
    path = output_path or settings.DATASET_PATH

    attempts = (
        db.query(TestAttempt)
        .filter(TestAttempt.completed.is_(True))
        .all()
    )
    if not attempts:
        return None

    rows = [
        {
            "user_id": a.user_id,
            "test_id": a.test_id,
            "accuracy": a.accuracy,
            "avg_difficulty": a.avg_difficulty,
            "attempt_time": a.attempt_time,
            "score": a.score,
            "competency_level": a.competency_level,
        }
        for a in attempts
    ]

    df = pd.DataFrame(rows).dropna(subset=["competency_level"])
    if df.empty:
        return None

    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    df.to_csv(path, index=False)
    return path
