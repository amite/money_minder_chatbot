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
if "query_dataframe" not in st.session_state:
    st.session_state.query_dataframe = None
if "query_title" not in st.session_state:
    st.session_state.query_title = "Sample Data Preview"


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
    try:
        # Build conversation history from session state
        messages = [
            {
                "role": "system",
                "content": """You are a financial assistant that helps users analyze their transactions.
                You have access to tools that can search transactions, analyze by category, and provide spending summaries.
                
                Tool selection guidelines:
                - Use get_spending_summary when users ask about categories, want to list all categories, or need an overview of spending across categories. This tool returns spending_by_category which shows all available categories.
                - Use analyze_by_category when users ask about spending for a specific category (e.g., "how much did I spend on food?").
                - Use analyze_merchant when users ask about spending at a specific merchant, want to group merchant transactions by category, or need merchant-specific analysis. Set group_by_category=True when users want to see merchant spending grouped by category. Only include start_date and end_date parameters if the user explicitly mentions specific dates or time periods - do not infer dates from the query.
                - Use search_transactions when users want to find specific transactions by description or merchant.
                
                Always use the appropriate tool based on the user's query. After getting tool results, provide a clear, 
                natural language explanation of the findings. When get_spending_summary is used, you can extract and list 
                the category names from the spending_by_category field in the results.""",
            }
        ]

        # Add conversation history
        for msg in st.session_state.messages:
            if msg["role"] in ["user", "assistant"]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        # Add current user query
        messages.append({"role": "user", "content": user_query})

        # First, let the LLM decide which tool to use
        response = ollama.chat(
            model="llama3.1:8b-instruct-q4_K_M",
            messages=messages,
            tools=st.session_state.agent.get_tools(),
        )

        # Check if LLM wants to use a tool
        if response.message.tool_calls:
            tool_call = response.message.tool_calls[0]
            tool_name = tool_call.function.name
            tool_args = dict(tool_call.function.arguments)

            # Execute the tool
            try:
                result = st.session_state.agent.execute_tool(tool_name, **tool_args)

                # Store relevant dataframe for the expander
                try:
                    if tool_name == "search_transactions":
                        df = st.session_state.agent.search_transactions_df(
                            tool_args.get("query", ""), tool_args.get("limit", 10)
                        )
                        st.session_state.query_dataframe = df
                        st.session_state.query_title = (
                            f"📊 Search Results: '{tool_args.get('query', '')}'"
                        )
                    elif tool_name == "analyze_by_category":
                        df = st.session_state.agent.analyze_by_category_df(
                            tool_args.get("category", ""),
                            tool_args.get("start_date"),
                            tool_args.get("end_date"),
                        )
                        st.session_state.query_dataframe = df
                        category = tool_args.get("category", "")
                        st.session_state.query_title = (
                            f"📊 Category Analysis: {category.title()}"
                        )
                    elif tool_name == "get_spending_summary":
                        df = st.session_state.agent.get_spending_summary_df(
                            tool_args.get("period", "last_month")
                        )
                        st.session_state.query_dataframe = df

                        # Check if query is about listing categories
                        query_lower = user_query.lower()
                        is_category_listing = any(
                            word in query_lower
                            for word in [
                                "list",
                                "types",
                                "kinds",
                                "categories",
                                "what categories",
                                "what kind",
                                "what types",
                                "expenditures",
                                "spendings",
                            ]
                        )

                        if is_category_listing:
                            st.session_state.query_title = "📊 Spending Categories"
                        else:
                            period = (
                                tool_args.get("period", "last_month")
                                .replace("_", " ")
                                .title()
                            )
                            st.session_state.query_title = (
                                f"📊 Spending Summary: {period}"
                            )
                    elif tool_name == "analyze_merchant":
                        df = st.session_state.agent.analyze_merchant_df(
                            tool_args.get("merchant", ""),
                            tool_args.get("group_by_category", False),
                            tool_args.get("start_date"),
                            tool_args.get("end_date"),
                        )
                        st.session_state.query_dataframe = df
                        merchant = tool_args.get("merchant", "")
                        if tool_args.get("group_by_category", False):
                            st.session_state.query_title = (
                                f"📊 {merchant} Spending by Category"
                            )
                        else:
                            st.session_state.query_title = f"📊 {merchant} Transactions"
                except Exception as df_error:
                    # If dataframe extraction fails, just continue without it
                    pass

            except Exception as e:
                error_msg = f"Error executing tool {tool_name}: {str(e)}"
                with st.chat_message("assistant"):
                    st.error(error_msg)
                st.session_state.messages.append(
                    {"role": "assistant", "content": error_msg}
                )
                return

            # Add tool result as context for the LLM to generate a natural language response
            # Format: Include the tool result in a user message asking for explanation
            tool_result_context = f"""I executed the {tool_name} tool.

The tool returned these results:
{result}

Please provide a clear, natural language explanation of these results for the user. Do not include the tool parameters or function call details in your response."""

            messages.append({"role": "user", "content": tool_result_context})

            # Get natural language response from LLM with tool results
            final_response = ollama.chat(
                model="llama3.1:8b-instruct-q4_K_M",
                messages=messages,
            )

            # Extract response content, handling various response formats
            assistant_response = None
            if hasattr(final_response, "message"):
                if hasattr(final_response.message, "content"):
                    assistant_response = final_response.message.content

            # If no content, check if there's tool call info (shouldn't happen but handle it)
            if not assistant_response:
                # Check if response has tool calls (unexpected at this stage)
                if hasattr(final_response, "message") and hasattr(
                    final_response.message, "tool_calls"
                ):
                    if final_response.message.tool_calls:
                        # This shouldn't happen, but if it does, create a fallback response
                        assistant_response = f"I analyzed your {tool_name.replace('_', ' ')} request. Here are the results:\n\n{result}"
                    else:
                        assistant_response = "I processed your request, but couldn't generate a response."
                else:
                    assistant_response = (
                        "I processed your request, but couldn't generate a response."
                    )

            # Filter out any tool call JSON that might be in the response
            # Sometimes LLM includes tool call info in the response text
            if assistant_response and assistant_response.strip().startswith("{"):
                try:
                    # Check if it's a tool call JSON structure
                    parsed = json.loads(assistant_response)
                    if "name" in parsed and "parameters" in parsed:
                        # This is a tool call JSON, not a proper response - create fallback
                        assistant_response = f"I analyzed your {tool_name.replace('_', ' ')} request. Here are the results:\n\n{result}"
                except json.JSONDecodeError:
                    # Not JSON, keep the response as is
                    pass

            with st.chat_message("assistant"):
                st.markdown(assistant_response)

                # Also show formatted results for better UX
                try:
                    result_data = json.loads(result)

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
                    # If result is not JSON, it's already in the response
                    pass

            # Save assistant response to session state
            st.session_state.messages.append(
                {"role": "assistant", "content": assistant_response}
            )
        else:
            # If no tool call, just show the response
            assistant_response = (
                response.message.content or "I couldn't generate a response."
            )
            with st.chat_message("assistant"):
                st.markdown(assistant_response)

            # Save assistant response to session state
            st.session_state.messages.append(
                {"role": "assistant", "content": assistant_response}
            )

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
