"""
LLM Provider Module.

Centralizes Claude LLM initialization and the system prompt definition.
All tools and the agent import ``get_llm()`` from here to ensure
consistent model configuration across the application.
"""

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

from config.settings import Settings

load_dotenv()

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


def get_llm():
    """
    Create a ChatAnthropic LLM instance with project-wide settings.

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
