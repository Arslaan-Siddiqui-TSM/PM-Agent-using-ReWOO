# Hardcoded Session Mode

## Overview

The hardcoded session mode allows you to bypass the full processing pipeline (PDF parsing, JSON conversion) and use pre-processed files for instant uploads during development and testing.

## Benefits

- **100x faster uploads**: < 1 second vs 3-5 minutes
- **No LLM costs**: Reuses existing JSON files
- **Easy toggle**: Switch via environment variable
- **No frontend changes**: Works with existing UI

## Setup

### 1. Files Already Created

The implementation has created the following structure:

```
data/hardcoded_session/
├── markdown/
│   ├── Functional Specification Document.md
│   ├── Non-Functional Requirement Document.md
│   ├── online_apparels_shopping_website.md
│   ├── Technical Specification Document.md
│   ├── Test Plan.md
│   └── Use Case.md
└── json/
    ├── Functional Specification Document.json
    ├── Non-Functional Requirement Document.json
    ├── online_apparels_shopping_website.json
    ├── Technical Specification Document.json
    ├── Test Plan.json
    └── Use Case.json
```

### 2. Create .env File

Create a `.env` file in the project root with the following content:

```bash
# Hardcoded Session Mode Toggle
USE_HARDCODED_SESSION=true
HARDCODED_MD_DIR=data/hardcoded_session/markdown
HARDCODED_JSON_DIR=data/hardcoded_session/json
```

## Usage

### Development Mode (Fast - Hardcoded)

1. Set in `.env`:
   ```bash
   USE_HARDCODED_SESSION=true
   ```

2. Restart backend:
   ```bash
   python server.py
   ```

3. Use frontend normally:
   - Click "Upload & Continue"
   - Upload completes in < 1 second
   - Status shows "completed" immediately
   - Frontend auto-advances to next step

### Production Mode (Full Pipeline)

1. Set in `.env`:
   ```bash
   USE_HARDCODED_SESSION=false
   ```

2. Restart backend:
   ```bash
   python server.py
   ```

3. Use frontend normally:
   - Upload takes 30-60 seconds (with cache) or 3-5 minutes (fresh)
   - Full processing: parsing → JSON → embedding
   - Frontend shows processing status

## How It Works

### With Hardcoded Mode Enabled

```python
# In src/routes/upload_handler.py
if feature_flags.use_hardcoded_session and use_default_files:
    # Skip parsing, JSON conversion, and embedding
    # Use pre-existing files from data/hardcoded_session/
    # Point to existing Qdrant collection
    # Return immediately with status="completed"
```

### Logs When Enabled

```
================================================================================
HARDCODED SESSION MODE ENABLED
Using pre-processed files
================================================================================

Hardcoded session created: abc-123-def
  MD files: 6
  JSON dir: data/hardcoded_session/json
```

### Logs When Disabled

```
🚀 Starting SYNCHRONOUS document processing...
   This will block until complete (30-60 seconds with cache)

📄 STEP 1: Parsing 6 PDFs to Markdown...
...
```

## Updating Hardcoded Files

To update the hardcoded session with new processed files:

```powershell
# Copy new markdown files
Copy-Item "output/session_NEWID_YYYYMMDD/raw/*.md" "data/hardcoded_session/markdown/" -Force

# Copy new JSON files
Copy-Item "output/session_NEWID_YYYYMMDD/json/*.json" "data/hardcoded_session/json/" -Force
```

## Fallback Behavior

If hardcoded mode fails (e.g., files missing), the system automatically falls back to the normal pipeline:

```
Hardcoded session failed: No MD files found in data/hardcoded_session/markdown
Falling back to normal pipeline...
```

## Testing

### Test Hardcoded Mode

```powershell
# 1. Enable hardcoded mode
# Set USE_HARDCODED_SESSION=true in .env

# 2. Restart backend
python server.py

# 3. Test upload (should be instant)
# Use frontend or:
Invoke-RestMethod -Uri "http://localhost:8000/api/upload?use_default_files=true" -Method Post

# Expected: Returns in < 1 second with status="completed"
```

### Test Full Pipeline

```powershell
# 1. Disable hardcoded mode
# Set USE_HARDCODED_SESSION=false in .env

# 2. Restart backend
python server.py

# 3. Test upload (should take 30-60 seconds)
# Use frontend or API as above

# Expected: Takes longer, shows "processing" status
```

## Configuration Reference

### Feature Flags (src/config/feature_flags.py)

```python
use_hardcoded_session: bool = False  # Toggle hardcoded mode
hardcoded_md_dir: str = "data/hardcoded_session/markdown"  # MD files path
hardcoded_json_dir: str = "data/hardcoded_session/json"  # JSON files path
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `USE_HARDCODED_SESSION` | `false` | Enable/disable hardcoded mode |
| `HARDCODED_MD_DIR` | `data/hardcoded_session/markdown` | Markdown files directory |
| `HARDCODED_JSON_DIR` | `data/hardcoded_session/json` | JSON files directory |

## Troubleshooting

### "No MD files found" Error

```bash
# Check if files exist
ls data/hardcoded_session/markdown/*.md

# If missing, copy from output directory
Copy-Item "output/session_468e90d3_20251106/raw/*.md" "data/hardcoded_session/markdown/"
```


### Mode Not Taking Effect

```bash
# Ensure .env file exists in project root
ls .env

# Restart backend after changing .env
# Press Ctrl+C then:
python server.py
```

## Notes

- The `.env` file is ignored by git (for security)
- Hardcoded mode only works with `use_default_files=true`
- Custom file uploads always use the full pipeline
- JSON files are optional but recommended for feasibility generation

