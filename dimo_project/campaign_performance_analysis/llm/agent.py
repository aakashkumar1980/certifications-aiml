"""
Campaign Agent Module — LLM Intelligence (Category 2).

Implements the LangGraph react agent that orchestrates tool calls
and maintains multi-turn conversation history. The agent uses Claude
as its reasoning engine — it decides which tool(s) to invoke based
on the user's question, executes them, and synthesizes results.

When no tool returns relevant data, Claude falls back to its trained
knowledge to provide general definitions and context.

RAG Pipeline Steps involved:
    Step 5:  User Query — received and forwarded to agent
    Step 9:  Contextually Augmented Prompt — agent assembles tool results + context
    Step 10: Fed to LLM — agent sends augmented context to Claude for synthesis
    Step 11: LLM Response — Claude generates final business-friendly answer
"""

import logging

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.prebuilt import create_react_agent

from llm.provider import get_llm, SYSTEM_PROMPT
from llm.tools import ALL_TOOLS

logger = logging.getLogger("rag_pipeline")


class CampaignAgent:
    """
    Conversational AI agent for campaign performance analysis.

    Wraps a LangGraph react agent with three domain-specific tools
    (SQL, RAG, performance summary) and maintains chat history for
    multi-turn conversations.
    """

    def __init__(self):
        llm = get_llm()

        self.agent = create_react_agent(
            model=llm,
            tools=ALL_TOOLS,
            prompt=SystemMessage(content=SYSTEM_PROMPT),
        )
        self.chat_history = []
        logger.info("[AGENT] CampaignAgent initialized with %d tools: %s",
                     len(ALL_TOOLS), [t.name for t in ALL_TOOLS])

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

            # --- STEP 9-10: Agent reasoning loop ---
            # The agent internally: (a) decides which tool to call, (b) calls it,
            # (c) assembles the augmented prompt with tool results, (d) sends to Claude
            logger.info("[STEP 9] AGENT REASONING: LangGraph react loop — selecting tools and building augmented prompt...")
            logger.info("[STEP 10] FED TO LLM: Agent sends messages + tool results to '%s' for final synthesis...",
                         SYSTEM_PROMPT[:50])
            result = self.agent.invoke({"messages": self.chat_history})

            messages = result.get("messages", [])

            answer = ""
            if messages:
                answer = messages[-1].content if hasattr(messages[-1], "content") else str(messages[-1])

            self.chat_history = messages

            response = {
                "answer": answer,
                "sql_query": None,
                "sources": [],
            }

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
            logger.info("[STEP 11] LLM RESPONSE (final answer, %d chars): \"%.300s...\"", len(answer), answer)
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
