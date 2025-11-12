# 🎨 System Architecture Diagrams

This reflects the current FastAPI-based API, Reflection planning workflow (draft → critique → revise), UnifiedLLM (OpenAI/Gemini/NVIDIA), and async document processing with session management.

## API Endpoints Overview

```
Health & Info:
  GET  /                         # API info and version
  GET  /health/                  # Health check
  GET  /docs                     # Swagger UI

Document Upload & Processing:
  POST /api/upload               # Upload PDFs or use defaults (creates session)
  GET  /api/upload-status/{id}   # Poll async processing status

Feasibility & Planning:
  POST /api/feasibility          # Generate feasibility assessment
  POST /api/generate-plan        # Generate project implementation plan

Utilities:
  GET  /api/document-types       # List supported document types
  GET  /api/sessions/{id}        # Get session info
  DELETE /api/sessions/{id}      # Delete session and files
  GET  /api/file-content         # Read generated files (outputs/ only)
```

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
│  • /api/upload → creates session, parses docs (async)       │
│  • /api/upload-status/{session_id} → check processing       │
│  • /api/feasibility → generate feasibility report           │
│  • /api/generate-plan → Reflection (draft→critique→revise)  │
│  • /api/file-content → read outputs/feasibility/plan files  │
│  • /api/sessions/{id} → get/delete session info             │
│  • /api/document-types → supported document types           │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│            DOCUMENT INTELLIGENCE PIPELINE                   │
│  • IntelligentDocumentParser (Docling-first; chunking)      │
│  • Classify → Extract → Analyze (cache-aware)               │
│  • Generates Planning Context (structured, compact)         │
│  • Async background processing with status tracking         │
└─────────────────────────────────────────────────────────────┘
                          │
                          ▼
┌─────────────────────────────────────────────────────────────┐
│             REFLECTION PLANNING AGENT (LangGraph)           │
│  • Iterates: draft → critique → revise                      │
│  • Uses Planning Context (+ feasibility, if available)      │
│  • UnifiedLLM: OpenAI, Gemini, or NVIDIA (env-controlled)   │
│  • Automatic fallback: OpenAI → Gemini → NVIDIA             │
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
│  - 3 routers: agent, utils, health         │
└───────────────┬────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│ Route Handlers (delegation pattern)        │
│  - UploadHandler (async processing)        │
│  - FeasibilityHandler                      │
│  - PlanGenerationHandler                   │
└───────────────┬────────────────────────────┘
                │
                ▼
┌─────────────────────────────────────────────┐
│ DocumentIntelligencePipeline                │
│  - Classifier / Extractor / Analyzer        │
│  - IntelligentDocumentParser (Docling)      │
│  - Parsing cache (data/parsing_cache)       │
└───────────────┬────────────────────────────┘
                │
                ▼
┌───────────────────────────────┐   ┌─────────────────────────┐
│ DoclingParser (PDF → MD)      │   │ UnifiedLLM (provider)   │
│  - Parsing cache (SHA256)     │   │  - OpenAI (gpt-4o-mini) │
│  - Output: MD + JSON files    │   │  - Gemini (gemini-2.5)  │
└───────────────────────────────┘   │  - NVIDIA (qwen3-next)  │
                │                   │  - Auto fallback support│
                └──────────────┬────└─────────────────────────┘
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
         │  (async background processing)
         ▼
Feasibility Assessment → Feasibility Graph (LangGraph)
         │  - Stage 1: Thinking Summary
         │  - Stage 2: Feasibility Report
         ▼
Project Plan → Reflection Graph (LangGraph)
         │  - Draft → Critique → Revise (iterative)
         ▼
