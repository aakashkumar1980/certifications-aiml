# TUTORIAL: AI Concepts for Beginners

A step-by-step guide to the core AI concepts used in modern AI-powered applications. No prior AI experience is needed.

---

## Step 1: Understanding the Problem AI Solves

Imagine a business team that needs to answer questions from data stored in databases. Traditionally, this requires:

1. A **data analyst** who knows SQL (a database query language)
2. A **domain expert** who understands the business terminology
3. A **report writer** who can summarize findings in plain English

Modern AI can replace all three by letting users ask questions in plain English and getting answers automatically.

---

## Step 2: LLM (Large Language Model) — The "Brain"

### What is an LLM?

A Large Language Model (LLM) is an AI that understands and generates human language. Think of it as a very smart auto-complete — but instead of finishing your sentence, it can write database queries, summarize data, and have multi-turn conversations.

### Popular LLMs

- **Claude** by Anthropic
- **GPT** by OpenAI
- **Gemini** by Google
- **LLaMA** by Meta (open source)

### What can an LLM do?

- Convert English questions into SQL database queries
- Read query results and explain them in plain English
- Generate summary reports
- Decide which tool to use for a given question

### Simple Analogy

The LLM is like a very experienced business analyst who speaks both "human language" and "database language." You tell it what you want in English, and it translates that into the right technical actions.

### Key Configuration Parameters

| Parameter | What It Controls | Example |
|-----------|-----------------|---------|
| **Model** | Which LLM to use | `claude-sonnet-4-20250514` |
| **Temperature** | Creativity vs. precision (0 = precise, 1 = creative) | `0` for data queries |
| **Max Tokens** | Maximum length of the response | `2048` |

---

## Step 3: RAG (Retrieval-Augmented Generation) — The "Reference Book"

### What is RAG?

RAG is a technique where the AI first *retrieves* relevant information from a knowledge base, and then *generates* an answer using that information. Without RAG, the AI only knows what it was trained on. With RAG, it can access your specific business data.

### Why is RAG needed?

An LLM knows general things about the world, but it does NOT know your specific business data — like "Campaign X targets student customers" or "redemption rate means the percentage of enrolled customers who use their reward." RAG bridges this gap.

### How RAG works — step by step

```mermaid
flowchart LR
    subgraph Ingestion["One-Time Setup"]
        D1["Business documents"] --> E1["Convert to embeddings"]
        E1 --> V1["Store in vector database"]
    end

    subgraph Query["Every Time You Ask"]
        Q["Your question"] --> E2["Convert to embedding"]
        E2 --> S["Find most similar documents"]
        V1 -.-> S
        S --> C["Send question + documents to LLM"]
        C --> A["LLM generates informed answer"]
    end

    style Ingestion fill:#e8f5e9
    style Query fill:#e3f2fd
```

1. **Ingestion (one-time):** You write documents (descriptions, definitions, summaries). These get converted into "embeddings" (numerical representations of meaning) and stored in a vector database.
2. **Query (every question):** Your question also becomes an embedding. The system finds the most similar documents. Those documents are sent to the LLM along with your question. The LLM generates an answer using both its own knowledge AND your documents.

### Simple Analogy

Imagine you are taking an open-book exam. The textbook is your knowledge base. RAG is the process of: (a) looking up the most relevant pages, then (b) writing your answer using those pages. Without RAG, it is a closed-book exam — you can only use what you memorized.

### Key Terms

| Term | Simple Definition |
|------|------------------|
| **Embedding** | A list of numbers that represents the *meaning* of a text. Similar texts have similar numbers. This is how the computer "understands" similarity. |
| **Vector Database** | A specialized database that stores embeddings and can quickly find "most similar" items. Think of it as a smart filing cabinet that organizes by meaning, not alphabetical order. |
| **Sentence Transformer** | A small AI model that converts text into embeddings. Popular choice: `all-MiniLM-L6-v2`. |

### Common Vector Databases

| Database | Key Feature |
|----------|------------|
| **ChromaDB** | Lightweight, runs locally, no server needed |
| **Pinecone** | Cloud-hosted, scalable |
| **Weaviate** | Open source, feature-rich |
| **FAISS** | By Meta, optimized for speed |

---

## Step 4: AI Agent — The "Decision Maker"

### What is an AI Agent?

An AI Agent is an LLM that can *use tools* and *make decisions* about which tool to use. Instead of just chatting, it can take actions — query a database, search a knowledge base, or generate a report.

### How an Agent works

```mermaid
flowchart TD
    Q["User asks a question"] --> Think["Agent thinks:<br/>What kind of question is this?"]
    Think -->|Data question| SQL["SQL Tool<br/>(query the database)"]
    Think -->|Context question| RAG["RAG Tool<br/>(search knowledge base)"]
    Think -->|Report request| Report["Summary Tool<br/>(combine data + context)"]
    SQL --> Review["Agent reviews tool results"]
    RAG --> Review
    Report --> Review
    Review --> Answer["Agent writes a friendly answer"]

    style Q fill:#e1f5fe
    style Think fill:#fff3e0
    style SQL fill:#e8f5e9
    style RAG fill:#e8f5e9
    style Report fill:#e8f5e9
    style Review fill:#fff3e0
    style Answer fill:#e1f5fe
```

1. You ask a question
2. The agent (powered by the LLM) analyzes what kind of question it is
3. It decides which tool is best suited and calls it
4. The tool executes (runs a query, searches documents, etc.)
5. The agent reviews the tool's output
6. It writes a final, human-readable answer

### Simple Analogy

The agent is like a manager with several employees (tools). When you give the manager a task, they decide which employee is best suited, delegate the work, review the result, and report back to you. The manager can even ask multiple employees for help on complex questions.

### Common Agent Frameworks

| Framework | Key Feature |
|-----------|------------|
| **LangChain** | Most popular, extensive tool ecosystem |
| **LlamaIndex** | Optimized for RAG workflows |
| **CrewAI** | Multi-agent collaboration |
| **AutoGen** | Microsoft's agent framework |

---

## Step 5: Putting It All Together

Here is how these three concepts combine into a complete AI application:

```mermaid
sequenceDiagram
    actor User
    participant UI as Web UI
    participant Agent as AI Agent
    participant LLM as LLM (Claude)
    participant Tools as Tools
    participant DB as Databases

    User->>UI: Ask a question in English
    UI->>Agent: Forward question
    Agent->>LLM: "Which tool should I use?"
    LLM-->>Agent: "Use the SQL tool"
    Agent->>Tools: Call SQL tool
    Tools->>LLM: "Generate SQL for this question"
    LLM-->>Tools: SQL query
    Tools->>DB: Execute query
    DB-->>Tools: Result rows
    Tools-->>Agent: Formatted results
    Agent->>LLM: "Summarize these results"
    LLM-->>Agent: Plain English answer
    Agent-->>UI: Display answer
    UI-->>User: See the answer!
```

### The key insight

Each component has a clear role:
- **LLM** = understands language and generates text
- **RAG** = gives the LLM access to your specific data
- **Agent** = decides what actions to take and coordinates everything

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
| **Context Window** | How much text the AI can "see" at once (e.g., 200K tokens) |
| **Fine-tuning** | Training an existing LLM on your specific data |
| **Inference** | When the LLM generates a response (as opposed to training) |
