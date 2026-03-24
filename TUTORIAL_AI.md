# TUTORIAL: AI Concepts Used in This Project

This tutorial explains the AI and Machine Learning concepts used in the **Campaign Performance Analysis** project. It is written for beginners — no prior AI experience is needed.

---

## What Problem Are We Solving?

Imagine you work at a credit card company. You run marketing campaigns (like "5% cashback on groceries") and need to answer questions such as:

- "Which campaign got the most customers?"
- "What does ROI mean?"
- "Show me a performance summary for campaign CMP-003"

Normally, answering these questions requires:
1. A **data analyst** who knows SQL (database query language)
2. A **business analyst** who understands the domain terminology
3. A **report writer** who can summarize findings in plain English

**Our AI assistant replaces all three.** You type a question in plain English, and it figures out what to do.

---

## The Three AI Concepts We Use

### 1. LLM (Large Language Model) — The "Brain"

**What it is:** A Large Language Model (LLM) is an AI that understands and generates human language. Think of it as a very smart auto-complete — but instead of finishing your sentence, it can write SQL queries, summarize data, and have conversations.

**Which one we use:** Claude by Anthropic (specifically the `claude-sonnet-4-20250514` model).

**How we use it in this project:**
- Convert your English question into a SQL database query
- Read query results and explain them in plain English
- Generate performance summary reports
- Decide which tool to use for your question

**Simple analogy:** The LLM is like a very experienced business analyst who speaks both "human language" and "database language." You tell it what you want in English, and it translates that into the right technical actions.

---

### 2. RAG (Retrieval-Augmented Generation) — The "Knowledge Library"

**What it is:** RAG is a technique where the AI first *retrieves* relevant information from a knowledge base, and then *generates* an answer using that information. Without RAG, the AI only knows what it was trained on. With RAG, it can access your specific business data.

**Why we need it:** Claude knows general things about marketing, but it does NOT know the specific details of YOUR campaigns — like "CMP-003 is a dining deal targeting students" or "redemption rate means the percentage of enrolled customers who use their reward."

**How it works (step by step):**

```
1. We write campaign descriptions and business definitions
2. These documents get converted into "embeddings" (numerical representations)
3. Embeddings are stored in a vector database (ChromaDB)
4. When you ask a question, your question also becomes an embedding
5. The system finds the most similar documents to your question
6. Those documents are sent to Claude along with your question
7. Claude generates an answer using both its own knowledge AND your documents
```

**Simple analogy:** Imagine you are taking an open-book exam. The textbook is your knowledge base. RAG is the process of: (a) looking up the most relevant pages, then (b) writing your answer using those pages. Without RAG, it is a closed-book exam — you can only use what you memorized.

**Key terms:**
- **Embedding** — A list of numbers that represents the *meaning* of a text. Similar texts have similar numbers. This is how the computer "understands" similarity.
- **Vector Database (ChromaDB)** — A specialized database that stores embeddings and can quickly find "most similar" items. Think of it as a smart filing cabinet that organizes by meaning, not alphabetical order.
- **Sentence Transformer** — The model (`all-MiniLM-L6-v2`) that converts text into embeddings. It was trained to make semantically similar sentences have similar embeddings.

---

### 3. AI Agent — The "Decision Maker"

**What it is:** An AI Agent is an LLM that can *use tools* and *make decisions* about which tool to use. Instead of just chatting, it can take actions — query a database, search a knowledge base, or generate a report.

**How it works in our project:**

The agent has three tools available:

| Tool | What It Does | When the Agent Uses It |
|------|-------------|----------------------|
| `sql_query_tool` | Runs SQL queries on the database | Data questions: counts, comparisons, trends |
| `rag_search_tool` | Searches the knowledge base | Context questions: definitions, campaign details |
| `performance_summary_tool` | Generates a full report | Summary requests for a specific campaign |

**The decision flow:**

