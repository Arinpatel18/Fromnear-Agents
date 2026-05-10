# 🚀 FromNear — Multi-Agent AI Sales & Marketing Intelligence

An autonomous, multi-agent AI pipeline that researches, analyses, and generates personalized vendor onboarding strategies and launch marketing plans for [FromNear](https://fromnear.com) — India's hyperlocal quick-commerce platform.

> **One click. Six agents. Complete vendor intelligence.**

---

## 📋 Table of Contents

- [Architecture](#-architecture)
- [Multi-Agent System](#-multi-agent-system)
- [Model Choices](#-model-choices)
- [Local AI Setup](#-local-ai-setup)
- [Orchestration](#-orchestration)
- [Memory & CRM](#-memory--crm)
- [Structured Output](#-structured-output)
- [Scaling Approach](#-scaling-approach)
- [Getting Started](#-getting-started)
- [Project Structure](#-project-structure)
- [Environment Variables](#-environment-variables)

---

## 🏗 Architecture

![Alt text](images/Architecture_diagram.png)

### Pipeline Flow

```
User Input (URL + Instagram + Category + Location)
    │
    ▼
┌─────────────────────────────────────────────────┐
│  1. INPUT NODE                                  │
│     • Crawl4AI: Scrape website content          │
│     • Apify: Scrape Instagram profile + posts   │
│     • LLM: Extract business intelligence (JSON) │
│     • Regex: Extract contacts, emails, socials  │
└──────────────────┬──────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────┐
│  2. RESEARCH AGENT                              │
│     • Market positioning (size, niche, pricing) │
│     • Competitive landscape analysis            │
│     • Digital footprint scoring                 │
│     • Vendor readiness assessment               │
│     • Key business insights                     │
└──────────────────┬──────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────┐
│  3. MEMORY NODE                                 │
│     • Query SQLite for similar past vendors     │
│     • Inject historical context into state      │
│     • Enable learning from past analyses        │
└──────────────┬───────────┬──────────────────────┘
               ▼           ▼
┌──────────────────┐ ┌──────────────────┐
│ 4. SALES AGENT   │ │ 5. MARKETING     │  ← Parallel
│  • Reasoning     │ │    AGENT         │
│  • Lead scoring  │ │  • Reasoning     │
│  • Outreach plan │ │  • Ad campaigns  │
│  • Pitch         │ │  • IG content    │
│  • Follow-ups    │ │  • Launch plan   │
│  • Next steps    │ │  • Growth plan   │
└────────┬─────────┘ └────────┬─────────┘
         ▼                    ▼
┌─────────────────────────────────────────────────┐
│  6. VALIDATOR AGENT                             │
│     • Data grounding check                      │
│     • Cross-agent consistency validation        │
│     • Actionability scoring                     │
│     • Quality score (0-100)                     │
└──────────────────┬──────────────────────────────┘
                   ▼
┌─────────────────────────────────────────────────┐
│  7. AGGREGATOR                                  │
│     • Combine all outputs                       │
│     • Generate markdown report                  │
│     • Save to CRM memory                        │
│     • Track proposed campaigns                  │
└─────────────────────────────────────────────────┘
```

---

## 🤖 Multi-Agent System

| # | Agent | Role | Key Outputs |
|---|-------|------|-------------|
| 1 | **Input Node** | Web & Instagram scraping + data extraction | Structured business data, contacts, products |
| 2 | **Research Agent** | Deep market & competitive intelligence | Market position, digital footprint, vendor readiness |
| 3 | **Memory Node** | Historical context retrieval from CRM | Past similar analyses, scoring benchmarks |
| 4 | **Sales Agent** | Onboarding strategy & lead qualification | Lead score, outreach plan, personalized pitch, next steps |
| 5 | **Marketing Agent** | Launch campaign planning & growth strategy | Ad campaigns, IG content calendar, reels hooks |
| 6 | **Validator Agent** | Quality assurance & consistency checking | Quality score, data grounding, issue flagging |

Each agent demonstrates:
- **Reasoning** — Chain-of-thought analysis explaining decisions
- **Memory** — Access to past vendor analyses for consistency
- **Tool Usage** — Crawl4AI (web), Apify (Instagram), SQLite (CRM)
- **Task Execution** — Structured JSON output for each responsibility
- **Structured Workflow** — LangGraph orchestration with parallel execution

---

## 🧠 Model Choices

### Primary Model: `gemma3:12b`

| Attribute | Details |
|-----------|---------|
| **Model** | Google Gemma 3 12B |
| **Parameters** | 12 billion |
| **Size** | ~8.6 GB |
| **Why chosen** | Best balance of speed, quality, and structured output for a 12B model. Excellent at JSON generation, follows complex multi-section prompts reliably, and runs well on consumer hardware with 16GB+ RAM |

### Why Not Other Models?

| Model | Reason Not Used |
|-------|----------------|
| `llama3:8b` | Good speed but weaker at structured JSON output and multi-section prompts |
| `gemma3:27b` | Better quality but 2-3x slower; diminishing returns for our use case |
| `mistral:7b` | Fast but inconsistent with complex JSON schemas |
| `phi3:3.8b` | Too small for the nuanced business analysis required |

### Model Usage Across Agents

| Agent | Model | Temperature | Why |
|-------|-------|-------------|-----|
| Input (LLM extraction) | `gemma3:12b` | 0.0 | Pure extraction — needs deterministic output |
| Research | `gemma3:12b` | 0.2 | Low creativity, high accuracy for market analysis |
| Sales | `gemma3:12b` | 0.3 | Slight creativity for pitch personalization |
| Marketing | `gemma3:12b` | 0.3 | Creative campaign ideas with data grounding |
| Validator | `gemma3:12b` | 0.1 | Strict, factual validation — minimal creativity |

### Switching Models

Change models in `.env` without touching code:

```env
SALES_AGENT_MODEL=gemma3:27b        # upgrade for better quality
MARKETING_AGENT_MODEL=mistral:7b     # downgrade for faster speed
```

---

## 🖥 Local AI Setup

### Prerequisites

1. **Ollama** — Local LLM inference server
2. **Python 3.11+** — Runtime
3. **16GB+ RAM** — Recommended for `gemma3:12b`

### Step 1: Install Ollama

```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.com/install.sh | sh

# Windows
# Download from https://ollama.com/download
```

### Step 2: Pull the Model

```bash
# Pull the primary model (required)
ollama pull gemma3:12b

# Verify it's available
ollama list
```

### Step 3: Start Ollama Server

```bash
# Start the server (runs on http://localhost:11434)
ollama serve
```

### Step 4: Set Up the Project

```bash
# Clone the repository
git clone https://github.com/Arinpatel18/Fromnear-Agents.git
cd Fromnear-Agents

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env   # or edit .env directly
```

### Step 5: Run

```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

### Switching to Cloud Ollama

To use Ollama Cloud instead of local, simply update `.env`:

```env
OLLAMA_BASE_URL=https://api.ollama.com
OLLAMA_API_KEY=your_cloud_api_key_here
```

No code changes required — the `llm_client.py` auto-detects and applies auth headers.

---

## 🔄 Orchestration

### LangGraph Workflow

The pipeline is built with **LangGraph** — a framework for building stateful, multi-actor applications with LLMs.

```python
# Simplified graph structure
workflow = StateGraph(AgentState)

workflow.add_node("input_node", process_input)
workflow.add_node("research_agent", research_agent)
workflow.add_node("memory_node", memory_node)
workflow.add_node("sales_agent", sales_agent)
workflow.add_node("marketing_agent", marketing_agent)
workflow.add_node("validator_agent", validator_agent)
workflow.add_node("aggregator", aggregator)

# Sequential: input → research → memory
workflow.add_edge("input_node", "research_agent")
workflow.add_edge("research_agent", "memory_node")

# Parallel fan-out: memory → [sales, marketing]
workflow.add_edge("memory_node", "sales_agent")
workflow.add_edge("memory_node", "marketing_agent")

# Convergence: [sales, marketing] → validator
workflow.add_edge("sales_agent", "validator_agent")
workflow.add_edge("marketing_agent", "validator_agent")

# Final: validator → aggregator → END
workflow.add_edge("validator_agent", "aggregator")
workflow.add_edge("aggregator", END)
```

### Key Orchestration Features

| Feature | Implementation |
|---------|---------------|
| **Parallel Execution** | Sales & Marketing agents run simultaneously via LangGraph fan-out |
| **State Management** | `AgentState` TypedDict flows through all nodes — each agent reads/writes specific fields |
| **Autonomous Flow** | End-to-end execution with zero manual intervention |
| **Error Isolation** | Each agent catches exceptions independently — one failure doesn't crash the pipeline |
| **Async Support** | `nest_asyncio` enables async scraping within Streamlit's event loop |

### State Flow

```python
class AgentState(TypedDict):
    raw_input: Dict              # User input (URLs, category, location)
    structured_data: Dict        # Scraped + extracted business data
    research_output: Dict        # Research agent findings
    memory_context: Dict         # Past similar vendor analyses
    sales_output: Dict           # Sales strategy + lead score
    marketing_output: Dict       # Campaign plans + content ideas
    validation_report: Dict      # Quality validation results
    aggregated_output: Dict      # Final combined output
```

---

## 💾 Memory & CRM

### Local CRM Database (SQLite)

The pipeline maintains a persistent local CRM at `data/memory.db` with three tables:

| Table | Purpose | Auto-populated |
|-------|---------|----------------|
| `vendor_analyses` | Full analysis history with scores, research, validation | ✅ After every pipeline run |
| `vendor_notes` | CRM-style interaction logs per vendor | ✅ Auto-noted on analysis |
| `campaign_tracking` | Proposed campaigns with status lifecycle | ✅ Campaigns auto-tracked |

### How Memory Works

1. **Save**: After every analysis, the Aggregator saves the full output (lead score, confidence, research, validation) to SQLite
2. **Recall**: Before each new analysis, the Memory Node queries for vendors with similar category/location
3. **Inject**: Past analyses are injected into Sales & Marketing agent prompts as context
4. **Learn**: Agents use past scoring patterns to stay consistent across analyses

### Campaign Lifecycle

```
proposed → active → completed
                  → cancelled
```

---

## 📊 Structured Output

Every pipeline run produces structured JSON with:

```json
{
  "sales_output": {
    "reasoning": "Chain-of-thought analysis...",
    "confidence_level": 0.85,
    "business_summary": "...",
    "lead_score": {
      "overall": 8,
      "reason": "...",
      "breakdown": {
        "digital_presence": 7,
        "market_fit": 9,
        "growth_potential": 8,
        "engagement_quality": 7
      }
    },
    "pain_point_analysis": ["..."],
    "outreach_strategy": ["..."],
    "personalized_sales_pitch": ["..."],
    "follow_up_suggestions": ["..."],
    "actionable_next_steps": [
      {"action": "...", "priority": "high", "timeline": "Day 1", "owner": "BD Team"}
    ]
  },
  "marketing_output": {
    "reasoning": "...",
    "confidence_level": 0.85,
    "ad_campaigns": [...],
    "instagram_content_calendar": [...],
    "launch_campaigns": [...],
    "reels_and_hooks": [...],
    "growth_strategies": [...]
  },
  "research_output": {
    "market_positioning": {...},
    "competitive_landscape": {...},
    "digital_footprint": {"score": 7},
    "vendor_readiness": {"score": 8},
    "key_insights": [...]
  },
  "validation_report": {
    "overall_quality_score": 92,
    "data_grounding": {"score": 9, "status": "pass"},
    "consistency_check": {"score": 9, "status": "pass"},
    "actionability": {"score": 8, "status": "pass"}
  }
}
```

---

## 📈 Scaling Approach

### Current Architecture (Local)

- **Single machine** with Ollama running locally
- **SQLite** for CRM persistence
- **Streamlit** for the web interface
- Best for: Individual use, demos, development

### Scaling to Team Use

| Component | Current | Scaled |
|-----------|---------|--------|
| **LLM** | Local Ollama | Ollama Cloud / vLLM cluster |
| **Database** | SQLite | PostgreSQL with connection pooling |
| **Queue** | Synchronous LangGraph | Celery + Redis task queue |
| **UI** | Streamlit (single user) | FastAPI backend + React frontend |
| **Deployment** | Local machine | Docker Compose / Kubernetes |

### Scaling Strategies

#### 1. **Horizontal LLM Scaling**
```
Load Balancer
    ├── Ollama Instance 1 (GPU 1)
    ├── Ollama Instance 2 (GPU 2)
    └── Ollama Instance 3 (GPU 3)
```
- Deploy multiple Ollama instances behind a load balancer
- Each instance handles one agent's inference
- Parallel agents (Sales + Marketing) hit different instances

#### 2. **Database Scaling**
```env
# Switch from SQLite to PostgreSQL
DATABASE_URL=postgresql://user:pass@host:5432/fromnear_crm
```
- Migrate `memory.py` to use SQLAlchemy/asyncpg
- Add connection pooling for concurrent users
- Enable full-text search on vendor analyses

#### 3. **Async Pipeline Scaling**
```python
# Future: Replace synchronous LangGraph with async task queue
from celery import Celery

@app.task
def run_analysis(vendor_data):
    return pipeline.invoke(vendor_data)
```
- Celery workers process multiple analyses simultaneously
- Redis for task queue and result caching
- Webhook notifications on completion

#### 4. **Containerized Deployment**
```yaml
# docker-compose.yml (future)
services:
  ollama:
    image: ollama/ollama
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
  app:
    build: .
    depends_on: [ollama]
    ports: ["8501:8501"]
```

---

## 🚀 Getting Started

```bash
# 1. Clone
git clone https://github.com/Arinpatel18/Fromnear-Agents.git
cd Fromnear-Agents

# 2. Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 3. Pull the model
ollama pull gemma3:12b

# 4. Start Ollama
ollama serve

# 5. Run (in a new terminal)
streamlit run app.py
```

---

## 📁 Project Structure

```
Fromnear-Agents/
├── app.py                          # Streamlit UI — multi-agent dashboard
├── main.py                         # CLI entry point (alternative to Streamlit)
├── requirements.txt                # Python dependencies
├── .env                            # Environment configuration
├── .gitignore
│
├── src/
│   ├── state.py                    # AgentState TypedDict (pipeline state schema)
│   ├── graph.py                    # LangGraph workflow definition
│   ├── llm_client.py               # Ollama client factory (local/cloud)
│   ├── memory.py                   # SQLite CRM memory system
│   ├── company_context.py          # FromNear company context for prompts
│   ├── models.py                   # Pydantic models (if used)
│   │
│   └── nodes/
│       ├── input_node.py           # Web + Instagram scraping + extraction
│       ├── research_agent_node.py  # Market research & competitive analysis
│       ├── memory_node.py          # Memory retrieval from CRM
│       ├── sales_agent_node.py     # Sales strategy & lead scoring
│       ├── marketing_agent_node.py # Campaign planning & content strategy
│       ├── validator_node.py       # Quality validation & consistency check
│       └── aggregator_node.py      # Final assembly + CRM save
│
└── data/
    └── memory.db                   # SQLite CRM database (auto-created)
```

---

## ⚙️ Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `OLLAMA_BASE_URL` | Yes | `http://localhost:11434` | Ollama server URL (local or cloud) |
| `OLLAMA_API_KEY` | Cloud only | — | API key for Ollama Cloud |
| `SALES_AGENT_MODEL` | Yes | `gemma3:12b` | Model for Sales Agent |
| `MARKETING_AGENT_MODEL` | Yes | `gemma3:12b` | Model for Marketing Agent |
| `APIFY_API_TOKEN` | Yes | — | Apify API token for Instagram scraping |
| `LANGSMITH_TRACING` | No | `false` | Enable LangSmith trace logging |
| `LANGSMITH_API_KEY` | No | — | LangSmith API key |

---

## 📄 License

This project is built for [FromNear](https://fromnear.com) — Revolutionizing Commerce, One Local Store at a Time.
