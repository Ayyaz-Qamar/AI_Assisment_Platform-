from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.ml.pipeline import export_dataset
from app.ml.predict import predict_level, reset_model_cache
from app.ml.train import train_model
from app.models import User
from app.schemas import PredictionRequest, PredictionResponse
from app.utils.auth import get_current_user, require_admin

router = APIRouter(prefix="/api/ml", tags=["Machine Learning"])


@router.post("/generate-dataset")
def generate_dataset(
    db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    path = export_dataset(db)
    if not path:
        raise HTTPException(
            status_code=400,
            detail="No completed attempts found yet. Take some tests first.",
        )
    return {"message": "Dataset generated successfully", "path": path}


@router.post("/train")
def train(db: Session = Depends(get_db), _: User = Depends(require_admin)):
    """Auto-export dataset, then train RandomForest."""
    path = export_dataset(db)
    if not path:
        raise HTTPException(
            status_code=400, detail="No completed attempts available for training."
        )
    try:
        result = train_model(path)
        reset_model_cache()
        return {"message": "Model trained successfully", **result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Training failed: {e}") from e


@router.post("/predict", response_model=PredictionResponse)
def predict(
    payload: PredictionRequest, _: User = Depends(get_current_user)
):
    level, confidence = predict_level(
        payload.accuracy, payload.avg_difficulty, payload.attempt_time
    )
    return PredictionResponse(predicted_level=level, confidence=confidence)
