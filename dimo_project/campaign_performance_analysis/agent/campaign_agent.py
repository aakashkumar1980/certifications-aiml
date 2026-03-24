"""
Campaign Agent Module for Campaign Performance Analysis.

Implements a LangChain tool-calling agent powered by Claude that orchestrates
three specialized tools to answer natural language questions about credit
card campaign data:

1. **sql_query_tool** — Translates natural language to SQL, validates the
   query, executes it against SQLite, and returns structured results.
2. **rag_search_tool** — Performs semantic search over the ChromaDB knowledge
   base for campaign context, performance summaries, and business glossary.
3. **performance_summary_tool** — Combines database metrics with RAG context
   to produce a narrative performance report for a specific campaign.

The agent maintains multi-turn conversation history via LangChain's
``ConversationBufferMemory``, enabling follow-up questions.

Example Usage::

    from agent.campaign_agent import CampaignAgent
    agent = CampaignAgent()
    result = agent.ask("Which campaign has the highest enrollment?")
    print(result["answer"])
"""

import os
import sys
import json

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.memory import ConversationBufferMemory

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings
from database.campaign_db import get_schema, execute_query
from rag.vector_store import search_similar

load_dotenv()

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
    """
    Create a ChatAnthropic LLM instance with project-wide settings.

    Reads the API key from ``Settings.ANTHROPIC_API_KEY`` and applies
    the model name, temperature, and max_tokens from ``config.settings``.

    Returns:
        ChatAnthropic: Configured LangChain Claude chat model.

    Raises:
        ValueError: If ``ANTHROPIC_API_KEY`` is not set in the environment.
    """
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
        response = llm.invoke(sql_prompt)
        sql = response.content.strip()

        # Strip markdown code fences if the model wraps the SQL
        sql = sql.replace("```sql", "").replace("```", "").strip()

        results = execute_query(sql)

        if isinstance(results, str):
            return f"SQL: {sql}\n\nResult: {results}"

        result_str = json.dumps(results, indent=2, default=str)
        return f"SQL: {sql}\n\nResults ({len(results)} rows):\n{result_str}"

    except Exception as e:
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
    try:
        results = search_similar(query, n_results=Settings.RAG_DEFAULT_RESULTS)
        if not results:
            return "No relevant documents found in the knowledge base."

        formatted_parts = []
        for i, r in enumerate(results, 1):
            doc_type = r["metadata"].get("type", "unknown")
            campaign_id = r["metadata"].get("campaign_id", "N/A")
            formatted_parts.append(
                f"[Source {i}] Type: {doc_type} | Campaign: {campaign_id}\n{r['content']}"
            )
        return "\n\n---\n\n".join(formatted_parts)

    except Exception as e:
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
    try:
        # Fetch monthly performance metrics joined with campaign info
        perf_sql = (
            f"SELECT cp.*, c.campaign_name, c.campaign_type, c.target_segment, c.budget_allocated "
            f"FROM campaign_performance cp "
            f"JOIN campaigns c ON cp.campaign_id = c.campaign_id "
            f"WHERE cp.campaign_id = '{campaign_id}' ORDER BY cp.month"
        )
        perf_data = execute_query(perf_sql)

        # Fetch aggregate enrollment and redemption stats
        enroll_data = execute_query(
            f"SELECT COUNT(*) as total_enrollments FROM enrollments WHERE campaign_id = '{campaign_id}'"
        )
        redeem_data = execute_query(
            f"SELECT COUNT(*) as total_redemptions, SUM(redemption_amount) as total_amount "
            f"FROM redemptions WHERE campaign_id = '{campaign_id}'"
        )

        # Supplement with RAG context for qualitative insights
        rag_context = search_similar(f"performance summary for {campaign_id}", n_results=2)
        rag_text = "\n".join([r["content"] for r in rag_context])

        if isinstance(perf_data, str):
            return f"Could not find performance data for {campaign_id}: {perf_data}"

        # Assemble all data for the summary prompt
        data_payload = json.dumps({
            "performance_metrics": perf_data,
            "enrollment_totals": enroll_data,
            "redemption_totals": redeem_data,
        }, indent=2, default=str)

        llm = _get_llm()
        summary_prompt = (
            f"Generate a concise business-friendly performance summary for campaign {campaign_id}.\n\n"
            f"Data:\n{data_payload}\n\n"
            f"Additional Context:\n{rag_text}\n\n"
            "Format: 3-4 paragraphs covering enrollment trends, redemption patterns, "
            "ROI analysis, and a recommendation. Use specific numbers from the data."
        )

        response = llm.invoke(summary_prompt)
        return response.content

    except Exception as e:
        return f"Error generating performance summary: {str(e)}"


