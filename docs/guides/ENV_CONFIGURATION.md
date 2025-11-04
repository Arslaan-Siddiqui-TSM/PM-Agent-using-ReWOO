# Environment Configuration Guide

This guide explains all environment variables needed to run the PM Agent application.

## Quick Setup

1. Create a `.env` file in the project root
2. Copy the template below and fill in your API keys
3. Adjust optional settings as needed

## Environment Variables Template

```env
# ================================================================
# PM Agent using ReWOO - Environment Configuration
# ================================================================

# -------------------- API Keys (REQUIRED) --------------------

# Google Gemini API Key (for LLM operations)
# Get yours at: https://aistudio.google.com/app/api-keys
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Tavily API Key (for web search)
# Get yours at: https://tavily.com/
TAVILY_API_KEY=your_tavily_api_key_here

# OpenAI API Key (for embeddings and optional GPT-4 usage)
# Get yours at: https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# -------------------- LLM Configuration --------------------

OPENAI_MODEL=gpt-4
EMBEDDING_MODEL=text-embedding-3-large

# -------------------- Document Processing (Docling) --------------------

# Docling is the PRIMARY document processor
# Supports: PDF, DOCX, PPTX, XLSX, images, HTML, MD, TXT

DOCLING_OCR_DEFAULT=false  # Enable for scanned docs (slower)
DOCLING_TABLE_MODE=fast  # or "accurate"
DOCLING_EXPORT_FORMAT=markdown  # or "text"
DOCLING_TABLE_EXTRACTION=true

# -------------------- RAG (Vector Database) --------------------

CHROMA_PERSIST_DIRECTORY=./chroma_db
CHROMA_COLLECTION_NAME=docs_collection
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# -------------------- Kroki Diagram Generation --------------------

# Kroki is FREE and requires NO API KEY!
KROKI_URL=https://kroki.io
ENABLE_DIAGRAM_GENERATION=false

# -------------------- Advanced Features (Opt-In) --------------------

ENABLE_RAG=false  # RAG-powered document querying
ENABLE_CHAT=false  # Conversational plan refinement
ENABLE_VALIDATION=false  # Plan validation agent

# -------------------- Performance & Limits --------------------

MAX_FILE_SIZE_MB=50
PARALLEL_WORKERS=4
```

## Required API Keys

### Google Gemini API

**Purpose**: Primary LLM for document analysis and plan generation

**How to get**:
1. Visit https://aistudio.google.com/app/api-keys
2. Create a new API key
3. Copy to `GOOGLE_API_KEY` in `.env`

**Free Tier**: Generous free tier available

### Tavily API

**Purpose**: Web search for domain clarifications

**How to get**:
1. Visit https://tavily.com/
2. Sign up for an account
3. Get your API key from the dashboard
4. Copy to `TAVILY_API_KEY` in `.env`

**Free Tier**: 1,000 requests/month

### OpenAI API

**Purpose**: Embeddings for RAG (optional), GPT-4 for advanced features

**How to get**:
1. Visit https://platform.openai.com/api-keys
2. Create a new API key
3. Copy to `OPENAI_API_KEY` in `.env`

**Note**: Only required if using RAG or GPT-4 model

## Docling Configuration

Docling is the primary document processor, replacing PyMuPDF for better performance and broader format support.

### `DOCLING_OCR_DEFAULT`

- **Default**: `false` (recommended for performance)
- **When to enable**: Processing scanned PDFs or images with text
- **Impact**: Significantly slower processing when enabled

### `DOCLING_TABLE_MODE`

- **Options**: `fast` or `accurate`
- **Default**: `fast`
- **Recommendation**: Use `fast` unless you need precise table extraction

### `DOCLING_EXPORT_FORMAT`

- **Options**: `markdown` or `text`
- **Default**: `markdown`
- **Recommendation**: `markdown` preserves more structure

### `DOCLING_TABLE_EXTRACTION`

- **Default**: `true`
- **Purpose**: Extract table structures from documents
- **Note**: First run may download ML models (~100MB)

## Kroki Diagram Generation

**Status**: ✅ FREE - No API key required!

### `KROKI_URL`

- **Default**: `https://kroki.io`
- **Purpose**: Public Kroki instance for diagram generation
- **Self-hosted**: Can use your own Kroki instance if preferred

### `ENABLE_DIAGRAM_GENERATION`

- **Default**: `false` (opt-in)
- **When enabled**: Generates visual diagrams (Gantt, dependencies, architecture, etc.)
- **Diagram types**: Mermaid, PlantUML, Graphviz, BPMN, ERD, Flowcharts

## Advanced Features

