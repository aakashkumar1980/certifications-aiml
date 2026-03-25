# TUTORIAL: Python Concepts for Beginners

A step-by-step guide to the Python programming concepts, patterns, and libraries commonly used in AI-powered applications. Written for someone learning Python who wants to understand how each piece works.

---

## Step 1: Project Structure — Why Organize Code This Way?

A well-organized Python project separates code by responsibility. This project uses a **two-category** architecture that mirrors the RAG pipeline:

```
my_project/
├── config/                     # Settings and constants
│   ├── __init__.py
│   └── settings.py
├── database/                   # Data infrastructure
│   ├── __init__.py
│   ├── campaign_db.py          # Database operations
│   └── data/
│       ├── __init__.py
│       └── generate_mock_data.py
│
├── rag/                        # CATEGORY 1: RAG Pipeline (Knowledge Retrieval)
│   ├── __init__.py             #   Re-exports public API
│   ├── documents.py            #   Step 1: Document sources
│   ├── chunking.py             #   Step 2: Text splitting logic
│   └── vector_store.py         #   Steps 3-4, 6-8: Embed, store, search
│
├── llm/                        # CATEGORY 2: LLM Intelligence (Content Generation)
│   ├── __init__.py             #   Re-exports CampaignAgent
│   ├── provider.py             #   Claude LLM initialization
│   ├── tools/                  #   One file per tool
│   │   ├── __init__.py         #   ALL_TOOLS list
│   │   ├── sql_query.py        #   Steps 9-11: NL → SQL → execute
│   │   ├── rag_search.py       #   Bridge to Category 1
│   │   └── performance_summary.py  # Steps 9-11: Hybrid report
│   └── agent.py                #   Steps 5, 9-11: Agent orchestrator
│
├── app.py                      # Application entry point (FastAPI)
├── requirements.txt            # Python package dependencies
└── .env.example                # Template for secrets
```

### Why two packages (`rag/` and `llm/`)?

Each package maps to a distinct responsibility in the RAG architecture:

- **`rag/`** handles **finding information** — loading documents, chunking, embedding, vector storage, semantic search. The LLM is NOT involved here.
- **`llm/`** handles **thinking and generating** — agent reasoning, SQL generation, response synthesis, tool orchestration. This is where Claude lives.

This separation means you could swap ChromaDB for Pinecone (only touching `rag/`) or swap Claude for GPT (only touching `llm/`) without cross-contamination.

### What is `__init__.py`?

Every folder with an `__init__.py` file becomes a **Python package**. This allows you to do imports like:

```python
from database.campaign_db import execute_query
from rag.vector_store import search_similar
from llm.agent import CampaignAgent
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

A class is a blueprint for creating objects. Objects bundle related data and functions together.

```python
class DatabaseManager:
    def __init__(self, db_path=None):   # Constructor — runs when you create an instance
        self.db_path = db_path          # Instance attribute — each object has its own

    def initialize(self):               # Method — a function that belongs to the object
        # ... load data into the database

    def execute_query(self, sql):       # Another method
        # ... run a SQL query

# Usage:
db = DatabaseManager("/path/to/data.db")  # Create an instance (object)
db.initialize()                            # Call a method on that object
results = db.execute_query("SELECT * FROM users")
```

### Why classes instead of plain functions?

- **Encapsulation** — Related data (db_path) and behavior (initialize, execute_query) live together
- **Reusability** — You can create multiple instances with different settings
- **Configuration** — Each instance can have different paths, parameters, etc.

---

## Step 3: Decorators

### What is a decorator?

A decorator is a function that wraps another function to add extra behavior. Written with `@` above the function.

```python
# Example 1: Register a function as an AI tool
@tool
def search_database(question: str) -> str:
    """This docstring becomes the tool's description for the AI."""
    ...

# Example 2: Make a method work on the class itself, not an instance
@classmethod
def validate(cls):
    ...

# Example 3: Cache the result so the function only runs once
@cache_resource
def initialize_system():
    ...
```

### Simple Analogy

A decorator is like gift wrapping. The gift (function) stays the same inside, but the wrapping (decorator) adds something extra — like caching, registration, or metadata.

---

## Step 4: Environment Variables and `.env` Files

### What are environment variables?

Sensitive values (like API keys) should never be written directly in code. Instead, they are stored in environment variables.

```python
# .env file (NOT committed to git):
API_KEY=sk-xxxxx-your-secret-key

# In Python code:
from dotenv import load_dotenv
import os

load_dotenv()  # Reads .env file and sets environment variables
api_key = os.getenv("API_KEY")  # Read the value
```

### Why?

If you accidentally push your code to GitHub, your API key stays safe because `.env` is listed in `.gitignore`. The `.env.example` file (without real values) tells other developers which variables they need to set.

---

## Step 5: The `if __name__ == "__main__"` Pattern

### What does this do?

This Python idiom lets a file work both as an importable module AND as a standalone script.

```python
class DatabaseManager:
    ...

def init_database():
    ...

# This block ONLY runs when you execute: python db_manager.py
# It does NOT run when another file does: from db_manager import ...
if __name__ == "__main__":
    print("Initializing database...")
    init_database()
