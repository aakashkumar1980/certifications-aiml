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
3. Looks up relevant business context
4. Gives you a clear, human-readable answer

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
        Endpoints["POST /ask  •  POST /ask/sql  •  POST /ask/search<br/>GET /campaigns  •  GET /campaigns/:id/summary  •  GET /health"]
    end

    subgraph Agent["AI Agent (llm/agent.py)"]
        direction LR
        T1["sql_query_tool"]
        T2["rag_search_tool"]
        T3["performance_summary_tool"]
    end

    subgraph RAG["RAG Pipeline (rag/)"]
        direction LR
        Docs["Documents"] --> Chunker["Chunker"] --> VecStore["ChromaDB"]
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

At startup, domain knowledge is converted into searchable vectors. Here is exactly what happens to real data:

#### Step 1 — Load Documents

Three types of documents are loaded from `rag/documents.py`:

```
CAMPAIGN DESCRIPTION (CMP-003):
"Spring Dining Deal: A dining rewards campaign targeting student cardholders.
 Offers 10% cashback at partner restaurants including Olive Garden and Starbucks.
 Designed to increase engagement among younger customers. Budget: $100,000."

PERFORMANCE SUMMARY (CMP-001):
"CMP-001 Performance Summary: The Summer Cashback Bonanza achieved a 12% enrollment
 rate with 142 enrollments from premium customers. Redemption rate was 68%, driven
 primarily by grocery purchases at Whole Foods and Costco. ROI came in at 185%..."

BUSINESS GLOSSARY:
"ROI (Return on Investment): Measures campaign profitability.
 Calculated as ((revenue - cost) / cost) * 100. For credit card campaigns,
 ROI above 100% is considered successful. Top campaigns achieve 150-250% ROI."
```

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

Total: 17 documents → ~40 chunks → 40 vectors stored in ChromaDB.

---

### Part 2: Runtime Query — Case-by-Case Data Flows

At runtime, the AI Agent receives the user's question and decides which tool(s) to call. Here are three cases, from simplest to most complex:

---

#### Case 1: Definition Only (Partial RAG + LLM Fallback)

> **"What is enrollment and what are the different types of enrollment?"**

The knowledge base has "Enrollment Rate" (a metric) but NOT a general definition of enrollment or its types. RAG finds partial matches; Claude fills the gaps from its trained knowledge.

```
USER QUESTION
│  "What is enrollment and what are the different types of enrollment?"
│
▼
AGENT DECISION
│  "This is a definition question → use rag_search_tool"
│
▼
RAG SEARCH (partial match — knowledge base does NOT have a full answer)
│
│  ┌─ Step 6: Embed the Query ──────────────────────────────────────────┐
│  │ "What is enrollment and what are the different types"               │
│  │     ↓ all-MiniLM-L6-v2 model                                       │
│  │ Query Vector: [-0.033, 0.215, 0.087, ..., 0.142]  (384 dims)       │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Step 7: Semantic Search (cosine similarity) ──────────────────────┐
│  │ Compare query vector against all 40 stored vectors...               │
│  │                                                                     │
│  │ Glossary "Enrollment Rate" chunk   → distance: 0.82  ✓ closest     │
│  │ CMP-005 summary "163 new customers"→ distance: 0.95  ✓ 2nd        │
│  │ CMP-003 summary "180 enrollments"  → distance: 0.98  ✓ 3rd        │
│  │                                                                     │
│  │ Note: distances are high (>0.8) = weak matches, not exact answers   │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Step 8: Retrieved Chunks (top 3) ─────────────────────────────────┐
│  │ [Source 1] Type: business_glossary                                  │
│  │ "Enrollment Rate: The percentage of users who enroll in a           │
│  │  campaign after seeing it. Calculated as                            │
│  │  (enrollments / impressions) * 100..."                              │
│  │                                                                     │
│  │ [Source 2] Type: performance_summary | Campaign: CMP-005            │
│  │ "Launch Cashback Offer onboarded 163 new customers across           │
│  │  all segments..."                                                   │
│  │                                                                     │
│  │ [Source 3] Type: performance_summary | Campaign: CMP-003            │
│  │ "Spring Dining Deal was highly effective with students,             │
│  │  achieving 180 enrollments through mobile channel..."               │
│  └─────────────────────────────────────────────────────────────────────┘
│
▼
AGENT SYNTHESIZES (LLM Fallback)
│  RAG provided: "enrollment rate" metric + campaign enrollment numbers
│  Claude adds from trained knowledge: general definition of enrollment
│  + types (open, targeted, auto-enrollment) that are NOT in the vector DB
│
▼
FINAL ANSWER
   "Enrollment refers to the process of signing up or registering for a
    program or campaign. Types include:
    - Open enrollment: anyone can sign up during a defined window
    - Targeted enrollment: only pre-selected customers are eligible
    - Auto-enrollment: customers are enrolled automatically
    In our campaign data, enrollment rate is tracked as the percentage
    of users who enroll after seeing a campaign (typically 5-15%).
    For example, CMP-003 achieved 180 enrollments and CMP-005 had 163."
```

