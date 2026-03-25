"""
SQL Query Tool.

Translates natural language questions into SQL, validates the query,
executes it against the SQLite database, and returns structured results.
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
    try:
        logger.info("[SQL TOOL] Sending schema + question to Claude for SQL generation...")
        logger.debug("[SQL TOOL] SQL generation prompt:\n%s", sql_prompt)
        response = llm.invoke(sql_prompt)
        sql = response.content.strip()

        sql = sql.replace("```sql", "").replace("```", "").strip()

        logger.info("[SQL TOOL] Generated SQL: %s", sql)
        logger.info("[SQL TOOL] Executing SQL against SQLite database at '%s'...", Settings.DB_PATH)

        results = execute_query(sql)

        if isinstance(results, str):
            logger.warning("[SQL TOOL] Query returned message: %s", results)
            return f"SQL: {sql}\n\nResult: {results}"

        result_str = json.dumps(results, indent=2, default=str)
        logger.info("[SQL TOOL] Query returned %d rows", len(results))
        logger.debug("[SQL TOOL] Results:\n%s", result_str[:500])
        logger.info("=" * 80)
        return f"SQL: {sql}\n\nResults ({len(results)} rows):\n{result_str}"

    except Exception as e:
        logger.error("[SQL TOOL] Error: %s", str(e))
        return f"Error generating/executing SQL: {str(e)}"
