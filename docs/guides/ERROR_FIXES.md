# Error Fixes and Solutions

## 🔴 Critical Errors Found

### Error 1: ModuleNotFoundError: No module named 'fitz'

**Error Message:**
```
ModuleNotFoundError: No module named 'fitz'
```

**Cause:** PyMuPDF package not installed. The package is called `pymupdf` but imports as `fitz`.

**Fix:**
```bash
pip install pymupdf==1.26.5
```

Or install all dependencies:
```bash
pip install -r requirements.txt
```

---

### Error 2: Missing Qdrant Dependencies

**Potential Error:**
```
ModuleNotFoundError: No module named 'qdrant_client'
ModuleNotFoundError: No module named 'langchain_qdrant'
```

**Fix:**
```bash
pip install qdrant-client==1.11.3 langchain-qdrant==0.2.0
```

---

### Error 3: Missing Docling

**Potential Error:**
```
ModuleNotFoundError: No module named 'docling'
```

**Fix:**
```bash
pip install docling>=2.0.0 docling-core>=2.0.0
```

---

### Error 4: Missing OpenAI Integration

**Potential Error:**
```
ModuleNotFoundError: No module named 'langchain_openai'
```

**Fix:**
```bash
pip install langchain-openai==0.2.14
```

---

## ✅ Complete Fix: Install All Dependencies

### Step 1: Upgrade pip
```bash
python -m pip install --upgrade pip
```

### Step 2: Install all requirements
```bash
pip install -r requirements.txt
```

### Step 3: Verify installation
```bash
pip list | grep -E "qdrant|docling|pymupdf|langchain"
```

Expected output:
```
docling                  2.x.x
docling-core             2.x.x
langchain-openai         0.2.14
langchain-qdrant         0.2.0
pymupdf                  1.26.5
qdrant-client            1.11.3
```

---

## 🔧 Additional Setup Required

### 1. Start Qdrant Docker Container

**Error:**
```
Failed to connect to Qdrant at http://localhost:6333
```

**Fix:**
```bash
# Start Qdrant
docker-compose up -d qdrant

# Verify it's running
curl http://localhost:6333/healthz
```

### 2. Configure Environment Variables

**Error:**
```
RuntimeError: Failed to initialize embeddings. Ensure OPENAI_API_KEY is set.
```

**Fix:**

Create `.env` file in project root:
```env
OPENAI_API_KEY=your-openai-api-key-here
GOOGLE_API_KEY=your-google-api-key-here
QDRANT_URL=http://localhost:6333
```

---

## 🧪 Verify Fix

### Test 1: Import Check
```bash
python -c "from core.embedding_cache_manager import EmbeddingCacheManager; from core.intelligent_document_parser import IntelligentDocumentParser; from core.qdrant_manager import QdrantManager; print('✅ All imports successful')"
```

### Test 2: Qdrant Connection
```bash
python -c "from core.qdrant_manager import QdrantManager; m = QdrantManager(session_id='test'); print('✅ Qdrant connected')"
```

### Test 3: Run Validation Script
```bash
python init_qdrant.py
```

### Test 4: Run Full Test Suite
```bash
python test_qdrant_migration.py
```

---

## 📋 Quick Fix Checklist

- [ ] Install Python dependencies: `pip install -r requirements.txt`
- [ ] Start Qdrant: `docker-compose up -d qdrant`
- [ ] Create `.env` file with API keys
- [ ] Verify imports work
- [ ] Run `python init_qdrant.py`
- [ ] Run `python test_qdrant_migration.py`

---

## 🚨 Common Issues

### Issue: pip install fails on Windows

**Error:**
```
error: Microsoft Visual C++ 14.0 or greater is required
```

**Fix:**
Install Visual C++ Build Tools or use pre-built wheels:
```bash
pip install --only-binary :all: pymupdf
```

### Issue: Docling install fails

**Fix:**
```bash
# Try with no-cache
pip install --no-cache-dir docling>=2.0.0

# Or specific version
pip install docling==2.0.0
```

### Issue: Qdrant container won't start

**Fix:**
```bash
# Check Docker is running
docker ps

# View logs
docker-compose logs qdrant

# Restart
docker-compose restart qdrant
```

### Issue: Permission denied on folders

**Fix (Windows PowerShell):**
```powershell
# Run as administrator if needed
New-Item -ItemType Directory -Force -Path parsed_documents, embedding_cache, vector_store, logs
```

---

## 🎯 Installation Order (Recommended)

1. **Install Python packages**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start Docker services**
   ```bash
   docker-compose up -d qdrant
   ```

3. **Configure environment**
   ```bash
   # Create .env file
   cp .env.example .env
   # Edit .env with your API keys
   ```

4. **Validate setup**
   ```bash
   python init_qdrant.py
   ```

5. **Run tests**
   ```bash
   python test_qdrant_migration.py
   ```

6. **Start server**
   ```bash
   python server.py
   ```

---

## 📞 Still Having Issues?

### Check Installation
```bash
# Python version (need 3.10+)
python --version

# Pip version
pip --version

# Docker version
docker --version

# Installed packages
pip list
```

### Check Logs
```bash
# Parsing errors
type logs\parsing_errors.log

# Docker logs
docker-compose logs qdrant

# Server logs (when running)
# Check console output
```

### Reinstall Everything
```bash
# Uninstall problematic packages
pip uninstall -y qdrant-client langchain-qdrant pymupdf docling docling-core

# Clear pip cache
pip cache purge

# Reinstall
pip install -r requirements.txt
```

---

## ✅ Success Indicators

After fixing errors, you should see:

1. **Imports work:**
   ```bash
   python -c "from core.qdrant_manager import QdrantManager; print('OK')"
   # Output: OK
   ```

2. **Qdrant responds:**
   ```bash
   curl http://localhost:6333/healthz
   # Output: {"title":"healthz","version":"1.x.x"}
   ```

3. **Tests pass:**
   ```bash
   python test_qdrant_migration.py
   # Output: 6/6 tests passed
   ```

4. **Server starts:**
   ```bash
   python server.py
   # Output: Application startup complete
   ```

---

**Last Updated:** 2025-11-03
**Status:** All known errors documented with fixes