class CampaignAgent:
    """
    Conversational AI agent for campaign performance analysis.

    Wraps a LangChain ``AgentExecutor`` with three domain-specific tools
    (SQL, RAG, performance summary) and maintains chat history for
    multi-turn conversations.

    The agent uses Claude as its reasoning engine and follows a tool-calling
    pattern: it decides which tool(s) to invoke based on the user's question,
    executes them, and synthesizes the results into a business-friendly answer.

    Attributes:
        executor (AgentExecutor): The LangChain agent executor instance.

    Example::

        agent = CampaignAgent()
        result = agent.ask("Which campaign has the highest ROI?")
        print(result["answer"])
        print(result["sql_query"])  # SQL used, if any
    """

    def __init__(self):
        """
        Initialize the campaign agent with tools, prompt, and memory.

        Creates a LangChain tool-calling agent backed by Claude, registers
        all three tools, sets up the system prompt, and attaches a
        conversation buffer memory for multi-turn context.

        Raises:
            ValueError: If ANTHROPIC_API_KEY is not configured.
        """
        llm = _get_llm()
        tools = [sql_query_tool, rag_search_tool, performance_summary_tool]

        prompt = ChatPromptTemplate.from_messages([
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        agent = create_tool_calling_agent(llm, tools, prompt)

        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True,
        )

        self.executor = AgentExecutor(
            agent=agent,
            tools=tools,
            memory=self.memory,
            verbose=True,
            handle_parsing_errors=True,
            max_iterations=Settings.AGENT_MAX_ITERATIONS,
        )

    def ask(self, question):
        """
        Send a question to the agent and return a structured response.

        The agent may invoke one or more tools (SQL, RAG, summary) to
        answer the question. The response includes the answer text plus
        metadata about which tools were used.

        Args:
            question (str): Natural language question from the user.

        Returns:
            dict: Response dictionary with keys:
                - ``answer`` (str): The agent's natural language response.
                - ``sql_query`` (str | None): The SQL query if sql_query_tool was used.
                - ``sources`` (list[str]): RAG document excerpts if rag_search_tool was used.
        """
        try:
            result = self.executor.invoke({"input": question})
            output = result.get("output", "I couldn't generate a response.")

            response = {
                "answer": output,
                "sql_query": None,
                "sources": [],
            }

            # Extract metadata from intermediate tool-call steps
            for step in result.get("intermediate_steps", []):
                if hasattr(step[0], "tool"):
                    tool_name = step[0].tool
                    tool_output = str(step[1])

                    if tool_name == "sql_query_tool" and "SQL:" in tool_output:
                        lines = tool_output.split("\n")
                        sql_line = next((l for l in lines if l.startswith("SQL:")), None)
                        if sql_line:
                            response["sql_query"] = sql_line.replace("SQL: ", "")

                    elif tool_name == "rag_search_tool":
                        response["sources"].append(tool_output[:500])

            return response

        except Exception as e:
            return {
                "answer": (
                    f"I encountered an error processing your question: {str(e)}. "
                    "Please try rephrasing or ask a different question."
                ),
                "sql_query": None,
                "sources": [],
            }

    def clear_memory(self):
        """
        Clear the conversation history.

        Resets the memory buffer so the agent starts fresh without
        any prior conversation context.
        """
        self.memory.clear()


# --- Module-Level Convenience Functions ---

def create_agent():
    """
    Create and return a new CampaignAgent instance.

    Convenience factory function for use by the Streamlit UI
    and other entry points.

    Returns:
        CampaignAgent: A fully initialized agent ready for queries.
    """
    return CampaignAgent()


def ask(agent, question):
    """
    Send a question to an existing agent instance.

    Convenience wrapper that delegates to ``CampaignAgent.ask``.

    Args:
        agent (CampaignAgent): An initialized agent instance.
        question (str): Natural language question.

    Returns:
        dict: Response dictionary (see ``CampaignAgent.ask``).
    """
    return agent.ask(question)


# --- Script Entry Point ---
if __name__ == "__main__":
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
