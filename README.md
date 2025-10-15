# ReWOO Demonstration Project

A sophisticated implementation of the **ReWOO (Reasoning WithOut Observation)** paradigm using LangGraph, designed to generate comprehensive project plans from Business Requirement Documents (BRDs). This project demonstrates advanced agentic reasoning by decoupling planning from execution, enabling efficient multi-step reasoning with minimal LLM calls.

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
- [Dependencies](#dependencies)
- [Contributing](#contributing)
- [License](#license)

---

## 🎯 Overview

This project implements the **ReWOO (Reasoning WithOut Observation)** framework, which is an advanced reasoning pattern that separates planning from execution. It's specifically designed to analyze Business Requirement Documents (BRDs) and automatically generate structured, comprehensive project plans in Markdown format.

### What is ReWOO?

ReWOO is an agentic reasoning pattern that:

- **Plans first**: Creates a complete execution plan upfront
- **Executes sequentially**: Runs each step without re-planning
- **Synthesizes results**: Combines all evidence into a final solution
- **Minimizes LLM calls**: More efficient than traditional ReAct patterns

This implementation uses:

- **LangGraph** for orchestrating the reasoning workflow
- **Google Gemini 2.5 Flash** for language model operations
- **PyMuPDF** for PDF document processing
- **Tavily Search** for web-based information retrieval

---

## 🏗️ Architecture

The project follows a **state-driven graph architecture** powered by LangGraph:

```
┌─────────────────────────────────────────────────────────┐
│                    ReWOO State                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │ • task: str                                       │  │
│  │ • plan_string: str                                │  │
│  │ • steps: List[tuple]                              │  │
│  │ • results: dict                                   │  │
│  │ • result: str                                     │  │
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

1. **States** (`states/rewoo_state.py`): Pydantic model defining the agent's state
2. **Planner** (`app/plan.py`): Generates multi-step reasoning plans
3. **Tool Executor** (`app/tool_executor.py`): Executes tools (LLM, FileReader, Google Search)
4. **Solver** (`app/solver.py`): Synthesizes results into final output
5. **Graph** (`app/graph.py`): Orchestrates the workflow using LangGraph
6. **Main** (`main.py`): Entry point with rich console output

---

## 🔄 Project Flow

### 1. **Planning Stage** 🧩

```
Input: Task description (e.g., "Create project plan from BRD")
         ↓
   Planner reads planner_prompt.txt
         ↓
   LLM generates structured plan with steps
         ↓
   Output: Plan string + parsed steps
```

**Example Plan:**

```
Plan: Read the BRD document to extract raw text
#E1 = FileReader['files/brd_1.pdf']

Plan: Identify key project epics from the BRD
#E2 = LLM[Extract high-level modules from #E1]

Plan: Generate user stories for each epic
#E3 = LLM[Break down #E2 into user stories]
...
```

### 2. **Tool Execution Stage** 🔧

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

**Conditional Routing:**

- If more steps remain → Loop back to TOOL node
- If all steps complete → Route to SOLVE node

### 3. **Solving Stage** 🧠

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

- **🤖 Automated Planning**: Intelligent multi-step plan generation from prompts
- **📄 PDF Processing**: Extracts and analyzes BRD documents using PyMuPDF
- **🔍 Web Search Integration**: Tavily-powered search for domain clarifications
- **🧠 LLM Reasoning**: Google Gemini 2.5 Flash for analysis and synthesis
- **📊 Structured Output**: Comprehensive Markdown project plans with 8 sections
- **🎨 Rich Console UI**: Beautiful terminal output with tables, panels, and progress indicators
- **🔁 Stateful Execution**: LangGraph manages state transitions seamlessly
- **🛡️ Error Handling**: Robust validation for query truncation and tool execution
- **📦 Modular Design**: Clean separation of concerns across components

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
├── config/                       # Configuration modules
│   └── llm_config.py             # LLM setup (Google Gemini)
│
├── states/                       # State definitions
│   └── rewoo_state.py            # ReWOO state Pydantic model
│
├── tools/                        # External tool integrations
│   └── search_tool.py            # Tavily search wrapper
│
├── utils/                        # Helper utilities
│   └── helper.py                 # Routing, task management, prompt loading
│
├── prompts/                      # LLM prompt templates
│   ├── planner_prompt.txt        # Planning stage instructions
│   └── solver_prompt.txt         # Solving stage instructions
│
├── files/                        # Input documents (BRDs)
│   └── brd_1.pdf                 # Example BRD
│
├── outputs/                      # Generated project plans
│   └── project_plan_*.md         # Timestamped Markdown outputs
│
├── main.py                       # Application entry point
├── pyproject.toml                # Project metadata and dependencies
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

[UV](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. **Install UV** (if not already installed):

   ```bash
   # Windows (PowerShell)
   powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

   # macOS/Linux
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # If your system does not have curl, you can use wget:
   wget -qO- https://astral.sh/uv/install.sh | sh
   ```

2. **Clone the repository**:

   ```bash
   git clone https://github.com/Arslaan-Siddiqui-TSM/PM-Agent-using-ReWOO.git
   cd rewoo-demonstration
   ```

3. **Install dependencies**:

   ```bash
   uv sync
   ```

4. **Activate the virtual environment**:

   ```bash
   # Windows
   .venv\Scripts\activate

   # macOS/Linux
   source .venv/bin/activate
   ```

### Using pip

1. **Clone the repository**:

   ```bash
   git clone https://github.com/Arslaan-Siddiqui-TSM/PM-Agent-using-ReWOO.git
   cd rewoo-demonstration
   ```

2. **Create a virtual environment**:

   ```bash
   python -m venv venv
   ```

3. **Activate the virtual environment**:

   ```bash
   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

4. **Install dependencies**:

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

1. **Google Gemini API**:

   - Visit [Google AI Studio](https://aistudio.google.com/app/api-keys)
   - Create a new API key
   - Copy to `.env` file

2. **Tavily API**:
   - Sign up at [Tavily](https://tavily.com/)
   - Get your API key from the dashboard
   - Copy to `.env` file

### Model Configuration

Edit `config/llm_config.py` to customize the LLM:

```python
model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",  # Change model here
    temperature=0.6,            # Adjust creativity (0.0-1.0)
    google_api_key=GOOGLE_API_KEY
)
```

---

## 💻 Usage

### Basic Usage

1. **Place your BRD** in the `files/` directory (e.g., `files/brd_1.pdf`)

2. **Update the task** in `main.py`:

   ```python
   task = "Create a complete project plan in Markdown format based on the BRD document located at 'files/brd_1.pdf'."
   ```

3. **Run the application**:

   ```bash
   python main.py
   ```

4. **View the output**:
   - Console: Real-time progress with rich formatting
   - File: `outputs/project_plan_YYYYMMDD_HHMMSS.md`

### Console Output

The application provides beautiful formatted output:

```
════════════════════════════════════════════════
🔍 Executing ReWOO Reasoning Graph
════════════════════════════════════════════════

═══════════════ 🧩 Planning Stage ═══════════════
┌─── Generated Plan ───────────────────────────┐
│ Plan: Read the BRD document...               │
│ #E1 = FileReader['files/brd_1.pdf']          │
│ ...                                           │
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
│ ...                                           │
└───────────────────────────────────────────────┘
```

---

## 🔍 How It Works

### ReWOO Pattern Explained

1. **Separation of Planning and Execution**:

   - Traditional ReAct: Plan → Observe → Plan → Observe (multiple LLM calls)
   - ReWOO: Plan all → Execute all → Solve (fewer LLM calls, more efficient)

2. **Evidence-Based Reasoning**:

   - Each step produces evidence (e.g., #E1, #E2)
   - Subsequent steps reference previous evidence
   - Final solver uses all evidence to generate output

3. **Tool Orchestration**:
   - **FileReader**: Reads PDF documents, extracts text
   - **LLM**: Performs reasoning, analysis, extraction
   - **Google**: Searches web for clarifications (max 400 chars)

### State Management

The `ReWOO` state object flows through the graph:

```python
class ReWOO(BaseModel):
    task: str              # Initial user request
    plan_string: str       # Generated plan text
    steps: List[tuple]     # Parsed steps [(plan, evidence_id, tool, input)]
    results: dict          # Execution results {evidence_id: result}
    result: str            # Final synthesized output
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

**Purpose**: Generate structured multi-step reasoning plans

**Process**:

1. Loads `planner_prompt.txt`
2. Invokes LLM with task description
3. Parses output using regex: `Plan:\s*(.+)\s*(#E\d+)\s*=\s*(\w+)\s*\[([^\]]+)\]`
4. Returns structured steps

**Example Output**:

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

**Purpose**: Execute tools defined in the plan

**Supported Tools**:

- **FileReader**:

  ```python
  with fitz.open(file_path) as doc:
      text = "".join(page.get_text("text") for page in doc)
  ```

- **LLM**:

  ```python
  result = model.invoke(tool_input)
  ```

- **Google**:
  ```python
  # Truncates query to 400 chars if needed
  result = search.invoke(tool_input)
  ```

**Dependency Resolution**:

- Replaces `#E1`, `#E2`, etc. with actual results
- Example: `"Analyze #E1"` → `"Analyze [actual BRD text]"`

### 3. Solver (`app/solver.py`)

**Purpose**: Synthesize final project plan from all evidence

**Process**:

1. Combines all plans and results
2. Loads `solver_prompt.txt`
3. Invokes LLM with complete context
4. Saves output to `outputs/project_plan_TIMESTAMP.md`

**Generated Sections**:

1. Project Overview
2. Epics/Modules
3. Functional Requirements (User Stories)
4. Non-Functional Requirements
5. Dependencies & Constraints
6. Risks & Assumptions
7. Project Milestones
8. Summary

### 4. Graph (`app/graph.py`)

**Purpose**: Orchestrate the workflow using LangGraph

**Nodes**:

- `plan`: Planning stage
- `tool`: Tool execution (with loop)
- `solve`: Final synthesis

**Edges**:

- `START → plan`: Initialize
- `plan → tool`: Execute first tool
- `tool → (conditional)`: Route based on completion
  - If incomplete → `tool` (loop)
  - If complete → `solve`
- `solve → END`: Finish

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


## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Commit your changes**: `git commit -m 'Add amazing feature'`
4. **Push to the branch**: `git push origin feature/amazing-feature`
5. **Open a Pull Request**


## 🙏 Acknowledgments

- **ReWOO Paper**: [Reasoning WithOut Observation](https://arxiv.org/abs/2305.18323)
- **LangGraph**: State-of-the-art agent orchestration
- **Google Gemini**: Powerful language model capabilities
- **Tavily**: Advanced AI search API

---

## 📧 Support

For questions, issues, or feature requests:

- Open an issue on GitHub
- Contact the maintainers

---