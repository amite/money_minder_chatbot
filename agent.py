import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from vector_store import TransactionVectorStore
import json


class FinancialAgent:
    def __init__(self):
        self.vector_store = TransactionVectorStore()
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "search_transactions",
                    "description": """Search for transactions by description keywords or text.

USE THIS WHEN:
- User searches by description keywords (e.g., "coffee", "subscription", "gas")
- User wants to find transactions matching text in descriptions
- User asks "Find my [item] purchases" or "Show me [keyword] transactions"
- User wants to search across all merchants/categories by description

DO NOT USE FOR:
- Queries about a specific merchant (use analyze_merchant)
- Queries about a specific category (use analyze_by_category)
- Queries about spending summaries (use get_spending_summary)

Examples:
✓ "Find my coffee purchases"
✓ "Show me all my Spotify transactions" (searching by description)
✓ "Search for subscription payments"
✓ "Find transactions with 'grocery' in description"
✗ "Show my Amazon spending" (use analyze_merchant - specific merchant)
✗ "How much did I spend on food?" (use analyze_by_category - specific category)""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Search query describing what to look for",
                            },
                            "limit": {
                                "type": "integer",
                                "description": "Maximum number of results",
                                "default": 10,
                            },
                        },
                        "required": ["query"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_by_category",
                    "description": """Analyze spending for a SPECIFIC single category.

USE THIS WHEN:
- User asks about spending in ONE specific category (food, shopping, entertainment, transport, utilities, health)
- User mentions category WITHOUT mentioning a specific merchant
- User asks "How much did I spend on [category]?"

DO NOT USE FOR:
- Queries mentioning a specific merchant (use analyze_merchant instead)
- Keyword searches by description (use search_transactions)
- Queries about multiple categories (use get_spending_summary)
- Queries like "Whole Foods" (this is a merchant, not a category)

