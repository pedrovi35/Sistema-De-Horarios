from contextlib import asynccontextmanager
from datetime import date

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .models import Appointment
from .schemas import AppointmentCreate, AppointmentResponse, AvailabilityResponse
from .services import TIMEZONE, get_available_times, is_valid_slot, validate_business_day


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    # Migração mínima para bancos criados antes do campo de data de criação.
    if "created_at" not in {
        column["name"] for column in inspect(engine).get_columns("appointments")
    }:
        with engine.begin() as connection:
            connection.execute(
                text("ALTER TABLE appointments ADD COLUMN created_at DATETIME")
            )
    yield


app = FastAPI(
    title="API de Agendamentos da Clínica",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://[::1]:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok", "timezone": str(TIMEZONE)}


@app.get("/available", response_model=AvailabilityResponse)
async def available(
    date_value: date = Query(alias="date"),
    db: Session = Depends(get_db),
):
    await validate_business_day(date_value)
    return AvailabilityResponse(
        date=date_value,
        timezone=str(TIMEZONE),
        holiday=False,
        available_times=get_available_times(db, date_value),
    )


@app.post(
    "/appointments",
    response_model=AppointmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_appointment(
    payload: AppointmentCreate,
    db: Session = Depends(get_db),
):
    await validate_business_day(payload.date)
    if not is_valid_slot(payload.time):
        raise HTTPException(
            status_code=400,
            detail="Escolha um horário entre 08:00 e 17:00, em hora cheia.",
        )

    existing = db.scalar(
        select(Appointment.id).where(
            Appointment.date == payload.date,
            Appointment.time == payload.time,
        )
    )
    if existing is not None:
        raise HTTPException(
            status_code=409,
            detail="Este horário já está ocupado. Escolha outro.",
        )

    appointment = Appointment(**payload.model_dump())
    db.add(appointment)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Este horário acabou de ser ocupado. Escolha outro.",
        ) from exc
    db.refresh(appointment)
    return appointment


@app.get("/appointments", response_model=list[AppointmentResponse])
def list_appointments(db: Session = Depends(get_db)):
    return db.scalars(
        select(Appointment).order_by(Appointment.date, Appointment.time)
    ).all()
