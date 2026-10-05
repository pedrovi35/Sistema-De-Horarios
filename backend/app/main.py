from contextlib import asynccontextmanager
from datetime import date, time
from unicodedata import normalize

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import inspect, select, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from .calendar import build_calendar_event
from .models import Appointment
from .schemas import AppointmentCreate, AppointmentResponse, AvailabilityResponse
from .services import TIMEZONE, get_available_times, is_valid_slot, validate_business_day


def patient_name_key(name: str) -> str:
    return " ".join(normalize("NFKC", name).casefold().split())


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


@app.get("/calendar.ics")
def download_calendar(
    selected_date: date = Query(alias="date"),
    selected_time: time = Query(alias="time"),
):
    if selected_date.year != 2026 or not is_valid_slot(selected_time) or selected_time.tzinfo is not None:
        raise HTTPException(status_code=400, detail="Data ou horário de agenda inválido.")
    filename = f"consulta-{selected_date.isoformat()}-{selected_time.strftime('%H%M')}.ics"
    return Response(
        content=build_calendar_event(selected_date, selected_time),
        media_type="text/calendar; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


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

    # SQLite serializa a verificação e a gravação, inclusive entre processos.
    # Assim, duas requisições simultâneas não reservam dois horários para a pessoa.
    db.execute(text("BEGIN IMMEDIATE"))
    patient_key = patient_name_key(payload.patient_name)
    previous = next((
        appointment
        for appointment in db.scalars(
            select(Appointment).where(
                Appointment.phone == payload.phone,
                Appointment.date == payload.date,
            )
        )
        if patient_name_key(appointment.patient_name) == patient_key
    ), None)
    if previous is not None:
        appointment_date = previous.date.strftime("%d/%m/%Y")
        appointment_time = previous.time.strftime("%H:%M")
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=(
                f"Você já tem uma consulta marcada para {appointment_date} às {appointment_time}. "
                "Não é possível marcar outro horário neste dia com o mesmo nome e telefone. "
                "Para alterar sua consulta, entre em contato com a clínica."
            ),
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
