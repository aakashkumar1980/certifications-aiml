"""
LLM Intelligence Package for Campaign Performance Analysis.

Handles all LLM-powered reasoning, content generation, and agent orchestration.
Claude serves as:
  - SQL generator (translates natural language → SQL)
  - Response synthesizer (combines data + context → business-friendly answers)
  - Fallback knowledge source (general definitions from trained knowledge)

Sub-modules:
    provider — Claude LLM initialization and system prompt
    tools/   — Domain-specific tool functions (SQL, RAG search, performance summary)
    agent    — CampaignAgent orchestrator with LangGraph react agent
"""

from llm.agent import CampaignAgent
