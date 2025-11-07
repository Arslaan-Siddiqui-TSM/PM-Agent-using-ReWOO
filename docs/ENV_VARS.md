# Environment Variables Configuration

Complete guide to configuring your `.env` file for the PM Agent using ReWOO.

## Quick Start Templates

### Option 1: NVIDIA NIM (Recommended for NVIDIA Credits)

```env
# ============ PRIMARY LLM PROVIDER ============
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-your-key-here
NVIDIA_MODEL=qwen3-next-80b-a3b-instruct

# ============ EMBEDDING PROVIDER ============
EMBEDDING_PROVIDER=nvidia
NVIDIA_EMBEDDING_MODEL=llama-3.2-nemoretriever-1b-vlm-embed-v1

# ============ CONVERTER (MD→JSON) ============
CONVERTER_PROVIDER=nvidia
CONVERTER_MODEL=qwen3-next-80b-a3b-instruct

# ============ SEARCH & OTHER ============
TAVILY_API_KEY=tvly-your-key-here
QDRANT_URL=http://localhost:6333
```

### Option 2: OpenAI

```env
LLM_PROVIDER=openai
OPENAI_API_KEY=sk-your-key-here
OPENAI_MODEL=gpt-4o-mini

EMBEDDING_PROVIDER=openai
EMBEDDING_MODEL=text-embedding-3-large

CONVERTER_PROVIDER=openai
CONVERTER_MODEL=gpt-4o-mini

TAVILY_API_KEY=tvly-your-key-here
QDRANT_URL=http://localhost:6333
```

### Option 3: Google Gemini

```env
LLM_PROVIDER=gemini
GOOGLE_API_KEY=your-google-key-here
GEMINI_MODEL=gemini-2.5-pro

EMBEDDING_PROVIDER=gemini
GEMINI_EMBEDDING_MODEL=models/text-embedding-004

CONVERTER_PROVIDER=gemini
CONVERTER_MODEL=gemini-1.5-flash

TAVILY_API_KEY=tvly-your-key-here
QDRANT_URL=http://localhost:6333
```

### Option 4: Multi-Provider with Automatic Fallback

```env
# Primary: NVIDIA, Fallback: OpenAI → Gemini
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-your-key-here
OPENAI_API_KEY=sk-your-key-here
GOOGLE_API_KEY=your-google-key-here

# All providers configured for maximum reliability
NVIDIA_MODEL=qwen3-next-80b-a3b-instruct
OPENAI_MODEL=gpt-4o-mini
GEMINI_MODEL=gemini-2.5-pro

EMBEDDING_PROVIDER=nvidia
NVIDIA_EMBEDDING_MODEL=llama-3.2-nemoretriever-1b-vlm-embed-v1

TAVILY_API_KEY=tvly-your-key-here
QDRANT_URL=http://localhost:6333
```

---

## Complete Variable Reference

### LLM Provider Configuration

#### `LLM_PROVIDER` (Required)
**Values:** `nvidia`, `openai`, `gemini`  
**Default:** `openai`  
**Description:** Primary LLM provider for chat/reasoning tasks. The system will automatically fall back to other configured providers if primary fails.

#### NVIDIA Configuration
- **`NVIDIA_API_KEY`** (Required if using NVIDIA)
  - Get from: https://build.nvidia.com/
  - Format: `nvapi-xxxxx`
  
- **`NVIDIA_MODEL`** (Optional)
  - Default: `qwen3-next-80b-a3b-instruct`
  - Other options: `meta/llama-3.1-405b-instruct`, `mistralai/mixtral-8x7b-instruct-v0.1`

#### OpenAI Configuration
- **`OPENAI_API_KEY`** (Required if using OpenAI)
  - Get from: https://platform.openai.com/api-keys
  - Format: `sk-xxxxx`
  
- **`OPENAI_MODEL`** (Optional)
  - Default: `gpt-4o-mini`
  - Other options: `gpt-4o`, `gpt-4-turbo`, `o1`, `o3-mini`

#### Google Gemini Configuration
- **`GOOGLE_API_KEY`** (Required if using Gemini)
  - Get from: https://aistudio.google.com/app/apikey
  
- **`GEMINI_MODEL`** (Optional)
  - Default: `gemini-2.5-pro`
  - Other options: `gemini-1.5-flash`, `gemini-1.5-pro`

---

### Embedding Provider Configuration

#### `EMBEDDING_PROVIDER` (Required)
**Values:** `nvidia`, `openai`, `gemini`  
**Default:** `openai`  
**Description:** Provider for vector embeddings used in RAG/semantic search.

#### NVIDIA Embeddings
- **`NVIDIA_EMBEDDING_MODEL`** (Optional)
  - Default: `llama-3.2-nemoretriever-1b-vlm-embed-v1`
  - Other options: `nvidia/nv-embedqa-e5-v5`, `nvidia/nv-embed-v1`
  - Dimensions: 2048

