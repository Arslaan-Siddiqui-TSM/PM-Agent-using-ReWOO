# Project Planning Assistant (ReWOO demo)

Turn multiple project PDFs (specs, BRDs, test plans) into a feasibility assessment and a polished project plan. Backend is FastAPI; frontend is React (Vite). Documents are parsed, classified, and analyzed; embeddings go to Qdrant for retrieval; the plan is generated via an LLM workflow.

Quick, simple, and local-friendly.

## What’s inside

- FastAPI backend (http://localhost:8000)
- React/Vite frontend (http://localhost:5173)
- Document Intelligence Pipeline (classify → extract → analyze)
- Qdrant vector DB (Docker) for embeddings and retrieval

## Prerequisites

- Python 3.13+
- Node.js 18+ (for the frontend)
- Docker (for Qdrant)
- API keys:
  - OpenAI or Google Gemini: for the LLM (choose via `LLM_PROVIDER` env var)
  - OpenAI or Google Gemini: for embeddings (choose via `EMBEDDING_PROVIDER` env var)

Note: You can mix and match providers! For example: use Gemini for LLM and OpenAI for embeddings, or vice versa.

## Setup (Windows cmd)

1. Clone and create your environment file

```cmd
copy .env.example .env
```

Open `.env` and set at least:

```env
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
TAVILY_API_KEY=...
LLM_PROVIDER=openai          # or gemini (for chat/reasoning)
EMBEDDING_PROVIDER=openai    # or gemini (for vector embeddings)
```

2. Start Qdrant (vector DB)

```cmd
docker compose -f docker-compose.yml up -d qdrant
```

3. Backend: create venv and install

```cmd
py -3.13 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

4. Run the backend API

```cmd
python server.py
```

5. Frontend: install and run

```cmd
cd frontend
npm install
npm run dev
```

Frontend runs at http://localhost:5173 and proxies API calls to http://localhost:8000.

## Try it

Option A – UI

- Visit http://localhost:5173
- Keep “Use default sample files” checked and click “Upload & Continue”
- Continue to Feasibility → Generate Project Plan

Option B – API (quick smoke test)

```cmd
curl http://localhost:8000/health/

curl -X POST "http://localhost:8000/api/upload?use_default_files=true"

:: Use the returned session_id below
curl -X POST http://localhost:8000/api/feasibility ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"<SESSION_ID>\",\"use_intelligent_processing\":true}"

curl -X POST http://localhost:8000/api/generate-plan ^
  -H "Content-Type: application/json" ^
  -d "{\"session_id\":\"<SESSION_ID>\",\"use_intelligent_processing\":true,\"max_iterations\":5}"
```

Outputs are saved under `outputs/` (feasibility report and final plan markdown files). Uploaded files are stored under `data/uploads/`.

## Key endpoints

- GET `/health/` – service status
- POST `/api/upload?use_default_files=true` – load PDFs from `data/files/`
- POST `/api/upload` – upload your own PDFs (multipart, max 15 files)
- POST `/api/feasibility` – body: `{ session_id, use_intelligent_processing, development_context? }`
- POST `/api/generate-plan` – body: `{ session_id, use_intelligent_processing, max_iterations }`
- GET `/api/file-content?file_path=<path>` – read saved markdown files (restricted to `outputs/` and `uploads/`)

## Folders you’ll use

- `data/files/` – sample input PDFs
- `data/uploads/` – uploaded PDFs (runtime)
- `outputs/` – feasibility and plan markdown files
- `qdrant_storage/` – persistent vector DB data (Docker volume)

## Troubleshooting

- Qdrant connection failed – ensure Docker is running: `docker compose up -d qdrant`
- 401/invalid API key – check `OPENAI_API_KEY` (embeddings) and your chosen `LLM_PROVIDER` envs
- Rate limits (429) – try again later or reduce iterations
- Upload errors – only PDFs are accepted; max 15 files

## More docs

- Environment/config: `docs/ENV_CONFIGURATION.md`
- Architecture and structure: `docs/PROJECT_STRUCTURE.md`, `docs/ARCHITECTURE_DIAGRAMS.md`
- Migration and implementation notes: `docs/implementation/*`

—