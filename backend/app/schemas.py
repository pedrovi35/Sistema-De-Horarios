import re
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator


class AppointmentCreate(BaseModel):
    patient_name: str = Field(min_length=2, max_length=100)
    phone: str = Field(min_length=8, max_length=30)
    date: date
    time: time

    @field_validator("time")
    @classmethod
    def time_must_be_on_the_hour(cls, value: time) -> time:
        if value.minute != 0 or value.second != 0 or value.microsecond != 0:
            raise ValueError("O horário deve começar em uma hora cheia")
        return value

    @field_validator("phone")
    @classmethod
    def validate_brazilian_mobile(cls, value: str) -> str:
        digits = re.sub(r"\D", "", value)
        if not re.fullmatch(r"[1-9]{2}9\d{8}", digits):
            raise ValueError("Informe um celular válido com DDD e 11 dígitos")
        return digits


class AppointmentResponse(AppointmentCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime | None = None


class AvailabilityResponse(BaseModel):
    date: date
    timezone: str
    holiday: bool
    holiday_name: str | None = None
    available_times: list[str]
