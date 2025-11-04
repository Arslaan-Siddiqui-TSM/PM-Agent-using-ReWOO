# Quick Start

A minimal guide to run the demo locally. For a fuller overview, see the root `README.md`.

## Prerequisites

- Python 3.13+
- Node.js 18+
- Docker (for Qdrant)
- API keys: OpenAI (embeddings), Google Gemini or OpenAI (LLM)

## 1) Configure environment

Copy the example and edit values:

```cmd
copy .env.example .env
```

Set at least:

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
TAVILY_API_KEY=...
LLM_PROVIDER=openai   # or gemini
```

## 2) Start Qdrant

```cmd
docker compose -f docker-compose.yml up -d qdrant
```

## 3) Run backend (FastAPI)

```cmd
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python server.py
```

Backend: http://localhost:8000 (Swagger at /docs)

## 4) Run frontend (React/Vite)

```cmd
cd frontend
npm install
npm run dev
```

Frontend: http://localhost:5173 (proxies /api to 8000)

## 5) Try it

- UI: open http://localhost:5173, keep “Use default sample files” checked, and run through the steps.
- API: quick smoke test (Windows cmd):

```cmd
curl http://localhost:8000/health/

curl -X POST "http://localhost:8000/api/upload?use_default_files=true"

:: Replace <SESSION_ID> with the value returned above
curl -X POST http://localhost:8000/api/feasibility ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"<SESSION_ID>\",\"use_intelligent_processing\":true}"

curl -X POST http://localhost:8000/api/generate-plan ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"<SESSION_ID>\",\"use_intelligent_processing\":true,\"max_iterations\":5}"
```

Outputs are in `outputs/` (feasibility + plan markdown). Uploaded files: `data/uploads/`.
