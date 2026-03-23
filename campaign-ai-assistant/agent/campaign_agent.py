"""
Campaign Agent Module for Campaign AI Assistant
LangChain agent with SQL, RAG, and performance summary tools powered by Claude.
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

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.campaign_db import get_schema, execute_query
from rag.vector_store import search_similar

load_dotenv()

# --- LLM Setup ---
MODEL_NAME = "claude-sonnet-4-20250514"


def get_llm():
    """Initialize the Claude LLM via LangChain."""
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise ValueError("ANTHROPIC_API_KEY environment variable is not set. "
                         "Please set it in your .env file.")
    return ChatAnthropic(
        model=MODEL_NAME,
        anthropic_api_key=api_key,
        temperature=0,
        max_tokens=2048,
    )


# --- Tool Definitions ---

@tool
def sql_query_tool(question: str) -> str:
    """
    Takes a natural language question about campaign data, generates a SQL query,
    executes it against the SQLite database, and returns the results.
    Use this tool when the user asks questions that can be answered with data
    from the campaigns, enrollments, redemptions, or campaign_performance tables.
    """
    schema = get_schema()
    llm = get_llm()

    # Ask Claude to generate SQL from the natural language question
    sql_prompt = f"""You are a SQL expert. Given this database schema:

{schema}

Generate a SQLite SELECT query to answer this question: "{question}"

Rules:
- Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP)
- Return ONLY the SQL query, no explanation or markdown
- Use appropriate JOINs when data spans multiple tables
- Use aggregations (COUNT, SUM, AVG) when appropriate
- Limit results to 20 rows maximum
"""
    try:
        response = llm.invoke(sql_prompt)
        sql = response.content.strip()
        # Clean up markdown code blocks if present
        sql = sql.replace("```sql", "").replace("```", "").strip()

        results = execute_query(sql)

        if isinstance(results, str):
            # Error message returned
            return f"SQL: {sql}\n\nResult: {results}"

        # Format results nicely
        result_str = json.dumps(results, indent=2, default=str)
        return f"SQL: {sql}\n\nResults ({len(results)} rows):\n{result_str}"

    except Exception as e:
        return f"Error generating/executing SQL: {str(e)}"


@tool
def rag_search_tool(query: str) -> str:
    """
    Searches the campaign knowledge base for relevant context about campaigns,
    performance summaries, and business terminology.
    Use this tool when the user asks about campaign strategy, business definitions,
    or needs qualitative context beyond raw data.
    """
    try:
        results = search_similar(query, n_results=3)
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
    Generates a narrative performance summary for a specific campaign.
    Use this tool when the user asks for a detailed summary or report for a specific campaign.
    Provide the campaign_id (e.g., 'CMP-001').
    """
    try:
        # Fetch performance data from database
        sql = f"""
            SELECT cp.*, c.campaign_name, c.campaign_type, c.target_segment, c.budget_allocated
            FROM campaign_performance cp
            JOIN campaigns c ON cp.campaign_id = c.campaign_id
            WHERE cp.campaign_id = '{campaign_id}'
            ORDER BY cp.month
        """
        perf_data = execute_query(sql)

        # Fetch enrollment and redemption counts
        enroll_sql = f"SELECT COUNT(*) as total_enrollments FROM enrollments WHERE campaign_id = '{campaign_id}'"
        redeem_sql = f"SELECT COUNT(*) as total_redemptions, SUM(redemption_amount) as total_amount FROM redemptions WHERE campaign_id = '{campaign_id}'"
        enrollments = execute_query(enroll_sql)
        redemptions = execute_query(redeem_sql)

        # Also pull RAG context
        rag_context = search_similar(f"performance summary for {campaign_id}", n_results=2)
        rag_text = "\n".join([r["content"] for r in rag_context])

        if isinstance(perf_data, str):
            return f"Could not find performance data for {campaign_id}: {perf_data}"

        # Combine all data into a summary prompt
        data_summary = json.dumps({
            "performance_metrics": perf_data,
            "enrollment_totals": enrollments,
            "redemption_totals": redemptions,
        }, indent=2, default=str)

        llm = get_llm()
        summary_prompt = f"""Generate a concise business-friendly performance summary for campaign {campaign_id}.

Data:
{data_summary}

Additional Context:
{rag_text}

Format: 3-4 paragraphs covering enrollment trends, redemption patterns, ROI analysis,
and a recommendation. Use specific numbers from the data."""

        response = llm.invoke(summary_prompt)
        return response.content

    except Exception as e:
        return f"Error generating performance summary: {str(e)}"


# --- Agent Setup ---

SYSTEM_PROMPT = """You are a credit card campaign analytics assistant for a financial services company. \
You help business analysts understand campaign performance, enrollment trends and merchant metrics. \
Always ground your answers in actual data. Be concise and business-friendly.

You have access to these tools:
- sql_query_tool: Query the campaign database with natural language questions
- rag_search_tool: Search the knowledge base for campaign context and business definitions
- performance_summary_tool: Get a detailed performance summary for a specific campaign

When answering questions:
1. Use sql_query_tool for data-driven questions (counts, comparisons, trends)
2. Use rag_search_tool for context, definitions, and qualitative insights
3. Use performance_summary_tool for detailed campaign reports
4. Always cite which campaign or data source your answer comes from
5. If one tool fails, try another approach"""


def create_agent():
    """Create and return the LangChain agent executor with conversation memory."""
    llm = get_llm()

    tools = [sql_query_tool, rag_search_tool, performance_summary_tool]

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder(variable_name="chat_history"),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    agent = create_tool_calling_agent(llm, tools, prompt)

    memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors=True,
        max_iterations=5,
    )

    return executor


def ask(agent_executor, question: str) -> dict:
    """
    Send a question to the agent and return the response with metadata.
    Returns dict with 'answer', 'sql_query' (if used), and 'sources' (if RAG used).
    """
    try:
        result = agent_executor.invoke({"input": question})
        output = result.get("output", "I couldn't generate a response.")

        # Extract SQL and sources from intermediate steps if available
        response = {
            "answer": output,
            "sql_query": None,
            "sources": [],
        }

        # Parse intermediate steps for metadata
        for step in result.get("intermediate_steps", []):
            if hasattr(step[0], "tool"):
                if step[0].tool == "sql_query_tool" and "SQL:" in str(step[1]):
                    lines = str(step[1]).split("\n")
                    sql_line = next((l for l in lines if l.startswith("SQL:")), None)
                    if sql_line:
                        response["sql_query"] = sql_line.replace("SQL: ", "")
                elif step[0].tool == "rag_search_tool":
                    response["sources"].append(str(step[1])[:500])

        return response

    except Exception as e:
        return {
            "answer": f"I encountered an error processing your question: {str(e)}. "
                      "Please try rephrasing or ask a different question.",
            "sql_query": None,
            "sources": [],
        }


if __name__ == "__main__":
    print("Initializing Campaign Agent...")
    agent = create_agent()
    print("Agent ready! Type 'quit' to exit.\n")

    while True:
        question = input("You: ").strip()
        if question.lower() in ("quit", "exit", "q"):
            break
        if not question:
            continue
        result = ask(agent, question)
        print(f"\nAssistant: {result['answer']}\n")
        if result["sql_query"]:
            print(f"  [SQL Used: {result['sql_query']}]")
