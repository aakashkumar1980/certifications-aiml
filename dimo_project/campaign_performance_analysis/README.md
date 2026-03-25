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

## Two-Category Architecture

The system is built around two distinct categories that mirror the standard RAG pipeline:

### Category 1: RAG Pipeline — Knowledge Retrieval (`rag/` package)

Handles finding relevant information from the domain-specific knowledge base. The LLM is NOT used for generation here — only sentence-transformers are used for embedding.

**Steps 1-4** (one-time ingestion): Load Documents → Chunk → Embed → Store in ChromaDB
**Steps 6-8** (every query): Embed Query → Semantic Search → Retrieve Closest Chunks

### Category 2: LLM Intelligence — Content Generation (`llm/` package)

Handles all reasoning, decision-making, and natural language generation. Claude serves as:
- **SQL generator** — translates questions to database queries
- **Response synthesizer** — combines data + context into business-friendly answers
- **Fallback knowledge source** — provides general definitions from trained knowledge when RAG returns nothing relevant

**Step 5** (entry): User Query received
**Steps 9-11** (generation): Contextually Augmented Prompt → Fed to LLM → LLM Response

---

## How It Works — The 11-Step RAG Pipeline

Here is the complete end-to-end flow when a user asks a question, with entities grouped by category:

```mermaid
sequenceDiagram
    actor User as User

    box rgb(232, 245, 233) Category 1: RAG Pipeline (Knowledge Retrieval)
        participant Docs as Documents<br/>(rag/documents.py)
        participant Chunk as Chunker<br/>(rag/chunking.py)
        participant Embed as Embedding Model<br/>(all-MiniLM-L6-v2)
        participant VDB as Vector Database<br/>(ChromaDB)
    end

    box rgb(252, 228, 236) Category 2: LLM Intelligence (Content Generation)
        participant Agent as AI Agent<br/>(llm/agent.py)
        participant Tools as Agent Tools<br/>(llm/tools/)
        participant LLM as Claude LLM<br/>(llm/provider.py)
    end

    participant DB as SQLite DB<br/>(database/)

    Note over Docs, VDB: One-Time Ingestion (Steps 1-4)
    Docs->>Docs: Step 1: Load campaign descriptions,<br/>performance summaries, business glossary
    Docs->>Chunk: Step 2: Split documents into chunks<br/>(size=200, overlap=50)
    Chunk->>Embed: Step 3: Encode chunks into<br/>embedding vectors (384-dim)
    Embed->>VDB: Step 4: Store vectors + metadata<br/>in ChromaDB collection

    Note over User, DB: Query Flow (Steps 5-11)
    User->>Agent: Step 5: User Query<br/>"Which campaign has highest ROI?"
    Agent->>LLM: Agent asks: "Which tool should I use?"
    LLM-->>Agent: "Use sql_query_tool + rag_search_tool"

    Note over Agent, VDB: RAG Path (Steps 6-8 via Category 1)
    Agent->>Tools: Call rag_search_tool
    Tools->>Embed: Step 6: Embed the user query<br/>using same model
    Embed->>VDB: Step 7: Semantic Search<br/>(cosine similarity, top-3)
    VDB-->>Tools: Step 8: Return closest chunks<br/>with distance scores

    Note over Agent, DB: SQL Path (via Category 2)
    Agent->>Tools: Call sql_query_tool
    Tools->>LLM: Step 9: Augmented Prompt<br/>(schema + question → "Generate SQL")
    LLM-->>Tools: Step 10-11: Generated SQL query
    Tools->>DB: Execute SQL
    DB-->>Tools: Raw result rows (JSON)

    Note over Agent, LLM: Final Synthesis (Steps 9-11)
    Tools-->>Agent: DB results + RAG chunks
    Agent->>LLM: Step 9: Contextually Augmented Prompt<br/>(data + context + question)
    LLM-->>Agent: Step 10→11: Fed to LLM → LLM Response<br/>(business-friendly answer)
    Agent-->>User: "CMP-003 achieved the highest ROI at 210%..."
```

### The 11 Steps Explained

| Step | Name | Category | Module | What Happens |
|------|------|----------|--------|--------------|
| 1 | Loading Documents | RAG | `rag/documents.py` | Campaign descriptions, summaries, glossary gathered |
| 2 | Chunking | RAG | `rag/chunking.py` | Documents split into ~200-char overlapping chunks |
| 3 | Embedding Chunks | RAG | `rag/vector_store.py` | Chunks encoded to 384-dim vectors via sentence-transformers |
| 4 | Storing in Vector DB | RAG | `rag/vector_store.py` | Vectors + metadata stored in ChromaDB |
| 5 | User Query | LLM | `llm/agent.py` | Question received, agent decides tool(s) to call |
| 6 | Embedding Query | RAG | `rag/vector_store.py` | User query encoded using same embedding model |
| 7 | Semantic Search | RAG | `rag/vector_store.py` | Cosine similarity search against all stored vectors |
| 8 | Retrieve Closest Chunks | RAG | `rag/vector_store.py` | Top-N chunks returned with distance scores |
| 9 | Augmented Prompt | LLM | `llm/tools/*.py` | DB results + RAG chunks + question assembled into prompt |
| 10 | Fed to LLM | LLM | `llm/tools/*.py` | Augmented prompt sent to Claude for synthesis |
| 11 | LLM Response | LLM | `llm/agent.py` | Claude generates business-friendly natural language answer |