Examples:
✓ "How much did I spend on shopping?"
✓ "What were my food expenses in February?"
✓ "Show me entertainment spending"
✗ "Analyze Whole Foods spending" (use analyze_merchant - Whole Foods is a merchant)
✗ "Find coffee purchases" (use search_transactions - keyword search)
✗ "Show me my health expenses at Uber" (use analyze_merchant - merchant mentioned)""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Transaction category (food, shopping, entertainment, transport, utilities, health). Example queries: 'How much did I spend on shopping?', 'What were my food expenses in February?', 'Show me entertainment spending'.",
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format. When user mentions a month (e.g., 'February 2024'), use the first day of that month (e.g., '2024-02-01'). When user mentions a quarter (e.g., 'Q1 2024'), use the first day of that quarter (e.g., '2024-01-01'). When user mentions a specific date range, use the start of that range. Examples: 'February 2024' → '2024-02-01', 'in March' → '2024-03-01', 'from January 1st' → '2024-01-01', 'Q1 2024' → '2024-01-01'.",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format. When user mentions a month (e.g., 'February 2024'), use the last day of that month (e.g., '2024-02-29' for February 2024, '2024-02-28' for non-leap years). When user mentions a quarter, use the last day of that quarter. When user mentions a specific date range, use the end of that range. Examples: 'February 2024' → '2024-02-29', 'through March 15th' → '2024-03-15', 'Q1 2024' → '2024-03-31'.",
                            },
                        },
                        "required": ["category"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "get_spending_summary",
                    "description": "Get summary statistics showing spending breakdown across ALL categories. Use this tool when users want an overview of spending across multiple/all categories, want to see all available categories, or ask for general spending summaries. DO NOT use this for queries about a single specific category - use analyze_by_category instead. Examples: 'Give me an overview of all my spending', 'What's my spending summary?', 'Show me all my spending categories'.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {
                                "type": "string",
                                "description": "Time period (last_week, last_month, last_3_months, all_time). Example queries: 'Give me an overview of all my spending', 'What's my spending summary for last month?', 'Show me all my spending categories'.",
                                "default": "last_month",
                            }
                        },
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "analyze_merchant",
                    "description": """Analyze spending for a specific merchant.

USE THIS WHEN:
- User mentions a specific merchant name (Amazon, Walmart, Starbucks, Whole Foods, CVS, Uber, Spotify, etc.)
- User wants merchant spending grouped by category
- User asks "How much at [merchant]?" or "Show me [merchant] spending"
- User mentions BOTH merchant AND category (prioritize merchant)
- User asks about merchant transactions with date filters

DO NOT USE FOR:
- General category queries without merchant mention
- Keyword searches by description (use search_transactions)
- Queries like "coffee purchases" without merchant name

Examples:
✓ "Show my Amazon spending"
✓ "Analyze Whole Foods spending grouped by category"
✓ "How much did I spend at Walmart in March?"
✓ "Show me my health expenses at Uber in February" (merchant + category → use merchant tool)
✓ "What categories have I spent money on at Apple?"
✗ "Find coffee purchases" (use search_transactions - no merchant mentioned)
✗ "How much did I spend on shopping?" (use analyze_by_category - no merchant)""",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "merchant": {
                                "type": "string",
                                "description": "Merchant name (e.g., Amazon, Starbucks, Walmart)",
                            },
                            "group_by_category": {
                                "type": "boolean",
                                "description": "Whether to group results by category (default: false)",
                                "default": False,
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format. Only include if user explicitly mentions a specific date or time period (e.g., 'in January', 'this year', 'from 2024-01-01'). Do not infer or guess dates. When user mentions a month (e.g., 'in February', 'February 2024'), use the first day of that month (e.g., '2024-02-01'). When user mentions a quarter, use the first day of that quarter. Examples: 'in February' → '2024-02-01', 'from January 1st' → '2024-01-01', 'Q1 2024' → '2024-01-01'.",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format. Only include if user explicitly mentions a specific date or time period. Do not infer or guess dates. When user mentions a month (e.g., 'in February', 'February 2024'), use the last day of that month (e.g., '2024-02-29' for February 2024). When user mentions a quarter, use the last day of that quarter. Examples: 'in February' → '2024-02-29', 'through March 15th' → '2024-03-15', 'Q1 2024' → '2024-03-31'.",
                            },
                        },
                        "required": ["merchant"],
                    },
                },
            },
        ]

    def search_transactions(self, query: str, limit: int = 10) -> str:
        """Tool implementation: Search transactions"""
        results = self.vector_store.search_by_description(query, limit)
        return self._format_transactions(results)

    def search_transactions_df(self, query: str, limit: int = 10) -> pd.DataFrame:
        """Get search results as DataFrame"""
        results = self.vector_store.search_by_description(query, limit)
        if not results:
            return pd.DataFrame()
        return pd.DataFrame(results)

    def analyze_by_category(
        self,
        category: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Tool implementation: Analyze by category"""
        all_tx = self.vector_store.get_all_transactions()
        df = pd.DataFrame(all_tx)

        # Filter by category
        filtered = df[df["category"].str.lower() == category.lower()]

        # Convert date to datetime before filtering
        filtered["date"] = pd.to_datetime(filtered["date"])

        # Filter by date if provided
        if start_date:
            start_dt = pd.to_datetime(start_date)
            filtered = filtered[filtered["date"] >= start_dt]
        if end_date:
            end_dt = pd.to_datetime(end_date)
            filtered = filtered[filtered["date"] <= end_dt]

        if len(filtered) == 0:
            return f"No transactions found for category: {category}"

        # Convert amount to float
        filtered["amount"] = filtered["amount"].astype(float)

        summary = {
            "total_spent": filtered["amount"].sum(),
            "transaction_count": len(filtered),
            "average_transaction": filtered["amount"].mean(),
            "min_transaction": filtered["amount"].min(),
            "max_transaction": filtered["amount"].max(),
            "unique_merchants": filtered["merchant"].nunique(),  # type: ignore[attr-defined]
        }

        return json.dumps(summary, indent=2)

    def analyze_by_category_df(
        self,
        category: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Get category analysis results as DataFrame"""
        all_tx = self.vector_store.get_all_transactions()
        df = pd.DataFrame(all_tx)

        # Filter by category
        filtered = df[df["category"].str.lower() == category.lower()]

        # Convert date to datetime before filtering
        filtered["date"] = pd.to_datetime(filtered["date"])

        # Filter by date if provided
        if start_date:
            start_dt = pd.to_datetime(start_date)
            filtered = filtered[filtered["date"] >= start_dt]
        if end_date:
            end_dt = pd.to_datetime(end_date)
            filtered = filtered[filtered["date"] <= end_dt]

        if len(filtered) == 0:
            return pd.DataFrame()

        filtered["amount"] = filtered["amount"].astype(float)
        result_df: pd.DataFrame = pd.DataFrame(filtered.copy())
        return result_df

    def get_spending_summary(self, period: str = "last_month") -> str:
        """Tool implementation: Get spending summary"""
        all_tx = pd.DataFrame(self.vector_store.get_all_transactions())
        all_tx["date"] = pd.to_datetime(all_tx["date"])
        all_tx["amount"] = all_tx["amount"].astype(float)

        # Filter by period
        end_date = datetime.now()
        if period == "last_week":
            start_date = end_date - timedelta(days=7)
        elif period == "last_month":
            start_date = end_date - timedelta(days=30)
        elif period == "last_3_months":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = all_tx["date"].min()

        filtered = all_tx[all_tx["date"] >= start_date]

        if len(filtered) == 0:
            return "No transactions found in the specified period"

        # Calculate summary
        total = filtered["amount"].sum()
        by_category = filtered.groupby("category")["amount"].sum().to_dict()
        top_merchants_series = filtered.groupby("merchant")["amount"].sum()
        top_merchants = top_merchants_series.nlargest(5).to_dict()  # type: ignore[call-overload]

        summary = {
            "period": period,
            "total_spent": total,
            "transactions_count": len(filtered),
            "daily_average": total / max(1, (end_date - start_date).days),
            "spending_by_category": by_category,
            "top_merchants": top_merchants,
        }

        return json.dumps(summary, indent=2)

    def get_spending_summary_df(self, period: str = "last_month") -> pd.DataFrame:
        """Get spending summary results as DataFrame - returns category summary"""
        all_tx = pd.DataFrame(self.vector_store.get_all_transactions())
        all_tx["date"] = pd.to_datetime(all_tx["date"])
        all_tx["amount"] = all_tx["amount"].astype(float)

        # Filter by period
        end_date = datetime.now()
        if period == "last_week":
            start_date = end_date - timedelta(days=7)
        elif period == "last_month":
            start_date = end_date - timedelta(days=30)
        elif period == "last_3_months":
            start_date = end_date - timedelta(days=90)
        else:
            start_date = all_tx["date"].min()

        filtered = all_tx[all_tx["date"] >= start_date]

        if len(filtered) == 0:
            empty_df = pd.DataFrame(
                {
                    "Category": [],
                    "Total Spending": [],
                    "Transaction Count": [],
                    "Average": [],
                }
            )
            return empty_df

        # Group by category and calculate summary
        category_summary = (
            filtered.groupby("category")
            .agg({"amount": ["sum", "count", "mean"]})
            .reset_index()
        )

        category_summary.columns = [
            "Category",
            "Total Spending",
            "Transaction Count",
            "Average",
        ]
        category_summary = category_summary.sort_values(
            "Total Spending", ascending=False
        )
        category_summary["Total Spending"] = category_summary["Total Spending"].round(2)
        category_summary["Average"] = category_summary["Average"].round(2)

        result_df: pd.DataFrame = category_summary.copy()
        return result_df

    def analyze_merchant(
        self,
        merchant: str,
        group_by_category: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Tool implementation: Analyze merchant spending"""
        all_tx = self.vector_store.get_all_transactions()
        df = pd.DataFrame(all_tx)

        # Filter by merchant
        filtered: pd.DataFrame = df[df["merchant"].str.lower() == merchant.lower()]  # type: ignore[assignment]

        # Convert date to datetime before filtering
        filtered["date"] = pd.to_datetime(filtered["date"])

        # Filter by date if provided
        original_count = len(filtered)
        if start_date:
            start_dt = pd.to_datetime(start_date)
            filtered = filtered[filtered["date"] >= start_dt]  # type: ignore[assignment]
        if end_date:
            end_dt = pd.to_datetime(end_date)
            filtered = filtered[filtered["date"] <= end_dt]  # type: ignore[assignment]

        if len(filtered) == 0:
            # If we had transactions before date filtering, the date range might be wrong
            if original_count > 0:
                date_info = ""
                if start_date or end_date:
                    date_info = f" in the specified date range"
                return f"No transactions found for merchant: {merchant}{date_info}. Found {original_count} transaction(s) for this merchant without date filtering. The date range might not match your transaction data."
            return f"No transactions found for merchant: {merchant}"

        # Convert amount to float
        filtered["amount"] = filtered["amount"].astype(float)

        if group_by_category:
            # Group by category
            category_summary: pd.DataFrame = (
                filtered.groupby("category")
                .agg({"amount": ["sum", "count", "mean"]})
                .reset_index()
            )
            category_summary.columns = [
                "category",
                "total_spent",
                "transaction_count",
                "average",
            ]

            result = {
                "merchant": merchant,
                "grouped_by_category": True,
                "categories": category_summary.to_dict("records"),
                "overall_total": float(filtered["amount"].sum()),
                "overall_count": len(filtered),
            }
        else:
            # Overall summary
            result = {
                "merchant": merchant,
                "total_spent": float(filtered["amount"].sum()),
                "transaction_count": len(filtered),
                "average_transaction": float(filtered["amount"].mean()),
                "min_transaction": float(filtered["amount"].min()),
                "max_transaction": float(filtered["amount"].max()),
                "categories": filtered["category"].drop_duplicates().tolist(),  # type: ignore[attr-defined]
            }

        return json.dumps(result, indent=2)

    def analyze_merchant_df(
        self,
        merchant: str,
        group_by_category: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Get merchant analysis results as DataFrame"""
        all_tx = self.vector_store.get_all_transactions()
        df = pd.DataFrame(all_tx)

        # Filter by merchant
        filtered: pd.DataFrame = df[df["merchant"].str.lower() == merchant.lower()]  # type: ignore[assignment]

        # Convert date to datetime before filtering
        filtered["date"] = pd.to_datetime(filtered["date"])

        # Filter by date if provided
        if start_date:
            start_dt = pd.to_datetime(start_date)
            filtered = filtered[filtered["date"] >= start_dt]  # type: ignore[assignment]
        if end_date:
            end_dt = pd.to_datetime(end_date)
            filtered = filtered[filtered["date"] <= end_dt]  # type: ignore[assignment]

        if len(filtered) == 0:
            return pd.DataFrame()

        filtered["amount"] = filtered["amount"].astype(float)

        if group_by_category:
            # Group by category
            category_summary: pd.DataFrame = (
                filtered.groupby("category")
                .agg({"amount": ["sum", "count", "mean"]})
                .reset_index()
            )
            category_summary.columns = [
                "Category",
                "Total Spending",
                "Transaction Count",
                "Average",
            ]
            category_summary = category_summary.sort_values(
                "Total Spending", ascending=False
            )
            category_summary["Total Spending"] = category_summary[
                "Total Spending"
            ].round(2)
            category_summary["Average"] = category_summary["Average"].round(2)
            return category_summary.copy()
        else:
            return filtered.copy()

    def _format_transactions(self, transactions: List[Dict]) -> str:
        """Format transactions for display"""
        if not transactions:
            return "No transactions found"

        formatted = []
        for tx in transactions:
            formatted.append(
                f"Date: {tx['date']} | "
                f"Description: {tx['description']} | "
                f"Category: {tx['category']} | "
                f"Amount: ${tx['amount']} | "
                f"Merchant: {tx['merchant']}"
            )

        return "\n".join(formatted)

    def get_tools(self) -> List[Dict]:
        """Return tool definitions for LLM"""
        return self.tools

    def execute_tool(self, tool_name: str, **kwargs) -> str:
        """Execute a tool by name"""
        if tool_name == "search_transactions":
            return self.search_transactions(**kwargs)
        elif tool_name == "analyze_by_category":
            return self.analyze_by_category(**kwargs)
        elif tool_name == "get_spending_summary":
            return self.get_spending_summary(**kwargs)
        elif tool_name == "analyze_merchant":
            return self.analyze_merchant(**kwargs)
        else:
            return f"Unknown tool: {tool_name}"

    def get_langchain_tools(self):
        """Return LangChain tool instances"""
        from langchain_tools import (
            SearchTransactionsTool,
            AnalyzeByCategoryTool,
            GetSpendingSummaryTool,
            AnalyzeMerchantTool,
        )

        return [
            SearchTransactionsTool(self),
            AnalyzeByCategoryTool(self),
            GetSpendingSummaryTool(self),
            AnalyzeMerchantTool(self),
        ]
