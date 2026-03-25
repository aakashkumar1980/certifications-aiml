"""
RAG Search Tool.

Performs semantic similarity search over the ChromaDB knowledge base
and returns the most relevant document chunks to the agent.
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

    Performs a semantic similarity search over campaign descriptions,
    performance summaries, and business glossary definitions stored
    in ChromaDB. Returns the top-3 most relevant documents.

    Use this tool when the user asks about campaign strategy, business
    definitions, or needs qualitative context beyond raw data.

    Args:
        query: Natural language search query.

    Returns:
        Formatted string with up to 3 relevant knowledge base documents,
        each annotated with its type and campaign ID (if applicable).
    """
    logger.info("=" * 80)
    logger.info("[RAG TOOL] Received search query: \"%s\"", query)

    try:
        results = search_similar(query, n_results=Settings.RAG_DEFAULT_RESULTS)
        if not results:
            logger.warning("[RAG TOOL] No relevant documents found.")
            return "No relevant documents found in the knowledge base."

        formatted_parts = []
        for i, r in enumerate(results, 1):
            doc_type = r["metadata"].get("type", "unknown")
            campaign_id = r["metadata"].get("campaign_id", "N/A")
            formatted_parts.append(
                f"[Source {i}] Type: {doc_type} | Campaign: {campaign_id}\n{r['content']}"
            )

        output = "\n\n---\n\n".join(formatted_parts)
        logger.info("[RAG TOOL] Returning %d source chunks to agent", len(results))
        logger.info("=" * 80)
        return output

    except Exception as e:
        logger.error("[RAG TOOL] Error: %s", str(e))
        return f"Error searching knowledge base: {str(e)}"
