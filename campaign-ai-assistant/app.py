"""
Streamlit UI for Campaign AI Assistant
Clean chat interface with sidebar for campaign browsing and quick questions.
"""

import os
import sys
import streamlit as st

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.campaign_db import init_database, execute_query, DB_PATH
from rag.vector_store import build_knowledge_base
from agent.campaign_agent import create_agent, ask


# --- Page Configuration ---
st.set_page_config(
    page_title="Campaign AI Assistant",
    page_icon="📊",
    layout="wide",
)

st.title("Campaign AI Assistant")
st.caption("Ask plain-English questions about credit card campaign performance")


# --- Initialization (runs once per session) ---
@st.cache_resource
def initialize_system():
    """Initialize database and vector store on first load."""
    # Generate mock data if CSVs don't exist
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    if not os.path.exists(os.path.join(data_dir, "campaigns.csv")):
        from data.generate_mock_data import (
            generate_campaigns, generate_enrollments,
            generate_redemptions, generate_performance,
        )
        campaigns = generate_campaigns(5)
        enrollments = generate_enrollments(campaigns, 500)
        generate_redemptions(enrollments, campaigns, 300)
        generate_performance(campaigns, 6)

    # Initialize SQLite database
    if not os.path.exists(DB_PATH):
        init_database()

    # Build vector store knowledge base
    build_knowledge_base()

    return True


@st.cache_resource
def get_agent():
    """Create agent once per session."""
    return create_agent()


# Initialize system
try:
    initialize_system()
    agent = get_agent()
    system_ready = True
except Exception as e:
    st.error(f"System initialization error: {str(e)}")
    st.info("Make sure ANTHROPIC_API_KEY is set in your .env file.")
    system_ready = False


# --- Sidebar ---
with st.sidebar:
    st.header("Campaigns")

    # Load and display campaign list
    try:
        campaigns = execute_query(
            "SELECT campaign_id, campaign_name, campaign_type, status FROM campaigns ORDER BY campaign_id"
        )
        if isinstance(campaigns, list):
            for c in campaigns:
                status_icon = {"active": "🟢", "expired": "🔴", "upcoming": "🟡"}.get(c["status"], "⚪")
                st.markdown(f"{status_icon} **{c['campaign_id']}** — {c['campaign_name']}")
                st.caption(f"Type: {c['campaign_type']} | Status: {c['status']}")
    except Exception:
        st.caption("Campaign list will appear after initialization.")

    st.divider()
    st.header("Quick Questions")

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
    if st.button("Clear Chat", use_container_width=True, type="secondary"):
        st.session_state["messages"] = []
        st.cache_resource.clear()
        st.rerun()


# --- Chat Interface ---

# Initialize message history
if "messages" not in st.session_state:
    st.session_state["messages"] = []

# Display chat history
for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        # Show expandable sections for AI responses
        if msg["role"] == "assistant":
            if msg.get("sql_query"):
                with st.expander("View SQL Query"):
                    st.code(msg["sql_query"], language="sql")
            if msg.get("sources"):
                with st.expander("Sources"):
                    for src in msg["sources"]:
                        st.markdown(f"- {src}")

# Handle pending quick question
if "pending_question" in st.session_state:
    user_input = st.session_state.pop("pending_question")
else:
    user_input = st.chat_input("Ask about campaign performance...")

# Process new input
if user_input and system_ready:
    # Display user message
    st.session_state["messages"].append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get AI response
    with st.chat_message("assistant"):
        with st.spinner("Analyzing campaign data..."):
            result = ask(agent, user_input)

        st.markdown(result["answer"])

        if result.get("sql_query"):
            with st.expander("View SQL Query"):
                st.code(result["sql_query"], language="sql")
        if result.get("sources"):
            with st.expander("Sources"):
                for src in result["sources"]:
                    st.markdown(f"- {src}")

    # Save to history
    st.session_state["messages"].append({
        "role": "assistant",
        "content": result["answer"],
        "sql_query": result.get("sql_query"),
        "sources": result.get("sources", []),
    })
