from datetime import date, datetime, time, timedelta, timezone

from .services import TIMEZONE


def build_calendar_event(selected_date: date, selected_time: time) -> str:
    start = datetime.combine(selected_date, selected_time, tzinfo=TIMEZONE)
    end = start + timedelta(hours=1)

    def utc(value: datetime) -> str:
        return value.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Export only the slot and clinic details, without patient name or phone.
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//Clinica Bem-Estar//Agenda//PT-BR",
        "CALSCALE:GREGORIAN",
        "BEGIN:VEVENT",
        f"UID:consulta-{start.strftime('%Y%m%dT%H%M%S')}@clinica-bem-estar",
        f"DTSTAMP:{utc(datetime.now(timezone.utc))}",
        f"DTSTART:{utc(start)}",
        f"DTEND:{utc(end)}",
        "SUMMARY:Consulta · Clínica Bem-Estar",
        "DESCRIPTION:Consulta agendada na Clínica Bem-Estar.",
        "END:VEVENT",
        "END:VCALENDAR",
        "",
    ]
    return "\r\n".join(lines)