**Key takeaway:** When the knowledge base has only partial information, Claude supplements with its own trained knowledge. The user gets a complete answer either way.

---

#### Case 2: Simple Data Question (RAG + SQL + LLM)

> **"What is enrollment rate and which campaign has the highest enrollment?"**

This is a compound question. The agent calls BOTH `rag_search_tool` (for the definition) AND `sql_query_tool` (for the data), then synthesizes both results.

```
USER QUESTION
│  "What is enrollment rate and which campaign has the highest enrollment?"
│
▼
AGENT DECISION
│  "This has two parts:
│   - Definition of enrollment rate → use rag_search_tool
│   - Data about highest enrollment → use sql_query_tool"
│
▼
RAG SEARCH (definition — strong match this time)
│
│  ┌─ Step 6: Embed the Query ──────────────────────────────────────────┐
│  │ "enrollment rate definition"                                        │
│  │     ↓ all-MiniLM-L6-v2 model                                       │
│  │ Query Vector: [0.078, -0.142, 0.193, ..., 0.056]  (384 dims)       │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Step 7: Semantic Search ─────────────────────────────────────────┐
│  │ Glossary "Enrollment Rate" chunk   → distance: 0.31  ✓ strong!    │
│  │ Glossary "Cost Per Enrollment"     → distance: 0.72  ✓ 2nd       │
│  │ CMP-001 summary "12% enrollment"   → distance: 0.85  ✓ 3rd       │
│  └────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Step 8: Retrieved Chunks ─────────────────────────────────────────┐
│  │ [Source 1] Type: business_glossary                                  │
│  │ "Enrollment Rate: The percentage of users who enroll in a campaign  │
│  │  after seeing it. Calculated as (enrollments / impressions) * 100.  │
│  │  A good enrollment rate for credit card campaigns is typically      │
│  │  5-15%. Higher rates indicate strong campaign messaging."           │
│  └─────────────────────────────────────────────────────────────────────┘
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
AGENT SYNTHESIZES (combines RAG definition + SQL data)
│
▼
FINAL ANSWER
   "Enrollment rate is the percentage of users who enroll in a campaign
    after seeing it, calculated as (enrollments / impressions) × 100.
    A good rate for credit card campaigns is typically 5-15%.

    The Spring Dining Deal (CMP-003) has the highest enrollment with
    180 sign-ups, followed by Launch Cashback Offer (CMP-005) with
    163 and Summer Cashback Bonanza (CMP-001) with 142."
```

**Key takeaway:** The agent can call multiple tools on a single question and merge the results — RAG provides the definition, SQL provides the data, and Claude weaves them into one coherent answer.

---

#### Case 3: Complex Report Request (RAG + SQL + LLM)

> **"Give me a performance summary for CMP-003"**

The agent calls `performance_summary_tool`, which internally runs 3 SQL queries + 1 RAG search, assembles everything into an augmented prompt, and has Claude write a narrative report.

