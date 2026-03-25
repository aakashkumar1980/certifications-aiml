# TUTORIAL: AI Concepts for Beginners

A step-by-step guide to the core AI concepts used in modern AI-powered applications. No prior AI experience is needed. Concepts are explained generically — the accompanying `campaign_performance_analysis` project is referenced as a working example.

---

## Step 1: Understanding the Problem AI Solves

Imagine any team that needs to answer questions from data stored in databases — sales figures, inventory levels, patient records, marketing results. Traditionally, this requires:

1. A **data analyst** who knows SQL (a database query language)
2. A **domain expert** who understands the terminology
3. A **report writer** who can summarize findings in plain English

Modern AI can replace all three by letting users ask questions in plain English and getting answers automatically.

> **In our example project:** Business stakeholders ask questions like "Which campaign has the highest enrollment?" and the AI writes the SQL, runs it, and explains the results — no SQL knowledge needed.

---

## Step 2: The Two Categories of a RAG Application

Any RAG (Retrieval-Augmented Generation) application is built around two distinct categories:

```mermaid
flowchart TB
    subgraph cat1["Category 1: RAG Pipeline — Knowledge Retrieval"]
        direction LR
        D["Documents"] --> C["Chunking"]
        C --> E["Embedding"]
        E --> V["Vector DB"]
        V --> S["Semantic Search"]
    end

    subgraph cat2["Category 2: LLM Intelligence — Content Generation"]
        direction LR
        A["Agent"] --> T["Tools"]
        T --> L["LLM"]
        L --> R["Response"]
    end

    cat1 -.->|"Retrieved context<br/>feeds into"| cat2

    style cat1 fill:#e8f5e9
    style cat2 fill:#fce4ec
```

**Category 1 (RAG Pipeline)** finds relevant information from your domain-specific knowledge base. It uses embedding models (NOT the LLM) to convert text into numerical vectors and search by meaning. This is the "retrieval" part.

**Category 2 (LLM Intelligence)** thinks, reasons, and generates natural language. The LLM decides which tools to use, generates structured queries, synthesizes data into reports, and can fall back on its own trained knowledge when the knowledge base has no relevant answer. This is the "generation" part.

### Why separate them?

- You can swap your vector database (e.g., ChromaDB → Pinecone) without touching any LLM code
- You can swap your LLM provider (e.g., Claude → GPT) without touching any retrieval code
- Each category can be tested, debugged, and scaled independently

> **In our example project:** The `rag/` package handles Category 1 (documents, chunking, ChromaDB). The `llm/` package handles Category 2 (Claude, agent, tools). They communicate through a clean interface — `search_similar()`.

---

## Step 3: LLM (Large Language Model) — The "Brain" (Category 2)

### What is an LLM?

A Large Language Model is an AI that understands and generates human language. Think of it as a very smart auto-complete — but instead of finishing your sentence, it can write database queries, summarize data, and have multi-turn conversations.

### Popular LLMs

| LLM | Provider | Key Strength |
|-----|----------|-------------|
| **Claude** | Anthropic | Strong reasoning, tool use, long context |
| **GPT** | OpenAI | Broad ecosystem, multimodal |
| **Gemini** | Google | Multimodal, large context window |
| **LLaMA** | Meta | Open source, self-hostable |

### What can an LLM do in a RAG application?

1. **Convert natural language to structured queries** — "Show me top sellers" → `SELECT ... ORDER BY sales DESC`
2. **Synthesize multiple data sources** — combine database rows + knowledge base context into a coherent narrative
3. **Decide which tool to use** — "Is this a data question or a definition question?"
4. **Fall back on trained knowledge** — when your knowledge base doesn't have an answer, the LLM can provide general definitions from what it learned during training

### Key Configuration Parameters

| Parameter | What It Controls | Typical Value |
|-----------|-----------------|---------------|
| **Model** | Which LLM to use | `claude-sonnet-4-20250514` |
| **Temperature** | Creativity vs. precision (0 = deterministic, 1 = creative) | `0` for data queries |
| **Max Tokens** | Maximum length of the response | `1024`–`4096` |

