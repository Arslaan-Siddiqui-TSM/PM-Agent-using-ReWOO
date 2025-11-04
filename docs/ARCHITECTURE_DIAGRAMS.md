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
│  • EmbeddingCacheManager (copy cached points)               │
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
│  - EmbeddingCacheManager (data/embedding_cache)
└───────────────┬────────────────────────────┘
                │
                ▼
┌───────────────────────────────┐   ┌─────────────────────────┐
│ QdrantManager (vector store)  │   │ UnifiedLLM (provider)   │
│  - Qdrant (6333/6334)         │   │  - OpenAI (o4-mini)     │
│  - Collection: pm_agent_<id>  │   │  - Gemini (gemini-2.5)  │
└───────────────────────────────┘   └─────────────────────────┘
                │                            │
                └──────────────┬─────────────┘
                               ▼
                     Reflection Graph (LangGraph)
                     draft → critique → revise
```

## Data Flow (including RAG path)

```
PDFs (data/files or uploaded) → IntelligentDocumentParser
     ├─ Pre-chunked (Docling HybridChunker) if available
     └─ Fallback: RecursiveCharacterTextSplitter
         │
         ▼
Embeddings (OpenAI) → Qdrant (session collection)
         │
         ▼
Classification → Extraction → Analysis (cached)
         │
         ▼
Planning Context (structured text) → Reflection Agent
         │
         ▼
Feasibility (optional) + Final Plan → outputs/*.md
```

## Caching Strategy

```
1) Pipeline cache (cache/)
   - classifications/{hash}.json
   - extractions/{hash}.json
   - analysis/{set_hash}.json

2) Embedding cache (data/embedding_cache/)
   - Stores metadata per file hash:
     • parsed_md_path
     • qdrant_collection (usually pm_agent_cache)
     • qdrant_point_ids (reused via copy)
     • sessions_used_in [...]

3) Session collection in Qdrant
   - Name: pm_agent_<session_id[:8]>
   - New parses are embedded and added
   - Cached points copied into session collection for reuse
```

## Runtime Components & Ports

```
Frontend  : http://localhost:5173 (Vite dev server)
Backend   : http://localhost:8000 (FastAPI)
Qdrant    : http://localhost:6333 (REST), 6334 (gRPC)
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
→ Pipeline: classify/extract/analyze (cached where possible)
→ RAG: embed + store in Qdrant; copy cached points if available
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

Sessions are in-memory (`src/core/session_storage.py`); uploaded file paths, pipeline results, feasibility paths, and Qdrant info are stored per session id.

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
│  └─ embedding_cache/           # embedding metadata cache
├─ outputs/                      # feasibility + plan markdown
├─ frontend/                     # React app (Vite)
└─ docs/                         # this file + other docs
```
