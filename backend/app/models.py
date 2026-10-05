from datetime import date, datetime, time
from zoneinfo import ZoneInfo

from sqlalchemy import Date, DateTime, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from .database import Base


class Appointment(Base):
    __tablename__ = "appointments"
    __table_args__ = (
        UniqueConstraint("date", "time", name="uq_appointment_date_time"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    patient_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    time: Mapped[time] = mapped_column(Time, nullable=False)
    created_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
        default=lambda: datetime.now(ZoneInfo("America/Sao_Paulo")).replace(
            tzinfo=None
        ),
    )
