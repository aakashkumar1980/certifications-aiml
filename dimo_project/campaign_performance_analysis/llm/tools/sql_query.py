"""
SQL Query Tool — LLM Intelligence (Category 2).

Translates natural language questions into SQL, validates the query,
executes it against the SQLite database, and returns structured results.

RAG Pipeline Steps involved:
    Step 9:  Contextually Augmented Prompt — schema + question assembled
    Step 10: Fed to LLM — Claude generates SQL
    Step 11: LLM Response — SQL returned and executed
"""

import json
import logging

from langchain_core.tools import tool

from config.settings import Settings
from database.campaign_db import get_schema, execute_query
from llm.provider import get_llm

logger = logging.getLogger("rag_pipeline")


@tool
def sql_query_tool(question: str) -> str:
    """
    Translate a natural language question into SQL and execute it.

    Takes a plain-English question about campaign data, uses Claude to
    generate a corresponding SQLite SELECT query, validates it against
    the safety guard, executes it, and returns formatted results.

    Use this tool when the user asks questions that can be answered with
    data from the campaigns, enrollments, redemptions, or
    campaign_performance tables.

    Args:
        question: Natural language question about campaign data.

    Returns:
        Formatted string containing the generated SQL and query results,
        or an error message if generation/execution fails.
    """
    logger.info("=" * 80)
    logger.info("[SQL TOOL] Received question: \"%s\"", question)

    schema = get_schema()
    llm = get_llm()

    # --- STEP 9: Contextually Augmented Prompt ---
    sql_prompt = (
        f"You are a SQL expert. Given this database schema:\n\n{schema}\n\n"
        f'Generate a SQLite SELECT query to answer this question: "{question}"\n\n'
        "Rules:\n"
        "- Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP)\n"
        "- Return ONLY the SQL query, no explanation or markdown\n"
        "- Use appropriate JOINs when data spans multiple tables\n"
        "- Use aggregations (COUNT, SUM, AVG) when appropriate\n"
        "- Limit results to 20 rows maximum"
    )
    logger.info("[STEP 9] CONTEXTUALLY AUGMENTED PROMPT: DB schema (%d chars) + user question assembled for SQL generation",
                 len(schema))
    logger.debug("[STEP 9]   Full prompt:\n%s", sql_prompt[:800])

    try:
        # --- STEP 10: Fed to LLM ---
        logger.info("[STEP 10] FED TO LLM: Sending augmented prompt to '%s' for SQL generation...", Settings.LLM_MODEL)
        response = llm.invoke(sql_prompt)
        sql = response.content.strip()

        # Strip markdown code fences if the model wraps the SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()

        # --- STEP 11: LLM Response (SQL generated) ---
        logger.info("[STEP 11] LLM RESPONSE (generated SQL): \"%s\"", sql)
        logger.info("[SQL TOOL] Executing SQL against SQLite database at '%s'...", Settings.DB_PATH)

        results = execute_query(sql)

        if isinstance(results, str):
            logger.warning("[SQL TOOL] Query returned message: %s", results)
            return f"SQL: {sql}\n\nResult: {results}"

        result_str = json.dumps(results, indent=2, default=str)
        logger.info("[SQL TOOL] Query returned %d rows (DB results ready for agent to synthesize)", len(results))
        logger.debug("[SQL TOOL] Results:\n%s", result_str[:500])
        logger.info("=" * 80)
        return f"SQL: {sql}\n\nResults ({len(results)} rows):\n{result_str}"

    except Exception as e:
        logger.error("[SQL TOOL] Error: %s", str(e))
        return f"Error generating/executing SQL: {str(e)}"
