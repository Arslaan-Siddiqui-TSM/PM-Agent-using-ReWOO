# Environment Variables (Cheat Sheet)

Copy `.env.example` to `.env` and set values. Only the most relevant keys are listed below.

## Core

- `LLM_PROVIDER` (default: `openai`) — choose `openai` or `gemini`.
- `OPENAI_API_KEY` — required (used for embeddings; also for chat when `LLM_PROVIDER=openai`).
- `OPENAI_MODEL` (default: `o4-mini`) — model for OpenAI chat.
- `GOOGLE_API_KEY` — required when `LLM_PROVIDER=gemini`.
- `GEMINI_MODEL` (default: `gemini-2.5-pro`) — model for Gemini chat.

## Tools / Search

- `TAVILY_API_KEY` — optional; enables web search enrichment when available.

## Notes

- Embeddings use OpenAI under the hood for RAG and Qdrant; keep `OPENAI_API_KEY` set even if `LLM_PROVIDER=gemini`.
- Qdrant runs via Docker compose on ports 6333/6334 by default.
- Frontend proxies `/api` to the backend at `http://localhost:8000`.
