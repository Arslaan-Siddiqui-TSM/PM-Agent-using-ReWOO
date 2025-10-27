# ReWOO Demonstration Project

An end-to-end implementation of the ReWOO (Reasoning WithOut Observation) paradigm using LangGraph, designed to turn multiple project documents (BRDs, specs, test plans, etc.) into a comprehensive project plan. This repo adds a Document Intelligence Pipeline that classifies, extracts, and analyzes PDFs to produce a clean planning context before ReWOO planning and execution.

## 📋 Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Project Flow](#project-flow)
- [Features](#features)
- [Project Structure](#project-structure)
- [Installation](#installation)
  - [Using UV (Recommended)](#using-uv-recommended)
  - [Using pip](#using-pip)
- [Configuration](#configuration)
- [Usage](#usage)
- [How It Works](#how-it-works)
- [Components Deep Dive](#components-deep-dive)
- [Output Format](#output-format)
- [Testing](#testing)
- [Known quirks](#known-quirks)
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

This project implements the ReWOO (Reasoning WithOut Observation) framework, which is an advanced reasoning pattern that separates planning from execution. It's designed to analyze multiple project documents and automatically generate structured, comprehensive project plans in Markdown.

This implementation uses:

- LangGraph for orchestrating the reasoning workflow
- Google Gemini 2.0 Flash for language model operations
- PyMuPDF for PDF document processing
- Tavily Search for web-based information retrieval
- A custom Document Intelligence Pipeline for classification, extraction, cross-doc analysis, and caching

---

## 🏗️ Architecture

The system combines a pre-processing intelligence pipeline with a state-driven ReWOO graph powered by LangGraph:

```
              ┌──────────────────────────────────────────┐
              │     Document Intelligence Pipeline       │
              │  • Classification (LLM + caching)        │
              │  • Content extraction (LLM + PyMuPDF)    │
              │  • Cross-doc analysis (gaps/conflicts)   │
              │  • Planning context generation           │
              └──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────┐
│                    ReWOO State                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ • task: str                                       │  │
│  │ • plan_string: str                                │  │
│  │ • steps: List[tuple]                              │  │
│  │ • results: dict                                   │  │
│  │ • result: str                                     │  │
│  │ • document_context: str (from pipeline)           │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│              LangGraph Workflow                         │
│                                                          │
│  START → PLAN → TOOL → (route) → TOOL (loop) → SOLVE   │
│                   ↓                  ↓            ↓     │
│                Execute            Check if      Final   │
│                Tools              Complete      Result  │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### Core Components

#### Why ReWOO over ReAct for this use case

For multi-document planning (BRDs, specs, test plans) the plan-first nature of ReWOO is a better fit than ReAct’s stepwise observe-replan loop:

- Fewer LLM calls and lower latency: We plan once, then execute deterministically. ReAct re-prompts at every step, repeatedly re-ingesting context.
- Better use of Document Intelligence: The pipeline creates a compact planning context consumed once. ReAct would re-derive/merge context many times, increasing cost and drift.
- Evidence reuse and consistency: ReWOO’s evidence IDs (#E1, #E2, …) let later steps reference prior results without recomputation, keeping outputs consistent across documents.
- Reproducibility and caching: A fixed plan enables effective caching of classification/extraction/analysis and stable, auditable runs with a full Markdown execution log.

1. States (`states/rewoo_state.py`): Pydantic model defining the agent's state
2. Planner (`app/plan.py`): Generates multi-step reasoning plans (uses pipeline context if available)
3. Tool Executor (`app/tool_executor.py`): Executes tools (LLM, FileReader, Google Search)
4. Solver (`app/solver.py`): Synthesizes results into final output
5. Graph (`app/graph.py`): Orchestrates the workflow using LangGraph
6. Document Intelligence (`core/*`, `agents/*`): Smart pre-processing for planning
7. Main (`main.py`): Entry point with rich console output and Markdown execution log

---

## 🔄 Project Flow

### 0. Document Intelligence Stage (Recommended) 🧠

```
Input: All PDFs in files/ directory
      ↓
Classifier → Extractor → Analyzer → Planning Context
      ↓
Output: Clean, consolidated planning context string
        + Intermediate JSON/MD artifacts under outputs/intermediate/
```

### 1. Planning Stage 🧩

```
Input: Task description (+ feasibility notes + document context)
         ↓
   Planner reads planner_prompt.txt
         ↓
   LLM generates structured plan with steps
         ↓
   Output: Plan string + parsed steps
```

If the intelligence pipeline ran, the planner uses the generated context instead of raw PDFs.

Example Plan:

```
Plan: Read the BRD document to extract raw text
#E1 = FileReader['files/Functional Specification Document.pdf']

Plan: Identify key project epics from the BRD
#E2 = LLM[Extract high-level modules from #E1]

Plan: Generate user stories for each epic
#E3 = LLM[Break down #E2 into user stories]
...
```

### 2. Tool Execution Stage 🔧

```
For each step in the plan:
    ├── Get current task number
    ├── Parse step (tool, input, dependencies)
    ├── Resolve dependencies (#E1, #E2, etc.)
    ├── Execute tool:
    │   ├── FileReader: Extract PDF text
    │   ├── LLM: Process and analyze
    │   └── Google: Web search (max 400 chars)
    └── Store result with evidence ID
```

Conditional Routing:

- If more steps remain → Loop back to TOOL node
- If all steps complete → Route to SOLVE node

### 3. Solving Stage 🧠

```
Input: All plans + all evidence results
         ↓
   Solver reads solver_prompt.txt
         ↓
   LLM synthesizes final project plan
         ↓
   Save as Markdown file (outputs/project_plan_*.md)
         ↓
   Return final result
```

---

## ✨ Features

- 🤖 Automated Planning: Intelligent multi-step plan generation from prompts
- 🧠 Document Intelligence (NEW): Classify, extract, and analyze PDFs for a high-signal planning context
- 🗃️ Caching: Persist classifications/extractions/analysis for faster subsequent runs
- 📄 PDF Processing: Extracts and analyzes documents using PyMuPDF
- 🔍 Web Search Integration: Tavily-powered search for domain clarifications
- 🧠 LLM Reasoning: Google Gemini 2.0 Flash for analysis and synthesis
- 📊 Structured Output: Comprehensive Markdown project plans with 8 sections
- 📓 Full LLM Logs: All prompts/responses captured in a Markdown execution log
- 🎨 Rich Console UI: Beautiful terminal output with tables, panels, and progress indicators
- 🔁 Stateful Execution: LangGraph manages state transitions seamlessly
- 🛡️ Error Handling: Robust validation for query truncation and tool execution
- 📦 Modular Design: Clean separation of concerns across components

---

## 📁 Project Structure

```
rewoo-demonstration/
│
├── app/                          # Core application logic
│   ├── graph.py                  # LangGraph workflow definition
│   ├── plan.py                   # Planning node implementation
│   ├── solver.py                 # Solving node implementation
│   └── tool_executor.py          # Tool execution node
│
├── core/                         # Document Intelligence Pipeline
│   ├── document_intelligence_pipeline.py  # Orchestrates classify → extract → analyze
│   ├── document_analyzer.py      # Cross-doc analysis and reporting
│   └── cache_manager.py          # Caching for performance
│
├── agents/                       # LLM-based agents
│   ├── document_classifier.py    # Content-based PDF classification
│   └── content_extractor.py      # Type-aware content extraction
│
├── config/                       # Configuration modules
│   ├── llm_config.py             # LLM setup (Google Gemini)
│   └── document_intelligence_config.py  # Pipeline configuration
│
├── states/                       # State definitions
│   └── rewoo_state.py            # ReWOO state Pydantic model
│
├── tools/                        # External tool integrations
│   └── search_tool.py            # Tavily search wrapper
│
├── utils/                        # Helper utilities
│   └── helper.py                 # Routing, task mgmt, logging utils
│
├── prompts/                      # LLM prompt templates
│   ├── planner_prompt.txt        # Planning stage instructions
│   ├── solver_prompt.txt         # Solving stage instructions
│   └── feasibility_prompt.txt    # Feasibility Q/A generator
│
├── files/                        # Input documents (PDFs)
│   └── ...                       # Place your PDFs here
│
├── outputs/                      # Generated artifacts
│   ├── project_plan_*.md         # Final project plans
│   ├── agent_execution_log_*.md  # Full LLM prompts/responses log
│   └── intermediate/             # Pipeline JSON/MD reports
│
├── main.py                       # Application entry point (pipeline + ReWOO)
├── generate_feasibility_questions.py  # Create feasibility assessment MD
├── test_document_intelligence.py # Pipeline smoke test
├── pyproject.toml                # Project metadata and dependencies
├── requirements.txt              # Frozen deps for pip installs
├── uv.lock                       # UV lock file
└── README.md                     # This file
```

---

## 🚀 Installation

### Prerequisites

- Python 3.13 or higher
- Google Gemini API key
- Tavily API key

### Using UV (Recommended)

1. Install UV (if not already installed):

   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
   ```

2. From your project folder, install dependencies:

   ```bash
   uv sync
   ```

3. Activate the virtual environment:

   ```bash
   # Windows (cmd.exe)
   .venv\Scripts\activate
   ```

### Using pip

1. Create a virtual environment:

   ```bash
   python -m venv venv
   ```

2. Activate the virtual environment:

   ```bash
   # Windows (cmd.exe)
   venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_google_gemini_api_key_here
TAVILY_API_KEY=your_tavily_api_key_here
```

### API Keys Setup

1. Google Gemini API:

   - Visit https://aistudio.google.com/app/api-keys
   - Create a new API key
   - Copy to `.env`

2. Tavily API:
   - Sign up at https://tavily.com/
   - Get your API key from the dashboard
   - Copy to `.env`

### Model Configuration

By default we use Google Gemini 2.0 Flash (see `config/llm_config.py`). You can change model/temperature there:

```python
model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash",
    temperature=0.6,
    google_api_key=GOOGLE_API_KEY
)
```

---

## 💻 Usage

### Basic Usage

1. Place your PDFs in the `files/` directory (any names; multiple files supported).

2. (Recommended) Generate feasibility questions/assessment for Tech Lead review:

   ```bash
   # Windows (cmd.exe)
   python generate_feasibility_questions.py
   ```

   This creates `outputs/feasibility_assessment.md`. Review and optionally fill in answers.

   Important: the current planner/solver looks for `outputs/feasibility_questions.md`. Until we consolidate names, either:

   - Rename the generated file (Windows cmd):
     - `ren outputs\feasibility_assessment.md feasibility_questions.md`
   - OR update the code to point to your file.

3. Run the main application (automatically processes all PDFs and uses the Document Intelligence Pipeline by default):

   ```bash
   # Windows (cmd.exe)
   python main.py
   ```

4. View the outputs:
   - Final plan: `outputs/project_plan_YYYYMMDD_HHMMSS.md`
   - Full execution log: `outputs/agent_execution_log_*.md`
   - Intermediate artifacts: `outputs/intermediate/*`

### Customizing the task and pipeline

In `main.py`, you can tweak:

- `task` string passed to `run_agent`
- `use_document_intelligence=True|False` to enable/disable the pipeline
- `enable_cache=True|False` to control caching behavior

### Running Feasibility Agent directly

You can also run the agent directly on your current `files/*.pdf` via:

```bash
# Windows (cmd.exe)
python app\feasibility_agent.py
```

### Console Output

The application provides beautiful formatted output:

```
════════════════════════════════════════════════
🔍 Executing ReWOO Reasoning Graph
════════════════════════════════════════════════

═══════════════ 🧩 Planning Stage ═══════════════
┌─── Generated Plan ───────────────────────────┐
│ Plan: Read the BRD document...               │
│ #E1 = FileReader['files/...']                │
│ ...                                          │
└───────────────────────────────────────────────┘

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃           Parsed Plan Steps                 ┃
┣━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━┫
┃ Step  ┃ Evidence ID ┃ Tool     ┃ Input    ┃
┡━━━━━━━╇━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━━━━┩
│ 1     │ #E1         │ FileRead │ files/...│
└───────┴─────────────┴──────────┴──────────┘

═══════════════ 🔧 Tool Execution ═══════════════
┌─── Result of #E1 ───────────────────────────┐
│ [Extracted BRD content...]                   │
└───────────────────────────────────────────────┘

═══════════════ 🧠 Final Solution ═══════════════
┌─── Final Answer ─────────────────────────────┐
│ # Complete Project Plan                      │
│ ...                                          │
└───────────────────────────────────────────────┘
```

---

## 🔍 How It Works

### ReWOO Pattern Explained

1. Separation of Planning and Execution:

   - Traditional ReAct: Plan → Observe → Plan → Observe (multiple LLM calls)
   - ReWOO: Plan all → Execute all → Solve (fewer LLM calls, more efficient)

2. Evidence-Based Reasoning:

   - Each step produces evidence (e.g., #E1, #E2)
   - Subsequent steps reference previous evidence
   - Final solver uses all evidence to generate output

3. Tool Orchestration:
   - FileReader: Reads PDF documents, extracts text
   - LLM: Performs reasoning, analysis, extraction
   - Google: Searches web for clarifications (max 400 chars)

### State Management

```python
class ReWOO(BaseModel):
    task: str              # Initial user request
    plan_string: str       # Generated plan text
    steps: List[tuple]     # Parsed steps [(plan, evidence_id, tool, input)]
    results: dict          # Execution results {evidence_id: result}
    result: str            # Final synthesized output
    document_context: str  # Context from Document Intelligence Pipeline (if enabled)
```

### Routing Logic

```python
def route(state):
    current_task = get_current_task(state)
    if current_task is None:
        return "solve"  # All steps done, go to solver
    else:
        return "tool"   # More steps to execute, loop back
```

---

## 🧩 Components Deep Dive

### 1. Planner (`app/plan.py`)

Purpose: Generate structured multi-step reasoning plans

Process:

1. Loads `planner_prompt.txt`
2. Invokes LLM with task description and either:
   - Document Intelligence context (preferred)
   - or legacy raw PDF text from `files/`
3. Parses output using regex: `Plan:\s*(.+)\s*(#E\d+)\s*=\s*(\w+)\s*\[([^\]]+)\]`
4. Returns structured steps

Example Output:

```python
{
    "plan_string": "Plan: Read BRD...\n#E1 = FileReader['files/brd.pdf']...",
    "steps": [
        ("Read BRD document", "#E1", "FileReader", "files/brd.pdf"),
        ("Extract epics", "#E2", "LLM", "Identify modules from #E1"),
        ...
    ]
}
```

### 2. Tool Executor (`app/tool_executor.py`)

Purpose: Execute tools defined in the plan

Supported Tools:

- FileReader (PyMuPDF)
- LLM (Gemini 2.0 Flash)
- Google (Tavily Search; query truncated to 400 chars)

Dependency Resolution:

- Replaces `#E1`, `#E2`, etc. with actual results
- Example: `"Analyze #E1"` → `"Analyze [actual BRD text]"`

### 3. Solver (`app/solver.py`)

Purpose: Synthesize final project plan from all evidence

Process:

1. Combines all plans and results
2. Loads `solver_prompt.txt`
3. Invokes LLM with complete context
4. Saves output to `outputs/project_plan_TIMESTAMP.md`

Sections Generated:

- Project Overview
- Epics/Modules
- Functional Requirements (User Stories)
- Non-Functional Requirements
- Dependencies & Constraints
- Risks & Assumptions
- Project Milestones
- Summary

### 4. Graph (`app/graph.py`)

Purpose: Orchestrate the workflow using LangGraph

Nodes:

- `plan`: Planning stage
- `tool`: Tool execution (with loop)
- `solve`: Final synthesis

Edges:

- `START → plan`
- `plan → tool`
- `tool → (conditional: tool or solve)`
- `solve → END`

### 5. Document Intelligence (`core/*`, `agents/*`)

- `core/document_intelligence_pipeline.py`: Orchestrates classification, extraction, and analysis with caching
- `agents/document_classifier.py`: Content-only classification (ignores filename)
- `agents/content_extractor.py`: Type-aware extraction into a structured JSON-like schema
- `core/document_analyzer.py`: Finds gaps/conflicts, consolidates risks/dependencies/constraints, produces Markdown/JSON reports
- `core/cache_manager.py`: Caches per-file results and analysis for speed

---

## 📊 Output Format

Generated project plans follow this structure:

```markdown
# Project Name: Complete Project Plan

## 1. Project Overview

High-level summary, objectives, and scope

## 2. Epics / Modules

- Epic 1: Description
  - Module components
- Epic 2: Description
  ...

## 3. Functional Requirements (User Stories)

### Epic 1

- **US 1.1**: As a [user], I want [feature], so that [benefit]
  - Acceptance Criteria: [...]
- **US 1.2**: ...

## 4. Non-Functional Requirements

- Performance: [specifications]
- Security: [requirements]
- Scalability: [constraints]
- Technology Stack: [details]

## 5. Dependencies & Constraints

- Technical dependencies
- Third-party integrations
- Timeline constraints

## 6. Risks & Assumptions

### Risks

- Risk 1: [description] → Mitigation: [strategy]

### Assumptions

- Assumption 1: [description]

## 7. Project Milestones

### Phase 1: [Name] (Timeline)

- Deliverable 1
- Deliverable 2

### Phase 2: [Name] (Timeline)

...

## 8. Summary

Overall assessment and next steps
```

---

## 🧪 Testing

Run the pipeline smoke test and legacy loader test:

```bash
# Windows (cmd.exe)
python test_document_intelligence.py
```

Expected artifacts will be written under `outputs/test_intermediate/` and console will display coverage/readiness/confidence.

## ⚠️ Known quirks

- Feasibility file name mismatch: `generate_feasibility_questions.py` writes `outputs/feasibility_assessment.md` but the planner/solver currently read `outputs/feasibility_questions.md`. Until unified, please rename the file after generation (see Usage), or adjust the code paths in `app/plan.py` and `app/solver.py`.
- Python 3.13 required (see `pyproject.toml`). If your default `python` points to an older version, use `py -3.13` on Windows when creating the venv.

## 🧩 Dependencies

Key libraries (see `requirements.txt` / `pyproject.toml`):

- langgraph, langchain-core/community, langchain-google-genai, langchain-tavily
- PyMuPDF (fitz)
- rich, python-dotenv
- numpy, pydantic, pyyaml, requests

Python version: `>=3.13`

## 🤝 Contributing

Contributions are welcome! Typical flow:

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Commit your changes: `git commit -m "Add amazing feature"`
4. Push to the branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 🙏 Acknowledgments

- ReWOO Paper: https://arxiv.org/abs/2305.18323
- LangGraph: State-of-the-art agent orchestration
- Google Gemini: Powerful language model capabilities
- Tavily: Advanced AI search API

---

## 📧 Support

For assessment, issues, or feature requests:

- Open an issue on GitHub
- Contact the maintainers
