# Project Structure Documentation

## 📁 Overview

This document describes the reorganized project structure following industry best practices for Python applications.

## 🎯 New Directory Structure

```
pm-agent-using-rewoo/
├── src/                          # All application source code
│   ├── agents/                   # Document processing agents
│   │   ├── content_extractor.py # Type-aware content extraction
│   │   ├── diagram_generator.py # Diagram generation
│   │   ├── docling_processor.py # Docling integration
│   │   └── document_classifier.py # Document classification
│   │
│   ├── app/                      # Core application logic
│   │   ├── draft.py              # Draft generation (Reflection workflow)
│   │   ├── feasibility_agent.py  # Feasibility assessment
│   │   ├── graph.py              # LangGraph workflow orchestration
│   │   ├── reflect.py            # Reflection/critique generation
│   │   └── revise.py             # Revision decision logic
│   │
│   ├── config/                   # Configuration modules
│   │   ├── document_intelligence_config.py # Pipeline configuration
│   │   ├── feature_flags.py      # Feature toggles
│   │   └── llm_config.py         # LLM model configuration
│   │
│   ├── core/                     # Core business logic
│   │   ├── cache_manager.py      # Classification/extraction caching
│   │   ├── document_analyzer.py  # Cross-document analysis
│   │   ├── document_intelligence_pipeline.py # Main orchestration
│   │   ├── embedding_cache_manager.py # Global embedding cache
│   │   ├── intelligent_document_parser.py # Smart PDF parsing
│   │   ├── qdrant_manager.py     # Vector database management
│   │   ├── session.py            # Session data model
│   │   └── session_storage.py    # In-memory session store
│   │
│   ├── routes/                   # FastAPI route handlers
│   │   ├── health_check.py       # Health check endpoint
│   │   ├── planning_agent.py     # Main planning endpoints
│   │   └── utils_endpoints.py    # Utility endpoints
│   │
│   ├── states/                   # State definitions
│   │   ├── reflection_state.py   # Reflection workflow state
│   │   └── rewoo_state.py        # ReWOO workflow state (legacy)
│   │
│   ├── tools/                    # External tool integrations
│   │   └── search_tool.py        # Tavily search wrapper
│   │
│   └── utils/                    # Helper utilities
│       ├── constants.py          # Application constants
│       └── helper.py             # Common helper functions
│
├── docs/                         # All documentation
│   ├── setup/                    # Setup and installation guides
│   │   ├── DOCKER_SETUP.md       # Docker configuration
│   │   ├── QUICK_START.md        # Quick start guide
│   │   └── START_HERE.md         # New user guide
│   │
│   ├── implementation/           # Implementation details
│   │   ├── CHANGES.md            # Change log
│   │   ├── IMPLEMENTATION_SUMMARY.md # Feature summary
│   │   └── QDRANT_MIGRATION_COMPLETE.md # Qdrant details
│   │
│   ├── guides/                   # User guides and troubleshooting
│   │   ├── ENV_CONFIGURATION.md  # Environment configuration
│   │   ├── ERROR_FIXES.md        # Error resolution guide
│   │   ├── ERRORS_AND_SOLUTIONS.md # Common errors
│   │   ├── IMPLEMENTATION_STATUS.md # Feature status
│   │   ├── QUICKSTART_ENHANCED.md # Enhanced quickstart
│   │   └── README_ERRORS.txt     # Error reference
│   │
│   └── PROJECT_STRUCTURE.md      # This file
│
├── scripts/                      # Utility and setup scripts
│   ├── setup/                    # Setup scripts
│   │   ├── fix_errors.py         # Automated error fixing
│   │   ├── init_qdrant.py        # Qdrant initialization
│   │   └── populate_qdrant.py    # Qdrant data population
│   │
│   ├── testing/                  # Test scripts
│   │   ├── test_docling_qdrant.py # Docling + Qdrant tests
│   │   ├── test_document_intelligence.py # Pipeline tests
│   │   └── test_qdrant_migration.py # Migration tests
│   │
│   ├── generate_feasibility_questions.py # Feasibility generation
│   └── generate_project_plan.py  # Plan generation script
│
├── data/                         # All data directories
│   ├── files/                    # Input PDF documents
│   ├── uploads/                  # User-uploaded files
│   ├── embedding/                # Embedding data
│   ├── embedding_cache/          # Global embedding cache
│   ├── parsed_documents/         # Parsed document cache
│   ├── qdrant_storage/           # Qdrant vector database
│   ├── vector_store/             # Vector store data
│   └── logs/                     # Application logs
│
├── tests/                        # Test files
│   └── test_api.py               # API integration tests
│
├── prompts/                      # LLM prompt templates
│   ├── draft_prompt.txt          # Draft generation prompt
│   ├── feasibility_promptv2.txt  # Feasibility prompt v2
│   ├── feasprompt_enhanced.txt   # Enhanced feasibility prompt
│   ├── planner_prompt.txt        # Planning prompt (legacy)
│   ├── reflect_prompt.txt        # Reflection/critique prompt
│   ├── revise_prompt.txt         # Revision decision prompt
│   └── solver_prompt.txt         # Solver prompt (legacy)
│
├── frontend/                     # React frontend application
│   ├── src/
│   │   ├── App.jsx               # Main application component
│   │   ├── App.css               # Application styles
│   │   ├── index.css             # Global styles
│   │   └── main.jsx              # Entry point
│   ├── index.html                # HTML template
│   ├── package.json              # NPM dependencies
│   └── vite.config.js            # Vite configuration
│
├── .env                          # Environment variables (not in git)
├── .gitignore                    # Git ignore patterns
├── docker-compose.yml            # Docker services configuration
├── pyproject.toml                # Python project metadata
├── requirements.txt              # Python dependencies
├── README.md                     # Main project README
├── server.py                     # FastAPI server entry point
└── uv.lock                       # UV lock file

```

