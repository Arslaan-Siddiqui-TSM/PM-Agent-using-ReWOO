# 📐 Parsing & Embedding Architecture

## 🎯 Clean Separation of Concerns

The codebase follows a clear separation between **parsing** and **embedding**:

```
┌─────────────────────────────────────────────────────────────────┐
│                       Document Processing Pipeline               │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   PDF Files  │  ────>  │  Markdown    │  ────>  │   Qdrant     │
│  (.pdf)      │         │  Files (.md) │         │  Embeddings  │
└──────────────┘         └──────────────┘         └──────────────┘
       │                        │                         │
       ▼                        ▼                         ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ ParsingHandler  │    │  (File System)  │    │EmbeddingHandler │
│                 │    │                 │    │                 │
│ - PDF → MD      │    │  MD files are   │    │ - MD → Vectors  │
│ - PyMuPDF       │    │  stored here    │    │ - OpenAI API    │
│ - Docling       │    │  and passed     │    │ - Qdrant        │
│ - Caching       │    │  between stages │    │ - Caching       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

---

## 📁 File Structure

### Core Modules

```
src/core/
├── intelligent_document_parser.py  # Core parsing logic (PyMuPDF + Docling)
├── parsing_handler.py             # PDF → MD workflow orchestration
├── embedding_handler.py           # MD → Qdrant workflow orchestration
├── embedding_cache_manager.py     # Global cache for both handlers
└── qdrant_manager.py              # Qdrant vector store interface
```

---

## 🔧 Module Responsibilities

### 1. `intelligent_document_parser.py`
**Role:** Core PDF parsing implementation

**Responsibilities:**
- ✅ Analyze PDF complexity (images, tables, layout)
- ✅ Route to PyMuPDF (fast) or Docling (accurate)
- ✅ Extract text and convert to markdown
- ✅ Save `.md` files to `output/session_xxx/raw/`

**Does NOT:**
- ❌ Handle embeddings
- ❌ Store in Qdrant
- ❌ Manage caching (delegated to handler)

**Example:**
```python
from src.core.intelligent_document_parser import IntelligentDocumentParser

parser = IntelligentDocumentParser(session_id="abc123")
doc = parser.parse_document("document.pdf")
# Output: document.md saved to output/session_abc123/raw/
```

---

### 2. `parsing_handler.py`
**Role:** Orchestrate PDF → Markdown workflow

**Responsibilities:**
- ✅ Check global cache (avoid re-parsing)
- ✅ Batch process multiple PDFs
- ✅ Call `IntelligentDocumentParser` for each uncached PDF
- ✅ Track parsing statistics
- ✅ Return list of `ParsedDocument` objects with `.output_md_path`

**Does NOT:**
- ❌ Create embeddings
- ❌ Store in Qdrant
- ❌ Read existing `.md` files (only creates new ones)

**Input:** PDF file paths
**Output:** Markdown files + metadata

**Example:**
```python
from src.core.parsing_handler import ParsingHandler

handler = ParsingHandler(session_id="abc123")
result = handler.parse_documents(pdf_paths=["doc1.pdf", "doc2.pdf"])

print(result["parsed_documents"])  # List of ParsedDocument objects
print(result["cache_hits"])         # Number of cache hits
# MD files are now in: output/session_abc123/raw/*.md
```

---

### 3. `embedding_handler.py`
**Role:** Orchestrate Markdown → Qdrant workflow

**Responsibilities:**
- ✅ Read `.md` files from `ParsedDocument.output_md_path`
- ✅ Chunk markdown into smaller pieces
- ✅ Create embeddings using OpenAI API
- ✅ Store vectors in Qdrant collection
- ✅ Use global cache for duplicate documents

**Does NOT:**
- ❌ Parse PDFs
- ❌ Create `.md` files
- ❌ Handle PDF complexity analysis

**Input:** List of `ParsedDocument` objects (with `.output_md_path`)
**Output:** Qdrant collection with embeddings

**Example:**
```python
from src.core.embedding_handler import EmbeddingHandler

handler = EmbeddingHandler(session_id="abc123")
result = handler.embed_documents(
    parsed_documents=parsed_docs,  # From parsing_handler
    cached_documents_info=cached_info
)

print(result["collection_name"])   # "pm_agent_abc123"
print(result["qdrant_stats"])      # Embedding statistics
# Embeddings are now in Qdrant!
```

---

## 🔄 Complete Workflow

### Step-by-Step Process

```python
from src.core.parsing_handler import ParsingHandler
from src.core.embedding_handler import EmbeddingHandler

# ========================================
# STEP 1: Parse PDFs to Markdown
# ========================================
parsing_handler = ParsingHandler(session_id="demo_session")

parsing_result = parsing_handler.parse_documents(
    pdf_paths=[
        "data/files/Functional Specification.pdf",
        "data/files/Technical Specification.pdf",
    ]
)

