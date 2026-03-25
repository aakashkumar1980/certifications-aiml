# TUTORIAL: Python Concepts for Beginners

A step-by-step guide to the Python programming concepts, patterns, and libraries commonly used in AI-powered applications. Written for someone learning Python who wants to understand how each piece works. Concepts are explained generically — the accompanying `campaign_performance_analysis` project is referenced as a working example.

---

## Step 1: Project Structure — Why Organize Code This Way?

A well-organized Python project separates code by responsibility. In a RAG application, this naturally maps to two main packages:

```
my_ai_project/
├── config/                     # Settings and constants
│   ├── __init__.py
│   └── settings.py
├── database/                   # Data infrastructure
│   ├── __init__.py
│   └── db_manager.py
│
├── rag/                        # CATEGORY 1: Knowledge Retrieval
│   ├── __init__.py
│   ├── documents.py            #   Document loading
│   ├── chunking.py             #   Text splitting
│   └── vector_store.py         #   Embedding, storage, search
│
├── llm/                        # CATEGORY 2: Content Generation
│   ├── __init__.py
│   ├── provider.py             #   LLM initialization
│   ├── tools/                  #   One file per tool
│   │   ├── __init__.py
│   │   ├── db_query.py
│   │   └── knowledge_search.py
│   └── agent.py                #   Agent orchestrator
│
├── app.py                      # Application entry point
├── requirements.txt
└── .env.example
```

### Why two packages (`rag/` and `llm/`)?

Each package maps to a distinct responsibility:

- **`rag/`** handles **finding information** — loading documents, chunking, embedding, vector storage, semantic search. The LLM is NOT involved here.
- **`llm/`** handles **thinking and generating** — agent reasoning, query generation, response synthesis, tool orchestration.

This separation means you could swap your vector database (only touching `rag/`) or swap your LLM provider (only touching `llm/`) without cross-contamination.

> **In our example project:** `rag/` contains `documents.py` (campaign data sources), `chunking.py` (text splitter), and `vector_store.py` (ChromaDB). `llm/` contains `provider.py` (Claude init), `tools/` (SQL, RAG search, summary), and `agent.py` (LangGraph orchestrator).

### What is `__init__.py`?

> **Jargon: Package** — A folder with an `__init__.py` file that Python treats as an importable unit. Packages let you organize code into logical groups (e.g., `rag/`, `llm/`).

> **Jargon: Module** — A single `.py` file. A package contains modules.

Every folder with an `__init__.py` file becomes a **Python package**. This allows imports like:

```python
from database.db_manager import execute_query
from rag.vector_store import search_similar
from llm.agent import MyAgent
```

The `__init__.py` can also re-export symbols for convenience:

```python
# rag/__init__.py
from rag.vector_store import build_knowledge_base, search_similar
# Now other files can do: from rag import search_similar
```

Without `__init__.py`, Python would not recognize these folders as importable packages.

---

## Step 2: Classes and Object-Oriented Programming (OOP)

### What is a class?

> **Jargon: Class** — A blueprint for creating objects. Defines what data (attributes) and behavior (methods) an object will have.

> **Jargon: Instance** — A specific object created from a class. `store = VectorStore()` creates one instance. You can create many instances from the same class, each with different data.

> **Jargon: Constructor (`__init__`)** — The special method that runs when you create an instance. Sets up the object's initial state.

A class is a blueprint for creating objects. Objects bundle related data and functions together.

```python
class VectorStore:
    def __init__(self, db_path=None, model_name=None):   # Constructor
        self.db_path = db_path                            # Instance attribute
        self.model_name = model_name
        self._collection = None                           # Lazy initialization

    def build(self):                                      # Method
        # ... load and embed documents

    def search(self, query, n_results=3):                 # Another method
        # ... find similar documents

# Usage:
store = VectorStore("/path/to/chroma_db", "all-MiniLM-L6-v2")
store.build()
results = store.search("What is ROI?")
```

### Why classes instead of plain functions?

> **Jargon: Encapsulation** — Bundling data and the functions that operate on it into a single unit (the class), hiding internal details from outside code.

