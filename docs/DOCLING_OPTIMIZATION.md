# 🚀 Docling Optimization Guide

## ⚡ Why is Docling Slow?

Docling is **comprehensive but resource-intensive**:
- ✅ **Pros**: Handles complex PDFs (tables, images, layouts)
- ❌ **Cons**: Slow for large/complex documents (30-120s per PDF)

**Common causes of slowness**:
1. Complex PDF layouts (multi-column, nested tables)
2. High-resolution images and graphics
3. Large document size (>50 pages)
4. OCR processing for scanned documents
5. Memory limitations

---

## 🎯 Optimization Techniques

### 1. **Timeout Protection** ✅ (Implemented)

**Location**: `src/core/intelligent_document_parser.py`

```python
# Adjust timeout based on your document complexity
DOCLING_TIMEOUT = 120  # 2 minutes per PDF
```

**Recommendations**:
- Simple docs (<10 pages): `DOCLING_TIMEOUT = 60`
- Medium docs (10-50 pages): `DOCLING_TIMEOUT = 120`
- Complex docs (>50 pages): `DOCLING_TIMEOUT = 300`

---

### 2. **Image Processing Optimization**

**Current Settings**:
```python
DOCLING_MAX_IMAGE_SIZE = 1024  # Reduce image processing overhead
DOCLING_SKIP_EMBEDDED_IMAGES = False  # Set to True for faster parsing
```

**Fast Mode (Skip Images)**:
```python
DOCLING_SKIP_EMBEDDED_IMAGES = True  # Faster, but loses image content
```

**Optimization Levels**:
- **Ultra-Fast**: Skip images entirely
- **Balanced**: Resize images to 1024px (current)
- **High-Quality**: Keep original image resolution (slow)

---

### 3. **Intelligent Routing** ✅ (Implemented)

**How it works**:
1. Analyze PDF complexity score
2. Simple PDFs → PyMuPDF (fast, 1-2s)
3. Complex PDFs → Docling (slow, 30-120s)

**Adjust complexity threshold**:
```python
# In src/core/parsing_handler.py
ParsingHandler(
    complexity_threshold=0.3,  # Lower = more PyMuPDF usage
    force_docling=False        # Override intelligent routing
)
```

**Threshold Recommendations**:
- `0.2`: Aggressive PyMuPDF (faster, less accurate)
- `0.3`: Balanced (current, recommended)
- `0.5`: Conservative (slower, more Docling usage)

---

### 4. **Caching** ✅ (Implemented)

**Global cache** avoids re-parsing the same PDFs:
- Cache location: `data/embedding_cache/`
- Cache key: SHA-256 hash of PDF file

**How to use**:
```python
# First upload: Slow (parses all PDFs)
POST /upload → 6 PDFs × 60s = 6 minutes

# Second upload (same files): Instant
POST /upload → Cache hits → <1 second
```

**Force re-parse** (bypass cache):
```python
POST /generate-embeddings
{
  "session_id": "xxx",
  "force_reprocess": true  # Re-parse everything
}
```

---

### 5. **Parallel Processing**

**Current**: Sequential (1 PDF at a time)
**Optimization**: Parallel processing

**Implementation** (add to `parse_batch`):
```python
from concurrent.futures import ThreadPoolExecutor

def parse_batch_parallel(self, pdf_paths: List[str]) -> List[ParsedDocument]:
    """Parse multiple PDFs in parallel"""
    with ThreadPoolExecutor(max_workers=DOCLING_PARALLEL_WORKERS) as executor:
        futures = {executor.submit(self.parse_document, pdf): pdf for pdf in pdf_paths}
        
        parsed_docs = []
        for future in concurrent.futures.as_completed(futures):
            try:
                doc = future.result()
                parsed_docs.append(doc)
            except Exception as e:
                logger.error(f"Failed: {e}")
        
        return parsed_docs
```

**Warnings**:
- ⚠️ High memory usage (each worker loads full Docling model)
- ⚠️ May crash on limited RAM systems
- ✅ Good for powerful servers with 16GB+ RAM

---

### 6. **Async Background Processing** ✅ (Implemented)

**How it works**:
1. Frontend uploads files → immediate response
2. Backend processes in background thread
3. Frontend polls `/upload-status/{session_id}` for progress

**User experience**:
- ❌ Before: Frontend blocked for 6+ minutes
- ✅ After: Frontend returns instantly, shows progress

---

### 7. **Pre-process PDFs**

**External optimization** (before upload):
1. **Compress PDFs**: Use Adobe Acrobat or `ghostscript`
   ```bash
   gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
      -dNOPAUSE -dQUIET -dBATCH \
      -sOutputFile=output.pdf input.pdf
   ```

2. **Remove images**: For text-only analysis
   ```bash
   pdf2ps input.pdf - | ps2pdf - output.pdf
   ```

3. **Split large PDFs**: Process in smaller chunks
   ```bash
   pdftk input.pdf burst output page_%02d.pdf
   ```