```
USER QUESTION
│  "Give me a performance summary for CMP-003"
│
▼
AGENT DECISION
│  "This is a report request → use performance_summary_tool"
│
▼
PERFORMANCE SUMMARY TOOL (hybrid — SQL + RAG + LLM all in one tool)
│
│  ┌─ SQL Query 1: Monthly performance metrics ─────────────────────────┐
│  │ SELECT cp.*, c.campaign_name, c.campaign_type, c.budget_allocated   │
│  │ FROM campaign_performance cp JOIN campaigns c ...                    │
│  │ WHERE cp.campaign_id = 'CMP-003' ORDER BY cp.month                  │
│  │                                                                     │
│  │ Result:                                                             │
│  │  [{month: "2024-03", enrollments: 45, redemptions: 33, roi: 185},  │
│  │   {month: "2024-04", enrollments: 72, redemptions: 55, roi: 210},  │
│  │   {month: "2024-05", enrollments: 63, redemptions: 48, roi: 225}]  │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ SQL Query 2: Total enrollments ───────────────────────────────────┐
│  │ SELECT COUNT(*) as total_enrollments FROM enrollments               │
│  │ WHERE campaign_id = 'CMP-003'                                       │
│  │                                                                     │
│  │ Result: [{total_enrollments: 180}]                                  │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ SQL Query 3: Total redemptions + amount ──────────────────────────┐
│  │ SELECT COUNT(*) as total_redemptions, SUM(redemption_amount)        │
│  │ FROM redemptions WHERE campaign_id = 'CMP-003'                      │
│  │                                                                     │
│  │ Result: [{total_redemptions: 136, total_amount: 8420.50}]           │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ RAG Search: Qualitative context (Steps 6-8) ─────────────────────┐
│  │ Query: "performance summary for CMP-003"                            │
│  │                                                                     │
│  │ Retrieved:                                                          │
│  │   "CMP-003 Performance Summary: Spring Dining Deal was highly       │
│  │    effective with students, achieving 180 enrollments through        │
│  │    mobile channel (72% of total). Redemption rate was 74% —         │
│  │    highest across all campaigns. Starbucks drove 45% of             │
│  │    redemptions. ROI was 210% on a modest budget."                   │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  ┌─ Step 9: Augmented Prompt (ALL data assembled) ────────────────────┐
│  │ "Generate a concise business-friendly performance summary for       │
│  │  campaign CMP-003.                                                  │
│  │                                                                     │
│  │  Data:                                                              │
│  │    performance_metrics: [3 monthly rows with enrollments,           │
│  │                          redemptions, ROI]                          │
│  │    enrollment_totals: [{total_enrollments: 180}]                    │
│  │    redemption_totals: [{total_redemptions: 136,                     │
│  │                         total_amount: 8420.50}]                     │
│  │                                                                     │
│  │  Additional Context: CMP-003 Performance Summary: Spring Dining...  │
│  │                                                                     │
│  │  Format: 3-4 paragraphs covering enrollment trends, redemption      │
│  │  patterns, ROI analysis, and a recommendation."                     │
│  └─────────────────────────────────────────────────────────────────────┘
│
│  Steps 10-11: Claude generates the narrative from all the above data
│
▼
FINAL ANSWER
   "The Spring Dining Deal (CMP-003) demonstrated strong performance,
    particularly among student cardholders. With 180 total enrollments
    and a 74% redemption rate — the highest across all campaigns —
    the campaign exceeded expectations on every metric.

    Mobile was the dominant enrollment channel at 72%. Starbucks drove
    45% of all redemptions, with total redemption value reaching $8,420.
    Monthly trends show enrollment peaking in April (72) before settling
    to 63 in May, while ROI climbed steadily from 185% to 225%.

    On a modest $100,000 budget, the campaign achieved an impressive
    210% average ROI. Recommendation: expand dining partnerships and
    increase budget allocation for the student segment next quarter."
```

**Key takeaway:** The most complex flow. One tool internally orchestrates 3 SQL queries + 1 RAG search + 1 LLM synthesis — the user just asks a simple question and gets a complete narrative report.

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
│   ├── documents.py                         #   Step 1: Document sources
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
