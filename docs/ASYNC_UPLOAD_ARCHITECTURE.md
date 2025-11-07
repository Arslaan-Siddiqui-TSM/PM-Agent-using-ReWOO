# Async Upload Architecture

## Overview

The upload system now uses **true async processing** with background threads and frontend status polling. This prevents browser timeouts and provides a much better UX.

## Architecture Flow

```
┌──────────────┐
│   Frontend   │
└──────┬───────┘
       │ 1. POST /api/upload (files)
       ▼
┌──────────────┐
│   Backend    │
│              │
│ ┌──────────┐ │
│ │ Upload   │ │ 2. Save files, create session
│ │ Handler  │ │
│ └────┬─────┘ │
│      │       │ 3. Start background thread
│      ▼       │    (parsing, embedding, etc.)
│ ┌──────────┐ │
│ │Background│ │
│ │  Thread  │ │
│ └──────────┘ │
└──────────────┘
       │ 4. Return immediately
       │    {session_id, status: "processing"}
       ▼
┌──────────────┐
│   Frontend   │ 5. Poll /api/upload-status/{id}
│              │    every 2 seconds
│  [Spinner]   │
└──────────────┘
```

## Backend Changes

### 1. Upload Handler (`src/routes/upload_handler.py`)

**Before (Synchronous):**
```python
# Blocked for 3-5 minutes
session.processing_status = "processing"
self._process_with_rag_sync(session, uploaded_files)  # BLOCKS!

return {"status": session.processing_status}  # After 3-5 min
```

**After (Asynchronous):**
```python
# Returns in < 1 second
session.processing_status = "processing"

# Start background thread
threading.Thread(
    target=self._process_with_rag_sync,
    args=(session, uploaded_files),
    daemon=True
).start()

return {"status": "processing"}  # Immediately!
```

### 2. Status Endpoint

The existing `/api/upload-status/{session_id}` endpoint returns:

```json
{
  "status": "processing | completed | failed",
  "message": "Processing documents...",
  "parsed_documents": 6,
  "chunks_created": 125
}
```

## Frontend Changes

### 1. API Service (`frontend/src/services/api.js`)

Added new function:

```javascript
export const checkUploadStatus = async (sessionId) => {
  const response = await fetch(`${API_BASE_URL}/upload-status/${sessionId}`);
  return await response.json();
};
```

### 2. Workflow Hook (`frontend/src/hooks/useProjectWorkflow.js`)

**Key Changes:**
- Added `processingStatus` state
- Added `pollingInterval` ref to track polling
- `handleUpload` now starts polling instead of waiting
- Poll every 2 seconds until status is "completed" or "failed"

```javascript
const pollUploadStatus = async (sessionId) => {
  const statusData = await checkUploadStatus(sessionId);
  
  if (statusData.status === "completed") {
    clearInterval(pollingInterval.current);
    setLoading(false);
    setStep(WORKFLOW_STEPS.DEVELOPMENT_PROCESS);
  } else if (statusData.status === "failed") {
    clearInterval(pollingInterval.current);
    setLoading(false);
    setError(statusData.message);
  }
};

// Start polling after upload
pollingInterval.current = setInterval(() => {
  pollUploadStatus(data.session_id);
}, 2000);
```

### 3. Upload UI (`frontend/src/components/steps/UploadStep.jsx`)

Added visual feedback:
- Processing spinner animation
- Status message: "Processing documents in background (30-60 seconds)..."
- Hint text: "Parsing PDFs, extracting text, and creating embeddings"

## Benefits

✅ **No More Timeouts**: Browser won't timeout on long-running requests  
✅ **Better UX**: User sees progress instead of frozen UI  
✅ **Responsive**: Frontend remains interactive during processing  
✅ **Scalable**: Backend can handle multiple concurrent uploads  
✅ **Robust**: Network errors during polling don't break the flow  

## Testing

1. Start backend:
   ```bash
   python server.py
   ```

2. Start frontend:
   ```bash
   cd frontend
   npm run dev
   ```

3. Upload files and observe:
   - ✅ Upload completes in < 1 second
   - ✅ Spinner appears with "Processing..." message
   - ✅ Status polls every 2 seconds
   - ✅ Automatically proceeds to next step when complete

## Monitoring

You can monitor background processing in the backend logs:

```
🚀 Starting ASYNC document processing...
   Processing in background - request returns immediately

📄 Parsing document 1/6: Functional Specification Document.pdf
   ✓ Parsed successfully (45 pages)
...
✅ RAG processing completed successfully!
```

## Error Handling

- **Upload fails**: Error shown immediately
- **Processing fails**: Detected via polling, error shown in UI
- **Network error during polling**: Polling continues (doesn't crash)
- **Server restart**: Session lost (in-memory), user must re-upload

## Future Enhancements

Potential improvements:
- Add WebSocket support for real-time updates
- Add progress percentage (e.g., "3/6 documents parsed")
- Persist sessions to database instead of in-memory
- Add resume capability for interrupted processing

