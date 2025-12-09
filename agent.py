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
                    "description": "Search for transactions by description, category, or merchant",
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
                    "description": "Analyze spending by category within a date range",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Transaction category (food, shopping, entertainment, transport, utilities, health)",
                            },
                            "start_date": {
                                "type": "string",
                                "description": "Start date in YYYY-MM-DD format",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format",
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
                    "description": "Get summary statistics of spending. Returns spending breakdown by category, which can be used to list all available categories. Use this tool when users ask about categories, want to see all spending categories, or need an overview of spending across all categories.",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "period": {
                                "type": "string",
                                "description": "Time period (last_week, last_month, last_3_months, all_time)",
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
                    "description": "Analyze spending for a specific merchant, optionally grouped by category. Use this tool when users ask about spending at a specific merchant, want to see merchant transactions grouped by category, or need merchant-specific analysis.",
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
                                "description": "Start date in YYYY-MM-DD format. Only include if user explicitly mentions a specific date or time period (e.g., 'in January', 'this year', 'from 2024-01-01'). Do not infer or guess dates.",
                            },
                            "end_date": {
                                "type": "string",
                                "description": "End date in YYYY-MM-DD format. Only include if user explicitly mentions a specific date or time period. Do not infer or guess dates.",
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

        # Filter by date if provided
        if start_date:
            filtered = filtered[filtered["date"] >= start_date]
        if end_date:
            filtered = filtered[filtered["date"] <= end_date]

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

        # Filter by date if provided
        if start_date:
            filtered = filtered[filtered["date"] >= start_date]
        if end_date:
            filtered = filtered[filtered["date"] <= end_date]

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

        # Filter by date if provided
        original_count = len(filtered)
        if start_date:
            filtered = filtered[filtered["date"] >= start_date]  # type: ignore[assignment]
        if end_date:
            filtered = filtered[filtered["date"] <= end_date]  # type: ignore[assignment]

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

        # Filter by date if provided
        if start_date:
            filtered = filtered[filtered["date"] >= start_date]  # type: ignore[assignment]
        if end_date:
            filtered = filtered[filtered["date"] <= end_date]  # type: ignore[assignment]

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
