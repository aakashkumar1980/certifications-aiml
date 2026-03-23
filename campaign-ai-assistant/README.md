# Campaign AI Assistant

A RAG-based conversational AI assistant for credit card campaign performance analysis. Business stakeholders can ask plain-English questions about campaign data — no SQL knowledge required. Built with LangChain, ChromaDB, Claude API, and Streamlit.

## Setup

```bash
# 1. Clone and navigate to the project
cd campaign-ai-assistant

# 2. Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set your Anthropic API key
cp .env.example .env
# Edit .env and add your ANTHROPIC_API_KEY

# 5. Generate mock data
python data/generate_mock_data.py

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

## Tech Stack

| Component | Technology |
|-----------|-----------|
| LLM | Claude (claude-sonnet-4-20250514) |
| Orchestration | LangChain |
| Vector Store | ChromaDB |
| Embeddings | sentence-transformers (all-MiniLM-L6-v2) |
| Database | SQLite |
| UI | Streamlit |
| Mock Data | Faker |