All advanced features are **disabled by default** (opt-in).

### RAG (Retrieval-Augmented Generation)

**Status**: Experimental

Enable with `ENABLE_RAG=true`

**Requirements**:
- `OPENAI_API_KEY` must be set
- ChromaDB will store embeddings locally

**Use cases**:
- Semantic search across uploaded documents
- Context-aware question answering
- Enhanced draft iterations with relevant context

### Chat Interface

**Status**: Experimental

Enable with `ENABLE_CHAT=true`

**Requirements**:
- RAG must be enabled (`ENABLE_RAG=true`)
- Frontend chat component

**Features**:
- Query documents conversationally
- Refine plan sections interactively
- Get citations from source documents

### Plan Validation

**Status**: Experimental

Enable with `ENABLE_VALIDATION=true`

**Features**:
- Check plan completeness
- Validate dependencies
- Timeline feasibility analysis
- Generate validation report

## Performance Settings

### `MAX_FILE_SIZE_MB`

- **Default**: `50`
- **Purpose**: Maximum size for uploaded files
- **Recommendation**: Adjust based on your server capacity

### `PARALLEL_WORKERS`

- **Default**: `4`
- **Purpose**: Thread pool size for CPU-bound tasks (Docling processing)
- **Recommendation**: Set to number of CPU cores for best performance

## RAG/ChromaDB Settings

Only used when `ENABLE_RAG=true`

### `CHROMA_PERSIST_DIRECTORY`

- **Default**: `./chroma_db`
- **Purpose**: Where ChromaDB stores vector embeddings
- **Note**: Directory created automatically

### `MAX_CHUNK_SIZE` and `CHUNK_OVERLAP`

- **Defaults**: `1000` and `200`
- **Purpose**: How documents are split for embedding
- **Recommendation**: Default values work well for most cases

## Troubleshooting

### Missing API Keys

If you see authentication errors, ensure all required keys are set:
- `GOOGLE_API_KEY`
- `TAVILY_API_KEY`
- `OPENAI_API_KEY` (if using RAG)

### Docling Errors

**"Model not found"**: Table extraction models downloading on first run (one-time)

**"OCR failed"**: Ensure Tesseract is installed if using OCR (optional)

### Performance Issues

**Slow document processing**:
- Disable OCR if not needed (`DOCLING_OCR_DEFAULT=false`)
- Use `fast` table mode
- Increase `PARALLEL_WORKERS` to match CPU cores

**Out of memory**:
- Reduce `MAX_FILE_SIZE_MB`
- Process fewer documents at once
- Reduce `MAX_CHUNK_SIZE` if using RAG

## Best Practices

1. **Start simple**: Use default settings initially
2. **Enable features gradually**: Add RAG, Chat, Validation one at a time
3. **Monitor performance**: Check processing times and adjust workers
4. **Secure your keys**: Never commit `.env` to version control
5. **Use OCR sparingly**: Only enable for scanned documents

## Example Configurations

### Minimal (Fast, Basic Features)

```env
GOOGLE_API_KEY=your_key
TAVILY_API_KEY=your_key
OPENAI_API_KEY=your_key

DOCLING_OCR_DEFAULT=false
DOCLING_TABLE_MODE=fast
ENABLE_DIAGRAM_GENERATION=false
ENABLE_RAG=false
ENABLE_CHAT=false
```

### Full-Featured (All Features)

```env
GOOGLE_API_KEY=your_key
TAVILY_API_KEY=your_key
OPENAI_API_KEY=your_key

DOCLING_OCR_DEFAULT=false
DOCLING_TABLE_MODE=accurate
ENABLE_DIAGRAM_GENERATION=true
ENABLE_RAG=true
ENABLE_CHAT=true
ENABLE_VALIDATION=true
PARALLEL_WORKERS=8
```

### Scanned Documents (OCR Enabled)

```env
GOOGLE_API_KEY=your_key
TAVILY_API_KEY=your_key
OPENAI_API_KEY=your_key

DOCLING_OCR_DEFAULT=true  # Enable OCR
DOCLING_TABLE_MODE=accurate  # Better for scanned tables
MAX_FILE_SIZE_MB=25  # Smaller limit (OCR is memory-intensive)
PARALLEL_WORKERS=2  # Fewer workers (OCR is CPU-intensive)
```

## Getting Help

- Check [README.md](../README.md) for general setup
- See [DOCLING_GUIDE.md](./DOCLING_GUIDE.md) for document processing details
- See [RAG_GUIDE.md](./RAG_GUIDE.md) for RAG setup (if enabled)
- Open an issue on GitHub for problems




