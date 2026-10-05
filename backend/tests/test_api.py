from datetime import date

from fastapi.testclient import TestClient
from sqlalchemy import delete

from app import services
from app.database import Base, SessionLocal, engine
from app.main import app
from app.models import Appointment


client = TestClient(app)


async def fake_holidays():
    return {date(2026, 1, 1): "Confraternização Universal"}


def setup_module():
    services.get_holidays = fake_holidays
    Base.metadata.create_all(bind=engine)


def teardown_module():
    Base.metadata.drop_all(bind=engine)


def setup_function():
    with SessionLocal() as db:
        db.execute(delete(Appointment))
        db.commit()


def test_weekend_is_blocked():
    response = client.get("/available?date=2026-02-08")
    assert response.status_code == 400
    assert "finais de semana" in response.json()["detail"]


def test_holiday_is_blocked():
    response = client.get("/available?date=2026-01-01")
    assert response.status_code == 400
    assert "feriado" in response.json()["detail"]


def test_weekday_returns_hourly_slots():
    response = client.get("/available?date=2026-02-10")
    assert response.status_code == 200
    assert response.json()["available_times"] == [
        "08:00", "09:00", "10:00", "11:00", "12:00",
        "13:00", "14:00", "15:00", "16:00", "17:00",
    ]


def test_create_list_and_block_duplicate_slot():
    payload = {
        "patient_name": "Maria Silva",
        "phone": "85999999999",
        "date": "2026-02-10",
        "time": "09:00",
    }
    created = client.post("/appointments", json=payload)
    assert created.status_code == 201
    assert created.json()["patient_name"] == "Maria Silva"
    assert created.json()["created_at"] is not None

    availability = client.get("/available?date=2026-02-10")
    assert "09:00" not in availability.json()["available_times"]

    duplicate = client.post("/appointments", json=payload)
    assert duplicate.status_code == 409

    appointments = client.get("/appointments")
    assert appointments.status_code == 200
    assert len(appointments.json()) == 1


def test_rejects_invalid_mobile_number():
    response = client.post(
        "/appointments",
        json={
            "patient_name": "Nome Teste",
            "phone": "12345678",
            "date": "2026-02-10",
            "time": "11:00",
        },
    )
    assert response.status_code == 422