### Simple Analogy

The LLM is like a very experienced analyst who speaks both "human language" and "database language." You tell it what you want in English, and it translates that into the right technical actions.

> **In our example project:** Claude is initialized in `llm/provider.py` with `temperature=0` (deterministic for data accuracy) and used by all three tools — SQL generation, RAG search formatting, and performance report synthesis.

---

## Step 4: RAG (Retrieval-Augmented Generation) — The "Reference Book" (Category 1)

### What is RAG?

RAG is a technique where the AI first *retrieves* relevant information from a knowledge base, and then *generates* an answer using that information. Without RAG, the AI only knows what it was trained on. With RAG, it can access your specific domain data.

### Why is RAG needed?

An LLM knows general things about the world, but it does NOT know your specific data — your company's products, your internal terminology, your policies, your metrics. RAG bridges this gap by giving the LLM a "reference book" to consult before answering.

### How RAG works — The 11-Step Pipeline

Every RAG application follows this same fundamental pipeline, regardless of domain:

```mermaid
sequenceDiagram
    actor User as User

    box rgb(232, 245, 233) Category 1: RAG Pipeline
        participant Docs as Documents
        participant Chunk as Chunker
        participant Embed as Embedding Model
        participant VDB as Vector Database
    end

    box rgb(252, 228, 236) Category 2: LLM Intelligence
        participant Agent as AI Agent
        participant LLM as LLM
    end

    Note over Docs, VDB: One-Time Ingestion (Steps 1-4)
    Docs->>Docs: Step 1: Load documents
    Docs->>Chunk: Step 2: Split into chunks
    Chunk->>Embed: Step 3: Convert to embeddings
    Embed->>VDB: Step 4: Store in vector database

    Note over User, LLM: Every Query (Steps 5-11)
    User->>Agent: Step 5: Ask a question
    Agent->>Embed: Step 6: Embed the query
    Embed->>VDB: Step 7: Semantic search
    VDB-->>Agent: Step 8: Return closest chunks
    Agent->>Agent: Step 9: Build augmented prompt<br/>(question + retrieved chunks + any DB data)
    Agent->>LLM: Step 10: Feed to LLM
    LLM-->>User: Step 11: LLM Response
```

### The 11 Steps Explained

| Step | Name | Category | What Happens |
|------|------|----------|--------------|
| 1 | Loading Documents | RAG | Domain documents gathered — could be PDFs, text files, database records, or hard-coded content |
| 2 | Chunking | RAG | Documents split into smaller overlapping pieces for better search precision |
| 3 | Embedding Chunks | RAG | Each chunk converted to a numerical vector (e.g., 384 dimensions) |
| 4 | Storing in Vector DB | RAG | Vectors stored in a vector database (e.g., ChromaDB, Pinecone, FAISS) with metadata |
| 5 | User Query | LLM | User asks a question; agent decides which tool(s) to call |
| 6 | Embedding Query | RAG | User's question converted to a vector using the same embedding model |
| 7 | Semantic Search | RAG | Find vectors closest to the query vector (cosine similarity) |
| 8 | Retrieve Chunks | RAG | Return the most relevant document chunks with distance scores |
| 9 | Augmented Prompt | LLM | Combine retrieved chunks + any structured data + original question into one prompt |
| 10 | Fed to LLM | LLM | Send the augmented prompt to the LLM |
| 11 | LLM Response | LLM | LLM generates a natural language answer grounded in the retrieved data |

> **In our example project:** Steps 1-4 happen at startup — campaign descriptions, performance summaries, and a business glossary are chunked and stored in ChromaDB. Steps 5-11 happen on every API request — the user's question triggers semantic search, SQL queries, and Claude synthesis.

### Simple Analogy

Imagine you are taking an open-book exam. The textbook is your knowledge base. RAG is the process of: (a) looking up the most relevant pages, then (b) writing your answer using those pages. Without RAG, it is a closed-book exam — you can only use what you memorized.

### What is Chunking? (Step 2)

Documents are split into smaller, overlapping pieces before embedding. Why?

