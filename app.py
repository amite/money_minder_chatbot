import streamlit as st
import ollama
import json
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import FinancialAgent
from vector_store import TransactionVectorStore

# Page config
st.set_page_config(
    page_title="Financial Transaction Agent", page_icon="💰", layout="wide"
)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = FinancialAgent()
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transactions_loaded" not in st.session_state:
    st.session_state.transactions_loaded = False


def load_sample_data():
    """Load sample data into vector store"""
    try:
        df = pd.read_csv("data/transactions.csv")
        transactions = df.to_dict("records")

        vector_store = TransactionVectorStore()
        vector_store.add_transactions(transactions)

        st.session_state.transactions_loaded = True
        st.success(f"Loaded {len(transactions)} sample transactions!")
        return True
    except Exception as e:
        st.error(f"Error loading data: {e}")
        return False


def process_query(user_query):
    """Process user query with agent and LLM"""
    # First, let the LLM decide which tool to use
    response = ollama.chat(
        model="llama3.1:8b-instruct-q4_K_M",  # or 'llama3.1' if available
        messages=[
            {
                "role": "system",
                "content": """You are a financial assistant that helps users analyze their transactions.
                You have access to tools that can search transactions, analyze by category, and provide spending summaries.
                Always use the appropriate tool based on the user's query.""",
            },
            {"role": "user", "content": user_query},
        ],
        tools=st.session_state.agent.get_tools(),
    )

    # Check if LLM wants to use a tool
    if response.message.tool_calls:
        tool_call = response.message.tool_calls[0]
        tool_name = tool_call.function.name
        tool_args = dict(tool_call.function.arguments)

        # Execute the tool
        result = st.session_state.agent.execute_tool(tool_name, **tool_args)

        # Display tool execution
        with st.chat_message("assistant"):
            st.markdown(f"**Using tool:** `{tool_name}`")
            st.code(json.dumps(tool_args, indent=2), language="json")

        # Display results
        with st.chat_message("assistant"):
            st.markdown("**Results:**")

            # Try to parse as JSON for pretty display
            try:
                result_data = json.loads(result)
                st.json(result_data)

                # Create visualizations for summary data
                if (
                    tool_name == "get_spending_summary"
                    or tool_name == "analyze_by_category"
                ):
                    if (
                        isinstance(result_data, dict)
                        and "spending_by_category" in result_data
                    ):
                        df = pd.DataFrame(
                            list(result_data["spending_by_category"].items()),
                            columns=["Category", "Amount"],  # type: ignore[arg-type]
                        )
                        st.bar_chart(df.set_index("Category"))

            except:
                st.text(result)
    else:
        # If no tool call, just show the response
        with st.chat_message("assistant"):
            st.markdown(response.message.content)


# Sidebar for setup
with st.sidebar:
    st.title("💰 Financial Agent")
    st.markdown("---")

    if not st.session_state.transactions_loaded:
        st.warning("Sample data not loaded")
        if st.button("📥 Load Sample Transactions", type="primary"):
            with st.spinner("Loading sample data..."):
                load_sample_data()
    else:
        st.success("✅ Data loaded!")

    st.markdown("---")
    st.markdown("### Query Examples:")

    examples = [
        "Find my coffee purchases",
        "How much did I spend on shopping?",
        "Show my Amazon transactions",
        "What's my spending summary for last month?",
        "Analyze my food expenses",
        "What are my largest purchases?",
    ]

    for example in examples:
        if st.button(f"▸ {example}", key=example):
            st.session_state.user_query = example

# Main interface
st.title("💳 Financial Transaction Agent")
st.markdown("Ask questions about your spending patterns and transactions")

# Display chat messages
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# Chat input
if prompt := st.chat_input("Ask about your transactions..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process query
    if not st.session_state.transactions_loaded:
        with st.chat_message("assistant"):
            st.error("Please load sample data first from the sidebar!")
    else:
        process_query(prompt)

# Data preview section
if st.session_state.transactions_loaded:
    with st.expander("📊 Sample Data Preview"):
        df = pd.read_csv("data/transactions.csv")
        st.dataframe(df.head(10), use_container_width=True)

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Transactions", len(df))
        with col2:
            st.metric("Total Amount", f"${df['amount'].sum():.2f}")
        with col3:
            st.metric("Categories", int(df["category"].nunique()))
