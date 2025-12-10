import streamlit as st
import json
import pandas as pd
from datetime import datetime, timedelta
import sys
import os
import time
import uuid
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
from logger import get_logger

# Page config
st.set_page_config(
    page_title="Financial Transaction Agent", page_icon="💰", layout="wide"
)

# Initialize logger
logger = get_logger()

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
if "session_id" not in st.session_state:
    st.session_state.session_id = str(uuid.uuid4())


# Global store for tool execution info (thread-safe for Streamlit)
_tool_execution_store = {}


class ToolExecutionCallback(BaseCallbackHandler):
    """Callback to intercept tool execution and process results - supports multiple tool calls"""

    def __init__(
        self,
        handler_registry: HandlerRegistry,
        user_query: str,
        session_id: str,
        query_id: str,
    ):
        super().__init__()
        self.handler_registry = handler_registry
        self.user_query = user_query
        self.session_id = session_id
        self.query_id = query_id

        # Track MULTIPLE tool calls (parallel execution safe)
        self.tool_calls = []  # List of {name, args, result, execution_time}
        self.pending_tools = {}  # Map tool_call_id -> tool info for parallel execution

        # Legacy single-tool tracking (for backward compatibility)
        self.tool_name = None
        self.tool_args = None
        self.tool_executed = False

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Called when a tool starts running"""
        tool_name = serialized.get("name")
        start_time = time.time()

        # Parse tool input to extract arguments
        tool_args = {}
        try:
            import ast

            if isinstance(input_str, dict):
                tool_args = input_str
            elif isinstance(input_str, str):
                # Try to parse as Python literal (dict representation)
                try:
                    tool_args = ast.literal_eval(input_str)
                except:
                    # If that fails, try JSON
                    try:
                        tool_args = json.loads(input_str)
                    except:
                        # If both fail, store raw input
                        tool_args = {"raw_input": input_str}
            else:
                tool_args = {}
        except Exception as e:
            tool_args = {}

        # Use a unique key for parallel execution (tool_name + args hash)
        tool_key = f"{tool_name}_{start_time}_{id(tool_args)}"

        # Store in pending_tools for parallel execution safety
        self.pending_tools[tool_key] = {
            "name": tool_name,
            "args": tool_args,
            "start_time": start_time,
        }

        # Update legacy tracking (use last tool for backward compatibility)
        self.tool_name = tool_name
        self.tool_args = tool_args
        self.tool_executed = True

        # Log tool execution start
        if tool_name:
            logger.log_tool_execution_start(
                tool_name=tool_name,
                tool_args=tool_args or {},
                session_id=self.session_id,
                query_id=self.query_id,
            )

    def on_tool_end(self, output: str, **kwargs: Any) -> None:
        """Called when a tool finishes running"""
        # Find matching pending tool (FIFO - oldest first)
        if self.pending_tools:
            # Get the oldest pending tool
            tool_key = list(self.pending_tools.keys())[0]
            tool_info = self.pending_tools.pop(tool_key)

            execution_time = time.time() - tool_info["start_time"]

            # Create result summary (truncate if too long)
            result_summary = str(output)[:200] if output else None
            if result_summary and len(str(output)) > 200:
                result_summary += "..."

            # Complete tool info
            tool_info["result"] = output
            tool_info["execution_time"] = execution_time
            tool_info["result_summary"] = result_summary

            # Add to list of all tool calls
            self.tool_calls.append(tool_info)

            # Log tool execution end
            logger.log_tool_execution_end(
                tool_name=tool_info["name"],
                execution_time=execution_time,
                success=True,
                result_summary=result_summary,
                session_id=self.session_id,
                query_id=self.query_id,
            )


def load_sample_data():
    """Load sample data into vector store"""
    try:
        df = pd.read_csv("data/transactions.csv")
        transactions = df.to_dict("records")

        vector_store = TransactionVectorStore()
        vector_store.add_transactions(transactions)

        st.session_state.transactions_loaded = True
        st.success(f"Loaded {len(transactions)} sample transactions!")

        # Log successful data load
        logger.log_metric(
            metric_name="transactions_loaded",
            value=len(transactions),
            unit="count",
            session_id=st.session_state.get("session_id"),
        )

        return True
    except Exception as e:
        error_msg = f"Error loading data: {e}"
        st.error(error_msg)

        # Log error
        logger.log_error(
            error=e,
            context={"function": "load_sample_data"},
            session_id=st.session_state.get("session_id"),
        )

        return False


def get_langchain_agent():
    """Get or create LangChain agent using LangGraph with multi-step reasoning support"""
    if st.session_state.langchain_agent is None:
        llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M", temperature=0)
        tools = st.session_state.agent.get_langchain_tools()

        # System prompt to guide multi-step reasoning
        system_prompt = """You are a financial analysis assistant with access to transaction analysis tools.

**How to use tools:**
- For comparisons: call the tool once for each item, then state amounts and difference
- For totals/summaries: use analyze_by_category or analyze_merchant
- For finding specific transactions: use search_transactions
- For "top N" / "largest" / "smallest" queries: use search_transactions with sort_by and limit parameters
  Example: "3 largest Amazon purchases" → search_transactions(query="Amazon", sort_by="amount_desc", limit=3)

Examples of good responses:
- "Food: $977.46, Shopping: $217.60. You spent $759.86 more on food."
- "January: $956.62, February: $977.46. Spending increased by $20.84."
- "Your top 3 Amazon purchases: Item1 ($156.92), Item2 ($89.45), Item3 ($67.23)."

