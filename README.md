# SimpleAgentChatTemplate

Vue + FastAPI chat platform that turns YAML workflows (SimpleAgents) into an OpenAI-compatible chat API and custom desktop-first chat UI.

## What is implemented

- Split stack architecture:
  - `frontend/`: Vue 3 + Vite + TypeScript + Pinia
  - `backend/`: FastAPI + SQLAlchemy + Alembic + PostgreSQL
- OpenAI-compatible endpoints:
  - `GET /v1/models`
  - `POST /v1/chat/completions` (stream and non-stream)
- YAML workflow registry seeded from SimpleAgents examples
- Grouped registry starter bundle:
  - parent: `email-chat-orchestrator-with-subgraph-tool.yaml`
  - subgraph: `hr-warning-email-subgraph.yaml`
- Chat persistence in Postgres:
  - conversations, messages, workflow runs, workflow events
- Desktop-first chat UI in dark/light themes inspired by the provided Pencil design

## Repository structure

```text
.
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── models/
│   │   ├── schemas/
│   │   └── services/
│   ├── alembic/
│   ├── alembic.ini
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
└── TODO.md
```

## Quick start (local)

### One-command shortcuts

```bash
make help
```

Useful targets:

- `make install-backend`
- `make install-frontend`
- `make run-postgres`
- `make run-backend`
- `make run-frontend`
- `make reload-workflows`

### 1) Start Postgres

Use Docker:

```bash
docker compose up -d postgres
```

### 2) Backend

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 3) Frontend

```bash
cd frontend
cp .env.example .env
npm install
npm run dev
```

Frontend runs on `http://localhost:5173`, backend on `http://localhost:8000`.

## OpenAI-compatible API examples

### List models

```bash
curl -s http://localhost:8000/v1/models | jq
```

### Non-stream chat completion

```bash
curl -s http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "yaml/email-chat-draft-or-clarify",
    "stream": false,
    "messages": [
      {"role":"user","content":"Draft a warning email for repeated delays."}
    ]
  }' | jq
```

### Stream chat completion

```bash
curl -N http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "yaml/orchestrator-hr-bundle",
    "stream": true,
    "messages": [
      {"role":"user","content":"Draft HR warning email for repeated late submission"}
    ]
  }'
```

## Internal endpoints

- `GET /health`
- `GET /internal/workflows`
- `POST /internal/workflows/reload`
- `GET /internal/conversations/{conversation_id}`

## Notes

- This version is desktop-first responsive UI. Dedicated mobile UI comes in the next phase.
- Workflow execution depends on SimpleAgents provider credentials (`CUSTOM_API_KEY` / provider-specific keys).

## CI

GitHub Actions validates:

- Frontend build (`npm run build`)
- Backend tests (`pytest`)
- Backend syntax compilation (`python -m compileall app`)
