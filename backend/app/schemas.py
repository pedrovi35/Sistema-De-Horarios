import re
from datetime import date, datetime, time

from pydantic import BaseModel, ConfigDict, Field, field_validator


# Códigos nacionais (DDD) atribuídos pela Anatel, em todas as regiões.
VALID_BRAZILIAN_DDDS = frozenset(
    "11 12 13 14 15 16 17 18 19 21 22 24 27 28 "
    "31 32 33 34 35 37 38 41 42 43 44 45 46 47 48 49 "
    "51 53 54 55 61 62 63 64 65 66 67 68 69 "
    "71 73 74 75 77 79 81 82 83 84 85 86 87 88 89 "
    "91 92 93 94 95 96 97 98 99".split()
)


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
        if not re.fullmatch(r"\d{2}9\d{8}", digits):
            raise ValueError("Informe o DDD de dois dígitos e o celular de nove dígitos, começando com 9")
        if digits[:2] not in VALID_BRAZILIAN_DDDS:
            raise ValueError("Informe um DDD válido do Brasil, de qualquer região")
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
