# 🎨 System Architecture Diagrams

This reflects the current FastAPI-based API, Reflection planning workflow (draft → critique → revise), UnifiedLLM (OpenAI/Gemini), and Qdrant-backed RAG with an embedding cache.

## High-Level Flow

```
┌─────────────────────────────────────────────────────────────┐
│                 CLIENT (Web UI or direct API)               │
│   • React/Vite frontend (http://localhost:5173)             │
│   • FastAPI at /api, health at /health                      │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                 FASTAPI APPLICATION (server.py)             │
│  • /api/upload → creates session, parses docs, RAG ingest   │
│  • /api/generate-embeddings → manual RAG (re)processing     │
│  • /api/feasibility → generate feasibility report           │
│  • /api/generate-plan → Reflection (draft→critique→revise)  │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            DOCUMENT INTELLIGENCE PIPELINE                   │
│  • IntelligentDocumentParser (Docling-first; chunking)      │
│  • Classify → Extract → Analyze (cache-aware)               │
│  • Generates Planning Context (structured, compact)         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                     RAG / VECTOR STORE                      │
│  • OpenAI embeddings (text-embedding-3-*)                   │
│  • Qdrant (Docker) for vector storage                       │
│  • Parsing cache (SHA256-based deduplication)               │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│             REFLECTION PLANNING AGENT (LangGraph)           │
│  • Iterates: draft → critique → revise                      │
│  • Uses Planning Context (+ feasibility, if available)      │
│  • UnifiedLLM: OpenAI o4-mini or Gemini (env-controlled)    │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│                   PROJECT IMPLEMENTATION PLAN               │
│  • Markdown saved to outputs/                               │
└─────────────────────────────────────────────────────────────┘
```

## Component Interaction (API-centric)

```
┌─────────────────────────────────────────────┐
│ FastAPI (server.py)                        │
│  - routes: /api/*, /health/*               │
└───────────────┬────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│ DocumentIntelligencePipeline                │
│  - Classifier / Extractor / Analyzer        │
│  - IntelligentDocumentParser (Docling)      │
│  - Parsing cache (data/parsing_cache)
└───────────────┬────────────────────────────┘
                │
                ▼
┌───────────────────────────────┐   ┌─────────────────────────┐
│ DoclingParser (PDF → MD)      │   │ UnifiedLLM (provider)   │
│  - Parsing cache (SHA256)     │   │  - OpenAI (o4-mini)     │
│  - Output: MD + JSON files    │   │  - Gemini (gemini-2.5)  │
└───────────────────────────────┘   └─────────────────────────┘
                │                            │
                └──────────────┬─────────────┘
                               ▼
                     Reflection Graph (LangGraph)
                     draft → critique → revise
```

## Data Flow

```
PDFs (data/files or uploaded) → DoclingParser
         │
         ▼
Markdown Files (.md) + JSON Files (.json)
         │
         ▼
Feasibility Assessment (optional) → LLM
         │
         ▼
Project Plan → Reflection Agent
         │
         ▼
Final Plan → outputs/*.md
```

## Caching Strategy

```
1) Pipeline cache (cache/)
   - classifications/{hash}.json
   - extractions/{hash}.json
   - analysis/{set_hash}.json

2) Parsing cache (within DoclingParser)
   - Avoids re-parsing same PDFs
   - Uses SHA256 file hashing
   - Stores parsed markdown files
```

## Runtime Components & Ports

```
Frontend  : http://localhost:5173 (Vite dev server)
Backend   : http://localhost:8000 (FastAPI)
```

## Decision Tree (Document Classification)

```
PDF → sample pages → LLM classify
   ├─ confidence ≥ 0.8 → type-specific extraction
   ├─ 0.5 ≤ conf < 0.8 → keep type + add generic fallback
   └─ conf < 0.5       → "unknown" + generic extraction
          │
          └→ cache classification by file hash
```

## Analysis Report Generation

```
Inputs: classifications + extractions for all docs
   ├─ Gap analysis
   ├─ Conflict detection
   ├─ Cross-document references
   └─ Coverage / readiness scoring
→ Export JSON + Markdown under outputs/intermediate/
```

## Example Walkthrough (condensed)

```
Input: requirements.pdf, tech-spec.pdf
→ Parse: PDF → Markdown + JSON (cached where possible)
→ Feasibility: /api/feasibility saves two markdown files
→ Plan: /api/generate-plan saves project_plan_*.md
```

## State Management (Reflection)

The planning flow uses a `ReflectionState` passed through the LangGraph:

- task: description of the planning goal
- document_context: structured context from the pipeline
- max_iterations: number of reflection cycles
- iterations: collected iteration artifacts
- final_plan: captured from the `revise` node

Sessions are in-memory (`src/core/session_storage.py`); uploaded file paths, parsed documents, and feasibility paths are stored per session id.

## File Structure (relevant parts)

```
rewoo-demonstration/
├─ server.py                     # FastAPI entrypoint
├─ docker-compose.yml            # Qdrant service
├─ src/
│  ├─ routes/                    # /api endpoints
│  ├─ core/                      # pipeline, qdrant, cache
│  ├─ agents/                    # classifier, extractor, etc.
│  ├─ config/                    # llm_config, feature flags
│  ├─ states/                    # ReflectionState
│  └─ app/                       # reflection graph
├─ data/
│  ├─ files/                     # sample PDFs
│  ├─ uploads/                   # user uploads (runtime)
│  ├─ parsed_documents/          # parser outputs
│  └─ parsing_cache/             # parsing metadata cache
├─ outputs/                      # feasibility + plan markdown
├─ frontend/                     # React app (Vite)
└─ docs/                         # this file + other docs
```