---

### 8. **Use PyMuPDF for Speed**

**When your documents are simple**:
```python
# Force PyMuPDF for all documents (fastest)
ParsingHandler(
    force_pymupdf=True  # Skip Docling entirely
)
```

**Speed comparison**:
- PyMuPDF: 1-2 seconds per PDF ⚡
- Docling: 30-120 seconds per PDF 🐌

**Trade-off**:
- ✅ Faster
- ❌ Loses tables, images, complex layouts

---

### 9. **Docling Configuration Options**

**Advanced settings** (modify `DoclingLoader` initialization):
```python
from docling.document_converter import DocumentConverter, PdfFormatOption

# Custom Docling configuration
pdf_options = PdfFormatOption(
    pipeline_options={
        "do_ocr": False,              # Disable OCR (faster)
        "do_table_structure": True,    # Keep table detection
        "images_scale": 0.5,           # Reduce image resolution
        "accelerator_device": "cpu"    # Or "cuda" for GPU
    }
)

converter = DocumentConverter(
    allowed_formats=[InputFormat.PDF],
    format_options={InputFormat.PDF: pdf_options}
)
```

**GPU Acceleration** (if available):
```python
"accelerator_device": "cuda"  # 2-5x faster with NVIDIA GPU
```

---

## 📊 Performance Benchmarks

### Current Performance (6 PDFs)
| Method | Time | Cache | Notes |
|--------|------|-------|-------|
| **First upload (cache miss)** | 6-10 min | ❌ | All PDFs parsed with Docling |
| **Repeat upload (cache hit)** | <1 sec | ✅ | Reuses cached results |
| **PyMuPDF forced** | 10-15 sec | ❌ | Fast but loses complex content |

### Optimization Impact
| Optimization | Speed Improvement | Implementation |
|--------------|-------------------|----------------|
| **Caching** | 99% faster | ✅ Implemented |
| **Async processing** | UX improvement | ✅ Implemented |
| **Timeout protection** | Prevents hanging | ✅ Implemented |
| **Intelligent routing** | 50-70% faster | ✅ Implemented |
| **Parallel processing** | 2-3x faster | ⚠️ Optional (high RAM) |
| **GPU acceleration** | 2-5x faster | ⚠️ Requires NVIDIA GPU |

---

## 🎛️ Quick Settings Reference

### Fast Mode (Speed Priority)
```python
# In src/core/intelligent_document_parser.py
DOCLING_TIMEOUT = 60
DOCLING_SKIP_EMBEDDED_IMAGES = True

# In src/core/parsing_handler.py
ParsingHandler(
    complexity_threshold=0.2,  # Use PyMuPDF more often
    force_pymupdf=False         # Keep intelligent routing
)
```

### Quality Mode (Accuracy Priority)
```python
# In src/core/intelligent_document_parser.py
DOCLING_TIMEOUT = 300
DOCLING_SKIP_EMBEDDED_IMAGES = False

# In src/core/parsing_handler.py
ParsingHandler(
    complexity_threshold=0.5,  # Use Docling more often
    force_docling=False        # Keep intelligent routing
)
```

### Balanced Mode (Recommended)
```python
# In src/core/intelligent_document_parser.py
DOCLING_TIMEOUT = 120
DOCLING_SKIP_EMBEDDED_IMAGES = False

# In src/core/parsing_handler.py
ParsingHandler(
    complexity_threshold=0.3,  # Current settings
    force_docling=False
)
```

---

## 🔧 Troubleshooting

### Issue: Docling hangs/takes forever
**Solution**: 
1. Check terminal logs for which PDF is stuck
2. Increase `DOCLING_TIMEOUT` or skip that PDF
3. Try forcing PyMuPDF for that specific document

### Issue: Out of memory errors
**Solution**:
1. Reduce `DOCLING_PARALLEL_WORKERS` to 1
2. Enable `DOCLING_SKIP_EMBEDDED_IMAGES = True`
3. Process PDFs in smaller batches

### Issue: Poor extraction quality
**Solution**:
1. Increase `complexity_threshold` to use Docling more
2. Disable `DOCLING_SKIP_EMBEDDED_IMAGES`
3. Increase `DOCLING_TIMEOUT` for complex docs

---

## 📝 Recommended Workflow

1. **First time**: Use default settings, let cache build
2. **Subsequent uploads**: Benefit from instant cache hits
3. **Complex docs**: Increase timeout to 300s
4. **Simple docs**: Lower complexity threshold to 0.2
5. **Production**: Enable GPU acceleration if available

---

## 🚀 Next Steps

1. ✅ Monitor first parsing run (use terminal logs)
2. ✅ Verify cache is working (check `data/embedding_cache/`)
3. ✅ Adjust settings based on your document types
4. ⚠️ Consider GPU acceleration for high-volume workloads
5. ⚠️ Implement parallel processing if you have sufficient RAM

---

**Last Updated**: 2025-11-04  
**Docling Version**: Latest (LangChain integration)

