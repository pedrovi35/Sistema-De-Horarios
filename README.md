# Agenda da clínica

Mini sistema full stack para consultar horários e criar agendamentos. O backend valida fins de semana, feriados nacionais do Brasil e conflitos de horário.

## Por que o QR code ainda não funciona no celular?

O sistema está sendo executado localmente. O QR code do recibo aponta para `http://localhost:8000/calendar.ics`, que só está disponível no computador onde o backend está rodando. Ao ler o código no celular, `localhost` aponta para o próprio celular; por isso o endereço fica indisponível.

Para funcionar fora do computador de teste, o sistema precisa ser publicado com um backend acessível pela internet, e `VITE_API_URL` deve apontar para esse endereço antes do build do frontend. Publicar somente o frontend na Vercel não disponibiliza automaticamente o backend nem o arquivo da agenda. O QR já é gerado; falta um endereço público para acessar o evento da consulta.

## Agendamentos duplicados

Uma pessoa com o mesmo nome e telefone não pode ocupar dois horários no mesmo dia. Ela pode agendar normalmente em outra data. Ao tentar repetir no mesmo dia, o sistema mostra o dia e o horário da consulta já registrada, mantém o novo horário livre e orienta a pessoa a entrar em contato com a clínica para alterações. A comparação ignora maiúsculas, minúsculas e espaços extras no nome e usa somente os dígitos do telefone.

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
- `GET /calendar.ics?date=2026-02-10&time=09:00`: baixa o evento de uma hora em formato iCalendar, no fuso de Brasília, sem nome ou telefone do paciente.

No rodapé do recibo de confirmação, um QR code pequeno nas cores da clínica permite baixar o evento da consulta já marcada em formato `.ics`. A pessoa lê o código com a câmera do celular e confirma o salvamento em um calendário compatível. Isso não cria outro agendamento na clínica. A abertura e importação do arquivo dependem do aplicativo instalado.

Para ler o QR em outro celular, configure `VITE_API_URL` com um endereço do backend acessível nesse aparelho antes do build. Endereços `localhost` funcionam apenas no computador que executa o sistema. O QR contém somente data e horário, sem dados pessoais do paciente.

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
