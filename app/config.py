import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# Saved model files, trained earlier and loaded once at startup
MODEL_PATH = BASE_DIR / "models" / "model.pkl"
ENCODER_PATH = BASE_DIR / "models" / "encoder.pkl"
POLY_PATH = BASE_DIR / "models" / "poly.pkl"

# Prediction history is stored in a local SQLite file unless DATABASE_URL is set
DATABASE_URL = os.getenv(
    "DATABASE_URL", f"sqlite:///{(BASE_DIR / 'predictions.db').as_posix()}"
)

# The model was trained on Washington State data only
ZIPCODE_RANGE = (98001, 99001)

# Fixed margin added above and below the predicted price
RANGE_MARGIN = 20000