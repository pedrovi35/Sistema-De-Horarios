from datetime import date, time
from zoneinfo import ZoneInfo

import httpx
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Appointment


TIMEZONE = ZoneInfo("America/Sao_Paulo")
HOLIDAYS_URL = "https://date.nager.at/api/v3/PublicHolidays/2026/BR"
OPENING_HOUR = 8
CLOSING_HOUR = 18

_holiday_cache: dict[date, str] | None = None


async def get_holidays() -> dict[date, str]:
    global _holiday_cache
    if _holiday_cache is not None:
        return _holiday_cache

    try:
        async with httpx.AsyncClient(timeout=8) as client:
            response = await client.get(HOLIDAYS_URL)
            response.raise_for_status()
            data = response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(
            status_code=503,
            detail="Não foi possível consultar os feriados. Tente novamente.",
        ) from exc

    _holiday_cache = {
        date.fromisoformat(item["date"]): item["localName"] for item in data
    }
    return _holiday_cache


async def validate_business_day(selected_date: date) -> str | None:
    if selected_date.year != 2026:
        raise HTTPException(
            status_code=400,
            detail="Este sistema aceita agendamentos apenas para 2026.",
        )
    if selected_date.weekday() >= 5:
        raise HTTPException(
            status_code=400,
            detail="Não há atendimento aos finais de semana.",
        )

    holidays = await get_holidays()
    holiday_name = holidays.get(selected_date)
    if holiday_name:
        raise HTTPException(
            status_code=400,
            detail=f"Não há atendimento no feriado: {holiday_name}.",
        )
    return holiday_name


def get_available_times(db: Session, selected_date: date) -> list[str]:
    occupied = set(
        db.scalars(
            select(Appointment.time).where(Appointment.date == selected_date)
        ).all()
    )
    return [
        f"{hour:02d}:00"
        for hour in range(OPENING_HOUR, CLOSING_HOUR)
        if time(hour=hour) not in occupied
    ]


def is_valid_slot(selected_time: time) -> bool:
    return (
        OPENING_HOUR <= selected_time.hour < CLOSING_HOUR
        and selected_time.minute == 0
        and selected_time.second == 0
        and selected_time.microsecond == 0
    )
