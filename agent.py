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
                    "description": "Get summary statistics of spending",
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
        ]

    def search_transactions(self, query: str, limit: int = 10) -> str:
        """Tool implementation: Search transactions"""
        results = self.vector_store.search_by_description(query, limit)
        return self._format_transactions(results)

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
        else:
            return f"Unknown tool: {tool_name}"
