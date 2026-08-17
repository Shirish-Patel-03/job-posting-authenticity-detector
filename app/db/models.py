# app/db/models.py — ORM model for storing every analysis made through the API
from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func

from app.db.database import Base


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True)
    check_id = Column(String, unique=True, index=True, nullable=False)  # the uuid CONTRACTS.md expects in the response
    posting_text = Column(String, nullable=False)
    risk_score = Column(Float, nullable=False)
    verdict = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    red_flags = Column(JSON, nullable=False)
    source = Column(String, default="text")  # "text" or "image" — set once an OCR endpoint exists
    created_at = Column(DateTime(timezone=True), server_default=func.now())
