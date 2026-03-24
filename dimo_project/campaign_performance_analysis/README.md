# Campaign Performance Analysis — AI Assistant

A RAG-based conversational AI assistant for credit card campaign performance analysis. Business stakeholders can ask plain-English questions about campaign data — no SQL knowledge required. Built with LangChain, ChromaDB, Claude API, and Streamlit.

## Architecture

```
┌─────────────────────────────────────────────────┐
│  Streamlit UI (app.py)                          │
│  Chat interface + sidebar + expandable sections │
└──────────────────┬──────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────┐
│  LangChain Agent (agent/campaign_agent.py)      │
│  Claude claude-sonnet-4-20250514 + ConversationBufferMemory   │
├─────────┬────────────┬──────────────────────────┤
│ SQL Tool│  RAG Tool  │  Performance Summary Tool│
└────┬────┴─────┬──────┴────────┬─────────────────┘
     │          │               │
┌────▼────┐ ┌───▼────┐   ┌─────▼─────┐
│ SQLite  │ │ChromaDB│   │ Both DBs  │
│  (DB)   │ │ (RAG)  │   │ + Claude  │
└─────────┘ └────────┘   └───────────┘
```

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

## Sample Questions

- "Which campaign has the highest enrollment?"
- "Compare cashback vs travel offer performance"
- "What is the ROI trend for Q4?"
- "Which merchant category drives the most redemptions?"
- "Give me a performance summary for CMP-003"
- "What does redemption rate mean?"
- "Which state has the most enrollments?"
- "What is the average cost per enrollment across all campaigns?"

## Project Structure

```
campaign_performance_analysis/
├── config/
│   ├── __init__.py
│   └── settings.py              # Centralized configuration & constants
├── database/
│   ├── __init__.py
│   ├── campaign_db.py           # SQLite loader, schema, safe query exec
│   └── data/
│       ├── __init__.py
│       └── generate_mock_data.py  # Faker-based CSV data generator
├── rag/
│   ├── __init__.py
│   └── vector_store.py          # ChromaDB knowledge base & search
├── agent/
│   ├── __init__.py
│   └── campaign_agent.py        # LangChain agent with 3 tools
├── app.py                       # Streamlit chat UI
├── requirements.txt
├── .env.example
└── README.md
```

## Tech Stack

| Component      | Technology                               |
|----------------|------------------------------------------|
| LLM            | Claude (claude-sonnet-4-20250514)                  |
| Orchestration  | LangChain                                |
| Vector Store   | ChromaDB                                 |
| Embeddings     | sentence-transformers (all-MiniLM-L6-v2) |
| Database       | SQLite                                   |
| UI             | Streamlit                                |
| Mock Data      | Faker                                    |