- **Better retrieval** — A 200-character chunk specifically about "ROI calculation" is more relevant to an ROI question than a 2000-character document that mentions ROI in one sentence
- **Overlap** — Chunks overlap so no information is lost at boundaries
- **Configurable** — Chunk size and overlap are tunable parameters that affect retrieval quality

```
Original document (400 chars):
[==================================================]

After chunking (size=200, overlap=50):
[===================]           ← Chunk 1 (chars 0-200)
            [===================]     ← Chunk 2 (chars 150-350)
                        [===================]  ← Chunk 3 (chars 300-400)
```

Common chunking strategies:
- **RecursiveCharacterTextSplitter** (LangChain) — tries paragraph → sentence → word boundaries before character splits
- **TokenTextSplitter** — splits by token count (useful when you care about LLM token limits)
- **SemanticChunker** — uses embeddings to find natural topic boundaries

> **In our example project:** `rag/chunking.py` uses `RecursiveCharacterTextSplitter` with `chunk_size=200` and `chunk_overlap=50`, splitting at `["\n\n", "\n", ". ", ", ", " "]` boundaries.

### What is an Embedding?

An embedding is a list of numbers (a "vector") that represents the *meaning* of text. Two sentences with similar meanings will have similar vectors, even if they use completely different words.

```
"The dog chased the cat"  → [0.12, 0.85, -0.33, 0.67, ...]  (384 numbers)
"A canine pursued a feline" → [0.11, 0.84, -0.31, 0.68, ...]  (very similar!)
"Stock prices fell today"   → [-0.55, 0.12, 0.91, -0.23, ...]  (very different)
```

The embedding model (e.g., `all-MiniLM-L6-v2`) is a small, fast model — NOT the same as the LLM. It runs locally, has no API costs, and produces vectors in milliseconds.

### Key Terms

| Term | Simple Definition |
|------|------------------|
| **Embedding** | A list of numbers representing the meaning of text. Similar texts → similar numbers. |
| **Vector Database** | A database that stores embeddings and finds "most similar" items by meaning. |
| **Sentence Transformer** | A small AI model that converts text into embeddings. Runs locally, no API needed. |
| **Chunking** | Splitting documents into smaller pieces for more precise retrieval. |
| **Cosine Similarity** | A math formula that measures how similar two vectors are. Score 0–1 (1 = identical). |

### Common Vector Databases

| Database | Key Feature | Best For |
|----------|------------|----------|
| **ChromaDB** | Lightweight, runs locally, no server | Prototypes, small-medium datasets |
| **Pinecone** | Cloud-hosted, fully managed | Production at scale |
| **Weaviate** | Open source, feature-rich | Self-hosted production |
| **FAISS** | By Meta, optimized for speed | Large-scale similarity search |
| **Milvus** | Open source, distributed | Enterprise deployments |

---

## Step 5: AI Agent — The "Decision Maker" (Category 2)

### What is an AI Agent?

An AI Agent is an LLM that can *use tools* and *make decisions* about which tool to use. Instead of just chatting, it can take actions — query a database, search a knowledge base, call an API, or generate a report.

The key difference from a simple chatbot:
- **Chatbot:** You ask → it answers from its training data
- **Agent:** You ask → it *thinks* about what it needs → *calls tools* → *reviews results* → answers

### How an Agent works

```mermaid
flowchart TD
    Q["User asks a question"] --> Think["Agent thinks:<br/>What kind of question is this?"]

    subgraph cat1["Category 1: RAG Pipeline"]
        RAG["Knowledge Search Tool<br/>(search vector database)"]
    end

    subgraph cat2["Category 2: LLM Intelligence"]
        SQL["Database Query Tool<br/>(generate and run SQL)"]
        Report["Report Tool<br/>(combine data + context)"]
        Review["Agent reviews tool results"]
    end

    Think -->|Data question| SQL
    Think -->|Context question| RAG
    Think -->|Report request| Report
    SQL --> Review
    RAG --> Review
    Report --> Review
    Review --> Answer["Agent writes a friendly answer"]

    style Q fill:#e1f5fe
    style Think fill:#fff3e0
    style cat1 fill:#e8f5e9
    style cat2 fill:#fce4ec
    style SQL fill:#fce4ec
    style RAG fill:#e8f5e9
    style Report fill:#fce4ec
    style Review fill:#fff3e0
    style Answer fill:#e1f5fe
```