# Result:
# - Markdown files created in: output/session_demo_session/raw/
# - parsed_documents: [ParsedDocument(...), ParsedDocument(...)]
# - Each ParsedDocument has .output_md_path pointing to the .md file

print(f"Parsed {len(parsing_result['parsed_documents'])} documents")
print(f"Cache hits: {parsing_result['cache_hits']}")

# ========================================
# STEP 2: Embed Markdown to Qdrant
# ========================================
embedding_handler = EmbeddingHandler(session_id="demo_session")

embedding_result = embedding_handler.embed_documents(
    parsed_documents=parsing_result["parsed_documents"],
    cached_documents_info=parsing_result["cached_documents_info"]
)

# Result:
# - Embeddings stored in Qdrant collection: "pm_agent_demo_ses"
# - qdrant_manager: QdrantManager instance for querying
# - qdrant_stats: Statistics about embedding creation

print(f"Collection: {embedding_result['collection_name']}")
print(f"Chunks added: {embedding_result['qdrant_stats']['chunks_added']}")
```

---

## 🗂️ Data Flow

### 1. Parsing Stage (PDF → MD)

```
Input:  data/files/*.pdf
        │
        ▼
   ParsingHandler
        │
        ├─ Check cache (SHA256 hash)
        │  ├─ Cache HIT → Skip parsing
        │  └─ Cache MISS → Call IntelligentDocumentParser
        │
        ├─ IntelligentDocumentParser
        │  ├─ Analyze PDF complexity
        │  ├─ Route to PyMuPDF or Docling
        │  └─ Convert to Markdown
        │
        ▼
Output: output/session_xxx/raw/*.md
        ParsedDocument objects with .output_md_path
```

### 2. Embedding Stage (MD → Qdrant)

```
Input:  ParsedDocument objects (contain .output_md_path)
        │
        ▼
   EmbeddingHandler
        │
        ├─ Read MD files from .output_md_path
        │
        ├─ Check cache (SHA256 hash)
        │  ├─ Cache HIT → Copy existing embeddings
        │  └─ Cache MISS → Create new embeddings
        │
        ├─ QdrantManager
        │  ├─ Chunk markdown text
        │  ├─ Call OpenAI embedding API
        │  └─ Store vectors in Qdrant
        │
        ▼
Output: Qdrant collection: pm_agent_xxx
        Vector embeddings ready for search
```

---

## 🎨 Benefits of This Architecture

### ✅ Separation of Concerns
- **Parsing** and **Embedding** are completely independent
- Can test/debug each stage separately
- Can swap out Docling for another parser without touching embedding code

### ✅ Reusability
- Parse once → Embed multiple times (different chunk sizes)
- Parse once → Use MD files for other purposes (documentation, analysis)
- Embed once → Query many times

### ✅ Performance
- **Global caching** at both stages
- Skip parsing if PDF already processed
- Skip embedding if document already embedded
- Parallel processing possible (parse in batch, embed in batch)

### ✅ Clear Data Flow
- MD files are the **contract** between stages
- Easy to debug: Check MD files between stages
- Easy to monitor: Watch `output/session_xxx/raw/` folder

---

## 🔍 Debugging

### Check Parsing Output
```bash
# After parsing, check MD files:
ls output/session_*/raw/*.md

# Check parsing logs:
cat output/session_*/metadata/parsing_log.json
```

### Check Embedding Output
```bash
# Check Qdrant collections:
curl http://localhost:6333/collections

# Check collection details:
curl http://localhost:6333/collections/pm_agent_xxx

# View Qdrant dashboard:
# Open: http://localhost:6333/dashboard
```

---

## 📊 Cache System

Both handlers use a **shared global cache** via `EmbeddingCacheManager`:

```
data/embedding_cache/
├── metadata/
│   ├── document_cache.json       # PDF parsing cache
│   └── embedding_cache.json      # Embedding cache
└── sessions/
    └── session_usage.json        # Track which sessions used which docs
```

**Cache Key:** SHA-256 hash of PDF file
**Benefits:**
- Upload same PDF in different sessions → Instant (cache hit)
- Re-parse after crash → Resume from cache
- Track document reuse across sessions

---

## 🎯 Summary

| Module | Input | Output | Purpose |
|--------|-------|--------|---------|
| **intelligent_document_parser.py** | PDF file path | ParsedDocument + .md file | Core parsing logic |
| **parsing_handler.py** | List of PDF paths | List of ParsedDocument | Orchestrate PDF → MD |
| **embedding_handler.py** | List of ParsedDocument | Qdrant collection | Orchestrate MD → Vectors |

**Data Contract:** `ParsedDocument.output_md_path` is the link between parsing and embedding!

---

**Last Updated:** 2025-11-04  
**Architecture:** Fully Separated Parsing & Embedding

