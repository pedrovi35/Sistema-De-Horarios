from datetime import date

import pytest
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


@pytest.mark.parametrize("second_booking", [
    {"date": "2026-02-10", "time": "10:00"},
    {"patient_name": "  VÍTOR   Silva  ", "phone": "(85) 99999-9999", "time": "10:00"},
])
def test_same_patient_cannot_reserve_another_slot_on_same_day(second_booking):
    payload = {
        "patient_name": "Vítor Silva",
        "phone": "85999999999",
        "date": "2026-02-10",
        "time": "09:00",
    }
    assert client.post("/appointments", json=payload).status_code == 201
    attempted = {**payload, **second_booking}
    duplicate = client.post("/appointments", json=attempted)
    assert duplicate.status_code == 409
    assert "Você já tem uma consulta marcada para 10/02/2026 às 09:00" in duplicate.json()["detail"]
    assert "entre em contato com a clínica" in duplicate.json()["detail"]
    assert len(client.get("/appointments").json()) == 1
    availability = client.get(f"/available?date={attempted['date']}").json()
    assert attempted["time"] in availability["available_times"]


@pytest.mark.parametrize("other_patient", [
    {"patient_name": "Outra Pessoa"},
    {"phone": "85988888888"},
    {"date": "2026-02-11"},
])
def test_other_patients_or_other_dates_can_book(other_patient):
    payload = {
        "patient_name": "Vítor Silva",
        "phone": "85999999999",
        "date": "2026-02-10",
        "time": "09:00",
    }
    assert client.post("/appointments", json=payload).status_code == 201
    response = client.post("/appointments", json={**payload, **other_patient, "time": "10:00"})
    assert response.status_code == 201


def test_same_patient_concurrent_requests_only_reserve_one_slot():
    from concurrent.futures import ThreadPoolExecutor

    payload = {
        "patient_name": "Vítor Silva",
        "phone": "85999999999",
        "date": "2026-02-10",
    }
    with ThreadPoolExecutor(max_workers=2) as executor:
        responses = list(executor.map(
            lambda slot: client.post("/appointments", json={**payload, "time": slot}),
            ["09:00", "10:00"],
        ))
    assert sorted(response.status_code for response in responses) == [201, 409]
    assert len(client.get("/appointments").json()) == 1


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


@pytest.mark.parametrize("ddd", ["11", "21", "31", "41", "51", "61", "71", "85", "88", "92", "99"])
def test_accepts_valid_ddds_from_all_regions(ddd):
    response = client.post("/appointments", json={
        "patient_name": "Teste DDD",
        "phone": f"({ddd}) 99999-9999",
        "date": "2026-02-10",
        "time": "11:00",
    })
    assert response.status_code == 201
    assert response.json()["phone"] == f"{ddd}999999999"


@pytest.mark.parametrize("ddd", ["00", "10", "20", "23", "36", "52", "60", "70", "90"])
def test_rejects_unassigned_ddds(ddd):
    response = client.post("/appointments", json={
        "patient_name": "Teste DDD",
        "phone": f"{ddd}999999999",
        "date": "2026-02-10",
        "time": "11:00",
    })
    assert response.status_code == 422
    assert "DDD válido do Brasil" in response.json()["detail"][0]["msg"]


def test_calendar_download_has_correct_timezone_and_no_patient_data():
    client.post("/appointments", json={
        "patient_name": "Maria Silva",
        "phone": "85999999999",
        "date": "2026-02-10",
        "time": "17:00",
    })
    response = client.get("/calendar.ics?date=2026-02-10&time=17:00")
    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/calendar")
    assert 'filename="consulta-2026-02-10-1700.ics"' in response.headers["content-disposition"]
    content = response.content.decode("utf-8")
    assert content.startswith("BEGIN:VCALENDAR\r\nVERSION:2.0\r\n")
    assert content.endswith("END:VCALENDAR\r\n")
    assert "DTSTART:20260210T200000Z\r\n" in content
    assert "DTEND:20260210T210000Z\r\n" in content
    assert "SUMMARY:Consulta · Clínica Bem-Estar\r\n" in content
    assert "Maria Silva" not in content
    assert "85999999999" not in content
    assert all(len(line.encode("utf-8")) <= 75 for line in content.split("\r\n"))
    # Importing the same slot again keeps a stable event identity.
    again = client.get("/calendar.ics?date=2026-02-10&time=17:00")
    uid = next(line for line in content.split("\r\n") if line.startswith("UID:"))
    assert uid in again.text


def test_calendar_download_rejects_invalid_slots():
    for query in (
        "date=2026-02-10&time=18:00",
        "date=2026-02-10&time=09:30",
        "date=2027-02-10&time=09:00",
        "date=2026-02-10&time=09:00Z",
    ):
        assert client.get(f"/calendar.ics?{query}").status_code == 400
    assert client.get("/calendar.ics?date=2026-02-30&time=09:00").status_code == 422