1. User asks a question
2. The agent (powered by the LLM) analyzes what kind of question it is
3. It decides which tool is best suited and calls it
4. The tool executes (runs a query, searches documents, calls an API, etc.)
5. The agent reviews the tool's output
6. It writes a final, human-readable answer

### The ReAct Pattern (Reason + Act)

Most modern agents use the **ReAct** pattern — the LLM alternates between:
- **Reasoning:** "This question asks for data, I should use the SQL tool"
- **Acting:** Calls the SQL tool with the question
- **Observing:** Reads the tool's output
- **Reasoning again:** "I have the data, now I can answer"

This loop continues until the agent has enough information to respond.

### What are Tools?

Tools are regular functions that the agent can call. Each tool has:
- A **name** — so the agent can refer to it
- A **description** (from the docstring) — so the agent knows *when* to use it
- **Parameters** — what inputs it needs
- A **return value** — what it gives back

In LangChain, you define a tool with the `@tool` decorator:

```python
from langchain_core.tools import tool

@tool
def search_knowledge_base(query: str) -> str:
    """Search the knowledge base for relevant context.
    Use when the user asks about definitions or qualitative information."""
    results = vector_store.search(query)
    return format_results(results)
```

The docstring is critical — it's what the LLM reads to decide whether to use this tool.

> **In our example project:** Three tools are defined in `llm/tools/` — `sql_query_tool` (generates and runs SQL), `rag_search_tool` (searches ChromaDB), and `performance_summary_tool` (combines both for narrative reports).

### Simple Analogy

The agent is like a manager with several employees (tools). When you give the manager a task, they decide which employee is best suited, delegate the work, review the result, and report back to you. The manager can even ask multiple employees for help on complex questions.

### Common Agent Frameworks

| Framework | Key Feature | Pattern |
|-----------|------------|---------|
| **LangChain + LangGraph** | Most popular, stateful graph-based agents | ReAct with message state |
| **LlamaIndex** | Optimized for RAG-heavy workflows | Query engines + tools |
| **CrewAI** | Multi-agent collaboration | Role-based agent teams |
| **AutoGen** | Microsoft's framework | Conversational agent groups |

> **In our example project:** `llm/agent.py` uses LangGraph's `create_react_agent()` which implements the ReAct pattern. The agent maintains conversation history via LangGraph's built-in message state.

---

## Step 6: LLM Fallback — When RAG Has No Answer

An important behavior: what happens when the user asks something NOT in your knowledge base?

```
User: "What is the definition of enrollment and what are its types?"
```

Your vector database might have "Enrollment Rate: The percentage of users who enroll..." but NOT a general definition of enrollment or its types. In this case:

1. **RAG search returns partial matches** — the glossary entry about "enrollment rate"
2. **The LLM fills in the gaps** — Claude knows the general concept of enrollment from its training data
3. **The answer blends both** — domain-specific context from RAG + general knowledge from the LLM

This is a key advantage of the two-category architecture. Category 1 (RAG) provides what it can; Category 2 (LLM) supplements with its broader trained knowledge. The user gets a complete answer either way.

> **In our example project:** The Postman collection includes a "Scenario 1: LLM Fallback" that demonstrates this — asking about enrollment types that aren't in the vector DB.

---

## Step 7: Putting It All Together

Here is how the two categories combine into a complete application:

