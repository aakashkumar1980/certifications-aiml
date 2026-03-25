"""
Tool Definitions for the Campaign Agent.

Each tool is a LangChain ``@tool``-decorated function that the LangGraph
react agent can invoke. The agent decides which tool to call based on
the user's question.
"""

from llm.tools.sql_query import sql_query_tool
from llm.tools.rag_search import rag_search_tool
from llm.tools.performance_summary import performance_summary_tool

ALL_TOOLS = [sql_query_tool, rag_search_tool, performance_summary_tool]