> **Jargon: Lazy Initialization** — Delaying the creation of an expensive resource (like a database connection) until it's actually needed. In the example above, `self._collection = None` starts as empty and is only created when first accessed.

- **Encapsulation** — Related data (paths, model names) and behavior (build, search) live together
- **Reusability** — You can create multiple instances with different settings
- **State** — The object remembers its configuration (db_path, collection handle) across method calls

> **In our example project:** `CampaignKnowledgeStore` in `rag/vector_store.py` encapsulates ChromaDB path, collection name, embedding model, and the lazily-initialized collection handle. `CampaignDatabase` in `database/campaign_db.py` encapsulates the SQLite path and connection logic.

---

## Step 3: Decorators

### What is a decorator?

> **Jargon: Decorator** — A function that wraps another function to add extra behavior, written with `@` above the function definition. The original function stays unchanged; the decorator adds something on top (like registering it as an API route or an AI tool).

A decorator is a function that wraps another function to add extra behavior. Written with `@` above the function.

```python
# Example 1: Register a function as an AI tool
from langchain_core.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    """Search for relevant context. Use for definition questions."""
    # The docstring becomes the tool description the LLM reads
    results = vector_store.search(query)
    return format_results(results)

# Example 2: Make a method work on the class itself, not an instance
@classmethod
def validate(cls):
    if not cls.API_KEY:
        raise ValueError("API key not set")

# Example 3: FastAPI route decorator
from fastapi import FastAPI
app = FastAPI()

@app.post("/ask")
async def ask_question(request: AskRequest):
    return agent.ask(request.question)
```

### Simple Analogy

A decorator is like gift wrapping. The gift (function) stays the same inside, but the wrapping (decorator) adds something extra — like registration as an AI tool, HTTP route binding, or caching.

> **In our example project:** `@tool` is used in `llm/tools/sql_query.py`, `llm/tools/rag_search.py`, and `llm/tools/performance_summary.py` to register functions as tools the LangGraph agent can call. `@app.post` and `@app.get` in `app.py` register FastAPI endpoints.

---

## Step 4: Environment Variables and `.env` Files

### What are environment variables?

> **Jargon: Environment Variable** — A key-value pair stored outside your code, in the operating system's environment. Programs read these at runtime. Used for secrets (API keys), configuration (database URLs), and settings that change between environments (dev vs. production).

Sensitive values (like API keys) should never be written directly in code. Instead, they are stored in environment variables.

```python
# .env file (NOT committed to git):
ANTHROPIC_API_KEY=sk-ant-xxxxx-your-secret-key
DATABASE_URL=postgresql://user:pass@host/db

# In Python code:
from dotenv import load_dotenv
import os

load_dotenv()  # Reads .env file and sets environment variables
api_key = os.getenv("ANTHROPIC_API_KEY")  # Read the value
```

### Why?

If you accidentally push your code to GitHub, your API key stays safe because `.env` is listed in `.gitignore`. The `.env.example` file (without real values) tells other developers which variables they need to set.

> **In our example project:** `config/settings.py` calls `load_dotenv()` at import time, then reads `ANTHROPIC_API_KEY` from the environment. The `Settings.validate()` classmethod raises a clear error if the key is missing.

---

## Step 5: The `if __name__ == "__main__"` Pattern

### What does this do?

This Python idiom lets a file work both as an importable module AND as a standalone script.

```python
class VectorStore:
    ...

def build_knowledge_base():
    ...

def search_similar(query):
    ...

# This block ONLY runs when you execute: python vector_store.py
# It does NOT run when another file does: from vector_store import search_similar
if __name__ == "__main__":
    print("Building knowledge base...")
    build_knowledge_base()
    print("Testing search...")
    results = search_similar("test query")
    print(results)
```

### Why use it?

You can test each module individually by running it as a script, but when the main app imports it, the test code does not execute. This is especially useful in RAG applications where you want to test each step independently — build the vector store, run a search, test a tool — without starting the full server.

> **In our example project:** Both `rag/vector_store.py` and `llm/agent.py` have `if __name__ == "__main__"` blocks for standalone testing.

---

## Step 6: List Comprehensions