## 🔄 Changes from Previous Structure

### Improvements Made

1. **Source Code Organization (`src/`)**
   - All application code moved to `src/` directory
   - Clear separation of concerns with dedicated subdirectories
   - Follows Python package best practices

2. **Documentation Organization (`docs/`)**
   - Setup guides in `docs/setup/`
   - Implementation details in `docs/implementation/`
   - User guides and troubleshooting in `docs/guides/`
   - Easy to find relevant documentation

3. **Script Organization (`scripts/`)**
   - Setup scripts in `scripts/setup/`
   - Test scripts in `scripts/testing/`
   - Utility scripts at `scripts/` root level
   - Clear purpose and organization

4. **Data Consolidation (`data/`)**
   - All data files in one place
   - Easy to backup, exclude from git, or migrate
   - Consistent structure for all data types

5. **Test Organization (`tests/`)**
   - Dedicated test directory
   - Separate from source code
   - Easy to run test suites

6. **Removed Deprecated Code**
   - Deleted `mmrag/` directory (old RAG implementation)
   - Deleted `multiple_doc_support_rag/` directory (old implementation)
   - Cleaner codebase with only active code

## 📝 Import Statement Changes

All imports have been updated to use the `src.` prefix:

**Before:**
```python
from config.llm_config import model
from core.document_intelligence_pipeline import DocumentIntelligencePipeline
from agents.document_classifier import DocumentClassifierAgent
```

**After:**
```python
from src.config.llm_config import model
from src.core.document_intelligence_pipeline import DocumentIntelligencePipeline
from src.agents.document_classifier import DocumentClassifierAgent
```

## 🛣️ Path Configuration Changes

File paths have been updated to reflect the new `data/` directory:

- `files/` → `data/files/`
- `uploads/` → `data/uploads/`
- `embedding_cache/` → `data/embedding_cache/`
- `parsed_documents/` → `data/parsed_documents/`
- `qdrant_storage/` → `data/qdrant_storage/`
- `logs/` → `data/logs/`

## 🚀 Running the Application

### Development Server

```bash
python server.py
```

The server imports from `src.*` packages automatically.

### Scripts

All scripts have been updated with correct imports:

```bash
# Generate feasibility assessment
python scripts/generate_feasibility_questions.py

# Generate project plan
python scripts/generate_project_plan.py

# Initialize Qdrant
python scripts/setup/init_qdrant.py

# Run tests
python scripts/testing/test_document_intelligence.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## 📋 Benefits of New Structure

1. **Professional Organization**
   - Follows Python packaging conventions
   - Clear separation of concerns
   - Industry-standard structure

2. **Easier Navigation**
   - Logical grouping of related files
   - Clear hierarchy
   - Self-documenting structure

3. **Better Scalability**
   - Easy to add new modules
   - Clear place for new features
   - Maintainable as project grows

4. **Cleaner Root Directory**
   - Only essential files at root
   - No clutter
   - Professional appearance

5. **Improved Development Experience**
   - Easy to find files
   - Clear import paths
   - Better IDE support

6. **Better Git Management**
   - Clear .gitignore patterns
   - Easy to see what's tracked
   - Consolidated data directory

## 🔧 Configuration Files Location

| File | Location | Purpose |
|------|----------|---------|
| `.env` | Root | Environment variables |
| `pyproject.toml` | Root | Python project metadata |
| `requirements.txt` | Root | Python dependencies |
| `docker-compose.yml` | Root | Docker services |
| `server.py` | Root | FastAPI entry point |

## 📚 Documentation Navigation

- **Getting Started**: `docs/setup/START_HERE.md`
- **Quick Setup**: `docs/setup/QUICK_START.md`
- **Docker Setup**: `docs/setup/DOCKER_SETUP.md`
- **Troubleshooting**: `docs/guides/ERROR_FIXES.md`
- **Environment Config**: `docs/guides/ENV_CONFIGURATION.md`
- **Implementation Status**: `docs/guides/IMPLEMENTATION_STATUS.md`

## 🎯 Next Steps

1. Update your IDE/editor settings if needed
2. Review and update any custom scripts
3. Update CI/CD pipelines if applicable
4. Test all functionality to ensure everything works
5. Update any external documentation or wikis

## ⚠️ Migration Notes

If you have existing data or outputs:

1. Move `files/*.pdf` → `data/files/*.pdf`
2. Move `uploads/*` → `data/uploads/*`
3. Move `parsed_documents/*` → `data/parsed_documents/*`
4. Move `qdrant_storage/*` → `data/qdrant_storage/*`
5. Move `embedding_cache/*` → `data/embedding_cache/*`

The `.gitignore` has been updated to handle the new structure automatically.

## 📞 Support

For questions or issues with the new structure:
- Check `docs/guides/ERROR_FIXES.md` for common issues
- Review `docs/guides/ERRORS_AND_SOLUTIONS.md` for solutions
- Refer to `README.md` for general project information

