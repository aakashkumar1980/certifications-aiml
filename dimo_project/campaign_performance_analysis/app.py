"""
FastAPI REST API for Campaign Performance Analysis.

Exposes the campaign AI assistant as a set of HTTP endpoints that can be
consumed by any client (curl, Postman, frontend apps, other services).

Endpoints:
    - ``GET  /health``              — Health check and system status
    - ``GET  /campaigns``           — List all campaigns
    - ``POST /ask``                 — Ask a natural language question
    - ``POST /ask/sql``             — Ask a data question (SQL tool only)
    - ``POST /ask/search``          — Search the knowledge base (RAG tool only)
    - ``GET  /campaigns/{id}/summary`` — Get a performance summary for a campaign

On startup, the app automatically:
    1. Generates mock CSV data (if not present)
    2. Initializes the SQLite database
    3. Builds the ChromaDB knowledge base
    4. Creates the LangChain agent

Launch Command::

    uvicorn app:app --reload --port 8000

Environment Variables:
    ANTHROPIC_API_KEY (str): Required. Set in ``.env`` file.
"""

import os
import sys
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

# Add project root to path for package imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# --- Configure RAG Pipeline Logging ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("rag_pipeline")

from config.settings import Settings
from database.campaign_db import init_database, execute_query, get_schema
from rag.vector_store import build_knowledge_base, search_similar
from llm.agent import CampaignAgent


# --- Pydantic Models (Request / Response) ---

class AskRequest(BaseModel):
    """
    Request body for the /ask endpoint.

    Attributes:
        question: Natural language question about campaign data.
    """
    question: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        examples=["Which campaign has the highest enrollment?"],
    )


class AskResponse(BaseModel):
    """
    Response body for the /ask endpoint.

    Attributes:
        answer: The agent's natural language response.
        sql_query: The SQL query used (if sql_query_tool was invoked), or null.
        sources: List of RAG source excerpts (if rag_search_tool was invoked).
    """
    answer: str
    sql_query: str | None = None
    sources: list[str] = []


class SearchRequest(BaseModel):
    """
    Request body for the /ask/search endpoint.

    Attributes:
        query: Semantic search query for the knowledge base.
        n_results: Number of results to return (1-10, default 3).
    """
    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        examples=["What is ROI?"],
    )
    n_results: int = Field(default=3, ge=1, le=10)


class SearchResult(BaseModel):
    """
    A single knowledge base search result.

    Attributes:
        content: The matched document text.
        type: Document type (campaign_description, performance_summary, business_glossary).
        campaign_id: Associated campaign ID, or null for glossary entries.
        distance: Cosine distance score (lower = more relevant).
    """
    content: str
    type: str
    campaign_id: str | None = None
    distance: float | None = None


class HealthResponse(BaseModel):
    """
    Response body for the /health endpoint.

    Attributes:
        status: "ok" if all systems are initialized.
        database: True if SQLite database is accessible.
        knowledge_base: True if ChromaDB collection is populated.
        agent: True if the CampaignAgent is ready.
    """
    status: str
    database: bool
    knowledge_base: bool
    agent: bool


# --- Global State ---

_agent: CampaignAgent | None = None


def _initialize_system():
    """
    Bootstrap all backend services.

    Performs the following steps in order:
        1. Generates mock CSV data if ``campaigns.csv`` does not exist.
        2. Loads CSVs into the SQLite database if ``campaign.db`` does not exist.
        3. Builds the ChromaDB knowledge base (idempotent if already populated).
        4. Creates the CampaignAgent.

    Returns:
        CampaignAgent: The initialized agent instance.

    Raises:
        ValueError: If ANTHROPIC_API_KEY is not set.
    """
    # Step 1: Generate mock data if missing
    if not os.path.exists(os.path.join(Settings.DATA_DIR, "campaigns.csv")):
        logger.info("[STARTUP] Generating mock CSV data...")
        from database.data.generate_mock_data import MockDataGenerator
        generator = MockDataGenerator()
        generator.generate_all()
    else:
        logger.info("[STARTUP] Mock CSV data already exists. Skipping generation.")

    # Step 2: Initialize SQLite database if missing
    if not os.path.exists(Settings.DB_PATH):
        logger.info("[STARTUP] Initializing SQLite database from CSVs...")
        init_database()
    else:
        logger.info("[STARTUP] SQLite database already exists at '%s'.", Settings.DB_PATH)

    # Step 3: Build vector store knowledge base (Steps 1-4 of RAG pipeline)
    logger.info("[STARTUP] Building ChromaDB knowledge base (RAG Steps 1-4: Load → Chunk → Embed → Store)...")
    build_knowledge_base()

    # Step 4: Create agent
    logger.info("[STARTUP] Creating CampaignAgent with LangGraph react agent...")
    return CampaignAgent()


# --- Application Lifecycle ---

@asynccontextmanager
async def lifespan(application: FastAPI):
    """
    FastAPI lifespan handler — runs initialization on startup.

    On startup: initializes database, knowledge base, and agent.
    On shutdown: cleans up resources (currently no-op).
    """
    global _agent
    print("Initializing Campaign AI Assistant...")
    _agent = _initialize_system()
    print("System ready. API is accepting requests.")
    yield
    print("Shutting down.")