**Critical**: Always CALL the tools and provide natural language answers. Never output JSON or describe what you would do."""

        # Create agent using LangChain's create_agent with system prompt
        # This supports multiple tool calls automatically through the ReAct pattern
        agent = create_agent(llm, tools, system_prompt=system_prompt)

        st.session_state.langchain_agent = agent

    return st.session_state.langchain_agent


def preprocess_query(query: str) -> str:
    """Add explicit instructions for comparative queries"""
    # Don't modify the query - let the system prompt handle it
    # The problem is that adding instructions to the query makes the agent
    # describe what it would do instead of actually doing it
    return query


def process_query(user_query):
    """Process user query with LangChain agent"""
    query_id = str(uuid.uuid4())
    session_id = st.session_state.get("session_id", "unknown")
    process_start_time = time.time()

    # Log query and processing start
    logger.log_query(
        query=user_query,
        session_id=session_id,
        query_id=query_id,
    )
    logger.log_query_processing_start(
        query=user_query,
        session_id=session_id,
        query_id=query_id,
    )

    try:
        # Get or create LangChain agent
        agent = get_langchain_agent()

        # NEW: Preprocess query for comparative analysis
        enhanced_query = preprocess_query(user_query)

        # Create callback to intercept tool execution
        callback = ToolExecutionCallback(
            st.session_state.handler_registry,
            enhanced_query,  # Use enhanced query
            session_id,
            query_id,
        )

        # Build messages from conversation history
        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                from langchain_core.messages import AIMessage

                messages.append(AIMessage(content=msg["content"]))

        # Add current user query (enhanced version)
        messages.append(HumanMessage(content=enhanced_query))

        # Run the agent with messages
        config: RunnableConfig = {"callbacks": [callback]}
        result = agent.invoke({"messages": messages}, config=config)

        # Extract the final response from the last message
        if result.get("messages"):
            last_message = result["messages"][-1]
            full_response = (
                last_message.content
                if hasattr(last_message, "content")
                else str(last_message)
            )
        else:
            full_response = str(result)

        # NEW: Use ResponseProcessor instead of extract_final_answer
        from response_processor import ResponseProcessor

        tool_results = []
        for call in callback.tool_calls:
            # Extract content from result (might be a ToolMessage object)
            result = call.get("result", "")
            if hasattr(result, "content"):
                content = result.content
            else:
                content = str(result) if result else ""

            args = call.get("args", {})

            # Debug: Log what we're extracting
            logger.log_warning(
                message=f"Building tool_result - name: {call.get('name')}, args: {args}",
                context={"call": call},
                session_id=session_id,
            )

            tool_results.append(
                {
                    "content": content,
                    "tool_name": call.get("name", ""),
                    "args": args,
                }
            )

        response = ResponseProcessor.process_response(
            query=user_query,  # Use original query for pattern detection
            response=full_response,
            tool_results=tool_results,
        )

        # Calculate response time
        response_time = time.time() - process_start_time

        # Update session state with tool results (in main thread)
        # Handle multiple tool calls for complex queries
        tool_used = None
        if callback.tool_calls:
            # Get list of tool names used (for logging)
            tool_names = [tc["name"] for tc in callback.tool_calls]
            tool_used = ", ".join(tool_names) if len(tool_names) > 1 else tool_names[0]

            # For display purposes, use the LAST tool's result
            # (or aggregate if needed in future)
            last_tool = callback.tool_calls[-1]

            try:
                result_info = callback.handler_registry.handle_result(
                    last_tool["name"], last_tool["args"], user_query
                )

                # Update session state
                if result_info.get("dataframe") is not None:
                    df = result_info["dataframe"]
                    st.session_state.query_dataframe = df

                    # Log dataframe (first 10 rows)
                    logger.log_dataframe(
                        dataframe=df,
                        tool_name=last_tool["name"],
                        session_id=session_id,
                        query_id=query_id,
                    )
                st.session_state.query_title = result_info["title"]
            except Exception as e:
                # If processing fails, continue without updating state
                logger.log_warning(
                    message="Failed to process tool result",
                    context={
                        "function": "process_query",
                        "tool_name": last_tool["name"],
                        "error": str(e),
                    },
                    session_id=session_id,
                )
        elif callback.tool_executed and callback.tool_name and callback.tool_args:
            # Fallback to legacy single-tool handling
            tool_used = callback.tool_name
            try:
                result_info = callback.handler_registry.handle_result(
                    callback.tool_name, callback.tool_args, user_query
                )

                # Update session state
                if result_info.get("dataframe") is not None:
                    df = result_info["dataframe"]
                    st.session_state.query_dataframe = df

                    # Log dataframe (first 10 rows)
                    logger.log_dataframe(
                        dataframe=df,
                        tool_name=callback.tool_name,
                        session_id=session_id,
                        query_id=query_id,
                    )
                st.session_state.query_title = result_info["title"]
            except Exception as e:
                # If processing fails, continue without updating state
                logger.log_warning(
                    message="Failed to process tool result",
                    context={
                        "function": "process_query",
                        "tool_name": callback.tool_name,
                        "error": str(e),
                    },
                    session_id=session_id,
                )

        # Log response generation
        logger.log_response(
            query=user_query,
            response=response,
            response_time=response_time,
            tool_used=tool_used,
            session_id=session_id,
            query_id=query_id,
        )

        # Display the response
        with st.chat_message("assistant"):
            st.markdown(response)

        # Save assistant response to session state
        st.session_state.messages.append({"role": "assistant", "content": response})

        # Log response displayed
        logger.log_response_displayed(
            response=response,
            session_id=session_id,
            query_id=query_id,
        )

    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        response_time = time.time() - process_start_time

        # Log error with full context
        logger.log_error(
            error=e,
            context={
                "function": "process_query",
                "user_query": user_query,
                "response_time": response_time,
            },
            session_id=session_id,
            query_id=query_id,
        )

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
