# Migration Guide - New Codebase Structure

## 📖 Quick Reference

Your codebase has been professionally restructured. Here's what you need to know:

---

## ✅ What Changed

### Directory Structure

**Before:**
```
project_root/
├── agents/
├── app/
├── config/
├── core/
├── files/
├── uploads/
├── (10+ markdown docs at root)
├── (8+ scripts at root)
└── ...
```

**After:**
```
project_root/
├── src/           # All source code
├── docs/          # All documentation (organized)
├── scripts/       # All scripts (organized)
├── data/          # All data files
├── tests/         # All tests
├── frontend/      # React app
├── prompts/       # LLM prompts
└── (clean root with only essentials)
```

---

## 🚀 How to Use the New Structure

### 1. Running the Application

**No changes needed!** Just run:

```bash
python server.py
```

The server automatically imports from `src.*` packages.

### 2. Accessing Your Data

All data is now in the `data/` directory:

| Old Path | New Path |
|----------|----------|
| `files/*.pdf` | `data/files/*.pdf` |
| `uploads/*` | `data/uploads/*` |
| `outputs/*` | `data/outputs/*` |
| `parsed_documents/*` | `data/parsed_documents/*` |
| `embedding_cache/*` | `data/embedding_cache/*` |
| `qdrant_storage/*` | `data/qdrant_storage/*` |
| `logs/*` | `data/logs/*` |

### 3. Running Scripts

Scripts are now organized in `scripts/`:

```bash
# Setup scripts
python scripts/setup/init_qdrant.py
python scripts/setup/populate_qdrant.py
python scripts/setup/fix_errors.py

# Test scripts
python scripts/testing/test_document_intelligence.py
python scripts/testing/test_qdrant_migration.py

# Utility scripts
python scripts/generate_feasibility_questions.py
python scripts/generate_project_plan.py
```

### 4. Finding Documentation

All docs are in `docs/` organized by category:

```bash
# Setup guides
docs/setup/START_HERE.md
docs/setup/QUICK_START.md
docs/setup/DOCKER_SETUP.md

# Implementation details
docs/implementation/CHANGES.md
docs/implementation/IMPLEMENTATION_SUMMARY.md
docs/implementation/QDRANT_MIGRATION_COMPLETE.md

# User guides
docs/guides/ENV_CONFIGURATION.md
docs/guides/ERROR_FIXES.md
docs/guides/ERRORS_AND_SOLUTIONS.md
```

---

## 🔄 If You Have Existing Data

If you already have data in the old locations, move it to the new `data/` directory:

### Windows (PowerShell)

```powershell
# Move input files
Move-Item files\*.pdf data\files\ -ErrorAction SilentlyContinue

# Move uploaded files
Move-Item uploads\* data\uploads\ -ErrorAction SilentlyContinue

# Move parsed documents
Move-Item parsed_documents\* data\parsed_documents\ -ErrorAction SilentlyContinue

# Move cache
Move-Item embedding_cache\* data\embedding_cache\ -ErrorAction SilentlyContinue

# Move Qdrant storage
Move-Item qdrant_storage\* data\qdrant_storage\ -ErrorAction SilentlyContinue

# Move logs
Move-Item logs\* data\logs\ -ErrorAction SilentlyContinue
```

---

## 🛠️ For Developers

### Import Changes

All imports now use the `src.` prefix:

**Old:**
```python
from config.llm_config import model
from core.document_intelligence_pipeline import DocumentIntelligencePipeline
from agents.document_classifier import DocumentClassifierAgent
```

**New:**
```python
from src.config.llm_config import model
from src.core.document_intelligence_pipeline import DocumentIntelligencePipeline
from src.agents.document_classifier import DocumentClassifierAgent
```

**Note:** All existing files have already been updated!

### Creating New Files

When creating new modules, follow the structure:

- **Agents**: `src/agents/your_agent.py`
- **Core Logic**: `src/core/your_module.py`
- **API Routes**: `src/routes/your_route.py`
- **Configuration**: `src/config/your_config.py`
- **Utilities**: `src/utils/your_util.py`
- **Tests**: `tests/test_your_feature.py`
- **Scripts**: `scripts/your_script.py`

### Path References

When referencing data files in code, use the `data/` prefix:

```python
# Good
files_dir = "data/files"
upload_dir = "data/uploads"
cache_dir = "data/embedding_cache"

# Old (don't use)
files_dir = "files"
upload_dir = "uploads"
cache_dir = "embedding_cache"
```

---

## 📚 Documentation Map

| Need | See |
|------|-----|
| **Full structure details** | [`docs/PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md) |
| **What changed** | [`RESTRUCTURING_SUMMARY.md`](../RESTRUCTURING_SUMMARY.md) |
| **Getting started** | [`docs/setup/START_HERE.md`](setup/START_HERE.md) |
| **Quick setup** | [`docs/setup/QUICK_START.md`](setup/QUICK_START.md) |
| **Troubleshooting** | [`docs/guides/ERROR_FIXES.md`](guides/ERROR_FIXES.md) |
| **Environment setup** | [`docs/guides/ENV_CONFIGURATION.md`](guides/ENV_CONFIGURATION.md) |
| **This guide** | [`docs/MIGRATION_GUIDE.md`](MIGRATION_GUIDE.md) |

---

## ✅ Verification Checklist

After migration, verify everything works:

- [ ] Server starts: `python server.py`
- [ ] Can access API: `http://localhost:8000/docs`
- [ ] Can upload files to `data/files/`
- [ ] Scripts run from `scripts/` directory
- [ ] Documentation accessible in `docs/`
- [ ] Tests run from `tests/` or `scripts/testing/`
- [ ] Frontend works (if using): `cd frontend && npm run dev`

---

## 🎯 Key Benefits

1. **Professional Organization** - Follows industry standards
2. **Easy Navigation** - Logical grouping of files
3. **Clean Root** - No clutter at project root
4. **Better Scalability** - Clear place for new features
5. **Improved Git** - Clear .gitignore patterns
6. **Better Documentation** - Organized by category

---

## 🆘 Troubleshooting

### Import Errors

If you see import errors like:
```
ModuleNotFoundError: No module named 'config'
```

**Solution:** Update imports to use `src.` prefix:
```python
from src.config.llm_config import model
```

### Path Errors

If you see file not found errors:
```
FileNotFoundError: 'files/document.pdf'
```

**Solution:** Update paths to use `data/` prefix:
```python
file_path = "data/files/document.pdf"
```

### Missing Data

If data is missing after restructuring:

**Solution:** Move data from old locations to `data/` directory (see "If You Have Existing Data" section above)

---

## 📞 Need Help?

1. Check the troubleshooting guide: [`docs/guides/ERROR_FIXES.md`](guides/ERROR_FIXES.md)
2. Review the full structure: [`docs/PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md)
3. See what changed: [`RESTRUCTURING_SUMMARY.md`](../RESTRUCTURING_SUMMARY.md)
4. Check the main README: [`README.md`](../README.md)

---

## 🎉 You're All Set!

The restructuring is complete. Your codebase now follows professional Python project standards and is ready for continued development.

**Happy coding!** 🚀