Final Plan → outputs/*.md
```

## Caching Strategy

```
1) Document Processing Cache (data/parsing_cache/)
   - SHA256-based file hashing
   - Stores parsed markdown + JSON metadata
   - Avoids re-parsing identical PDFs

2) Document Intelligence Cache (data/embedding_cache/)
   - Classification results cache
   - Extraction results cache
   - Analysis results cache
```

## Runtime Components & Ports

```
Frontend  : http://localhost:5173 (Vite dev server)
Backend   : http://localhost:8000 (FastAPI)

LLM Providers (configurable via LLM_PROVIDER env var):
  - OpenAI (default)
  - Google Gemini
  - NVIDIA NIM
  - Automatic fallback chain
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

## Async Processing Flow

```
1. Upload Request (POST /api/upload)
   ├─ Create session
   ├─ Copy/validate files
   ├─ Set status = "processing"
   └─ Start background thread

2. Background Processing
   ├─ Parse PDFs → Markdown (Docling)
   ├─ Convert MD → JSON (Document Intelligence)
   ├─ Update session.parsed_documents
   └─ Set status = "completed" or "failed"

3. Client Polling (GET /api/upload-status/{session_id})
   ├─ Returns: status, message, parsed_documents count
   └─ Frontend polls until status != "processing"

4. Feasibility/Plan Generation
   ├─ Validates status == "completed"
   ├─ Returns 425 (Too Early) if still processing
   └─ Proceeds only when all processing done
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

## LLM Provider Architecture

```
UnifiedLLM (src/config/llm_config.py)
   │
   ├─ Primary Provider Selection (env: LLM_PROVIDER)
   │  ├─ nvidia → NVIDIA NIM (qwen3-next-80b-a3b-instruct)
   │  ├─ openai → OpenAI (gpt-4o-mini, default)
   │  └─ gemini → Google Gemini (gemini-2.5-pro)
   │
   ├─ Automatic Fallback Chain
   │  └─ If primary fails → try: OpenAI → Gemini → NVIDIA
   │
   ├─ Features
   │  ├─ Pure LangChain (init_chat_model)
   │  ├─ Runtime provider switching
   │  ├─ Token usage tracking with Rich UI
   │  └─ Session-level statistics
   │
   └─ Configuration
      ├─ LLM_PROVIDER (nvidia/openai/gemini)
      ├─ NVIDIA_MODEL, OPENAI_MODEL, GEMINI_MODEL
      └─ NVIDIA_API_KEY, OPENAI_API_KEY, GOOGLE_API_KEY
```

## Example Walkthrough (condensed)

```
Input: requirements.pdf, tech-spec.pdf
→ Upload: POST /api/upload (creates session, starts async processing)
→ Poll: GET /api/upload-status/{session_id} (until status=completed)
→ Parse: PDF → Markdown + JSON (cached where possible)
→ Feasibility: POST /api/feasibility (saves two files: thinking + report)
→ Plan: POST /api/generate-plan (saves project_plan_*.md)
→ View: GET /api/file-content?file_path=outputs/...
```

## State Management (Reflection)

The planning flow uses two state graphs with LangGraph:

**FeasibilityState** (feasibility_graph.py):

- md_file_paths: list of parsed markdown documents
- session_id: current session identifier
- development_context: optional user-provided context
- thinking_summary: stage 1 output (comprehensive analysis)
- feasibility_report: stage 2 output (final assessment)
- unified_context_path: path to unified context file

**ReflectionState** (graph.py):

- task: description of the planning goal
- document_context: structured context from the pipeline
- max_iterations: number of reflection cycles
- iterations: collected iteration artifacts (draft, critique, revise)
- final_plan: captured from the `revise` node
- current_draft: latest draft version
- current_critique: latest critique

Sessions are in-memory (`src/core/session_storage.py`) with these properties:

- session_id, created_at, expiry tracking
- document_paths, parsed_documents, parsed_documents_dir
- processing_status: pending/processing/completed/failed
- status_message, processing_error
- feasibility paths and pipeline results

## File Structure (relevant parts)

```
rewoo-demonstration/
├─ server.py                     # FastAPI entrypoint
├─ docker-compose.yml            # Qdrant service (optional)
├─ src/
│  ├─ routes/                    # /api endpoints
│  │  ├─ planning_agent.py       # Main API routes (upload, feasibility, plan)
│  │  ├─ upload_handler.py       # Upload logic with async processing
│  │  ├─ feasibility_handler.py  # Feasibility generation logic
│  │  ├─ plan_generation_handler.py  # Plan generation logic
│  │  ├─ utils_endpoints.py      # Utility endpoints (sessions, file-content)
│  │  └─ health_check.py         # Health check endpoint
│  ├─ core/                      # pipeline, session, cache
│  │  ├─ session.py              # Session class
│  │  ├─ session_storage.py      # In-memory session storage
│  │  └─ document_analyzer.py    # Document analysis pipeline
│  ├─ agents/                    # classifier, extractor, etc.
│  ├─ config/                    # llm_config, feature flags
│  │  └─ llm_config.py           # UnifiedLLM with multi-provider support
│  ├─ states/                    # State classes
│  │  ├─ reflection_state.py     # ReflectionState
│  │  └─ feasibility_state.py    # FeasibilityState
│  └─ app/                       # LangGraph implementations
│     ├─ graph.py                # Reflection graph (draft→reflect→revise)
│     ├─ feasibility_graph.py    # Feasibility graph
│     ├─ feasibility_agent.py    # Feasibility generation logic
│     ├─ draft.py                # Draft generation node
│     ├─ reflect.py              # Reflection/critique node
│     └─ revise.py               # Revision node
├─ data/
│  ├─ files/                     # sample PDFs
│  ├─ uploads/                   # user uploads (runtime)
│  ├─ parsing_cache/             # parsing metadata cache
│  └─ embedding_cache/           # document intelligence cache
├─ output/                       # feasibility + plan markdown
│  └─ intermediate/              # intermediate outputs
├─ outputs/                      # alternative output location
├─ frontend/                     # React app (Vite)
└─ docs/                         # this file + other docs
```
