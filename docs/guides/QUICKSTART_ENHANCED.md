# Quick Start Guide - Enhanced PM Agent

Get started with the enhanced PM Agent featuring multi-format document processing, diagram generation, and RAG-powered search.

## 🚀 Installation

### Prerequisites

- Python 3.10+
- Node.js 16+
- OpenAI API Key (for embeddings)
- Google Gemini API Key (for LLM)
- Tavily API Key (for web search)

### Step 1: Clone and Setup Backend

```bash
# Navigate to project root
cd PM-Agent-using-ReWOO

# Install Python dependencies
pip install -r requirements.txt

# Or use uv for faster installation
uv pip install -r requirements.txt
```

### Step 2: Configure Environment

Create a `.env` file in the project root:

```env
# Required API Keys
GOOGLE_API_KEY=your_google_gemini_api_key
TAVILY_API_KEY=your_tavily_api_key  
OPENAI_API_KEY=your_openai_api_key

# Docling Configuration (Recommended Defaults)
DOCLING_OCR_DEFAULT=false
DOCLING_TABLE_MODE=fast
DOCLING_EXPORT_FORMAT=markdown
DOCLING_TABLE_EXTRACTION=true

# Optional: Enable Advanced Features
ENABLE_DIAGRAM_GENERATION=false  # Set true to test diagrams
ENABLE_RAG=false  # Set true for semantic search
ENABLE_CHAT=false  # Set true for chat (requires RAG)

# RAG/Embedding Configuration (if enabled)
EMBEDDING_MODEL=text-embedding-3-large
CHROMA_PERSIST_DIRECTORY=./chroma_db
MAX_CHUNK_SIZE=1000
CHUNK_OVERLAP=200

# Kroki (FREE - No API key needed!)
KROKI_URL=https://kroki.io

# Performance
MAX_FILE_SIZE_MB=50
PARALLEL_WORKERS=4
```

See [`docs/ENV_CONFIGURATION.md`](./ENV_CONFIGURATION.md) for detailed configuration options.

### Step 3: Setup Frontend

```bash
cd frontend
npm install
```

### Step 4: Start Services

**Terminal 1 - Backend:**
```bash
# From project root
python server.py

# Expected output:
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Terminal 2 - Frontend:**
```bash
# From frontend directory
npm run dev

# Expected output:
# ➜  Local:   http://localhost:5173/
```

---

## 🎯 Testing New Features

### 1. Multi-Format Document Upload

**What's New**: Upload 15+ file formats (not just PDF)

**Supported Formats**:
- Documents: PDF, DOCX, PPTX, XLSX, XLS
- Images: PNG, JPG, JPEG, TIFF, BMP
- Text: HTML, MD, TXT, ASCIIDOC

**How to Test**:

1. Go to `http://localhost:5173`
2. Uncheck "Use default sample files"
3. Click file input (now accepts multiple formats)
4. Select multiple files of different types
5. See file list with sizes
6. Configure processing options:
   - **OCR**: Check only if you have scanned docs/images
   - **Table Mode**: Keep "Fast" unless you have complex tables
7. Click "Upload & Continue"

**Expected Result**:
- All formats processed successfully
- Console shows: `Processing 'filename.ext' with Docling...`
- Processing is 30-50% faster than before

---

### 2. Diagram Generation

**What's New**: Auto-generate visual diagrams from plans

**Diagram Types**:
- Gantt charts (timelines)
- Dependency graphs
- BPMN workflows
- Sequence diagrams
- ERDs
- Component diagrams
- Flowcharts

**How to Test**:

#### Option A: Via API (Postman/curl)

```bash
# After uploading documents and completing feasibility
curl -X POST http://localhost:8000/generate-plan \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "your_session_id",
    "use_intelligent_processing": true,
    "max_iterations": 5,
    "enable_diagrams": true,
    "diagram_types": ["gantt", "graph", "component"]
  }'
```

#### Option B: Via Frontend (Future - Not Yet Implemented)

The frontend UI for diagram selection will be added in Phase 7.

**Expected Result**:
- Response includes `diagrams` array with data URLs
- Final plan markdown has embedded diagrams
- Console shows: `Successfully generated N diagrams`

**Example Response**:
```json
{
  "diagrams": [
    {
      "type": "gantt",
      "title": "Project Timeline",
      "description": "4 phases over 9 months",
      "url": "data:image/svg+base64,...",
      "source_code": "gantt\n  title..."
    }
  ]
}
```

---

### 3. RAG-Powered Search

**What's New**: Semantic search across all uploaded documents

**Requirements**:
- Set `ENABLE_RAG=true` in `.env`
- Ensure `OPENAI_API_KEY` is set (for embeddings)

**How to Test**:

#### Python Test Script:

