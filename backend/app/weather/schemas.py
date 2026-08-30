from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator


SupportedVariable = Literal["temperature_2m", "precipitation", "wind_speed_10m"]


class ForecastRequest(BaseModel):
    location: str = Field(min_length=1, max_length=120)
    latitude: float | None = Field(default=None, ge=-90, le=90)
    longitude: float | None = Field(default=None, ge=-180, le=180)
    variable: SupportedVariable = "temperature_2m"
    lead_hours: int = Field(default=48, ge=1, le=240)


class EnsembleForecast(BaseModel):
    location: str
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    variable: SupportedVariable
    issue_time: datetime
    valid_time: datetime
    lead_hours: int = Field(ge=1, le=240)
    values: list[float] = Field(min_length=3)
    unit: str = "unknown"
    provider: str
    data_version: str

    @field_validator("values")
    @classmethod
    def values_must_be_finite(cls, values: list[float]) -> list[float]:
        if any(value != value or value in (float("inf"), float("-inf")) for value in values):
            raise ValueError("ensemble values must be finite")
        return values

    @field_validator("valid_time")
    @classmethod
    def valid_after_issue(cls, valid_time: datetime, info):
        issue_time = info.data.get("issue_time")
        if issue_time and valid_time <= issue_time:
            raise ValueError("valid_time must be after issue_time")
        return valid_time