#### OpenAI Embeddings
- **`EMBEDDING_MODEL`** (Optional)
  - Default: `text-embedding-3-large`
  - Other options: `text-embedding-3-small`
  - Dimensions: 3072 (large), 1536 (small)

#### Gemini Embeddings
- **`GEMINI_EMBEDDING_MODEL`** (Optional)
  - Default: `models/text-embedding-004`
  - Dimensions: 768

---

### Converter Configuration (Markdown → JSON)

#### `CONVERTER_PROVIDER` (Optional)
**Values:** `nvidia`, `openai`, `gemini`  
**Default:** Same as `LLM_PROVIDER`  
**Description:** Provider for converting parsed markdown to structured JSON. Usually set to use faster/cheaper models.

#### `CONVERTER_MODEL` (Optional)
**Default:** Provider-specific mini model  
**Description:** Specific model for conversion (e.g., `gpt-4o-mini`, `gemini-1.5-flash`)

#### `USE_LLM_CONVERTER` (Optional)
**Values:** `true`, `false`  
**Default:** `true`  
**Description:** Enable/disable LLM-based markdown to JSON conversion.

---

### External Services

#### `TAVILY_API_KEY` (Required for web search)
**Description:** API key for Tavily search service  
**Get from:** https://tavily.com/

#### `QDRANT_URL` (Optional)
**Default:** `http://localhost:6333`  
**Description:** URL of Qdrant vector database server

---

### Feature Flags

#### `ENABLE_DIAGRAM_GENERATION` (Optional)
**Values:** `true`, `false`  
**Default:** `false`  
**Description:** Enable automatic diagram generation via Kroki

---

### Performance & Advanced Settings

#### `DOCLING_OCR_DEFAULT` (Optional)
**Values:** `true`, `false`  
**Default:** `false`  
**Description:** Enable OCR for scanned PDFs (heavy processing)

#### `USE_INTELLIGENT_PARSING` (Optional)
**Values:** `true`, `false`  
**Default:** `true`  
**Description:** Enable intelligent parser routing based on document complexity

#### `FORCE_DOCLING` (Optional)
**Values:** `true`, `false`  
**Default:** `false`  
**Description:** Force Docling parser for all documents (debugging)

#### `MAX_FILE_SIZE_MB` (Optional)
**Default:** `50`  
**Description:** Maximum file size for upload in MB

#### `PARALLEL_WORKERS` (Optional)
**Default:** `4`  
**Description:** Thread pool size for CPU-bound tasks

---

## Automatic Fallback Logic

The system uses **LangChain's `init_chat_model()`** with automatic fallback:

1. **Primary provider** (from `LLM_PROVIDER`) is attempted first
2. If it fails, tries **OpenAI** (if `OPENAI_API_KEY` is set)
3. If that fails, tries **Gemini** (if `GOOGLE_API_KEY` is set)
4. If that fails, tries **NVIDIA** (if `NVIDIA_API_KEY` is set)

This ensures maximum reliability across providers!

### Common Failure Scenarios
- **API key missing/invalid** → tries next provider
- **Rate limit (429)** → tries next provider
- **Network timeout** → tries next provider
- **Model not available** → tries next provider

---

## Provider Comparison

| Feature | NVIDIA NIM | OpenAI | Gemini |
|---------|-----------|--------|--------|
| **Chat Models** | ✅ Qwen3, Llama3.1 | ✅ GPT-4o, O-series | ✅ Gemini 2.5/1.5 |
| **Cost** | 💰 Credit-based | 💰💰 Pay-per-token | 💰 Free tier + pay |
| **Speed** | ⚡ Fast | ⚡⚡ Very fast | ⚡ Fast |
| **Reliability** | ✅ Good | ✅✅ Excellent | ✅ Good |
| **Context Window** | 📄 Up to 128K | 📄 Up to 128K | 📄 Up to 2M |

---

## Getting API Keys

### NVIDIA NIM
1. Visit https://build.nvidia.com/
2. Sign in with NVIDIA account
3. Browse models and generate API key
4. Copy key (format: `nvapi-xxxxx`)

### OpenAI
1. Visit https://platform.openai.com/api-keys
2. Sign in or create account
3. Click "Create new secret key"
4. Copy key (format: `sk-xxxxx`)

### Google Gemini
1. Visit https://aistudio.google.com/app/apikey
2. Sign in with Google account
3. Click "Create API key"
4. Copy key

### Tavily Search
1. Visit https://tavily.com/
2. Sign up for account
3. Get API key from dashboard
4. Copy key (format: `tvly-xxxxx`)

---

## Troubleshooting

### "Failed to initialize any LLM provider"
- Check that at least one provider's API key is correctly set
- Verify API keys are not expired or invalid
- Test API keys using provider's official documentation

### Automatic fallback not working
- Ensure multiple provider API keys are configured
- Check logs to see which providers are being tried
- Verify fallback providers have valid API keys

---

## Example Complete .env File