# --- FastAPI App ---

app = FastAPI(
    title="Campaign AI Assistant API",
    description=(
        "A RAG-based REST API for credit card campaign performance analysis. "
        "Ask natural language questions about campaign data — the AI agent "
        "translates them into SQL queries, searches the knowledge base, "
        "and returns business-friendly answers."
    ),
    version="1.0.0",
    lifespan=lifespan,
)


# --- Endpoints ---

@app.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """
    Check the health and initialization status of all subsystems.

    Returns the status of the database, knowledge base, and agent.
    """
    db_ok = False
    kb_ok = False

    try:
        result = execute_query("SELECT COUNT(*) as cnt FROM campaigns")
        db_ok = isinstance(result, list) and len(result) > 0
    except Exception:
        pass

    try:
        results = search_similar("test", n_results=1)
        kb_ok = isinstance(results, list)
    except Exception:
        pass

    return HealthResponse(
        status="ok" if (db_ok and kb_ok and _agent is not None) else "degraded",
        database=db_ok,
        knowledge_base=kb_ok,
        agent=_agent is not None,
    )


@app.get("/campaigns", tags=["Campaigns"])
async def list_campaigns():
    """
    List all campaigns with their status, type, and budget.

    Returns:
        List of campaign dictionaries with all columns from the campaigns table.
    """
    result = execute_query(
        "SELECT campaign_id, campaign_name, campaign_type, start_date, end_date, "
        "target_segment, budget_allocated, merchant_category, status "
        "FROM campaigns ORDER BY campaign_id"
    )
    if isinstance(result, str):
        raise HTTPException(status_code=500, detail=result)
    return result


@app.get("/campaigns/{campaign_id}", tags=["Campaigns"])
async def get_campaign(campaign_id: str):
    """
    Get details for a specific campaign.

    Args:
        campaign_id: Campaign identifier (e.g., 'CMP-001').

    Returns:
        Campaign dictionary with all columns.
    """
    result = execute_query(
        f"SELECT * FROM campaigns WHERE campaign_id = '{campaign_id}'"
    )
    if isinstance(result, str) or not result:
        raise HTTPException(status_code=404, detail=f"Campaign '{campaign_id}' not found")
    return result[0]


@app.get("/campaigns/{campaign_id}/summary", response_model=AskResponse, tags=["Campaigns"])
async def get_campaign_summary(campaign_id: str):
    """
    Generate a narrative performance summary for a specific campaign.

    Uses the AI agent's performance_summary_tool to combine database
    metrics with RAG context into a business-friendly report.

    Args:
        campaign_id: Campaign identifier (e.g., 'CMP-001').

    Returns:
        AskResponse with the generated summary.
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    result = _agent.ask(f"Give me a detailed performance summary for {campaign_id}")
    return AskResponse(**result)


@app.post("/ask", response_model=AskResponse, tags=["AI Assistant"])
async def ask_question(request: AskRequest):
    """
    Ask the AI assistant a natural language question.

    The agent decides which tool(s) to use (SQL, RAG, or summary)
    and returns a business-friendly answer.

    Args:
        request: AskRequest with the question text.

    Returns:
        AskResponse with answer, optional SQL query, and optional sources.
    """
    if _agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    result = _agent.ask(request.question)
    return AskResponse(**result)


@app.post("/ask/sql", response_model=AskResponse, tags=["AI Assistant"])
async def ask_sql(request: AskRequest):
    """
    Ask a data question that will be answered using SQL only.

    Bypasses the agent and directly invokes the sql_query_tool.
    Use this when you know the question is purely data-driven.

    Args:
        request: AskRequest with the question text.

    Returns:
        AskResponse with the SQL tool's result as the answer, plus the SQL query used.
    """
    from llm.tools.sql_query import sql_query_tool

    result = sql_query_tool.invoke(request.question)
    sql_query = None
    if "SQL:" in result:
        lines = result.split("\n")
        sql_line = next((line for line in lines if line.startswith("SQL:")), None)
        if sql_line:
            sql_query = sql_line.replace("SQL: ", "")

    return AskResponse(answer=result, sql_query=sql_query)


@app.post("/ask/search", tags=["AI Assistant"])
async def ask_search(request: SearchRequest) -> list[SearchResult]:
    """
    Search the knowledge base directly using semantic similarity.

    Bypasses the agent and returns raw RAG search results.

    Args:
        request: SearchRequest with query text and result count.

    Returns:
        List of SearchResult objects with content, metadata, and distance.
    """
    results = search_similar(request.query, n_results=request.n_results)
    return [
        SearchResult(
            content=r["content"],
            type=r["metadata"].get("type", "unknown"),
            campaign_id=r["metadata"].get("campaign_id"),
            distance=r["distance"],
        )
        for r in results
    ]


@app.get("/schema", tags=["System"])
async def get_database_schema():
    """
    Return the database schema as a formatted string.

    Useful for debugging or understanding what data is available.
    """
    return {"schema": get_schema()}


# --- Script Entry Point ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
