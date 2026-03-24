# poc-ai

A proof-of-concept project that demonstrates how to build an **AI-powered campaign analysis assistant** using modern Python, LLMs, and RAG techniques.

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

Here is what happens when you ask the assistant a question:

```
  You (User)        Streamlit        LangChain         Claude          Tools         SQLite /
                     Web UI           Agent             LLM                          ChromaDB
      |                |                |                |               |              |
      | 1. Type a      |                |                |               |              |
      |    question     |                |                |               |              |
      |--------------->|                |                |               |              |
      |                |                |                |               |              |
      |                | 2. Send to     |                |               |              |
      |                |    agent       |                |               |              |
      |                |--------------->|                |               |              |
      |                |                |                |               |              |
      |                |                | 3. Ask Claude: |               |              |
      |                |                |    "Which tool |               |              |
      |                |                |     to use?"   |               |              |
      |                |                |--------------->|               |              |
      |                |                |                |               |              |
      |                |                | 4. Claude says: |              |              |
      |                |                |    "Use the    |               |              |
      |                |                |     SQL tool"  |               |              |
      |                |                |<---------------|               |              |
      |                |                |                |               |              |
      |                |                | 5. Run the chosen tool         |              |
      |                |                |------------------------------>|              |
      |                |                |                |               |              |
      |                |                |                |          6. Tool generates   |
      |                |                |                |             SQL and queries  |
      |                |                |                |             the database     |
      |                |                |                |               |------------->|
      |                |                |                |               |              |
      |                |                |                |               |  7. Return   |
      |                |                |                |               |     rows     |
      |                |                |                |               |<-------------|
      |                |                |                |               |              |
      |                |                | 8. Tool returns results       |              |
      |                |                |<------------------------------|              |
      |                |                |                |               |              |
      |                |                | 9. Ask Claude: |               |              |
      |                |                |    "Summarize  |               |              |
      |                |                |     these      |               |              |
      |                |                |     results"   |               |              |
      |                |                |--------------->|               |              |
      |                |                |                |               |              |
      |                |                | 10. Claude     |               |              |
      |                |                |     writes a   |               |              |
      |                |                |     friendly   |               |              |
      |                |                |     answer     |               |              |
      |                |                |<---------------|               |              |
      |                |                |                |               |              |
      |                | 11. Display    |                |               |              |
      |                |     answer     |                |               |              |
      |                |<---------------|                |               |              |
      |                |                |                |               |              |
      | 12. See the    |                |                |               |              |
      |     answer!    |                |                |               |              |
      |<---------------|                |                |               |              |
```

**In plain English:**
1. You type a question like "Which campaign has the highest enrollment?"
2. The web app sends it to the AI agent
3. The agent asks Claude (the LLM) which tool to use
4. Claude decides: "This is a data question, use the SQL tool"
5. The SQL tool generates a database query, runs it, and gets results
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

### How they work together:

```
Your Question --> Agent (decides what to do)
                    |
          +-------- +--------+
          |         |        |
       SQL Tool  RAG Tool  Report Tool
       (data)   (context)  (combines both)
          |         |        |
          +-------- +--------+
                    |
               Agent combines everything
                    |
              Friendly answer back to you
```

---

## Project Structure

```
poc-ai/
├── README.md                      # This file — project overview
├── TUTORIAL_AI.md                 # Tutorial: AI concepts explained for beginners
├── TUTORIAL_PYTHON.md             # Tutorial: Python concepts explained for beginners
└── dimo_project/
    └── campaign_performance_analysis/
        ├── config/
        │   └── settings.py        # All settings in one place
        ├── database/
        │   ├── campaign_db.py     # SQLite database operations
        │   └── data/
        │       └── generate_mock_data.py  # Creates realistic test data
        ├── rag/
        │   └── vector_store.py    # Knowledge base (ChromaDB)
        ├── agent/
        │   └── campaign_agent.py  # AI agent with 3 tools
        ├── app.py                 # Web chat interface (Streamlit)
        ├── requirements.txt       # Python dependencies
        ├── .env.example           # API key template
        └── README.md              # Detailed project setup guide
```

---

## Quick Start

```bash
# 1. Go to the project
cd dimo_project/campaign_performance_analysis

# 2. Create a virtual environment
python3 -m venv venv
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your API key
cp .env.example .env
# Edit .env and paste your ANTHROPIC_API_KEY

# 5. Run the app (auto-generates data on first launch)
streamlit run app.py
```

The app opens at `http://localhost:8501`. Type a question and press Enter.

---

## Tech Stack

| Component | Technology | What It Does |
|-----------|-----------|-------------|
| AI Brain | Claude (Anthropic) | Understands questions, writes SQL, generates summaries |
| Agent Framework | LangChain | Orchestrates tools and manages conversation |
| Knowledge Store | ChromaDB | Stores and searches campaign knowledge by meaning |
| Embeddings | sentence-transformers | Converts text into numerical meaning vectors |
| Database | SQLite | Stores campaign data (file-based, no server) |
| Web UI | Streamlit | Chat interface in the browser |
| Test Data | Faker | Generates realistic mock campaign data |

---

## Learn More

- **[TUTORIAL_AI.md](TUTORIAL_AI.md)** — Detailed explanation of LLM, RAG, and Agent concepts with analogies
- **[TUTORIAL_PYTHON.md](TUTORIAL_PYTHON.md)** — Python patterns and libraries used in this project
- **[Project README](dimo_project/campaign_performance_analysis/README.md)** — Detailed setup, sample questions, and architecture diagram
