import time
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.staticfiles import StaticFiles
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from .config import ENCODER_PATH, MODEL_PATH, POLY_PATH, RANGE_MARGIN, ZIPCODE_RANGE
from .database import Base, engine, get_db
from .client_id import get_client_id
from .models import Prediction
from .predictor import HousePricePredictor
from .schemas import HistoryItem, PredictionRequest, PredictionResult

STATIC_DIR = Path(__file__).resolve().parent / "static"


# Creates the history table and loads the model files when the server starts
@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    app.state.predictor = HousePricePredictor(MODEL_PATH, ENCODER_PATH, POLY_PATH)
    yield


app = FastAPI(title="Housing Price Predictor API", version="1.0.0", lifespan=lifespan)


@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok"}


# Predicts a price, saves it to this visitor's history and returns the predicted range
@app.post("/api/predict", response_model=PredictionResult, tags=["prediction"])
def predict(
    payload: PredictionRequest,
    request: Request,
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    predictor: HousePricePredictor = request.app.state.predictor
    if not predictor.supports_zipcode(payload.zipcode):
        raise HTTPException(
            status_code=422,
            detail=(
                f"ZIP code {payload.zipcode} is not covered by the model. "
                f"Try a Washington State ZIP between {ZIPCODE_RANGE[0]} and {ZIPCODE_RANGE[1]}."
            ),
        )

    features = payload.model_dump(exclude={"purpose"})
    price = round(predictor.predict(features), 2)

    record = Prediction(
        client_id=client_id,
        created_at=int(time.time() * 1000),
        purpose=payload.purpose,
        predicted_price=price,
        **features,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return PredictionResult(
        id=record.id,
        predicted_price=price,
        range_low=max(price - RANGE_MARGIN, 0),
        range_high=price + RANGE_MARGIN,
    )


# Returns this visitor's most recent predictions, newest first
@app.get("/api/history", response_model=list[HistoryItem], tags=["history"])
def get_history(
    limit: int = Query(default=50, ge=1, le=200),
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    stmt = (
        select(Prediction)
        .where(Prediction.client_id == client_id)
        .order_by(Prediction.created_at.desc(), Prediction.id.desc())
        .limit(limit)
    )
    return db.scalars(stmt).all()


# Deletes this visitor's whole prediction history
@app.delete("/api/history", status_code=204, tags=["history"])
def clear_history(
    client_id: str = Depends(get_client_id),
    db: Session = Depends(get_db),
):
    db.execute(delete(Prediction).where(Prediction.client_id == client_id))
    db.commit()


# The web page is served by the same app; mounted last so API routes take priority
if STATIC_DIR.is_dir():
    app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")