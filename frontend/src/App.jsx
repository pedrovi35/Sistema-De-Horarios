import { useEffect, useState } from "react";
import CalendarSave from "./CalendarSave.jsx";
import PhoneInput, { formatPhone } from "./PhoneInput.jsx";
import { API_URL } from "./calendar.js";

function getErrorMessage(error) {
  return error instanceof Error ? error.message : "Ocorreu um erro inesperado.";
}

function getApiError(data, fallback) {
  if (typeof data?.detail === "string") return data.detail;
  if (Array.isArray(data?.detail)) {
    const messages = data.detail
      .map((item) => item?.msg)
      .filter(Boolean)
      .map((message) => message.replace(/^Value error,\s*/i, ""));
    if (messages.length > 0) return messages.join(" ");
  }
  return fallback;
}

export default function App() {
  const [date, setDate] = useState("");
  const [times, setTimes] = useState([]);
  const [selectedTime, setSelectedTime] = useState("");
  const [patientName, setPatientName] = useState("");
  const [phone, setPhone] = useState("");
  const [confirmation, setConfirmation] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  useEffect(() => {
    setTimes([]);
    setSelectedTime("");
    setConfirmation(null);
    setError("");
    if (!date) return;

    async function loadAvailability() {
      setLoading(true);
      try {
        const response = await fetch(`${API_URL}/available?date=${date}`);
        const data = await response.json();
        if (!response.ok) throw new Error(getApiError(data, "Não foi possível consultar os horários."));
        setTimes(data.available_times);
      } catch (requestError) {
        setError(getErrorMessage(requestError));
      } finally {
        setLoading(false);
      }
    }

    loadAvailability();
  }, [date]);

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setConfirmation(null);
    setLoading(true);

    try {
      const response = await fetch(`${API_URL}/appointments`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          patient_name: patientName,
          phone,
          date,
          time: selectedTime,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(getApiError(data, "Não foi possível criar o agendamento."));

      setConfirmation(data);
      setTimes((current) => current.filter((time) => time !== selectedTime));
      setSelectedTime("");
      setPatientName("");
      setPhone("");
    } catch (requestError) {
      setError(getErrorMessage(requestError));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="page">
      <section className="card">
        <header>
          <span className="eyebrow">Clínica Bem-Estar</span>
          <h1>Agende sua consulta</h1>
          <p>Escolha um dia útil de 2026 e encontre o melhor horário para você.</p>
        </header>

        <form onSubmit={handleSubmit}>
          <label htmlFor="date">Data da consulta</label>
          <input
            id="date"
            type="date"
            min="2026-01-01"
            max="2026-12-31"
            value={date}
            onChange={(event) => setDate(event.target.value)}
            required
          />

          {loading && !selectedTime && <p className="status">Consultando horários…</p>}

          {times.length > 0 && (
            <fieldset>
              <legend>Horários disponíveis</legend>
              <div className="time-grid">
                {times.map((time) => (
                  <button
                    className={selectedTime === time ? "time selected" : "time"}
                    key={time}
                    type="button"
                    onClick={() => setSelectedTime(time)}
                  >
                    {time}
                  </button>
                ))}
              </div>
            </fieldset>
          )}

          {date && !loading && times.length === 0 && !error && (
            <p className="status">Não há horários disponíveis nesta data.</p>
          )}

          {selectedTime && (
            <div className="patient-fields">
              <label htmlFor="name">Nome completo</label>
              <input
                id="name"
                value={patientName}
                onChange={(event) => setPatientName(event.target.value)}
                minLength="2"
                required
                placeholder="Seu nome"
              />

              <label htmlFor="phone">Telefone / WhatsApp com DDD</label>
              <PhoneInput value={phone} onChange={setPhone} />

              <button className="submit" type="submit" disabled={loading}>
                {loading ? "Confirmando…" : `Confirmar ${selectedTime}`}
              </button>
            </div>
          )}
        </form>

        {error && <p className="alert error" role="alert">{error}</p>}
        {confirmation && (
          <section className="confirmation" role="status">
            <span className="confirmation-icon" aria-hidden="true">✓</span>
            <div>
              <strong>Agendamento confirmado!</strong>
              <p>Protocolo #{confirmation.id}</p>
              <dl>
                <div>
                  <dt>Paciente</dt>
                  <dd>{confirmation.patient_name}</dd>
                </div>
                <div>
                  <dt>Data e horário</dt>
                  <dd>
                    {confirmation.date.split("-").reverse().join("/")} às {confirmation.time.slice(0, 5)}
                  </dd>
                </div>
                <div>
                  <dt>Telefone</dt>
                  <dd>{formatPhone(confirmation.phone)}</dd>
                </div>
              </dl>
              <CalendarSave key={confirmation.id} appointment={confirmation} />
            </div>
          </section>
        )}

        <footer>Atendimento das 08:00 às 18:00 · Horário de Brasília</footer>
      </section>
    </main>
  );
}
