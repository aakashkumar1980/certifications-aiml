"""
Streamlit UI for Campaign Performance Analysis.

Provides a clean, conversational chat interface where business stakeholders
can ask natural language questions about credit card campaign performance.
The UI consists of:

- **Sidebar** — Lists available campaigns with status indicators, offers
  quick-question buttons for common queries, and a chat-clear control.
- **Main Area** — A scrollable chat history with expandable sections for
  the SQL query used and RAG source documents retrieved.

On first load, the app automatically:
    1. Generates mock CSV data (if not present)
    2. Initializes the SQLite database
    3. Builds the ChromaDB knowledge base
    4. Creates the LangChain agent

Launch Command::

    streamlit run app.py

Environment Variables:
    ANTHROPIC_API_KEY (str): Required. Set in ``.env`` file.
"""

import os
import sys

import streamlit as st

# Add project root to path for package imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.settings import Settings
from database.campaign_db import CampaignDatabase, init_database, execute_query
from rag.vector_store import build_knowledge_base
from agent.campaign_agent import CampaignAgent


# --- Page Configuration ---
st.set_page_config(
    page_title="Campaign AI Assistant",
    page_icon="📊",
    layout="wide",
)
st.title("Campaign AI Assistant")
st.caption("Ask plain-English questions about credit card campaign performance")


# --- One-Time System Initialization ---

@st.cache_resource
def _initialize_system():
    """
    Bootstrap all backend services on the first Streamlit load.

    Performs the following steps in order:
        1. Generates mock CSV data if ``campaigns.csv`` does not exist.
        2. Loads CSVs into the SQLite database if ``campaign.db`` does not exist.
        3. Builds the ChromaDB knowledge base (idempotent if already populated).

    This function is decorated with ``@st.cache_resource`` so it runs
    exactly once per Streamlit server process, even across page refreshes.

    Returns:
        bool: True if initialization completed without errors.
    """
    # Step 1: Generate mock data if missing
    if not os.path.exists(os.path.join(Settings.DATA_DIR, "campaigns.csv")):
        from data.generate_mock_data import MockDataGenerator
        generator = MockDataGenerator()
        generator.generate_all()

    # Step 2: Initialize SQLite database if missing
    if not os.path.exists(Settings.DB_PATH):
        init_database()

    # Step 3: Build vector store knowledge base
    build_knowledge_base()

    return True


@st.cache_resource
def _get_agent():
    """
    Create a singleton CampaignAgent for the Streamlit session.

    Cached via ``@st.cache_resource`` so the agent (and its memory)
    persist across Streamlit reruns within the same server process.

    Returns:
        CampaignAgent: Initialized agent ready for queries.
    """
    return CampaignAgent()


# --- Run Initialization ---
try:
    _initialize_system()
    agent = _get_agent()
    system_ready = True
except Exception as e:
    st.error(f"System initialization error: {str(e)}")
    st.info("Make sure ANTHROPIC_API_KEY is set in your .env file.")
    system_ready = False


# --- Sidebar: Campaign List & Quick Questions ---

with st.sidebar:
    st.header("Campaigns")

    # Display campaign list with status indicators
    try:
        campaigns = execute_query(
            "SELECT campaign_id, campaign_name, campaign_type, status "
            "FROM campaigns ORDER BY campaign_id"
        )
        if isinstance(campaigns, list):
            for c in campaigns:
                status_icon = {
                    "active": "🟢",
                    "expired": "🔴",
                    "upcoming": "🟡",
                }.get(c["status"], "⚪")
                st.markdown(f"{status_icon} **{c['campaign_id']}** — {c['campaign_name']}")
                st.caption(f"Type: {c['campaign_type']} | Status: {c['status']}")
    except Exception:
        st.caption("Campaign list will appear after initialization.")

    st.divider()
    st.header("Quick Questions")

    # Pre-defined questions for one-click exploration
    quick_questions = [
        "Which campaign has highest enrollment?",
        "Compare cashback vs travel offer performance",
        "What is the ROI trend for Q4?",
        "Which merchant category drives most redemptions?",
    ]

    for q in quick_questions:
        if st.button(q, key=f"quick_{q}", use_container_width=True):
            st.session_state["pending_question"] = q

    st.divider()

    # Clear chat resets both UI history and agent memory
    if st.button("Clear Chat", use_container_width=True, type="secondary"):
        st.session_state["messages"] = []
        st.cache_resource.clear()
        st.rerun()


# --- Main Chat Interface ---

# Initialize message history in session state
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Render all previous messages
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

        # Show expandable tool-output sections for assistant messages
        if msg["role"] == "assistant":
            if msg.get("sql_query"):
                with st.expander("View SQL Query"):
                    st.code(msg["sql_query"], language="sql")
            if msg.get("sources"):
                with st.expander("Sources"):
                    for src in msg["sources"]:
                        st.markdown(f"- {src}")

# Resolve input: either a pending quick question or the chat input box
if "pending_question" in st.session_state:
    user_input = st.session_state.pop("pending_question")
else:
    user_input = st.chat_input("Ask about campaign performance...")

# Process new user input
if user_input and system_ready:
    # Display and store the user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get agent response with a loading spinner
    with st.chat_message("assistant"):
        with st.spinner("Analyzing campaign data..."):
            result = agent.ask(user_input)

        st.markdown(result["answer"])

        # Expandable SQL section
        if result.get("sql_query"):
            with st.expander("View SQL Query"):
                st.code(result["sql_query"], language="sql")

        # Expandable RAG sources section
        if result.get("sources"):
            with st.expander("Sources"):
                for src in result["sources"]:
                    st.markdown(f"- {src}")

    # Persist the assistant message to session history
    st.session_state["messages"].append({
        "role": "assistant",
        "content": result["answer"],
        "sql_query": result.get("sql_query"),
        "sources": result.get("sources", []),
    })
