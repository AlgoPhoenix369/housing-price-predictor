from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .config import ZIPCODE_RANGE


# Property details sent by the web form; limits keep inputs in a realistic range
class PredictionRequest(BaseModel):
    sqft_living: int = Field(ge=200, le=10000)
    no_of_bedrooms: int = Field(ge=0, le=10)
    no_of_bathrooms: float = Field(ge=0, le=10)
    sqft_lot: int = Field(ge=500, le=500000)
    no_of_floors: float = Field(ge=1, le=4)
    house_age: int = Field(ge=0, le=150)
    zipcode: int = Field(ge=ZIPCODE_RANGE[0], le=ZIPCODE_RANGE[1])
    purpose: Literal["buy", "sell"] = "buy"


class PredictionResult(BaseModel):
    id: int
    predicted_price: float
    range_low: float
    range_high: float


# One saved prediction as shown in the history table
class HistoryItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: int
    purpose: str
    sqft_living: int
    no_of_bedrooms: int
    no_of_bathrooms: float
    sqft_lot: int
    no_of_floors: float
    house_age: int
    zipcode: int
    predicted_price: float