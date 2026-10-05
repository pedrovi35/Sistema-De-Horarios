# Agenda da clínica

Mini sistema full stack para consultar horários e criar agendamentos. O backend valida fins de semana, feriados nacionais do Brasil e conflitos de horário.

## Tecnologias

- Backend: Python, FastAPI, SQLAlchemy e SQLite
- Frontend: React com Vite
- Feriados: [Nager.Date API](https://date.nager.at/api/v3/PublicHolidays/2026/BR)
- Fuso horário de Brasília: `America/Sao_Paulo`

## Como executar

### Backend

Requer Python 3.10 ou superior.

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

O backend estará em `http://localhost:8000`. A documentação interativa fica em `http://localhost:8000/docs`.

### Frontend

Em outro terminal, requer Node.js 18 ou superior:

```bash
cd frontend
npm install
npm run dev
```

Abra `http://localhost:5173`.

## Endpoints

- `GET /available?date=2026-02-10`: lista os horários livres.
- `POST /appointments`: cria um agendamento.
- `GET /appointments`: lista os agendamentos.

Exemplo de criação:

```json
{
  "patient_name": "Maria Silva",
  "phone": "85999999999",
  "date": "2026-02-10",
  "time": "09:00"
}
```

O funcionamento é das 08:00 às 18:00, em blocos de uma hora. Assim, o último horário de início é 17:00.

## Testes

Com o ambiente virtual do backend ativo:

```bash
cd backend
pytest
```