---

## Technical Solution Explained Simply

This project combines three AI techniques. Here is what each one does, in the simplest terms possible:

### 1. LLM (Large Language Model) = "The Brain"

Claude is an AI that understands human language. When you ask "Which campaign did best?", Claude understands what "best" means in a business context, writes the correct SQL query, and explains the results clearly. It is the intelligence behind the whole system. When the knowledge base has no relevant answer, Claude can fall back on its own trained knowledge (e.g., providing a general definition of "enrollment").

### 2. RAG (Retrieval-Augmented Generation) = "The Reference Book"

Claude is smart, but it does not know YOUR specific campaign data. RAG solves this by giving Claude a "reference book" — a searchable collection of campaign descriptions, performance summaries, and business term definitions. Documents are first chunked into smaller pieces, then embedded as vectors and stored in ChromaDB. Before answering, the system looks up the most relevant chunks and hands them to Claude. This way, Claude's answers are grounded in your actual business data, not just general knowledge.

### 3. AI Agent = "The Manager"

The agent is the decision-maker. It has three tools (SQL queries, knowledge search, report generator) and decides which one to use based on your question. For a data question it picks SQL; for a definition question it picks the knowledge search; for a report request it combines both. It is like a manager delegating work to the right team member.

### How they work together

```mermaid
flowchart LR
    Q["Your Question"] --> Agent{"AI Agent<br/>(decides what to do)"}

    subgraph cat1["Category 1: RAG Pipeline"]
        RAG["RAG Tool<br/>Searches knowledge base"]
    end

    subgraph cat2["Category 2: LLM Intelligence"]
        SQL["SQL Tool<br/>Queries the database"]
        Report["Summary Tool<br/>Combines DB + RAG + LLM"]
        Combine["Agent synthesizes results"]
    end

    Agent -->|Data question| SQL
    Agent -->|Context question| RAG
    Agent -->|Report request| Report
    SQL --> Combine
    RAG --> Combine
    Report --> Combine
    Combine --> Answer["Friendly answer<br/>back to you"]

    style Q fill:#e1f5fe
    style Agent fill:#fff3e0
    style cat1 fill:#e8f5e9
    style cat2 fill:#fce4ec
    style SQL fill:#fce4ec
    style RAG fill:#e8f5e9
    style Report fill:#fce4ec
    style Combine fill:#fff3e0
    style Answer fill:#e1f5fe
```

---

## Architecture

```mermaid
graph TB
    subgraph API["FastAPI REST API (app.py)"]
        Ask["POST /ask"]
        AskSQL["POST /ask/sql"]
        AskSearch["POST /ask/search"]
        Campaigns["GET /campaigns"]
        Summary["GET /campaigns/:id/summary"]
        Health["GET /health"]
    end

    subgraph cat2["Category 2: LLM Intelligence (llm/)"]
        direction TB
        Provider["LLM Provider<br/>(llm/provider.py)"]
        AgentMod["Campaign Agent<br/>(llm/agent.py)"]
        T1["sql_query_tool<br/>(llm/tools/sql_query.py)"]
        T2["rag_search_tool<br/>(llm/tools/rag_search.py)"]
        T3["performance_summary_tool<br/>(llm/tools/performance_summary.py)"]
        Claude["Claude claude-sonnet-4-20250514"]
    end

    subgraph cat1["Category 1: RAG Pipeline (rag/)"]
        direction TB
        DocMod["Document Sources<br/>(rag/documents.py)"]
        ChunkMod["Text Chunker<br/>(rag/chunking.py)"]
        VecStore["Vector Store<br/>(rag/vector_store.py)"]
        Chroma["ChromaDB<br/>(vector embeddings)"]
    end

    subgraph DataLayer["Data Infrastructure"]
        SQLite["SQLite DB<br/>(campaign.db)"]
        Config["Config<br/>(config/settings.py)"]
    end

    subgraph DataGen["Data Generation"]
        Mock["MockDataGenerator<br/>(Faker)"]
        CSV["CSV Files"]
    end

    Ask --> AgentMod
    Summary --> AgentMod
    AskSQL --> T1
    AskSearch --> T2
    Campaigns --> SQLite
    AgentMod <--> Claude
    AgentMod --> T1
    AgentMod --> T2
    AgentMod --> T3
    Provider --> Claude
    T1 --> SQLite
    T1 --> Provider
    T2 --> VecStore
    T3 --> SQLite
    T3 --> VecStore
    T3 --> Provider
    DocMod --> ChunkMod
    ChunkMod --> VecStore
    VecStore --> Chroma
    Mock --> CSV
    CSV --> SQLite

    style API fill:#e3f2fd
    style cat2 fill:#fce4ec
    style cat1 fill:#e8f5e9
    style DataLayer fill:#f5f5f5
    style DataGen fill:#f3e5f5
```

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

- "Which campaign has the highest enrollment?"
- "Compare cashback vs travel offer performance"
- "What is the ROI trend for Q4?"
- "Which merchant category drives the most redemptions?"
- "Give me a performance summary for CMP-003"
- "What does redemption rate mean?"
- "Which state has the most enrollments?"
- "What is the average cost per enrollment across all campaigns?"

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
