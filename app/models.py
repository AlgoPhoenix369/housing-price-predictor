from sqlalchemy import BigInteger, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


# One row per prediction; client_id keeps each visitor's history separate
class Prediction(Base):
    __tablename__ = "predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    client_id: Mapped[str] = mapped_column(String(64), index=True)
    created_at: Mapped[int] = mapped_column(BigInteger)
    purpose: Mapped[str] = mapped_column(String(4))
    sqft_living: Mapped[int] = mapped_column(Integer)
    no_of_bedrooms: Mapped[int] = mapped_column(Integer)
    no_of_bathrooms: Mapped[float] = mapped_column(Float)
    sqft_lot: Mapped[int] = mapped_column(Integer)
    no_of_floors: Mapped[float] = mapped_column(Float)
    house_age: Mapped[int] = mapped_column(Integer)
    zipcode: Mapped[int] = mapped_column(Integer)
    predicted_price: Mapped[float] = mapped_column(Float)