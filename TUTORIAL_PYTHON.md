# TUTORIAL: Python Concepts Used in This Project

This tutorial explains the Python programming concepts, patterns, and libraries used in the **Campaign Performance Analysis** project. Written for someone learning Python who wants to understand how each piece works.

---

## Project Structure — Why Organize Code This Way?

```
campaign_performance_analysis/
├── config/                 # Settings and constants
│   ├── __init__.py
│   └── settings.py
├── database/               # Everything data-related
│   ├── __init__.py
│   ├── campaign_db.py      # SQLite operations
│   └── data/               # CSV data generation
│       ├── __init__.py
│       └── generate_mock_data.py
├── rag/                    # Vector store for AI knowledge
│   ├── __init__.py
│   └── vector_store.py
├── agent/                  # AI agent logic
│   ├── __init__.py
│   └── campaign_agent.py
├── app.py                  # Web UI entry point
├── requirements.txt        # Python package dependencies
└── .env.example            # Template for secrets
```

### What is `__init__.py`?

Every folder with an `__init__.py` file becomes a **Python package**. This allows you to do imports like:

```python
from database.campaign_db import execute_query
from rag.vector_store import search_similar
```

Without `__init__.py`, Python would not recognize these folders as importable packages.

---

## Key Python Concepts Used

### 1. Classes and Object-Oriented Programming (OOP)

**What:** A class is a blueprint for creating objects. Objects bundle related data and functions together.

**Where we use it:** Every major module uses a class.

```python
# database/campaign_db.py
class CampaignDatabase:
    def __init__(self, db_path=None):   # Constructor — runs when you create an instance
        self.db_path = db_path          # Instance attribute — each object has its own

    def initialize(self):               # Method — a function that belongs to the object
        # ... load CSVs into SQLite

    def execute_query(self, sql):       # Another method
        # ... run a SQL query

# Usage:
db = CampaignDatabase()                # Create an instance (object)
db.initialize()                        # Call a method on that object
results = db.execute_query("SELECT * FROM campaigns")
```

**Why classes instead of plain functions?**
- **Encapsulation** — Related data (db_path) and behavior (initialize, execute_query) live together
- **Reusability** — You can create multiple instances with different settings
- **Configuration** — Each instance can have different paths, parameters, etc.

---

### 2. Decorators

**What:** A decorator is a function that wraps another function to add extra behavior. Written with `@` above the function.

**Where we use them:**

```python
# In campaign_agent.py — tells LangChain this function is a tool
@tool
def sql_query_tool(question: str) -> str:
    """This docstring becomes the tool's description for the AI."""
    ...

# In settings.py — makes a method work on the class itself, not an instance
@classmethod
def validate(cls):
    ...

# In app.py — tells Streamlit to cache the result and only run once
@st.cache_resource
def _initialize_system():
    ...
```

**Simple analogy:** A decorator is like gift wrapping. The gift (function) stays the same inside, but the wrapping (decorator) adds something extra — like caching, registration, or metadata.

---

### 3. Environment Variables and `.env` Files

**What:** Sensitive values (like API keys) should never be written directly in code. Instead, they are stored in environment variables.

**How it works:**

```python
# .env file (NOT committed to git):
ANTHROPIC_API_KEY=sk-ant-api03-xxxxx

# In Python code:
from dotenv import load_dotenv
import os

load_dotenv()  # Reads .env file and sets environment variables
api_key = os.getenv("ANTHROPIC_API_KEY")  # Read the value
```

**Why?** If you accidentally push your code to GitHub, your API key stays safe because `.env` is listed in `.gitignore`.

---

### 4. The `if __name__ == "__main__"` Pattern

**What:** This Python idiom lets a file work both as an importable module AND as a standalone script.

```python
# database/campaign_db.py

class CampaignDatabase:
    ...

# This block ONLY runs when you execute: python database/campaign_db.py
# It does NOT run when another file does: from database.campaign_db import ...
if __name__ == "__main__":
    print("Initializing database...")
    init_database()
```

**Why?** You can test each module individually by running it as a script, but when the main app imports it, the test code does not execute.

---

### 5. List Comprehensions and Dictionary Comprehensions

**What:** A compact way to build lists or dictionaries from existing data.

```python
# Traditional loop:
col_descriptions = []
for col in columns:
    col_descriptions.append(f"  {col[1]} ({col[2]})")

# Same thing as a list comprehension (one line):
col_descriptions = [f"  {col[1]} ({col[2]})" for col in columns]

# Dictionary from two lists (used in get_schema):
row_dict = dict(zip(col_names, row_values))
# zip pairs them up: [("name", "CMP-001"), ("type", "cashback")]
# dict converts pairs to: {"name": "CMP-001", "type": "cashback"}
```

