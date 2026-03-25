"""
Campaign Agent Module for Campaign Performance Analysis.

Implements a LangGraph react agent powered by Claude that orchestrates
three specialized tools to answer natural language questions about credit
card campaign data:

1. **sql_query_tool** — Translates natural language to SQL, validates the
   query, executes it against SQLite, and returns structured results.
2. **rag_search_tool** — Performs semantic search over the ChromaDB knowledge
   base for campaign context, performance summaries, and business glossary.
3. **performance_summary_tool** — Combines database metrics with RAG context
   to produce a narrative performance report for a specific campaign.

The agent maintains multi-turn conversation history via LangGraph's
built-in message state, enabling follow-up questions.

Example Usage::

    from agent.campaign_agent import CampaignAgent
    agent = CampaignAgent()
    result = agent.ask("Which campaign has the highest enrollment?")
    print(result["answer"])
"""

import os
import sys
import json
import logging

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings
from database.campaign_db import get_schema, execute_query
from rag.vector_store import search_similar

load_dotenv()

logger = logging.getLogger("rag_pipeline")

# --- System Prompt ---
SYSTEM_PROMPT = (
    "You are a credit card campaign analytics assistant for a financial services company. "
    "You help business analysts understand campaign performance, enrollment trends and "
    "merchant metrics. Always ground your answers in actual data. Be concise and "
    "business-friendly.\n\n"
    "You have access to these tools:\n"
    "- sql_query_tool: Query the campaign database with natural language questions\n"
    "- rag_search_tool: Search the knowledge base for campaign context and business definitions\n"
    "- performance_summary_tool: Get a detailed performance summary for a specific campaign\n\n"
    "When answering questions:\n"
    "1. Use sql_query_tool for data-driven questions (counts, comparisons, trends)\n"
    "2. Use rag_search_tool for context, definitions, and qualitative insights\n"
    "3. Use performance_summary_tool for detailed campaign reports\n"
    "4. Always cite which campaign or data source your answer comes from\n"
    "5. If one tool fails, try another approach"
)


# --- Tool Definitions ---

def _get_llm():
    """Create a ChatAnthropic LLM instance with project-wide settings."""
    Settings.validate()
    return ChatAnthropic(
        model=Settings.LLM_MODEL,
        anthropic_api_key=Settings.ANTHROPIC_API_KEY,
        temperature=Settings.LLM_TEMPERATURE,
        max_tokens=Settings.LLM_MAX_TOKENS,
    )


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
    llm = _get_llm()

    # Prompt Claude to generate a safe SELECT query
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

        # Strip markdown code fences if the model wraps the SQL
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
        # Steps 6, 7, 8 are logged inside search_similar()
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
        llm = _get_llm()
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


class CampaignAgent:
    """
    Conversational AI agent for campaign performance analysis.

    Wraps a LangGraph react agent with three domain-specific tools
    (SQL, RAG, performance summary) and maintains chat history for
    multi-turn conversations.
    """

    def __init__(self):
        llm = _get_llm()
        tools = [sql_query_tool, rag_search_tool, performance_summary_tool]

        self.agent = create_react_agent(
            model=llm,
            tools=tools,
            prompt=SystemMessage(content=SYSTEM_PROMPT),
        )
        self.chat_history = []
        logger.info("[AGENT] CampaignAgent initialized with %d tools: %s",
                     len(tools), [t.name for t in tools])

    def ask(self, question):
        """
        Send a question to the agent and return a structured response.

        Args:
            question (str): Natural language question from the user.

        Returns:
            dict: Response with keys: answer, sql_query, sources.
        """
        try:
            # --- STEP 5: User Query ---
            logger.info("=" * 80)
            logger.info("[STEP 5] USER QUERY received: \"%s\"", question)
            logger.info("[STEP 5] Agent will decide which tool(s) to invoke...")

            self.chat_history.append(HumanMessage(content=question))

            # --- STEP 9/10: Agent reasoning loop (decides tools, builds augmented prompts, calls LLM) ---
            logger.info("[STEP 9-10] AGENT REASONING: Invoking LangGraph react agent loop...")
            result = self.agent.invoke({"messages": self.chat_history})

            messages = result.get("messages", [])

            # The last message is the agent's final response
            answer = ""
            if messages:
                answer = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

            # Update chat history with the full conversation
            self.chat_history = messages

            response = {
                "answer": answer,
                "sql_query": None,
                "sources": [],
            }

            # Extract metadata from tool call messages
            for msg in messages:
                if hasattr(msg, "name") and hasattr(msg, "content"):
                    tool_name = getattr(msg, "name", "")
                    tool_output = str(msg.content)

                    if tool_name == "sql_query_tool" and "SQL:" in tool_output:
                        lines = tool_output.split("\n")
                        sql_line = next((l for l in lines if l.startswith("SQL:")), None)
                        if sql_line:
                            response["sql_query"] = sql_line.replace("SQL: ", "")

                    elif tool_name == "rag_search_tool":
                        response["sources"].append(tool_output[:500])

            # --- STEP 11: LLM Response ---
            logger.info("[STEP 11] LLM RESPONSE (final answer): \"%.300s...\"", answer)
            logger.info("[STEP 11] Metadata — SQL used: %s | RAG sources: %d",
                         response["sql_query"] is not None, len(response["sources"]))
            logger.info("=" * 80)

            return response

        except Exception as e:
            logger.error("[AGENT] Error processing question: %s", str(e))
            return {
                "answer": (
                    f"I encountered an error processing your question: {str(e)}. "
                    "Please try rephrasing or ask a different question."
                ),
                "sql_query": None,
                "sources": [],
            }

    def clear_memory(self):
        """Clear the conversation history."""
        self.chat_history = []
        logger.info("[AGENT] Chat history cleared.")


# --- Module-Level Convenience Functions ---

def create_agent():
    """Create and return a new CampaignAgent instance."""
    return CampaignAgent()


def ask(agent, question):
    """Send a question to an existing agent instance."""
    return agent.ask(question)


# --- Script Entry Point ---
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
    print("Initializing Campaign Agent...")
    agent = CampaignAgent()
    print("Agent ready! Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue
        result = agent.ask(question)
        print(f"\nAssistant: {result['answer']}\n")
        if result["sql_query"]:
            print(f"  [SQL Used: {result['sql_query']}]")
