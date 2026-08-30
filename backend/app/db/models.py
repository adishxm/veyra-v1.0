from datetime import datetime, timezone
from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class PredictionLog(Base):
    __tablename__ = "prediction_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    location = Column(String, index=True)
    latitude = Column(Float)
    longitude = Column(Float)
    variable = Column(String)
    lead_hours = Column(Integer)

    # Feature Metrics
    forecast_mean = Column(Float, nullable=True)
    forecast_spread = Column(Float, nullable=True)
    member_count = Column(Integer, nullable=True)

    # Output Decisions
    bust_probability = Column(Float, nullable=True)
    risk_level = Column(String, nullable=True)
    trust_state = Column(String)
    abstain = Column(Boolean)
    model_version = Column(String, nullable=True)