### What is a list comprehension?

> **Jargon: List Comprehension** — A one-line Python syntax for creating lists by transforming or filtering existing data. Replaces multi-line `for` loops with a compact `[expression for item in iterable]` format.

A compact way to build lists from existing data.

```python
# Traditional loop:
formatted_results = []
for i, result in enumerate(search_results):
    formatted_results.append(f"[Source {i+1}] {result['content']}")

# Same thing as a list comprehension (one line):
formatted_results = [f"[Source {i+1}] {r['content']}" for i, r in enumerate(search_results)]

# Dictionary from two lists:
row_dict = dict(zip(column_names, row_values))
# zip pairs them up: [("name", "Alice"), ("age", 30)]
# dict converts pairs to: {"name": "Alice", "age": 30}
```

### Where you see this in RAG apps

```python
# Convert database rows to dictionaries:
results = [dict(row) for row in cursor.fetchall()]

# Extract content from search results:
context_texts = [r["content"] for r in rag_results]

# Build metadata for chunks:
chunk_ids = [f"{doc_id}_chunk{i}" for i in range(len(chunks))]
```

---

## Step 7: Context Managers (`with` Statement)

### What is a context manager?

> **Jargon: Context Manager** — A Python pattern (using `with`) that automatically sets up and cleans up resources. Guarantees cleanup happens even if an error occurs. Common for files, database connections, and network sockets.

Ensures resources (files, database connections) are properly cleaned up, even if an error occurs.

```python
# Opening a file — automatically closes when done:
with open("data.csv", "r") as f:
    content = f.read()

# Database connection with try/finally (same idea):
conn = sqlite3.connect("my_database.db")
try:
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
finally:
    conn.close()  # Always closes, even if an error occurred above
```

### FastAPI lifespan context manager

In modern FastAPI apps, the startup/shutdown lifecycle is managed with an async context manager:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: initialize database, build knowledge base, create agent
    agent = initialize_system()
    yield  # App runs here, handling requests
    # Shutdown: cleanup resources
    print("Shutting down")

app = FastAPI(lifespan=lifespan)
```

> **In our example project:** `app.py` uses this pattern to initialize the SQLite database, build the ChromaDB knowledge base, and create the CampaignAgent at startup.

---

## Step 8: Type Hints

### What are type hints?

> **Jargon: Type Hint / Annotation** — Optional labels on function parameters and return values that specify the expected data type. Python does NOT enforce them at runtime — they serve as documentation for developers and tools.

> **Jargon: Pydantic** — A data validation library that DOES enforce type hints at runtime. FastAPI uses Pydantic to automatically validate incoming JSON requests against your type-annotated models.

Annotations that tell developers (and tools) what type a parameter or return value should be.

```python
def search_similar(query: str, n_results: int = 3) -> list[dict]:
#                   ^^^^^ ^^^  ^^^^^^^^^ ^^^ ^^^    ^^^^^^^^^^
#                   param type  param    type default  return type

class AskResponse(BaseModel):
    answer: str
    sql_query: str | None = None     # Can be a string or None
    sources: list[str] = []          # List of strings, defaults to empty
```

### Why use them?

- They serve as documentation — you know at a glance what a function expects and returns
- IDEs provide better autocomplete and error highlighting
- Pydantic (used by FastAPI) uses them for automatic request/response validation
- Python does not enforce them at runtime — they are hints, not rules

> **In our example project:** All Pydantic models in `app.py` (`AskRequest`, `AskResponse`, `SearchResult`) use type hints for automatic JSON validation. Tool functions in `llm/tools/` use type hints so LangChain can generate the JSON schema the LLM reads.

---

## Step 9: Key Libraries for AI Applications

Here is how the libraries map to the two-category architecture:

```mermaid
flowchart TB
    subgraph cat2["Category 2: LLM Intelligence"]
        LC["LangChain — LLM wrappers, tool definitions"]
        LG["LangGraph — Agent orchestration, ReAct loop"]
        Anthropic["langchain-anthropic — Claude integration"]
    end

    subgraph cat1["Category 1: RAG Pipeline"]
        Chroma["ChromaDB — Vector database"]
        ST["sentence-transformers — Embedding model"]
        TS["langchain-text-splitters — Chunking"]
    end

    subgraph infra["Infrastructure"]
        FastAPI["FastAPI — REST API"]
        SQLite["sqlite3 — Database (built-in)"]
        Faker["Faker — Test data generation"]
        DotEnv["python-dotenv — Secret management"]
        Logging["logging — Structured logs (built-in)"]
    end

    style cat2 fill:#fce4ec
    style cat1 fill:#e8f5e9
    style infra fill:#f5f5f5
