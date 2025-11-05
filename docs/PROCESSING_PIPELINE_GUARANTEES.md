# Processing Pipeline Guarantees

## Sequential Processing Order

The document processing pipeline is **strictly sequential and synchronous** to ensure data consistency and prevent race conditions.

### Pipeline Steps (in order)

```
STEP 1: PDF → Markdown (Docling)
   ↓ (blocks until complete)
STEP 1.5: Markdown → JSON (LLM)
   ↓ (blocks until complete)
STEP 2: Markdown → Qdrant Embeddings
   ↓ (blocks until complete)
Session Status = "completed"
   ↓
STEP 3: Feasibility Analysis (can now proceed)
STEP 4: Plan Generation (can now proceed)
```

## Guarantees

### 1. **Synchronous Execution**
All processing steps run synchronously in the background thread:
- STEP 1 completes fully before STEP 1.5 starts
- STEP 1.5 completes fully before STEP 2 starts
- STEP 2 completes fully before session is marked "completed"

**No race conditions** - each step waits for the previous to finish.

### 2. **Status Validation**
Feasibility and Plan endpoints **require** `session.processing_status == "completed"`:

```python
# From src/routes/planning_agent.py

if session.processing_status != "completed":
    raise HTTPException(
        status_code=425,  # Too Early
        detail="Document processing is still in progress..."
    )
```

**Users cannot proceed** until all processing is complete.

### 3. **Data Validation**
Additional validation ensures required data exists:

```python
if not session.parsed_documents or not session.qdrant_manager:
    raise HTTPException(
        status_code=500,
        detail="Session processing incomplete..."
    )
```

## Processing Status States

| Status | Description | Can Generate Feasibility? | Can Generate Plan? |
|--------|-------------|---------------------------|-------------------|
| `pending` | Upload received, not started | ❌ No | ❌ No |
| `processing` | Parsing/JSON/Embedding in progress | ❌ No (returns 425) | ❌ No (returns 425) |
| `completed` | All steps finished successfully | ✅ Yes | ✅ Yes |
| `failed` | Processing encountered error | ❌ No (returns 500) | ❌ No (returns 500) |

## Checking Status

Use the `/upload-status/{session_id}` endpoint:

```bash
GET /upload-status/{session_id}
```

Response:
```json
{
  "session_id": "abc123...",
  "status": "completed",
  "message": "✅ Successfully processed 6 files. Created 6 MD files, Converted 6 documents to JSON. 245 embeddings. Ready for feasibility questions and plan generation!",
  "parsed_documents": 6,
  "chunks_created": 245,
  "qdrant_collection": "session_abc12345"
}
```

## Error Handling

### If Processing Fails
- Status set to `"failed"`
- Error details stored in `session.processing_error`
- Feasibility/Plan endpoints return HTTP 500 with error message

### If JSON Conversion Fails
- Pipeline continues with markdown-only processing
- Warning logged but not treated as fatal error
- Session still marked as `"completed"`
- Feasibility will fall back to text-based input

## Implementation Details

### Upload Handler (src/routes/upload_handler.py)

**Line 234-282**: JSON conversion runs synchronously
```python
# CRITICAL: This runs SYNCHRONOUSLY to ensure JSON files are ready
# before proceeding to embedding and marking session as complete.

# SYNCHRONOUS CONVERSION - blocks until all files are converted
json_conversion_result = convert_markdown_to_json(
    md_file_paths=md_file_paths,
    output_dir=json_dir,
    verbose=True
)
```

**Line 337**: Status only set to "completed" after ALL steps
```python
# CRITICAL: Only set to "completed" after ALL steps are done:
# - Parsing (PDF → MD)
# - JSON Conversion (MD → JSON) 
# - Embedding (MD → Qdrant)
session.processing_status = "completed"
```

### Feasibility Endpoint (src/routes/planning_agent.py)

**Line 279-313**: Validates processing complete
```python
# CRITICAL: Validate that all processing is complete before feasibility generation
if session.processing_status != "completed":
    if session.processing_status == "processing":
        raise HTTPException(status_code=425, ...)
    elif session.processing_status == "failed":
        raise HTTPException(status_code=500, ...)
```

### Plan Generation Endpoint (src/routes/planning_agent.py)

**Line 355-388**: Same validation as feasibility
```python
# CRITICAL: Validate that all processing is complete before plan generation
if session.processing_status != "completed":
    # Same validation logic...
```

## User Experience

### Timeline Example (6 documents)

```
00:00 - Upload documents
00:01 - Processing started (status: "processing")
00:05 - STEP 1: Parsing PDFs (20-30s each)
03:00 - STEP 1.5: Converting to JSON (1-3s each)
03:15 - STEP 2: Embedding to Qdrant (20-30s)
03:45 - Status set to "completed"
03:45 - User can now generate feasibility/plan
```

### User Workflow

1. **Upload documents** via `/upload`
   - Receive `session_id`
   - Status: `"processing"`

2. **Poll status** via `/upload-status/{session_id}` 
   - Check until `status == "completed"`
   - Usually 3-5 minutes for 6 documents

3. **Generate feasibility** via `/feasibility`
   - Only works when status is `"completed"`
   - Returns 425 if still processing

4. **Generate plan** via `/generate-plan`
   - Only works when status is `"completed"`
   - Returns 425 if still processing

## Testing Sequential Processing

To verify sequential processing:

1. Upload documents and note the session_id
2. Immediately try to generate feasibility
3. Should receive HTTP 425: "Document processing is still in progress"
4. Wait for processing to complete
5. Try again - should work

## Thread Safety

- Processing runs in **single background thread per session**
- Each session has its own thread (no cross-session interference)
- Thread runs all steps sequentially (no parallelism within session)
- Session object updated synchronously in thread
- FastAPI main thread reads session status (read-only)

## Summary

✅ **Guaranteed sequential execution** - no race conditions
✅ **Explicit status checks** - cannot proceed until complete
✅ **Data validation** - ensures required data exists
✅ **Clear error messages** - tells users to wait
✅ **Graceful degradation** - JSON conversion failure non-fatal

The pipeline is designed to be **safe, predictable, and user-friendly**.

---

**Last Updated:** November 5, 2025