```env
# ============ LLM PROVIDER ============
LLM_PROVIDER=nvidia
NVIDIA_API_KEY=nvapi-ABC123XYZ
NVIDIA_MODEL=qwen3-next-80b-a3b-instruct

# Fallback providers
OPENAI_API_KEY=sk-proj-DEF456
GOOGLE_API_KEY=AIzaSyGHI789

# ============ CONVERTER ============
CONVERTER_PROVIDER=nvidia
CONVERTER_MODEL=qwen3-next-80b-a3b-instruct
USE_LLM_CONVERTER=true

# ============ EXTERNAL SERVICES ============
TAVILY_API_KEY=tvly-JKL012

# ============ FEATURE FLAGS ============
ENABLE_DIAGRAM_GENERATION=false

# ============ PERFORMANCE ============
DOCLING_OCR_DEFAULT=false
USE_INTELLIGENT_PARSING=true
FORCE_DOCLING=false
MAX_FILE_SIZE_MB=50
PARALLEL_WORKERS=4

# ============ DEVELOPMENT/TESTING MODES ============
# Hardcoded Session Mode (skip document parsing)
USE_HARDCODED_SESSION=false
HARDCODED_MD_DIR=data/hardcoded_session/markdown
HARDCODED_JSON_DIR=data/hardcoded_session/json

# Hardcoded Feasibility Mode (skip LLM calls for feasibility generation)
USE_HARDCODED_FEASIBILITY=false
HARDCODED_FEASIBILITY_THINKING_FILE=data/hardcoded_session/thinking_summary.md
HARDCODED_FEASIBILITY_REPORT_FILE=data/hardcoded_session/feasibility_report.md
```

---

## Development/Testing Modes

### Hardcoded Session Mode

**Purpose**: Skip expensive document parsing and embedding during development/testing.

**What it does**:
- Uses pre-parsed markdown files from `data/hardcoded_session/markdown/`
- Uses pre-converted JSON files from `data/hardcoded_session/json/`
- Connects to existing Qdrant collection (no embedding generation)
- Bypasses entire upload and processing pipeline

**Cost savings**: 
- Saves ~$0.10-0.50 per test run (embedding costs)
- Saves 20-60 seconds processing time per session

**How to use**:
1. Run a full session once with `USE_HARDCODED_SESSION=false`
2. Copy generated files to `data/hardcoded_session/` directories
3. Set `USE_HARDCODED_SESSION=true` in `.env`
4. All subsequent upload requests will use pre-processed files

**Variables**:
```env
USE_HARDCODED_SESSION=true
HARDCODED_COLLECTION=pm_agent_468e90d3
HARDCODED_MD_DIR=data/hardcoded_session/markdown
HARDCODED_JSON_DIR=data/hardcoded_session/json
```

### Hardcoded Feasibility Mode

**Purpose**: Skip expensive LLM calls for feasibility generation during development/testing.

**What it does**:
- Loads pre-generated thinking summary from static file
- Loads pre-generated feasibility report from static file
- Bypasses two-stage LLM generation (both Stage 1 and Stage 2)
- Returns instant results without any API calls

**Cost savings**:
- Saves ~$0.50-2.00 per test run (2 LLM calls with large context)
- Saves 30-120 seconds generation time per feasibility check
- Perfect for testing plan generation without regenerating feasibility each time

**How to use**:
1. Run feasibility once with `USE_HARDCODED_FEASIBILITY=false` to generate good outputs
2. Copy the generated files:
   ```bash
   # Windows
   copy output\session_XXX\reports\thinking_summary_XXX.md data\hardcoded_session\thinking_summary.md
   copy output\session_XXX\reports\feasibility_report_XXX.md data\hardcoded_session\feasibility_report.md
   
   # Linux/Mac
   cp output/session_XXX/reports/thinking_summary_XXX.md data/hardcoded_session/thinking_summary.md
   cp output/session_XXX/reports/feasibility_report_XXX.md data/hardcoded_session/feasibility_report.md
   ```
3. Set `USE_HARDCODED_FEASIBILITY=true` in `.env`
4. All subsequent feasibility requests will use pre-generated files

**Variables**:
```env
USE_HARDCODED_FEASIBILITY=true
HARDCODED_FEASIBILITY_THINKING_FILE=data/hardcoded_session/thinking_summary.md
HARDCODED_FEASIBILITY_REPORT_FILE=data/hardcoded_session/feasibility_report.md
```

**Best Practice**:
- Enable both hardcoded modes together for maximum cost savings during development
- Disable both for production use to ensure fresh, accurate assessments
- Update hardcoded files periodically if requirements change

**Typical Development Workflow**:
```env
# Initial setup - generate once
USE_HARDCODED_SESSION=false
USE_HARDCODED_FEASIBILITY=false

# After initial run - use for testing
USE_HARDCODED_SESSION=true
USE_HARDCODED_FEASIBILITY=true

# Production deployment
USE_HARDCODED_SESSION=false
USE_HARDCODED_FEASIBILITY=false
```

---
