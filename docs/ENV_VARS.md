# Environment Variables (Cheat Sheet)

Copy `.env.example` to `.env` and set values. Only the most relevant keys are listed below.

## Core

- `LLM_PROVIDER` (default: `openai`) — choose `openai` or `gemini`.
- `OPENAI_API_KEY` — required (used for embeddings; also for chat when `LLM_PROVIDER=openai`).
- `OPENAI_MODEL` (default: `o4-mini`) — model for OpenAI chat.
- `GOOGLE_API_KEY` — required when `LLM_PROVIDER=gemini`.
- `GEMINI_MODEL` (default: `gemini-2.5-pro`) — model for Gemini chat.

## Markdown to JSON Converter

- `USE_LLM_CONVERTER` (default: `true`) — enable LLM-based MD→JSON conversion.
- `CONVERTER_PROVIDER` (default: same as `LLM_PROVIDER`) — LLM provider for conversion.
- `CONVERTER_MODEL` (default: `gpt-4o-mini`) — mini model for fast, cost-effective conversion.
  - OpenAI: `gpt-4o-mini`
  - Google: `gemini-1.5-flash`
  - Anthropic: `claude-3-haiku-20240307`

## Embeddings (RAG / Vector Store)

- `EMBEDDING_PROVIDER` (default: `openai`) — choose `openai` or `gemini` for embeddings.
- `EMBEDDING_MODEL` (default: `text-embedding-3-large`) — OpenAI embedding model.
- `GEMINI_EMBEDDING_MODEL` (default: `models/text-embedding-004`) — Gemini embedding model.

**When to Use Each:**
- **OpenAI** (`text-embedding-3-large`): High quality, 3072 dimensions, requires `OPENAI_API_KEY`.
- **Gemini** (`models/text-embedding-004`): Cost-effective, 768 dimensions, requires `GOOGLE_API_KEY`.

## Tools / Search

- `TAVILY_API_KEY` — optional; enables web search enrichment when available.

## Notes

- Set `EMBEDDING_PROVIDER=gemini` in `.env` to switch from OpenAI to Gemini embeddings.
- Qdrant runs via Docker compose on ports 6333/6334 by default.
- Frontend proxies `/api` to the backend at `http://localhost:8000`.