---

### 6. Context Managers (`with` Statement)

**What:** Ensures resources (files, database connections) are properly cleaned up, even if an error occurs.

```python
# Used in app.py for Streamlit layout:
with st.sidebar:
    st.header("Campaigns")   # Everything indented goes in the sidebar

with st.chat_message("assistant"):
    st.markdown(result["answer"])   # Renders inside a chat bubble

# The try/finally pattern in campaign_db.py is similar:
conn = self._connect()
try:
    # ... do database work
finally:
    conn.close()  # Always closes, even if an error occurred above
```

---

### 7. Type Hints

**What:** Annotations that tell developers (and tools) what type a parameter or return value should be.

```python
def sql_query_tool(question: str) -> str:
#                  ^^^^^^^^ ^^^    ^^^^^^
#                  param    type   return type
#                  name            (this function returns a string)
```

**Why?** They serve as documentation and help IDEs provide better autocomplete. Python does not enforce them at runtime — they are hints, not rules.

---

## Libraries Used — What Each One Does

### pandas (`import pandas as pd`)

**Purpose:** Data manipulation. Think of it as "Excel in Python."

```python
df = pd.read_csv("campaigns.csv")       # Read a CSV file into a DataFrame
df.to_sql("campaigns", conn)            # Write DataFrame into a SQL table
campaign = df.sample(1).iloc[0]          # Pick one random row
```

**Key concept — DataFrame:** A table with rows and columns, like a spreadsheet. Each column can be accessed by name: `df["campaign_id"]`.

---

### Faker (`from faker import Faker`)

**Purpose:** Generates realistic fake data for testing.

```python
fake = Faker()
fake.date_between(start_date="-6m", end_date="+1m")  # Random date within range
```

**Why?** We need realistic campaign data for the demo, but we do not have access to real financial data (nor would we want to use it).

---

### sqlite3 (built-in)

**Purpose:** A file-based SQL database built into Python. No server installation needed.

```python
conn = sqlite3.connect("campaign.db")   # Open (or create) database file
cursor = conn.cursor()
cursor.execute("SELECT * FROM campaigns")
rows = cursor.fetchall()                 # Get all results
conn.close()
```

---

### Streamlit (`import streamlit as st`)

**Purpose:** Turns Python scripts into interactive web apps with minimal code.

```python
st.title("Campaign AI Assistant")              # Display a title
user_input = st.chat_input("Ask a question")   # Chat input box
st.markdown(result["answer"])                   # Render markdown text

# Session state persists data across page refreshes:
if "messages" not in st.session_state:
    st.session_state["messages"] = []
```

**Key concept — `st.session_state`:** A dictionary that survives page reruns. Without it, Streamlit would forget everything each time the page refreshes. We use it to store chat history.

**Key concept — `@st.cache_resource`:** A decorator that runs the function once and caches the result. Our database and AI agent are initialized only once, not on every page refresh.

---

### python-dotenv (`from dotenv import load_dotenv`)

**Purpose:** Reads `.env` files and sets their values as environment variables.

```python
load_dotenv()  # Now os.getenv("ANTHROPIC_API_KEY") works
```

---

## Common Patterns in This Project

### Pattern: Module-Level Convenience Functions

```python
# At the bottom of campaign_db.py:
_default_db = CampaignDatabase()         # Create one default instance

def execute_query(sql):                   # Simple function that delegates to it
    return _default_db.execute_query(sql)
```

**Why?** This lets other modules do `from database.campaign_db import execute_query` without needing to create and manage their own `CampaignDatabase` instance. Simple callers get a simple API; advanced callers can still use the class directly.

### Pattern: Centralized Configuration

```python
# config/settings.py
class Settings:
    DB_PATH = os.path.join(PROJECT_ROOT, "database", "campaign.db")
    LLM_MODEL = "claude-sonnet-4-20250514"

# Every other module imports from here:
from config.settings import Settings
db_path = Settings.DB_PATH
```

**Why?** If you need to change a path or model name, you change it in ONE place. Without this, you would need to hunt through every file to find hardcoded values.

---

## How to Run Each Module Individually

```bash
# Generate mock data CSVs:
python database/data/generate_mock_data.py

# Initialize the SQLite database:
python database/campaign_db.py

# Build the RAG vector store:
python rag/vector_store.py

# Run the full web app:
streamlit run app.py
```

Each module can be tested independently because of the `if __name__ == "__main__"` pattern.

---

## Python Version Note

This project requires **Python 3.10 or higher** because it uses:
- Union type syntax `str | None` (3.10+)
- Modern f-string features

See the main `README.md` for instructions on checking and installing the correct Python version on Ubuntu.