```mermaid
sequenceDiagram
    actor User

    box rgb(232, 245, 233) Category 1: RAG Pipeline
        participant Embed as Embedding Model
        participant VDB as Vector Database
    end

    box rgb(252, 228, 236) Category 2: LLM Intelligence
        participant Agent as AI Agent
        participant Tools as Tools
        participant LLM as LLM
    end

    participant DB as Domain Database

    User->>Agent: Step 5: Ask a question in plain language
    Agent->>LLM: "Which tool should I use?"
    LLM-->>Agent: "Use the database tool + knowledge search"

    rect rgb(232, 245, 233)
        Note right of Agent: Category 1: Knowledge Retrieval
        Agent->>Tools: Call knowledge search tool
        Tools->>Embed: Step 6: Embed query
        Embed->>VDB: Step 7: Semantic search
        VDB-->>Tools: Step 8: Closest chunks
    end

    rect rgb(252, 228, 236)
        Note right of Agent: Category 2: Content Generation
        Agent->>Tools: Call database query tool
        Tools->>LLM: Step 9: Schema + question
        LLM-->>Tools: Steps 10-11: Generated query
        Tools->>DB: Execute query
        DB-->>Tools: Result rows
    end

    Tools-->>Agent: Combined: DB results + RAG chunks
    Agent->>LLM: Step 9: Augmented prompt (data + context)
    LLM-->>Agent: Steps 10-11: Natural language answer
    Agent-->>User: Friendly, data-grounded response
```

### The key insight

Each component has a clear role, mapped to two categories:

**Category 1 (RAG Pipeline):** Finds relevant information
- **Embedding Model** = converts text to numerical vectors (runs locally, no API cost)
- **Vector Database** = stores and searches by meaning
- **Chunker** = splits documents for precise retrieval

**Category 2 (LLM Intelligence):** Thinks and generates
- **LLM** = understands language, generates queries and text
- **Agent** = decides what actions to take and coordinates everything
- **Tools** = specialized functions the agent can call

---

## Step 8: Common Patterns Across RAG Applications

Regardless of the domain (healthcare, finance, e-commerce, legal), every RAG application uses these same patterns:

### Pattern: Hybrid Retrieval

Combining vector search (semantic) with structured queries (SQL/API) gives the best results. Vector search finds *context*; structured queries find *data*.

### Pattern: Augmented Prompt Assembly

The most critical step. The prompt sent to the LLM typically looks like:

```
Given the following context:
[Retrieved chunks from vector DB]
[Results from database query]

Answer the following question:
[User's original question]
```

The quality of this prompt directly determines the quality of the answer.

### Pattern: Safety Guards

Always validate LLM-generated queries before executing them. The LLM might generate a `DROP TABLE` or `DELETE` statement. A regex or allowlist guard prevents this.

### Pattern: Idempotent Initialization

The knowledge base should only be built once. On subsequent startups, check if data already exists and skip re-ingestion.

> **In our example project:** All four patterns are implemented — hybrid retrieval (SQL + ChromaDB), augmented prompts (in `performance_summary_tool`), SQL safety guards (regex in `campaign_db.py`), and idempotent init (ChromaDB count check in `vector_store.py`).

---

## Glossary of AI Terms

| Term | Simple Definition |
|------|------------------|
| **LLM** | An AI model that reads and writes human language |
| **RAG** | A technique: look up relevant info first, then answer |
| **Embedding** | Numbers that represent the meaning of text |
| **Vector Database** | A database that finds similar items by meaning |
| **Chunking** | Splitting documents into smaller overlapping pieces for better search |
| **Cosine Similarity** | A measure of how similar two vectors are (0 = unrelated, 1 = identical) |
| **Agent** | An AI that can decide which tools to use and take actions |
| **ReAct** | A pattern where the agent alternates between reasoning and acting |
| **Tool Calling** | When the AI decides to run a specific function (like a database query) |
| **Prompt** | The instruction/question you give to the AI |
| **Augmented Prompt** | A prompt enriched with retrieved context and data before sending to LLM |
| **Token** | A unit of text (roughly a word or part of a word) |
| **Temperature** | Controls randomness: 0 = deterministic, 1 = creative |
| **Context Window** | How much text the AI can "see" at once (e.g., 200K tokens for Claude) |
| **Fine-tuning** | Training an existing LLM on your specific data |
| **Inference** | When the LLM generates a response (as opposed to training) |
| **Sentence Transformer** | A small model that converts text to embeddings. Runs locally, no API cost. |
