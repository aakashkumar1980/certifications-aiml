"""
Performance Summary Tool.

Combines structured database metrics with RAG context to produce
a narrative performance report for a specific campaign. This is a
hybrid tool that uses both SQL queries and semantic search, then
feeds everything to Claude for synthesis.
"""

import json
import logging

from langchain_core.tools import tool

from config.settings import Settings
from database.campaign_db import execute_query
from rag.vector_store import search_similar
from llm.provider import get_llm

logger = logging.getLogger("rag_pipeline")


@tool
def performance_summary_tool(campaign_id: str) -> str:
    """
    Generate a narrative performance summary for a specific campaign.

    Combines structured database metrics (monthly performance, enrollment
    totals, redemption amounts) with qualitative RAG context to produce
    a business-friendly performance report using Claude.

    Use this tool when the user asks for a detailed summary or report
    for a specific campaign. Provide the campaign_id (e.g., 'CMP-001').

    Args:
        campaign_id: The campaign identifier (e.g., 'CMP-001').

    Returns:
        A 3-4 paragraph narrative covering enrollment trends, redemption
        patterns, ROI analysis, and recommendations.
    """
    logger.info("=" * 80)
    logger.info("[PERF TOOL] Generating summary for campaign: %s", campaign_id)

    try:
        # Fetch monthly performance metrics joined with campaign info
        perf_sql = (
            f"SELECT cp.*, c.campaign_name, c.campaign_type, c.target_segment, c.budget_allocated "
            f"FROM campaign_performance cp "
            f"JOIN campaigns c ON cp.campaign_id = c.campaign_id "
            f"WHERE cp.campaign_id = '{campaign_id}' ORDER BY cp.month"
        )
        logger.info("[PERF TOOL] Executing performance SQL: %s", perf_sql)
        perf_data = execute_query(perf_sql)

        # Fetch aggregate enrollment and redemption stats
        enroll_sql = f"SELECT COUNT(*) as total_enrollments FROM enrollments WHERE campaign_id = '{campaign_id}'"
        redeem_sql = (
            f"SELECT COUNT(*) as total_redemptions, SUM(redemption_amount) as total_amount "
            f"FROM redemptions WHERE campaign_id = '{campaign_id}'"
        )
        logger.info("[PERF TOOL] Executing enrollment SQL: %s", enroll_sql)
        enroll_data = execute_query(enroll_sql)
        logger.info("[PERF TOOL] Executing redemption SQL: %s", redeem_sql)
        redeem_data = execute_query(redeem_sql)

        # Supplement with RAG context for qualitative insights (logs steps 6-8 internally)
        logger.info("[PERF TOOL] Searching RAG for qualitative context...")
        rag_context = search_similar(f"performance summary for {campaign_id}", n_results=2)
        rag_text = "\n".join([r["content"] for r in rag_context])

        if isinstance(perf_data, str):
            logger.warning("[PERF TOOL] No performance data found: %s", perf_data)
            return f"Could not find performance data for {campaign_id}: {perf_data}"

        # Assemble all data for the summary prompt
        data_payload = json.dumps({
            "performance_metrics": perf_data,
            "enrollment_totals": enroll_data,
            "redemption_totals": redeem_data,
        }, indent=2, default=str)

        # --- STEP 9: Contextually Augmented Prompt ---
        summary_prompt = (
            f"Generate a concise business-friendly performance summary for campaign {campaign_id}.\n\n"
            f"Data:\n{data_payload}\n\n"
            f"Additional Context:\n{rag_text}\n\n"
            "Format: 3-4 paragraphs covering enrollment trends, redemption patterns, "
            "ROI analysis, and a recommendation. Use specific numbers from the data."
        )
        logger.info("[STEP 9] CONTEXTUALLY AUGMENTED PROMPT constructed:")
        logger.info("[STEP 9]   DB results: %d performance rows, enrollment totals, redemption totals", len(perf_data))
        logger.info("[STEP 9]   RAG context: %d chunks retrieved", len(rag_context))
        logger.debug("[STEP 9]   Full prompt:\n%s", summary_prompt[:1000])

        # --- STEP 10: Fed to LLM ---
        llm = get_llm()
        logger.info("[STEP 10] FED TO LLM: Sending augmented prompt to '%s' (temperature=%s, max_tokens=%d)...",
                     Settings.LLM_MODEL, Settings.LLM_TEMPERATURE, Settings.LLM_MAX_TOKENS)

        response = llm.invoke(summary_prompt)

        # --- STEP 11: LLM Response ---
        logger.info("[STEP 11] LLM RESPONSE received (%d chars): \"%.200s...\"",
                     len(response.content), response.content)
        logger.info("=" * 80)
        return response.content

    except Exception as e:
        logger.error("[PERF TOOL] Error: %s", str(e))
        return f"Error generating performance summary: {str(e)}"