```
You ask: "Which campaign has the highest enrollment?"
                    |
        Agent thinks: "This is a data question,
        I need to count enrollments per campaign"
                    |
        Agent calls: sql_query_tool
                    |
        Tool generates SQL: SELECT campaign_id, COUNT(*)
        FROM enrollments GROUP BY campaign_id ORDER BY ...
                    |
        Tool runs the SQL and returns results
                    |
        Agent reads results and writes a plain English answer:
        "CMP-005 has the highest enrollment with 163 customers..."
```

**Simple analogy:** The agent is like a manager with three employees (tools). When you give the manager a task, they decide which employee is best suited, delegate the work, review the result, and report back to you. The manager can even ask multiple employees for help on complex questions.

---

## How Everything Fits Together — Sequence Diagram

Below is the complete sequence of what happens when you type a question:

```
  User           Streamlit UI       LangChain Agent       Claude LLM        Tools           Databases
   |                  |                   |                    |                |                |
   |  Type question   |                   |                    |                |                |
   |----------------->|                   |                    |                |                |
   |                  |  Forward question |                    |                |                |
   |                  |------------------>|                    |                |                |
   |                  |                   |  "Which tool       |                |                |
   |                  |                   |   should I use?"   |                |                |
   |                  |                   |------------------->|                |                |
   |                  |                   |                    |                |                |
   |                  |                   |  "Use sql_query_   |                |                |
   |                  |                   |   tool with ..."   |                |                |
   |                  |                   |<-------------------|                |                |
   |                  |                   |                    |                |                |
   |                  |                   |  Call sql_query_tool                |                |
   |                  |                   |-------------------------------------->               |
   |                  |                   |                    |                |  Generate SQL  |
   |                  |                   |                    |                |  & query DB    |
   |                  |                   |                    |                |--------------->|
   |                  |                   |                    |                |    Results     |
   |                  |                   |                    |                |<---------------|
   |                  |                   |       Tool results                 |                |
   |                  |                   |<--------------------------------------|               |
   |                  |                   |                    |                |                |
   |                  |                   |  "Summarize these  |                |                |
   |                  |                   |   results nicely"  |                |                |
   |                  |                   |------------------->|                |                |
   |                  |                   |                    |                |                |
   |                  |                   |  Final answer in   |                |                |
   |                  |                   |  plain English     |                |                |
   |                  |                   |<-------------------|                |                |
   |                  |  Display answer   |                    |                |                |
   |                  |<------------------|                    |                |                |
   |  See answer      |                   |                    |                |                |
   |<-----------------|                   |                    |                |                |
```

---

## Key Technologies Used

| Technology | Role | Why We Chose It |
|-----------|------|----------------|
| **Claude** (Anthropic) | LLM — understands questions, generates SQL, writes summaries | Excellent reasoning, tool-calling support |
| **LangChain** | Agent framework — orchestrates tools and conversation | Industry standard, easy tool integration |
| **ChromaDB** | Vector database — stores and searches embeddings | Lightweight, runs locally, no server needed |
| **sentence-transformers** | Generates text embeddings for RAG | Fast, accurate, small model footprint |
| **SQLite** | Relational database for campaign data | Zero setup, file-based, great for demos |
| **Streamlit** | Web-based chat UI | Quick to build, interactive, Python-native |

---

## Glossary of AI Terms

| Term | Simple Definition |
|------|------------------|
| **LLM** | An AI model that reads and writes human language |
| **RAG** | A technique: look up relevant info first, then answer |
| **Embedding** | Numbers that represent the meaning of text |
| **Vector Database** | A database that finds similar items by meaning |
| **Agent** | An AI that can decide which tools to use and take actions |
| **Tool Calling** | When the AI decides to run a specific function (like a SQL query) |
| **Prompt** | The instruction/question you give to the AI |
| **Token** | A unit of text (roughly a word or part of a word) |
| **Temperature** | Controls randomness: 0 = deterministic, 1 = creative |
| **Context Window** | How much text the AI can "see" at once |