```python
import asyncio
from core.rag_manager import RAGManager
from agents.docling_processor import DoclingProcessor, DoclingConfig

async def test_rag():
    # 1. Process documents
    processor = DoclingProcessor(DoclingConfig())
    
    doc1 = processor.process_document("files/Functional Specification Document.pdf")
    doc2 = processor.process_document("files/Technical Specification Document.pdf")
    
    # 2. Initialize RAG
    rag = RAGManager(session_id="test_session_123")
    
    # 3. Ingest documents
    chunks_indexed = await rag.ingest_documents([doc1, doc2])
    print(f"Indexed {chunks_indexed} chunks")
    
    # 4. Query
    results = await rag.query("What are the authentication requirements?", top_k=5)
    
    for i, result in enumerate(results, 1):
        print(f"\n{i}. From {result['source']}:")
        print(f"   {result['content'][:200]}...")
        if 'relevance_score' in result:
            print(f"   Score: {result['relevance_score']:.3f}")
    
    # 5. Get stats
    stats = rag.get_stats()
    print(f"\nStats: {stats}")
    
    # 6. Cleanup
    rag.cleanup()

# Run
asyncio.run(test_rag())
```

**Expected Output**:
```
Indexed 127 chunks
1. From Functional Specification Document.pdf:
   Authentication requirements include JWT-based auth, OAuth2 support, and multi-factor authentication...
   Score: 0.892

Stats: {'total_chunks': 127, 'num_documents': 2, ...}
```

---

## 🧪 Verification Checklist

### Core Functionality (Existing Features)

- [ ] Upload PDF documents
- [ ] Answer development process questions
- [ ] Generate feasibility assessment
- [ ] Review feasibility and provide feedback
- [ ] Generate final project plan
- [ ] Plan includes all required sections
- [ ] Plan file saved to `outputs/` directory

### New Features (Phase 1-3)

- [ ] Upload non-PDF documents (DOCX, PPTX, XLSX, images)
- [ ] Multiple files uploaded at once
- [ ] OCR toggle works (test with scanned doc)
- [ ] Table mode selection works
- [ ] Processing is faster than before
- [ ] Diagrams generated (if enabled)
- [ ] Diagrams embedded in plan
- [ ] RAG indexing works (if enabled)
- [ ] RAG queries return relevant results
- [ ] No regressions in existing features

---

## 🐛 Troubleshooting

### "Docling model not found" on First Run

**Issue**: Table extraction downloads ML models (~100MB) on first use

**Solution**: Wait for download to complete (one-time only)

```bash
# Check logs:
# Downloading models...
# Model cached at: ~/.cache/docling/...
```

---

### "Failed to initialize OpenAI embeddings"

**Issue**: RAG enabled but OPENAI_API_KEY not set

**Solution**: 
1. Set OPENAI_API_KEY in `.env`
2. Or disable RAG: `ENABLE_RAG=false`

---

### "OCR processing is very slow"

**Issue**: OCR is CPU/memory intensive

**Solution**: 
- Only enable OCR for scanned documents/images
- Keep OCR disabled (default) for digital documents
- Reduce parallel workers if out of memory

---

### Frontend file upload fails with "Unsupported format"

**Issue**: File extension not in allowed list

**Check**:
- Backend allows: `.pdf, .docx, .pptx, .xlsx, .xls, .png, .jpg, .jpeg, .tiff, .bmp, .html, .htm, .md, .txt, .asciidoc`
- Frontend accepts same formats

**Solution**: Ensure backend and frontend accept lists match

---

### Diagrams not appearing

**Issue**: Diagrams disabled or generation failed

**Check**:
1. Is `enable_diagrams=true` in request?
2. Check backend logs for diagram generation errors
3. Verify Kroki.io is accessible: `curl https://kroki.io/health`

**Solution**: 
- Enable diagrams in request
- Check internet connection (Kroki.io is external)
- Diagrams fail gracefully (won't break plan generation)

---

## 📊 Performance Expectations

### Document Processing Time

| File Type | Size | PyMuPDF (Old) | Docling (New) | Improvement |
|-----------|------|---------------|---------------|-------------|
| PDF (text) | 10 pages | 5-10s | 2-5s | ~50% faster |
| PDF (scanned) | 10 pages | N/A | 30-60s (OCR) | New capability |
| DOCX | 20 pages | N/A | 1-3s | New capability |
| XLSX | 5 sheets | N/A | 2-4s | New capability |
| PNG (OCR) | 1 image | N/A | 10-20s | New capability |

### Diagram Generation

- 3-4 diagrams: 5-15 seconds
- Depends on LLM speed and Kroki.io response time

### RAG Indexing

- ~0.5 seconds per chunk (OpenAI embedding API)
- 100-page document → ~100 chunks → ~50 seconds
- Queries: <1 second

---

## 🎉 What's Next?

After verifying the implemented features, consider enabling:

### Phase 4: Validation Agent
- Automatic plan quality checks
- Completeness validation
- Dependency analysis

### Phase 5: Chat Interface
- Interactive plan refinement
- Document Q&A
- Conversational edits

### Phase 7: Advanced Frontend
- Diagram viewer with zoom/download
- Chat UI component
- Section-by-section plan editor

See [`docs/IMPLEMENTATION_STATUS.md`](./IMPLEMENTATION_STATUS.md) for full roadmap.

---

## 🆘 Getting Help

- Check [`docs/ENV_CONFIGURATION.md`](./ENV_CONFIGURATION.md) for configuration details
- See [`docs/IMPLEMENTATION_STATUS.md`](./IMPLEMENTATION_STATUS.md) for feature status
- Review backend logs in terminal for detailed error messages
- Open an issue on GitHub with error logs and environment info

---

**Ready to Test?** Start both services and visit `http://localhost:5173`! 🚀