```

### LangChain + LangGraph — AI orchestration

```python
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

# Initialize the LLM
llm = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)

# Define tools
@tool
def my_tool(query: str) -> str:
    """Tool description that the LLM reads to decide when to use it."""
    return do_something(query)

# Create an agent that can use tools
agent = create_react_agent(model=llm, tools=[my_tool])
result = agent.invoke({"messages": [HumanMessage(content="My question")]})
```

**LangChain** provides the building blocks (LLM wrappers, tool definitions, prompt templates). **LangGraph** builds on top with stateful agent graphs — the agent maintains conversation history and can loop through reasoning steps.

---

### ChromaDB + sentence-transformers — Vector search

```python
import chromadb
from chromadb.utils import embedding_functions

# Create a persistent vector database
client = chromadb.PersistentClient(path="./my_vector_db")
ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name="all-MiniLM-L6-v2")
collection = client.get_or_create_collection("my_knowledge", embedding_function=ef)

# Add documents (automatically embedded)
collection.add(documents=["doc1 text", "doc2 text"], ids=["doc1", "doc2"])

# Search by meaning (automatically embeds the query)
results = collection.query(query_texts=["my question"], n_results=3)
```

**ChromaDB** stores embeddings and searches by cosine similarity. **sentence-transformers** provides the embedding model that runs locally — no API calls, no cost.

---

### langchain-text-splitters — Document chunking

```python
from langchain_text_splitters import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=200,       # Max characters per chunk
    chunk_overlap=50,     # Characters shared between adjacent chunks
    separators=["\n\n", "\n", ". ", ", ", " ", ""],  # Try these boundaries first
)

chunks = splitter.split_text(long_document)
# Returns: ["chunk 1 text...", "chunk 2 text...", ...]
```

The `Recursive` part means it tries the first separator (`\n\n` = paragraph break), and only falls back to the next separator if chunks are still too large.

---

### pandas — Data processing

```python
import pandas as pd

df = pd.read_csv("data.csv")              # Read CSV into a DataFrame (table)
df.to_sql("my_table", connection,          # Write DataFrame into SQLite
           if_exists="replace", index=False)
```

**Key concept — DataFrame:** A table with rows and columns, like a spreadsheet. Used in RAG apps to load CSV data into databases during initialization.

---

### FastAPI — REST API framework

```python
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="My AI API")

class AskRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=1000)

@app.post("/ask")
async def ask_question(request: AskRequest):
    result = agent.ask(request.question)
    return {"answer": result}
```

FastAPI gives you: automatic JSON validation (via Pydantic), auto-generated Swagger docs at `/docs`, async support, and type-safe request/response handling.

---

### sqlite3 — Built-in database

```python
import sqlite3

conn = sqlite3.connect("my_database.db")
conn.row_factory = sqlite3.Row          # Return rows as dictionaries
cursor = conn.cursor()
cursor.execute("SELECT * FROM users WHERE age > ?", (18,))
rows = [dict(row) for row in cursor.fetchall()]
conn.close()
```

A file-based SQL database built into Python. No server installation needed — perfect for prototypes and demos.

---

### Faker — Realistic test data

```python
from faker import Faker
fake = Faker()
fake.seed_instance(42)                                    # Reproducible results

fake.name()                                               # "John Smith"
fake.date_between(start_date="-6m", end_date="now")       # Random recent date
fake.random_element(["active", "completed", "paused"])    # Random choice
```

Generates realistic fake data for testing. Useful when you need demo data but do not have (or should not use) real data.

---

### python-dotenv — Load secrets from files

```python
from dotenv import load_dotenv
load_dotenv()  # Now os.getenv("API_KEY") returns the value from .env
```

---

### logging — Structured application logs

```python
import logging

