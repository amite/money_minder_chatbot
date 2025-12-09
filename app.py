import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
from dotenv import load_dotenv
from typing import Any, Dict, List, Optional
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from langchain_core.runnables import RunnableConfig
from langchain_ollama import ChatOllama
from langchain.agents import create_agent

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import FinancialAgent
from vector_store import TransactionVectorStore
from tool_handlers import HandlerRegistry

# Page config
st.set_page_config(
    page_title="Financial Transaction Agent", page_icon="💰", layout="wide"
)

# Initialize session state
if "agent" not in st.session_state:
    st.session_state.agent = FinancialAgent()
if "handler_registry" not in st.session_state:
    st.session_state.handler_registry = HandlerRegistry(st.session_state.agent)
if "messages" not in st.session_state:
    st.session_state.messages = []
if "transactions_loaded" not in st.session_state:
    st.session_state.transactions_loaded = False
if "query_dataframe" not in st.session_state:
    st.session_state.query_dataframe = None
if "query_title" not in st.session_state:
    st.session_state.query_title = "Sample Data Preview"
if "langchain_agent" not in st.session_state:
    st.session_state.langchain_agent = None


# Global store for tool execution info (thread-safe for Streamlit)
_tool_execution_store = {}


class ToolExecutionCallback(BaseCallbackHandler):
    """Callback to intercept tool execution and process results"""

    def __init__(self, handler_registry: HandlerRegistry, user_query: str):
        super().__init__()
        self.handler_registry = handler_registry
        self.user_query = user_query
        self.tool_name = None
        self.tool_args = None
        self.tool_executed = False

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when a tool starts running"""
        self.tool_name = serialized.get("name")
        # Parse tool input to extract arguments
        try:
            import ast

            if isinstance(input_str, dict):
                self.tool_args = input_str
            elif isinstance(input_str, str):
                # Try to parse as Python literal (dict representation)
                try:
                    self.tool_args = ast.literal_eval(input_str)
                except:
                    # If that fails, try JSON
                    try:
                        self.tool_args = json.loads(input_str)
                    except:
                        # If both fail, store raw input
                        self.tool_args = {"raw_input": input_str}
            else:
                self.tool_args = {}
        except Exception as e:
            self.tool_args = {}

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool finishes running"""
        self.tool_executed = True
        # Don't update session state here - do it in main thread after execution


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


def get_langchain_agent():
    """Get or create LangChain agent using LangGraph"""
    if st.session_state.langchain_agent is None:
        llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M", temperature=0)
        tools = st.session_state.agent.get_langchain_tools()

        # Create agent using LangChain's create_agent
        agent = create_agent(llm, tools)

        st.session_state.langchain_agent = agent

    return st.session_state.langchain_agent


def process_query(user_query):
    """Process user query with LangChain agent"""
    try:
        # Get or create LangChain agent
        agent = get_langchain_agent()

        # Create callback to intercept tool execution
        callback = ToolExecutionCallback(st.session_state.handler_registry, user_query)

        # Build messages from conversation history
        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                from langchain_core.messages import AIMessage

                messages.append(AIMessage(content=msg["content"]))

        # Add current user query
        messages.append(HumanMessage(content=user_query))

        # Run the agent with messages
        config: RunnableConfig = {"callbacks": [callback]}
        result = agent.invoke({"messages": messages}, config=config)

        # Extract the final response from the last message
        if result.get("messages"):
            last_message = result["messages"][-1]
            response = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )
        else:
            response = str(result)

        # Update session state with tool results (in main thread)
        if callback.tool_executed and callback.tool_name and callback.tool_args:
            try:
                result_info = callback.handler_registry.handle_result(
                    callback.tool_name, callback.tool_args, user_query
                )

                # Update session state
                if result_info.get("dataframe") is not None:
                    st.session_state.query_dataframe = result_info["dataframe"]
                st.session_state.query_title = result_info["title"]
            except Exception as e:
                # If processing fails, continue without updating state
                pass

        # Display the response
        with st.chat_message("assistant"):
            st.markdown(response)

        # Save assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": response})

    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        with st.chat_message("assistant"):
            st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})


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

# Handle example button queries
if "user_query" in st.session_state and st.session_state.user_query:
    prompt = st.session_state.user_query
    # Clear the query so it doesn't trigger again
    del st.session_state.user_query

    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process query
    if not st.session_state.transactions_loaded:
        error_msg = "Please load sample data first from the sidebar!"
        with st.chat_message("assistant"):
            st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        process_query(prompt)
    st.rerun()

# Chat input
if prompt := st.chat_input("Ask about your transactions..."):
    # Add user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Process query
    if not st.session_state.transactions_loaded:
        error_msg = "Please load sample data first from the sidebar!"
        with st.chat_message("assistant"):
            st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})
    else:
        process_query(prompt)

# Data preview section - show relevant data based on query
if st.session_state.transactions_loaded:
    # Use query-specific dataframe if available, otherwise show sample data
    if (
        st.session_state.query_dataframe is not None
        and not st.session_state.query_dataframe.empty
    ):
        df = st.session_state.query_dataframe
        title = st.session_state.query_title
        with st.expander(title):
            st.dataframe(df, width="stretch")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Transactions", len(df))
            with col2:
                if "amount" in df.columns:
                    df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
                    st.metric("Total Amount", f"${df['amount'].sum():.2f}")
                else:
                    st.metric("Total Amount", "N/A")
            with col3:
                if "category" in df.columns:
                    st.metric("Categories", int(df["category"].nunique()))
                else:
                    st.metric("Categories", "N/A")
    else:
        # Default: show sample data preview
        with st.expander("📊 Sample Data Preview"):
            df = pd.read_csv("data/transactions.csv")
            st.dataframe(df.head(10), width="stretch")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Transactions", len(df))
            with col2:
                st.metric("Total Amount", f"${df['amount'].sum():.2f}")
            with col3:
                st.metric("Categories", int(df["category"].nunique()))