```

### Why use it?

You can test each module individually by running it as a script, but when the main app imports it, the test code does not execute.

---

## Step 6: List Comprehensions

### What is a list comprehension?

A compact way to build lists from existing data.

```python
# Traditional loop:
col_descriptions = []
for col in columns:
    col_descriptions.append(f"  {col[1]} ({col[2]})")

# Same thing as a list comprehension (one line):
col_descriptions = [f"  {col[1]} ({col[2]})" for col in columns]

# Dictionary from two lists:
row_dict = dict(zip(col_names, row_values))
# zip pairs them up: [("name", "Alice"), ("age", 30)]
# dict converts pairs to: {"name": "Alice", "age": 30}
```

---

## Step 7: Context Managers (`with` Statement)

### What is a context manager?

Ensures resources (files, database connections) are properly cleaned up, even if an error occurs.

```python
# Opening a file — automatically closes when done:
with open("data.csv", "r") as f:
    content = f.read()

# Database connection with try/finally (same idea):
conn = connect_to_database()
try:
    # ... do database work
finally:
    conn.close()  # Always closes, even if an error occurred above
```

---

## Step 8: Type Hints

### What are type hints?

Annotations that tell developers (and tools) what type a parameter or return value should be.

```python
def search_database(question: str) -> str:
#                   ^^^^^^^^ ^^^    ^^^^^^
#                   param    type   return type
#                   name            (this function returns a string)

def get_results(query: str, limit: int = 10) -> list[dict]:
#               default value ^^^^^            returns a list of dicts
```

### Why use them?

They serve as documentation and help IDEs provide better autocomplete. Python does not enforce them at runtime — they are hints, not rules.

---

## Step 9: Key Libraries for AI Applications

### pandas — "Excel in Python"

```python
import pandas as pd

df = pd.read_csv("data.csv")        # Read a CSV file into a DataFrame
df.to_sql("my_table", connection)    # Write DataFrame into a SQL table
row = df.sample(1).iloc[0]          # Pick one random row
```

**Key concept — DataFrame:** A table with rows and columns, like a spreadsheet. Each column can be accessed by name: `df["column_name"]`.

---

### Faker — Realistic test data

```python
from faker import Faker

fake = Faker()
fake.name()                                          # "John Smith"
fake.date_between(start_date="-6m", end_date="now")  # Random date in last 6 months
```

Generates realistic fake data for testing. Useful when you need demo data but do not have (or should not use) real data.

---

### sqlite3 — Built-in database

```python
import sqlite3

conn = sqlite3.connect("my_database.db")   # Open (or create) database file
cursor = conn.cursor()
cursor.execute("SELECT * FROM users")
rows = cursor.fetchall()                    # Get all results
conn.close()
```

A file-based SQL database built into Python. No server installation needed — perfect for prototypes and demos.

---

### Streamlit — Instant web apps

```python
import streamlit as st

st.title("My AI Assistant")                         # Display a title
user_input = st.chat_input("Ask a question...")     # Chat input box
st.markdown(result)                                 # Render markdown text

# Session state persists data across page refreshes:
if "messages" not in st.session_state:
    st.session_state["messages"] = []
```

**Key concept — `st.session_state`:** A dictionary that survives page reruns. Without it, Streamlit would forget everything each time the page refreshes. Used for storing chat history.

**Key concept — `@st.cache_resource`:** A decorator that runs the function once and caches the result. Database connections and AI models are initialized only once, not on every page refresh.

---

### python-dotenv — Load secrets from files

```python
from dotenv import load_dotenv

load_dotenv()  # Now os.getenv("API_KEY") returns the value from .env
```

---

## Step 10: Common Patterns in AI Applications

### Pattern: Module-Level Convenience Functions

```python
# Create one default instance at module level:
_default_db = DatabaseManager()

# Expose simple functions that delegate to it:
def execute_query(sql):
    return _default_db.execute_query(sql)
```

**Why?** This lets other modules do `from database import execute_query` without needing to create and manage their own `DatabaseManager` instance. Simple callers get a simple API; advanced callers can still use the class directly.

### Pattern: Centralized Configuration

```python
# config/settings.py — single source of truth:
class Settings:
    DB_PATH = os.path.join(PROJECT_ROOT, "database", "app.db")
    LLM_MODEL = "claude-sonnet-4-20250514"
    LLM_TEMPERATURE = 0

# Every other module imports from here:
from config.settings import Settings
db_path = Settings.DB_PATH
```

**Why?** If you need to change a path or model name, you change it in ONE place. Without this, you would need to hunt through every file to find hardcoded values.

---

## Step 11: Python Version Check (Ubuntu)

### Find installed Python versions

```bash
# List all python binaries:
ls -la /usr/bin/python*

# Check specific versions:
python3 --version

# See all installed python packages:
dpkg -l | grep python3
```

### Install Python 3.12 on Ubuntu (if needed)

```bash
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.12 python3.12-venv python3.12-dev
```

### Create a virtual environment

```bash
python3 -m venv venv            # Create
source venv/bin/activate         # Activate (Linux/Mac)
pip install -r requirements.txt  # Install dependencies
deactivate                       # When done
```

**Why virtual environments?** They isolate your project's dependencies from the system Python. Different projects can use different library versions without conflicting.
