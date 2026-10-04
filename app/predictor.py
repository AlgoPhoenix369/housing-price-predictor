import joblib
import numpy as np
import pandas as pd

# Column order the model was trained with; the one-hot ZIP columns are appended after these
NUMERIC_FEATURES = [
    "sqft_living",
    "no_of_bedrooms",
    "no_of_bathrooms",
    "sqft_lot",
    "no_of_floors",
    "house_age",
]


class HousePricePredictor:
    # Loads the three saved files once so every request can reuse them
    def __init__(self, model_path, encoder_path, poly_path):
        self.model = joblib.load(model_path)
        self.encoder = joblib.load(encoder_path)
        self.poly = joblib.load(poly_path)

        categories = self.encoder.categories_[0]
        self._zip_dtype = categories.dtype
        self.known_zipcodes = {int(float(z)) for z in categories}

    # True only for ZIP codes the model saw during training
    def supports_zipcode(self, zipcode: int) -> bool:
        return zipcode in self.known_zipcodes

    # Converts the ZIP to the type used in training, otherwise it silently encodes as "unknown"
    def _cast_zipcode(self, zipcode: int):
        if self._zip_dtype.kind in "iuf":
            return self._zip_dtype.type(zipcode)
        return str(zipcode)

    # Rebuilds the training pipeline: encode ZIP, order the columns, add polynomial features
    def _build_features(self, features: dict):
        numeric = pd.DataFrame(
            [{name: features[name] for name in NUMERIC_FEATURES}],
            columns=NUMERIC_FEATURES,
        ).astype(float)
        zip_frame = pd.DataFrame({"zipcode": [self._cast_zipcode(features["zipcode"])]})
        encoded = self.encoder.transform(zip_frame)
        encoded_frame = pd.DataFrame(
            encoded, columns=self.encoder.get_feature_names_out(["zipcode"])
        )
        combined = pd.concat([numeric, encoded_frame], axis=1)

        expected = getattr(self.poly, "feature_names_in_", None)
        if expected is not None:
            combined = combined[list(expected)]
        return self.poly.transform(combined)

    # Predicts log-price, then converts it back to dollars
    def predict(self, features: dict) -> float:
        log_price = self.model.predict(self._build_features(features))
        return float(np.expm1(log_price[0]))