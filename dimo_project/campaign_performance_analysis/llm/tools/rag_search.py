"""
RAG Search Tool — LLM Intelligence (Category 2).

Acts as the bridge between the agent (Category 2) and the RAG pipeline
(Category 1). The tool itself lives in the LLM package because it is
a tool the agent calls, but it delegates to ``rag.vector_store`` which
handles Steps 6-8 of the RAG pipeline.

RAG Pipeline Steps involved:
    Step 6: Embedding Query       — (delegated to rag/vector_store.py)
    Step 7: Semantic Search       — (delegated to rag/vector_store.py)
    Step 8: Retrieve Closest Chunks — (delegated to rag/vector_store.py)
    Step 9: Contextually Augmented Prompt — chunks formatted for agent
"""

import logging

from langchain_core.tools import tool

from config.settings import Settings
from rag.vector_store import search_similar

logger = logging.getLogger("rag_pipeline")


@tool
def rag_search_tool(query: str) -> str:
    """
    Search the campaign knowledge base for relevant context.

    Performs a semantic similarity search over campaign descriptions
    stored in ChromaDB. Returns the top-3 most relevant documents.
    Campaign descriptions contain company-specific information: campaign
    names, target segments, reward structures, partner merchants, budgets.

    Use this tool when the user asks about what a specific campaign offers,
    which campaigns target a certain segment, or needs campaign context.
    For generic business definitions (ROI, enrollment rate, etc.), you
    already know these — no need to search.

    Args:
        query: Natural language search query.

    Returns:
        Formatted string with up to 3 relevant campaign descriptions,
        each annotated with its campaign ID.
    """
    logger.info("=" * 80)
    logger.info("[RAG TOOL] Received search query: \"%s\"", query)

    try:
        # Steps 6, 7, 8 are logged inside search_similar() (Category 1: RAG Pipeline)
        results = search_similar(query, n_results=Settings.RAG_DEFAULT_RESULTS)
        if not results:
            logger.warning("[RAG TOOL] No relevant documents found.")
            return "No relevant documents found in the knowledge base."

        # --- STEP 9: Contextually Augmented Prompt (partial) ---
        # Format the retrieved chunks so the agent can include them in the augmented prompt
        formatted_parts = []
        for i, r in enumerate(results, 1):
            doc_type = r["metadata"].get("type", "unknown")
            campaign_id = r["metadata"].get("campaign_id", "N/A")
            formatted_parts.append(
                f"[Source {i}] Type: {doc_type} | Campaign: {campaign_id}\n{r['content']}"
            )

        output = "\n\n---\n\n".join(formatted_parts)
        logger.info("[STEP 9] CONTEXTUALLY AUGMENTED PROMPT (partial): %d RAG chunks formatted for agent consumption",
                     len(results))
        logger.info("=" * 80)
        return output

    except Exception as e:
        logger.error("[RAG TOOL] Error: %s", str(e))
        return f"Error searching knowledge base: {str(e)}"
