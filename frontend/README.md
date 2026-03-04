# Frontend (Vue)

Desktop-first chat client for the YAML workflow platform.

## Stack

- Vue 3 + TypeScript + Vite
- Pinia state management
- Vue Router

## Run

```bash
cp .env.example .env
npm install
npm run dev
```

## Build

```bash
npm run build
```

## Runtime contract

- Backend base URL is configured with `VITE_API_BASE`.
- Uses OpenAI-compatible endpoints:
  - `GET /v1/models`
  - `POST /v1/chat/completions`
- Persists `X-Conversation-Id` across chat turns.

## UI notes

- Desktop-first responsive behavior.
- Dark/light theme toggle aligned to the Pencil desktop previews.
