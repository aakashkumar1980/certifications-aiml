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
cp .env.example .env

# Open the .env file in any text editor
nano .env       # or: vim .env / code .env / gedit .env
```

Inside the `.env` file, replace the placeholder with your real key:

```
ANTHROPIC_API_KEY=sk-ant-api03-YOUR-ACTUAL-KEY-HERE
```

Save and close the file. The application reads this file automatically at startup.

> **How it works internally:** The `config/settings.py` module uses `python-dotenv` to load `.env` into environment variables. The agent module then reads `Settings.ANTHROPIC_API_KEY` when it creates the Claude LLM connection. If the key is missing, you will get a clear error message telling you to set it.

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

## How It Works — Sequence Diagram

Here is what happens end-to-end when you ask the assistant a question:

```mermaid
sequenceDiagram
    actor User
    participant UI as Streamlit Web UI
    participant Agent as LangChain Agent
    participant LLM as Claude LLM
    participant Tools as Agent Tools
    participant DB as SQLite / ChromaDB

    User->>UI: 1. Type a question
    UI->>Agent: 2. Forward question
    Agent->>LLM: 3. "Which tool should I use?"
    LLM-->>Agent: 4. "Use sql_query_tool"
    Agent->>Tools: 5. Call sql_query_tool
    Tools->>LLM: 6. "Generate SQL for this question"
    LLM-->>Tools: 7. Returns SQL query
    Tools->>DB: 8. Execute SQL query
    DB-->>Tools: 9. Return result rows
    Tools-->>Agent: 10. Formatted results
    Agent->>LLM: 11. "Summarize these results"
    LLM-->>Agent: 12. Plain English answer
    Agent-->>UI: 13. Display answer
    UI-->>User: 14. See the answer!
```

**In plain English:**
1. You type a question like "Which campaign has the highest enrollment?"
2. The web app sends it to the AI agent
3. The agent asks Claude (the LLM) which tool to use
4. Claude decides: "This is a data question, use the SQL tool"
5. The SQL tool asks Claude to generate the correct SQL, then runs it against the database
6. The agent sends the results back to Claude to write a friendly answer
7. You see the answer in the chat window

---

## Technical Solution Explained Simply

This project combines three AI techniques. Here is what each one does, in the simplest terms possible:

### 1. LLM (Large Language Model) = "The Brain"

Claude is an AI that understands human language. When you ask "Which campaign did best?", Claude understands what "best" means in a business context, writes the correct SQL query, and explains the results clearly. It is the intelligence behind the whole system.

### 2. RAG (Retrieval-Augmented Generation) = "The Reference Book"

Claude is smart, but it does not know YOUR specific campaign data. RAG solves this by giving Claude a "reference book" — a searchable collection of campaign descriptions, performance summaries, and business term definitions. Before answering, the system looks up the most relevant pages from this book and hands them to Claude. This way, Claude's answers are grounded in your actual business data, not just general knowledge.

### 3. AI Agent = "The Manager"

The agent is the decision-maker. It has three tools (SQL queries, knowledge search, report generator) and decides which one to use based on your question. For a data question it picks SQL; for a definition question it picks the knowledge search; for a report request it combines both. It is like a manager delegating work to the right team member.

### How they work together

```mermaid
flowchart TD
    Q["Your Question"] --> Agent{"AI Agent<br/>(decides what to do)"}
    Agent -->|Data question| SQL["SQL Tool<br/>Queries the database"]
    Agent -->|Context question| RAG["RAG Tool<br/>Searches knowledge base"]
    Agent -->|Report request| Report["Summary Tool<br/>Combines DB + RAG + LLM"]
    SQL --> Combine["Agent combines results"]
    RAG --> Combine
    Report --> Combine
    Combine --> Answer["Friendly answer<br/>back to you"]

    style Q fill:#e1f5fe
    style Agent fill:#fff3e0
    style SQL fill:#e8f5e9
    style RAG fill:#e8f5e9
    style Report fill:#e8f5e9
    style Combine fill:#fff3e0
    style Answer fill:#e1f5fe
```

---

## Architecture

```mermaid
graph TB
    subgraph UI["Streamlit Web UI (app.py)"]
        Chat["Chat Interface"]
        Sidebar["Campaign Sidebar"]
        Quick["Quick Questions"]
    end

    subgraph AgentLayer["LangChain Agent (agent/campaign_agent.py)"]
        Exec["AgentExecutor + ConversationBufferMemory"]
        T1["sql_query_tool"]
        T2["rag_search_tool"]
        T3["performance_summary_tool"]
    end

    subgraph LLMLayer["Claude LLM"]
        Claude["claude-sonnet-4-20250514"]
    end

    subgraph DataLayer["Data Storage"]
        SQLite["SQLite DB<br/>(campaign.db)"]
        Chroma["ChromaDB<br/>(vector embeddings)"]
    end

    subgraph DataGen["Data Generation"]
        Mock["MockDataGenerator<br/>(Faker)"]
        CSV["CSV Files"]
    end

    Chat --> Exec
    Exec <--> Claude
    Exec --> T1
    Exec --> T2
    Exec --> T3
    T1 --> SQLite
    T2 --> Chroma
    T3 --> SQLite
    T3 --> Chroma
    Mock --> CSV
    CSV --> SQLite

    style UI fill:#e3f2fd
    style AgentLayer fill:#fff8e1
    style LLMLayer fill:#fce4ec
    style DataLayer fill:#e8f5e9
    style DataGen fill:#f3e5f5
```

---

## Project Structure

```
campaign_performance_analysis/
├── config/
│   ├── __init__.py
│   └── settings.py                # Centralized configuration & constants
├── database/
│   ├── __init__.py
│   ├── campaign_db.py             # SQLite loader, schema, safe query exec
│   └── data/
│       ├── __init__.py
│       └── generate_mock_data.py  # Faker-based CSV data generator
├── rag/
│   ├── __init__.py
│   └── vector_store.py            # ChromaDB knowledge base & search
├── agent/
│   ├── __init__.py
│   └── campaign_agent.py          # LangChain agent with 3 tools
├── app.py                         # Streamlit chat UI
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
cp .env.example .env
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
streamlit run app.py
```

The app will open at `http://localhost:8501`.

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

| Component      | Technology                               | What It Does                                       |
|----------------|------------------------------------------|----------------------------------------------------|
| AI Brain       | Claude (claude-sonnet-4-20250514)                  | Understands questions, writes SQL, generates summaries |
| Orchestration  | LangChain                                | Orchestrates tools and manages conversation        |
| Knowledge Store| ChromaDB                                 | Stores and searches campaign knowledge by meaning  |
| Embeddings     | sentence-transformers (all-MiniLM-L6-v2) | Converts text into numerical meaning vectors       |
| Database       | SQLite                                   | Stores campaign data (file-based, no server)       |
| Web UI         | Streamlit                                | Chat interface in the browser                      |
| Mock Data      | Faker                                    | Generates realistic mock campaign data             |

---

## Learn More

- **[TUTORIAL_AI.md](../../TUTORIAL_AI.md)** — Step-by-step tutorial on LLM, RAG, and AI Agent concepts for beginners
- **[TUTORIAL_PYTHON.md](../../TUTORIAL_PYTHON.md)** — Step-by-step tutorial on Python patterns and libraries used here
