# Quick Start Guide - Qdrant RAG Pipeline

Get up and running in **5 minutes**!

## Prerequisites

- Python 3.10+
- Docker Desktop
- OpenAI API key
- Google Gemini API key (optional)

---

## Step-by-Step Setup

### 1️⃣ Install Dependencies (2 min)

```bash
# Upgrade pip first
python -m pip install --upgrade pip

# Install all requirements
pip install -r requirements.txt
```

**Expected output:** ~50 packages installed successfully

---

### 2️⃣ Start Qdrant (30 sec)

```bash
# Start Qdrant container
docker-compose up -d qdrant

# Verify it's running
curl http://localhost:6333/healthz
```

**Expected output:** `{"title":"healthz","version":"1.x.x"}`

---

### 3️⃣ Configure API Keys (1 min)

Create `.env` file in project root:

```env
OPENAI_API_KEY=sk-your-openai-key-here
GOOGLE_API_KEY=your-google-key-here
QDRANT_URL=http://localhost:6333
EMBEDDING_MODEL=text-embedding-3-large
```

**Get API keys:**
- OpenAI: https://platform.openai.com/api-keys
- Google Gemini: https://aistudio.google.com/app/apikey

---

### 4️⃣ Validate Setup (30 sec)

```bash
python init_qdrant.py
```

**Expected output:**
```
=====================================
  Qdrant RAG Setup - Initialization Check
=====================================

✅ PASS: Docker
✅ PASS: Qdrant
✅ PASS: Folders
✅ PASS: Cache
✅ PASS: Dependencies
✅ PASS: Environment

6 passed, 0 failed, 0 warnings

🎉 All critical checks passed!
```

---

### 5️⃣ Run Tests (1 min)

```bash
python test_qdrant_migration.py
```

**Expected output:**
```
TEST SUMMARY
✅ PASSED: Qdrant Connection
✅ PASSED: Embedding Cache
✅ PASSED: Intelligent Parsing
✅ PASSED: Qdrant Ingestion
✅ PASSED: Full Pipeline
✅ PASSED: Cache Reuse

Results: 6/6 tests passed

🎉 All tests passed! Qdrant migration successful!
```

---

### 6️⃣ Start Server (10 sec)

```bash
python server.py
```

**Expected output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete.
```

Server is now running! 🚀

---

## First API Call

### Upload Documents (Automatic RAG Processing)

```bash
curl -X POST "http://localhost:8000/api/upload?use_default_files=true"
```

**Response:**
```json
{
  "session_id": "abc12345-1234-1234-1234-123456789abc",
  "message": "Processed 6 files with RAG pipeline. Created 58 vector embeddings. Cache hits: 0/6.",
  "uploaded_files": [
    "Functional Specification Document.pdf",
    "Technical Specification Document.pdf",
    "Non-Functional Requirement Document.pdf",
    "online_apparels_shopping_website.pdf",
    "Test Plan.pdf",
    "Use Case.pdf"
  ],
  "total_files": 6
}
```

**What just happened:**
1. ✅ 6 PDFs uploaded
2. ✅ Documents analyzed for complexity
3. ✅ Parsed to markdown (simple → PyMuPDF, complex → Docling)
4. ✅ 58 chunks created
5. ✅ Embeddings generated (OpenAI)
6. ✅ Stored in Qdrant vector database
7. ✅ Cached for future reuse

---

## Verify It Worked

### Check Parsed Markdown Files

```bash
# Windows
dir parsed_documents\session_*\raw\*.md

# Expected: 6 markdown files
```

### Check Qdrant Collections

```bash
curl http://localhost:6333/collections
```

**Expected:** Collection named `pm_agent_<session_id>` with ~58 vectors

### Check Cache

```bash
# Windows
type embedding_cache\index.json
```

**Expected:** JSON with 6 cached documents

---

## Test Cache Reuse

Upload the same files again:

```bash
curl -X POST "http://localhost:8000/api/upload?use_default_files=true"
```

**Response:**
```json
{
  "message": "... Cache hits: 6/6. ..."
}
```

**Processing time:** ~90% faster (5 seconds instead of 45 seconds)!

---

## View API Documentation

Open browser: http://localhost:8000/docs

Interactive API documentation with:
- `/api/upload` - Upload documents
- `/api/generate-embeddings` - Manual embedding generation
- `/api/feasibility` - Feasibility assessment
- `/api/generate-plan` - Project plan generation

---

## Troubleshooting Quick Fixes

### ❌ "ModuleNotFoundError: No module named 'fitz'"

```bash
pip install pymupdf==1.26.5
```

### ❌ "Failed to connect to Qdrant"

```bash
docker-compose up -d qdrant
```

### ❌ "OPENAI_API_KEY not set"

Create `.env` file with your API key

### ❌ "Docker not running"

Start Docker Desktop application

---

## What's Next?

### Explore the Pipeline

1. **Check parsed documents:**
   - Look in `parsed_documents/session_*/raw/`
   - Open a `.md` file to see parsed content

2. **View logs:**
   - Parsing: `parsed_documents/session_*/metadata/parsing_log.json`
   - Errors: `logs/parsing_errors.log`

3. **Query Qdrant:**
   ```python
   from core.qdrant_manager import QdrantManager
   manager = QdrantManager(session_id="your-session-id")
   results = manager.query("system requirements", k=5)
   ```

### Run Full Feasibility Check

```bash
curl -X POST "http://localhost:8000/api/feasibility" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"<your-session-id>\", \"use_intelligent_processing\": true}"
```

### Generate Project Plan

```bash
curl -X POST "http://localhost:8000/api/generate-plan" \
  -H "Content-Type: application/json" \
  -d "{\"session_id\": \"<your-session-id>\", \"use_intelligent_processing\": true, \"max_iterations\": 5}"
```

---

## Performance Benchmarks

### First Upload (6 documents)
- **Time:** ~45 seconds
- **Parsing:** 3 simple (PyMuPDF) + 3 complex (Docling)
- **Chunks:** 58
- **Cost:** ~$0.03 (OpenAI embeddings)

### Cached Upload (same 6 documents)
- **Time:** ~5 seconds (90% faster!)
- **Parsing:** Skipped (from cache)
- **Chunks:** 58 (copied from cache)
- **Cost:** $0.00 (no API calls!)

---

## Success! 🎉

You now have a fully functional Qdrant RAG pipeline with:

✅ Intelligent document parsing  
✅ Global embedding cache  
✅ Semantic search capabilities  
✅ Persistent markdown storage  
✅ Session isolation  
✅ Graceful error handling  

**Total setup time:** ~5 minutes

---

## Documentation

- **Full Guide:** `IMPLEMENTATION_SUMMARY.md`
- **Docker Setup:** `DOCKER_SETUP.md`
- **Error Fixes:** `ERROR_FIXES.md`
- **Migration Details:** `QDRANT_MIGRATION_COMPLETE.md`

---

## Need Help?

1. Run validation: `python init_qdrant.py`
2. Check errors: `type ERROR_FIXES.md`
3. View logs: `type logs\parsing_errors.log`
4. Run tests: `python test_qdrant_migration.py`

**Stuck?** Check `ERROR_FIXES.md` for solutions to common issues.


