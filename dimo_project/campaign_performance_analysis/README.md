# Campaign Performance Analysis — AI Assistant

A RAG-based conversational AI assistant for credit card campaign performance analysis. Business stakeholders can ask plain-English questions about campaign data — no SQL knowledge required.

---

## Pre-requisites

Before you begin, you need to set up a few things. Follow these steps carefully:

### 1. Python 3.10+

This project requires Python 3.10 or higher. Check your version:

```bash
python3 --version
```

If the output is `Python 3.10.x` or higher, you are good to go. If not, see the [Python setup section](#python-setup-ubuntu) below.

### 2. Get an Anthropic API Key (required)

This project uses **Claude** by Anthropic as its AI brain. You need an API key to use it.

**Step-by-step:**

1. Go to [console.anthropic.com](https://console.anthropic.com)
2. Click **Sign Up** (or **Log In** if you already have an account)
3. After signing in, go to **API Keys** in the left sidebar (or visit [console.anthropic.com/settings/keys](https://console.anthropic.com/settings/keys))
4. Click **Create Key**
5. Give it a name (e.g., "campaign-analysis") and click **Create**
6. **Copy the key immediately** — it starts with `sk-ant-api03-...` and will only be shown once

> **Important:** The API key is a secret. Never commit it to Git, never share it publicly, and never paste it directly in your code.

**Cost note:** Anthropic charges per API call. For this demo project, typical usage costs a few cents. You can set a spending limit in the Anthropic console under **Plans & Billing**.

### 3. Configure the API Key in the Project

Once you have the key, you need to tell the project about it:

```bash
# Navigate to the project directory
cd dimo_project/campaign_performance_analysis

# Copy the example env file to create your actual .env file
cp .env .env

# Open the .env file in any text editor
nano .env       # or: vim .env / code .env / gedit .env
```

Inside the `.env` file, replace the placeholder with your real key:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
```

Save and close the file. The application reads this file automatically at startup.

> **How it works internally:** The `config/settings.py` module uses `python-dotenv` to load `.env` into environment variables. The LLM provider module then reads `Settings.ANTHROPIC_API_KEY` when it creates the Claude connection. If the key is missing, you will get a clear error message telling you to set it.

### 4. Disk Space

You need approximately **500 MB** of free disk space for:
- Python packages (~200 MB)
- The `all-MiniLM-L6-v2` sentence-transformer model (~90 MB, downloaded automatically on first run)
- The SQLite database and ChromaDB vector store (~10 MB)

### 5. No Other Infrastructure Needed

That's it. No Docker, no cloud services, no database servers, no GPU. Everything runs locally on your machine using CPU only.

---

### Python Setup (Ubuntu)

If you are on Ubuntu 22.04, Python 3.10 comes pre-installed. Verify:

```bash
python3 --version
# Expected output: Python 3.10.12 (or similar)
```

If you want to install a newer version (optional — 3.10 works fine):

```bash
# Add the deadsnakes PPA (trusted source for Python versions)
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.12
sudo apt install python3.12 python3.12-venv python3.12-dev

# Verify
python3.12 --version
```

To use the new version for this project, create the virtual environment with it:

```bash
python3.12 -m venv venv    # instead of python3 -m venv venv
source venv/bin/activate
```

---

## What This Project Does (In Simple Terms)

Credit card companies run marketing campaigns — things like "5% cashback on groceries" or "double miles on travel." After running these campaigns, business teams need to answer questions like:

- "Which campaign got the most sign-ups?"
- "What was the return on investment for the holiday campaign?"
- "Compare the performance of our cashback vs. travel campaigns"

**The problem:** Answering these questions traditionally requires knowing SQL (a database language), understanding business metrics, and manually writing reports.

**Our solution:** An AI chatbot that lets you ask these questions in plain English. You type your question, and the AI:
1. Figures out what data you need
2. Writes and runs the correct database query
3. Looks up campaign details from the knowledge base (what the campaign offers, who it targets)
4. Uses its own business knowledge to interpret the numbers (ROI, trends, benchmarks)
5. Gives you a clear, human-readable answer

No SQL knowledge, no manual reports, no waiting for the analytics team.

---

## Requirements

To run this project, you need:

1. **Python 3.10 or higher** — The programming language everything is written in
2. **pip** — Python's package manager (comes with Python)
3. **An Anthropic API key** — To access Claude, the AI model that powers the assistant. Get one at [console.anthropic.com](https://console.anthropic.com)
4. **About 500 MB of disk space** — For Python packages and the sentence-transformer model that gets downloaded on first run

That's it. No Docker, no cloud services, no database servers. Everything runs locally on your machine.

---

## Solution Architecture

```mermaid
graph TB
    subgraph API["FastAPI REST API"]
        E1["POST /ask"]
        E2["POST /ask/sql"]
        E3["POST /ask/search"]
        E4["GET /campaigns"]
        E5["GET /campaigns/:id/summary"]
        E6["GET /health"]
    end

    subgraph Agent["AI Agent (llm/agent.py)"]
        direction LR
        T1["sql_query_tool"]
        T2["rag_search_tool"]
        T3["performance_summary_tool"]
    end

    subgraph RAG["RAG Pipeline (rag/)"]
        direction LR
        Docs["Campaign<br/>Descriptions"] --> Chunker["Chunker"] --> VecStore["ChromaDB"]
    end

    subgraph Infra["Data Infrastructure"]
        direction LR
        SQLite["SQLite DB"]
        Config["Settings"]
    end

    Claude["Claude LLM"]

    API --> Agent
    Agent <--> Claude
    T1 --> SQLite
    T2 --> VecStore
    T3 --> SQLite
    T3 --> VecStore

    style API fill:#e3f2fd
    style Agent fill:#fce4ec
    style RAG fill:#e8f5e9
    style Infra fill:#f5f5f5
```

---

## How It Works — Data Flows with Examples

### Part 1: One-Time Ingestion (Startup)

At startup, **only company-specific data** is converted into searchable vectors. Generic business knowledge (ROI formulas, enrollment rate definitions, metric benchmarks) is NOT stored — the LLM already knows these.

#### Step 1 — Load Documents

Campaign descriptions are loaded from `rag/documents.py`. These contain facts the LLM cannot know — campaign names, target segments, reward structures, partner merchants, budgets:

```
CAMPAIGN DESCRIPTION (CMP-001):
"Summer Cashback Bonanza: A cashback rewards campaign targeting premium
 cardholders. Offers 5% cashback on grocery and gas station purchases.
 Runs during peak summer spending season. Budget: $250,000."

CAMPAIGN DESCRIPTION (CMP-003):
"Spring Dining Deal: A dining rewards campaign targeting student cardholders.
 Offers 10% cashback at partner restaurants including Olive Garden and Starbucks.
 Designed to increase engagement among younger customers. Budget: $100,000."

... (5 campaigns total)
```

**What is NOT stored here (and why):**
- Business glossary (ROI, enrollment rate, etc.) → the LLM already knows these definitions
- Performance summaries → the LLM should compute these from raw database data, not read pre-written ones

#### Step 2 — Chunk Documents

Each document is split into ~200-character overlapping pieces (`chunk_size=200`, `chunk_overlap=50`):

```
Original document (CMP-003 description, 230 chars):
┌──────────────────────────────────────────────────────────────────────────────┐
│ Spring Dining Deal: A dining rewards campaign targeting student cardholders.│
│ Offers 10% cashback at partner restaurants including Olive Garden and       │
│ Starbucks. Designed to increase engagement among younger customers.         │
│ Budget: $100,000.                                                           │
└──────────────────────────────────────────────────────────────────────────────┘

After chunking:
┌─ Chunk 0 (chars 0-200) ─────────────────────────────────────────────────────┐
│ Spring Dining Deal: A dining rewards campaign targeting student             │
│ cardholders. Offers 10% cashback at partner restaurants including Olive     │
│ Garden and Starbucks.                                                       │
└─────────────────────────────────────────────────────────────────────────────┘
┌─ Chunk 1 (chars 150-230) — overlaps with chunk 0 ──────────────────────────┐
│ including Olive Garden and Starbucks. Designed to increase engagement       │
│ among younger customers. Budget: $100,000.                                  │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Steps 3-4 — Embed and Store

Each chunk is converted to a 384-dimensional vector by the `all-MiniLM-L6-v2` model and stored in ChromaDB:

```
Chunk: "Spring Dining Deal: A dining rewards campaign targeting student
        cardholders. Offers 10% cashback at partner restaurants..."

        ↓ Embedding Model (all-MiniLM-L6-v2)

Vector: [0.042, -0.118, 0.231, 0.067, ..., -0.089]   (384 numbers)

        ↓ Stored in ChromaDB with metadata

ID:       "desc_CMP-003_chunk0"
Vector:   [0.042, -0.118, 0.231, ...]
Metadata: {type: "campaign_description", campaign_id: "CMP-003",
           chunk_index: 0, total_chunks: 2}
```

Total: 5 campaign descriptions → ~10 chunks → 10 vectors stored in ChromaDB.

---

### Part 2: Runtime Query — Case-by-Case Data Flows

At runtime, the AI Agent receives the user's question and decides which tool(s) to call. Here are three cases, from simplest to most complex:

---

#### Case 1: Definition Only (Partial RAG + LLM)

> **"What is enrollment and what are the different types of enrollment?"**

The vector DB only has campaign descriptions — no glossary, no definitions. RAG finds weak matches (campaign texts that mention "enrollment"). Claude provides the actual definition from its trained knowledge.

```
USER QUESTION
│  "What is enrollment and what are the different types of enrollment?"
│
▼
AGENT DECISION
│  "This is a definition question. I'll check the knowledge base for
│   context, but I likely know the definition myself → use rag_search_tool"
│
▼
RAG SEARCH (weak matches — vector DB has campaign descriptions, not definitions)
│
│  ┌─ Step 6: Embed the Query ──────────────────────────────────────────┐
│  │ "What is enrollment and what are the different types"               │
│  │     ↓ all-MiniLM-L6-v2 model                                       │
│  │ Query Vector: [-0.033, 0.215, 0.087, ..., 0.142]  (384 dims)       │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Step 7: Semantic Search (cosine similarity) ──────────────────────┐
│  │ Compare query vector against all ~10 stored vectors...              │
│  │                                                                     │
│  │ CMP-005 desc "...Targets all segments         │
│  │   to grow the cardholder base..."  → distance: 1.05  ✓ closest     │
│  │ CMP-001 desc "...targeting premium             │
│  │   cardholders..."                  → distance: 1.12  ✓ 2nd        │
│  │ CMP-003 desc "...targeting student             │
│  │   cardholders..."                  → distance: 1.15  ✓ 3rd        │
│  │                                                                     │
│  │ Note: ALL distances >1.0 = very weak matches. The vector DB        │
│  │ simply does not have definitions — only campaign descriptions.      │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Step 8: Retrieved Chunks (top 3) ─────────────────────────────────┐
│  │ [Source 1] Type: campaign_description | Campaign: CMP-005           │
│  │ "Launch Cashback Offer: A new customer acquisition campaign         │
│  │  offering flat 3% cashback on all purchases for the first 90 days.  │
│  │  Targets all segments to grow the cardholder base."                 │
│  │                                                                     │
│  │ [Source 2] Type: campaign_description | Campaign: CMP-001           │
│  │ "Summer Cashback Bonanza: A cashback rewards campaign targeting     │
│  │  premium cardholders..."                                            │
│  │                                                                     │
│  │ [Source 3] Type: campaign_description | Campaign: CMP-003           │
│  │ "Spring Dining Deal: A dining rewards campaign targeting student    │
│  │  cardholders..."                                                    │
│  └─────────────────────────────────────────────────────────────────────┘
│
▼
AGENT SYNTHESIZES (LLM provides the definition from its own knowledge)
│  RAG provided: campaign descriptions (weak matches, but some context
│  about how campaigns target different segments)
│  Claude provides: the actual definition of enrollment + types from
│  its trained knowledge — this is NOT in the vector DB at all
│
▼
FINAL ANSWER
   "Enrollment refers to the process of signing up or registering for a
    program or campaign. Types include:
    - Open enrollment: anyone can sign up during a defined window
    - Targeted enrollment: only pre-selected customers are eligible
    - Auto-enrollment: customers are enrolled automatically
    In our campaigns, different segments are targeted — for example,
    CMP-005 targets all segments while CMP-001 targets premium only."
```

**Key takeaway:** Generic business definitions belong in the LLM, not the vector DB. The LLM already knows what "enrollment" means. RAG is only useful for company-specific facts.

---

#### Case 2: Simple Data Question (RAG + SQL + LLM)

> **"What is enrollment rate and which campaign has the highest enrollment?"**

This is a compound question. The agent uses its own knowledge for the definition, calls `sql_query_tool` for the data, and optionally calls `rag_search_tool` for campaign context.

```
USER QUESTION
│  "What is enrollment rate and which campaign has the highest enrollment?"
│
▼
AGENT DECISION
│  "This has two parts:
│   - Definition of enrollment rate → I know this already (LLM knowledge)
│   - Data about highest enrollment → use sql_query_tool
│   - Campaign context → use rag_search_tool"
│
▼
SQL QUERY (data — which campaign has the most enrollments)
│
│  ┌─ Step 9: Augmented Prompt ──────────────────────────────────────────┐
│  │ "You are a SQL expert. Given this database schema:                  │
│  │  CREATE TABLE campaigns (campaign_id, campaign_name, ...)           │
│  │  CREATE TABLE enrollments (enrollment_id, campaign_id, ...)         │
│  │                                                                     │
│  │  Generate a SQLite SELECT query to answer:                          │
│  │  'Which campaign has the highest enrollment?'"                      │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Steps 10-11: Claude generates SQL ─────────────────────────────────┐
│  │ SELECT c.campaign_name, COUNT(e.enrollment_id) AS total             │
│  │ FROM campaigns c JOIN enrollments e ON c.campaign_id = e.campaign_id│
│  │ GROUP BY c.campaign_name ORDER BY total DESC LIMIT 5                │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ SQL Execution Result ──────────────────────────────────────────────┐
│  │ [{"campaign_name": "Spring Dining Deal", "total": 180},            │
│  │  {"campaign_name": "Launch Cashback Offer", "total": 163},         │
│  │  {"campaign_name": "Summer Cashback Bonanza", "total": 142}]       │
│  └─────────────────────────────────────────────────────────────────────┘
│
▼
RAG SEARCH (campaign context — what is "Spring Dining Deal"?)
│
│  ┌─ Steps 6-8: Semantic Search ──────────────────────────────────────┐
│  │ Query: "Spring Dining Deal campaign"                               │
│  │                                                                    │
│  │ CMP-003 desc "Spring Dining Deal: A dining  │
│  │   rewards campaign targeting student         │
│  │   cardholders..."                → distance: 0.25  ✓ strong!      │
│  └────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Retrieved: Campaign Description ─────────────────────────────────┐
│  │ "Spring Dining Deal: A dining rewards campaign targeting student   │
│  │  cardholders. Offers 10% cashback at partner restaurants including │
│  │  Olive Garden and Starbucks. Budget: $100,000."                    │
│  └────────────────────────────────────────────────────────────────────┘
│
▼
AGENT SYNTHESIZES
│  LLM knowledge: definition of enrollment rate
│  SQL data: which campaigns have the most enrollments
│  RAG context: what those campaigns actually are (target, rewards, budget)
│
▼
FINAL ANSWER
   "Enrollment rate is the percentage of users who enroll in a campaign
    after seeing it, calculated as (enrollments / impressions) × 100.
    A good rate for credit card campaigns is typically 5-15%.

    The Spring Dining Deal (CMP-003) has the highest enrollment with
    180 sign-ups — this is a dining rewards campaign targeting students
    with 10% cashback at Olive Garden and Starbucks on a $100K budget.
    Followed by Launch Cashback Offer (CMP-005) with 163 and Summer
    Cashback Bonanza (CMP-001) with 142."
```

**Key takeaway:** Each source provides what it's best at — LLM knows generic definitions, SQL has the numbers, RAG has company-specific campaign details. Claude weaves all three into one coherent answer.

---

#### Case 3: Complex Report Request (RAG + SQL + LLM)

> **"Give me a performance summary for CMP-003"**

The agent calls `performance_summary_tool`, which fetches raw data from SQL, campaign context from RAG, and then Claude **intelligently computes** metrics and writes the narrative.

```
USER QUESTION
│  "Give me a performance summary for CMP-003"
│
▼
AGENT DECISION
│  "This is a report request → use performance_summary_tool"
│
▼
PERFORMANCE SUMMARY TOOL
│
│  ┌─ SQL Query 1: Monthly performance metrics (RAW DATA) ─────────────┐
│  │ SELECT cp.*, c.campaign_name, c.campaign_type, c.budget_allocated   │
│  │ FROM campaign_performance cp JOIN campaigns c ...                    │
│  │ WHERE cp.campaign_id = 'CMP-003' ORDER BY cp.month                  │
│  │                                                                     │
│  │ Result (raw numbers — no interpretation yet):                       │
│  │  [{month: "2024-03", enrollments: 45, redemptions: 33, roi: 185},  │
│  │   {month: "2024-04", enrollments: 72, redemptions: 55, roi: 210},  │
│  │   {month: "2024-05", enrollments: 63, redemptions: 48, roi: 225}]  │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ SQL Query 2: Total enrollments (RAW DATA) ───────────────────────┐
│  │ SELECT COUNT(*) as total_enrollments FROM enrollments               │
│  │ WHERE campaign_id = 'CMP-003'                                       │
│  │                                                                     │
│  │ Result: [{total_enrollments: 180}]                                  │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ SQL Query 3: Total redemptions + amount (RAW DATA) ──────────────┐
│  │ SELECT COUNT(*) as total_redemptions, SUM(redemption_amount)        │
│  │ FROM redemptions WHERE campaign_id = 'CMP-003'                      │
│  │                                                                     │
│  │ Result: [{total_redemptions: 136, total_amount: 8420.50}]           │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ RAG Search: Campaign Description (COMPANY-SPECIFIC CONTEXT) ─────┐
│  │ Query: "campaign CMP-003 description"                               │
│  │                                                                     │
│  │ Retrieved (what this campaign is about — LLM can't know this):     │
│  │   "Spring Dining Deal: A dining rewards campaign targeting student  │
│  │    cardholders. Offers 10% cashback at partner restaurants including│
│  │    Olive Garden and Starbucks. Designed to increase engagement      │
│  │    among younger customers. Budget: $100,000."                      │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Step 9: Augmented Prompt ─────────────────────────────────────────┐
│  │ "Generate a performance summary for campaign CMP-003.               │
│  │                                                                     │
│  │  Raw Data (from database):                                          │
│  │    performance_metrics: [3 monthly rows]                            │
│  │    enrollment_totals: [{total_enrollments: 180}]                    │
│  │    redemption_totals: [{total_redemptions: 136,                     │
│  │                         total_amount: 8420.50}]                     │
│  │                                                                     │
│  │  Campaign Description (from knowledge base):                        │
│  │    Spring Dining Deal: targeting students, 10% cashback...          │
│  │                                                                     │
│  │  Instructions: Using YOUR knowledge of business metrics (ROI,       │
│  │  enrollment rate, redemption rate, cost-per-enrollment), analyze    │
│  │  the raw data and write a 3-4 paragraph report. Calculate derived  │
│  │  metrics yourself from the raw numbers."                            │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  Steps 10-11: Claude COMPUTES metrics and generates the narrative
│  - Redemption rate = 136/180 = 75.6% (Claude calculates this)
│  - Cost per enrollment = $100,000/180 = $556 (Claude calculates this)
│  - Trend analysis: enrollment peaked in April (Claude observes this)
│
▼
FINAL ANSWER
   "The Spring Dining Deal (CMP-003) demonstrated strong performance,
    particularly among student cardholders. With 180 total enrollments
    and a redemption rate of 75.6% (136 out of 180), the campaign
    exceeded typical industry benchmarks of 40-70%.

    Monthly trends show enrollment peaking in April (72) before settling
    to 63 in May, while ROI climbed steadily from 185% to 225%.
    Total redemption value reached $8,420.50, averaging $61.92 per
    redemption.

    On a modest $100,000 budget, cost-per-enrollment was $556, and
    the campaign achieved an impressive average ROI of 207%.
    Recommendation: expand dining partnerships with similar student-
    focused merchants and increase budget allocation next quarter."
```

**Key takeaway:** The vector DB provides only what the LLM can't know (campaign description). SQL provides raw numbers. The LLM does all the intelligent work — calculating derived metrics, interpreting trends, comparing against benchmarks, and writing the narrative. No pre-written summaries needed.

---

## Project Structure

```
campaign_performance_analysis/
├── config/
│   ├── __init__.py
│   └── settings.py                          # Centralized configuration & constants
├── database/
│   ├── __init__.py
│   ├── campaign_db.py                       # SQLite loader, schema, safe query exec
│   └── data/
│       ├── __init__.py
│       └── generate_mock_data.py            # Faker-based CSV data generator
│
├── rag/                                     # CATEGORY 1: RAG Pipeline (Knowledge Retrieval)
│   ├── __init__.py                          #   Public API re-exports
│   ├── documents.py                         #   Step 1: Campaign descriptions (company-specific only)
│   ├── chunking.py                          #   Step 2: Text splitting
│   └── vector_store.py                      #   Steps 3-4, 6-8: Embed, Store, Search
│
├── llm/                                     # CATEGORY 2: LLM Intelligence (Content Generation)
│   ├── __init__.py                          #   Public API re-exports
│   ├── provider.py                          #   Claude LLM init + system prompt
│   ├── tools/
│   │   ├── __init__.py                      #   ALL_TOOLS list
│   │   ├── sql_query.py                     #   Steps 9-11: NL → SQL → execute
│   │   ├── rag_search.py                    #   Bridge to Category 1 (Steps 6-8)
│   │   └── performance_summary.py           #   Steps 9-11: Hybrid DB+RAG report
│   └── agent.py                             #   Steps 5, 9-11: LangGraph react agent
│
├── postman/
│   └── collections/                         # API test collection
├── app.py                                   # FastAPI REST API server
├── requirements.txt
├── .env.example
└── README.md
```

---

## Setup

```bash
# 1. Navigate to the project
cd dimo_project/campaign_performance_analysis

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Anthropic API key
cp .env .env
# Edit .env and add your ANTHROPIC_API_KEY

# 5. Generate mock data
python database/data/generate_mock_data.py

# 6. Initialize the database
python database/campaign_db.py

# 7. Build the vector store
python rag/vector_store.py
```

## How to Run

```bash
uvicorn app:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. Interactive API docs (Swagger UI) at `http://localhost:8000/docs`.

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/health` | Health check — shows status of DB, knowledge base, agent |
| `GET` | `/campaigns` | List all campaigns with status, type, budget |
| `GET` | `/campaigns/{id}` | Get details for a specific campaign |
| `GET` | `/campaigns/{id}/summary` | AI-generated performance summary for a campaign |
| `POST` | `/ask` | Ask any natural language question (agent picks the best tool) |
| `POST` | `/ask/sql` | Ask a data question (forces SQL tool only) |
| `POST` | `/ask/search` | Search the knowledge base directly (RAG only) |
| `GET` | `/schema` | View the database schema |

## Example API Calls

```bash
# Health check
curl http://localhost:8000/health

# List all campaigns
curl http://localhost:8000/campaigns

# Ask a question (agent decides which tool to use)
curl -X POST http://localhost:8000/ask \
  -H "Content-Type: application/json" \
  -d '{"question": "Which campaign has the highest enrollment?"}'

# Ask a data question (SQL only)
curl -X POST http://localhost:8000/ask/sql \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the average ROI across all campaigns?"}'

# Search the knowledge base
curl -X POST http://localhost:8000/ask/search \
  -H "Content-Type: application/json" \
  -d '{"query": "What does redemption rate mean?", "n_results": 3}'

# Get a campaign summary
curl http://localhost:8000/campaigns/CMP-003/summary
```

---

## Sample Questions

**Case 1 — Definition only (Partial RAG + LLM Fallback):**
- "What is enrollment and what are the different types?"
- "What are the different campaign types in credit card marketing?"

**Case 2 — Simple data question (RAG + SQL + LLM):**
- "What is enrollment rate and which campaign has the highest enrollment?"
- "What does redemption rate mean and how does CMP-003 compare to CMP-001?"
- "Which state has the most enrollments?"
- "What is the average cost per enrollment across all campaigns?"

**Case 3 — Complex report request (RAG + SQL + LLM):**
- "Give me a performance summary for CMP-003"
- "Compare the Spring Dining Deal and Year-End Retail Special — which delivered better ROI?"

---

## Tech Stack

| Component      | Technology                               | Category | What It Does                                       |
|----------------|------------------------------------------|----------|----------------------------------------------------|
| AI Brain       | Claude (claude-sonnet-4-20250514)                  | LLM      | Understands questions, writes SQL, generates summaries |
| Orchestration  | LangChain + LangGraph                    | LLM      | Agent orchestration, tool management, conversation state |
| Knowledge Store| ChromaDB                                 | RAG      | Stores and searches campaign knowledge by meaning  |
| Text Chunking  | langchain-text-splitters                 | RAG      | Splits documents into overlapping chunks for better retrieval |
| Embeddings     | sentence-transformers (all-MiniLM-L6-v2) | RAG      | Converts text into numerical meaning vectors       |
| Database       | SQLite                                   | Infra    | Stores campaign data (file-based, no server)       |
| REST API       | FastAPI + Uvicorn                        | Infra    | HTTP endpoints with auto-generated Swagger docs    |
| Mock Data      | Faker                                    | Infra    | Generates realistic mock campaign data             |

---

## Learn More

- **[TUTORIAL_AI.md](../../TUTORIAL_AI.md)** — Step-by-step tutorial on LLM, RAG, and AI Agent concepts for beginners
- **[TUTORIAL_PYTHON.md](../../TUTORIAL_PYTHON.md)** — Step-by-step tutorial on Python patterns and libraries used here
