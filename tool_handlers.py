from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import pandas as pd
from agent import FinancialAgent


class ToolResultHandler(ABC):
    """Base class for handling tool results"""

    def __init__(self, agent: FinancialAgent):
        self.agent = agent

    @abstractmethod
    def get_dataframe(self, tool_args: Dict[str, Any]) -> Optional[pd.DataFrame]:
        """Extract dataframe from tool result"""
        pass

    @abstractmethod
    def generate_title(self, tool_args: Dict[str, Any], user_query: str) -> str:
        """Generate display title for the result"""
        pass

    def get_visualization(self, tool_args: Dict[str, Any]) -> Optional[str]:
        """Return visualization type if applicable"""
        return None


class SearchTransactionsHandler(ToolResultHandler):
    """Handler for search_transactions tool"""

    def get_dataframe(self, tool_args: Dict[str, Any]) -> Optional[pd.DataFrame]:
        query = tool_args.get("query", "")
        limit = tool_args.get("limit", 10)
        return self.agent.search_transactions_df(query, limit)

    def generate_title(self, tool_args: Dict[str, Any], user_query: str) -> str:
        query = tool_args.get("query", "")
        return f"📊 Search Results: '{query}'"


class AnalyzeByCategoryHandler(ToolResultHandler):
    """Handler for analyze_by_category tool"""

    def get_dataframe(self, tool_args: Dict[str, Any]) -> Optional[pd.DataFrame]:
        category = tool_args.get("category", "")
        start_date = tool_args.get("start_date")
        end_date = tool_args.get("end_date")
        return self.agent.analyze_by_category_df(category, start_date, end_date)

    def generate_title(self, tool_args: Dict[str, Any], user_query: str) -> str:
        category = tool_args.get("category", "")
        return f"📊 Category Analysis: {category.title()}"

    def get_visualization(self, tool_args: Dict[str, Any]) -> Optional[str]:
        return "bar_chart"


class GetSpendingSummaryHandler(ToolResultHandler):
    """Handler for get_spending_summary tool"""

    def get_dataframe(self, tool_args: Dict[str, Any]) -> Optional[pd.DataFrame]:
        period = tool_args.get("period", "last_month")
        return self.agent.get_spending_summary_df(period)

    def generate_title(self, tool_args: Dict[str, Any], user_query: str) -> str:
        # Check if query is about listing categories
        query_lower = user_query.lower()
        category_keywords = [
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

        if any(word in query_lower for word in category_keywords):
            return "📊 Spending Categories"

        period = tool_args.get("period", "last_month").replace("_", " ").title()
        return f"📊 Spending Summary: {period}"

    def get_visualization(self, tool_args: Dict[str, Any]) -> Optional[str]:
        return "bar_chart"


class AnalyzeMerchantHandler(ToolResultHandler):
    """Handler for analyze_merchant tool"""

    def get_dataframe(self, tool_args: Dict[str, Any]) -> Optional[pd.DataFrame]:
        merchant = tool_args.get("merchant", "")
        group_by_category = tool_args.get("group_by_category", False)
        start_date = tool_args.get("start_date")
        end_date = tool_args.get("end_date")
        return self.agent.analyze_merchant_df(
            merchant, group_by_category, start_date, end_date
        )

    def generate_title(self, tool_args: Dict[str, Any], user_query: str) -> str:
        merchant = tool_args.get("merchant", "")
        if tool_args.get("group_by_category", False):
            return f"📊 {merchant} Spending by Category"
        return f"📊 {merchant} Transactions"

    def get_visualization(self, tool_args: Dict[str, Any]) -> Optional[str]:
        if tool_args.get("group_by_category", False):
            return "bar_chart"
        return None


class HandlerRegistry:
    """Registry for mapping tool names to handlers"""

    def __init__(self, agent: FinancialAgent):
        self.agent = agent
        self.handlers = {
            "search_transactions": SearchTransactionsHandler(agent),
            "analyze_by_category": AnalyzeByCategoryHandler(agent),
            "get_spending_summary": GetSpendingSummaryHandler(agent),
            "analyze_merchant": AnalyzeMerchantHandler(agent),
        }

    def handle_result(
        self,
        tool_name: str,
        tool_args: Dict[str, Any],
        user_query: str,
    ) -> Dict[str, Any]:
        """
        Process tool result and return dataframe, title, and visualization info

        Returns:
            Dict with keys: 'dataframe', 'title', 'visualization'
        """
        handler = self.handlers.get(tool_name)
        if not handler:
            return {
                "dataframe": None,
                "title": f"📊 {tool_name.replace('_', ' ').title()}",
                "visualization": None,
            }

        try:
            df = handler.get_dataframe(tool_args)
            title = handler.generate_title(tool_args, user_query)
            visualization = handler.get_visualization(tool_args)

            return {
                "dataframe": df,
                "title": title,
                "visualization": visualization,
            }
        except Exception as e:
            # If handler fails, return minimal info
            return {
                "dataframe": None,
                "title": f"📊 {tool_name.replace('_', ' ').title()}",
                "visualization": None,
            }