# Configure once at app startup:
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
)

# Use in each module:
logger = logging.getLogger("rag_pipeline")
logger.info("[STEP 3] Embedding %d chunks using '%s'...", count, model_name)
logger.warning("No results found for query: %s", query)
logger.error("Failed to execute SQL: %s", str(error))
```

Unlike `print()`, logging supports log levels (DEBUG, INFO, WARNING, ERROR), timestamps, module names, and can be filtered or redirected to files.

> **In our example project:** All modules use `logging.getLogger("rag_pipeline")` with step labels like `[STEP 6]` so you can trace the complete 11-step RAG pipeline flow in the console output.

---

## Step 10: Common Patterns in AI Applications

### Pattern: Module-Level Convenience Functions

```python
# Create one default instance at module level:
_default_store = VectorStore()

# Expose simple functions that delegate to it:
def search_similar(query, n_results=3):
    return _default_store.search(query, n_results)
```

**Why?** This lets other modules do `from rag import search_similar` without needing to create and manage their own `VectorStore` instance. Simple callers get a simple API; advanced callers can still use the class directly.

> **In our example project:** Both `rag/vector_store.py` and `database/campaign_db.py` use this pattern — a `_default_store` / `_default_db` instance with module-level wrapper functions.

### Pattern: Centralized Configuration

```python
# config/settings.py — single source of truth:
class Settings:
    DB_PATH = os.path.join(PROJECT_ROOT, "database", "app.db")
    LLM_MODEL = "claude-sonnet-4-20250514"
    LLM_TEMPERATURE = 0
    CHUNK_SIZE = 200
    CHUNK_OVERLAP = 50

# Every other module imports from here:
from config.settings import Settings
llm = ChatAnthropic(model=Settings.LLM_MODEL, temperature=Settings.LLM_TEMPERATURE)
```

**Why?** If you need to change a model name, chunk size, or database path, you change it in ONE place. Without this, you would need to hunt through every file to find hardcoded values.

### Pattern: Safety Guards for LLM-Generated Code

```python
import re

_DESTRUCTIVE_PATTERN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE)\b", re.IGNORECASE
)

def execute_query(sql):
    if _DESTRUCTIVE_PATTERN.search(sql):
        return "Error: Only SELECT queries are allowed."
    # ... proceed with execution
```

**Why?** The LLM generates SQL from natural language. It *usually* generates safe SELECT queries, but you must validate — never trust LLM output for destructive operations.

### Pattern: Idempotent Initialization

```python
def build_knowledge_base(self):
    collection = self.get_collection()
    if collection.count() > 0:
        print("Already populated. Skipping.")
        return collection
    # ... proceed with ingestion
```

**Why?** During development, the app restarts frequently. Without this check, you would re-embed all documents every time — wasting time and potentially creating duplicates.

---

## Step 11: Python Version and Virtual Environments

### Find installed Python versions

```bash
python3 --version               # Check current version
ls -la /usr/bin/python*         # List all python binaries
```

### Install Python 3.12 on Ubuntu (if needed)

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

### Create a virtual environment

> **Jargon: Virtual Environment (venv)** — An isolated Python installation specific to one project. Each venv has its own `pip` and installed packages, completely separate from other projects and the system Python.

> **Jargon: pip** — Python's package installer. Reads `requirements.txt` to know what packages (and versions) to install.

> **Jargon: requirements.txt** — A file listing all packages your project needs, one per line (e.g., `langchain==0.2.0`, `chromadb>=0.4.0`). Ensures every developer installs the same versions.

```bash
python3 -m venv venv            # Create
source venv/bin/activate         # Activate (Linux/Mac)
pip install -r requirements.txt  # Install dependencies
deactivate                       # When done
```

**Why virtual environments?** They isolate your project's dependencies from the system Python. Different projects can use different library versions without conflicting. This is especially important in AI projects where library versions change rapidly (e.g., LangChain, ChromaDB).
