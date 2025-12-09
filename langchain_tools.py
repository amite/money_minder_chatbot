from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from agent import FinancialAgent


class SearchTransactionsInput(BaseModel):
    """Input schema for search_transactions tool"""

    query: str = Field(description="Search query describing what to look for")
    limit: int = Field(default=10, description="Maximum number of results")


class SearchTransactionsTool(BaseTool):
    """Tool for searching transactions by description, category, or merchant"""

    name: str = "search_transactions"
    description: str = "Search for transactions by description, category, or merchant"
    args_schema: type[BaseModel] = SearchTransactionsInput
    _agent: FinancialAgent = PrivateAttr()

    def __init__(self, agent: FinancialAgent, **kwargs):
        super().__init__(**kwargs)
        self._agent = agent

    def _run(self, query: str, limit: int = 10) -> str:
        """Execute the search_transactions tool"""
        return self._agent.search_transactions(query, limit)

    async def _arun(self, query: str, limit: int = 10) -> str:
        """Async execution (not implemented)"""
        raise NotImplementedError("Async not supported")


class AnalyzeByCategoryInput(BaseModel):
    """Input schema for analyze_by_category tool"""

    category: str = Field(
        description="Transaction category (food, shopping, entertainment, transport, utilities, health)"
    )
    start_date: Optional[str] = Field(
        default=None, description="Start date in YYYY-MM-DD format"
    )
    end_date: Optional[str] = Field(
        default=None, description="End date in YYYY-MM-DD format"
    )


class AnalyzeByCategoryTool(BaseTool):
    """Tool for analyzing spending by category within a date range"""

    name: str = "analyze_by_category"
    description: str = "Analyze spending by category within a date range"
    args_schema: type[BaseModel] = AnalyzeByCategoryInput
    _agent: FinancialAgent = PrivateAttr()

    def __init__(self, agent: FinancialAgent, **kwargs):
        super().__init__(**kwargs)
        self._agent = agent

    def _run(
        self,
        category: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Execute the analyze_by_category tool"""
        return self._agent.analyze_by_category(category, start_date, end_date)

    async def _arun(
        self,
        category: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Async execution (not implemented)"""
        raise NotImplementedError("Async not supported")


class GetSpendingSummaryInput(BaseModel):
    """Input schema for get_spending_summary tool"""

    period: str = Field(
        default="last_month",
        description="Time period (last_week, last_month, last_3_months, all_time)",
    )


class GetSpendingSummaryTool(BaseTool):
    """Tool for getting summary statistics of spending"""

    name: str = "get_spending_summary"
    description: str = "Get summary statistics of spending. Returns spending breakdown by category, which can be used to list all available categories. Use this tool when users ask about categories, want to see all spending categories, or need an overview of spending across all categories."
    args_schema: type[BaseModel] = GetSpendingSummaryInput
    _agent: FinancialAgent = PrivateAttr()

    def __init__(self, agent: FinancialAgent, **kwargs):
        super().__init__(**kwargs)
        self._agent = agent

    def _run(self, period: str = "last_month") -> str:
        """Execute the get_spending_summary tool"""
        return self._agent.get_spending_summary(period)

    async def _arun(self, period: str = "last_month") -> str:
        """Async execution (not implemented)"""
        raise NotImplementedError("Async not supported")


class AnalyzeMerchantInput(BaseModel):
    """Input schema for analyze_merchant tool"""

    merchant: str = Field(
        description="Merchant name (e.g., Amazon, Starbucks, Walmart)"
    )
    group_by_category: bool = Field(
        default=False,
        description="Whether to group results by category (default: false)",
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format. Only include if user explicitly mentions a specific date or time period (e.g., 'in January', 'this year', 'from 2024-01-01'). Do not infer or guess dates.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format. Only include if user explicitly mentions a specific date or time period. Do not infer or guess dates.",
    )


class AnalyzeMerchantTool(BaseTool):
    """Tool for analyzing spending for a specific merchant"""

    name: str = "analyze_merchant"
    description: str = "Analyze spending for a specific merchant, optionally grouped by category. Use this tool when users ask about spending at a specific merchant, want to see merchant transactions grouped by category, or need merchant-specific analysis."
    args_schema: type[BaseModel] = AnalyzeMerchantInput
    _agent: FinancialAgent = PrivateAttr()

    def __init__(self, agent: FinancialAgent, **kwargs):
        super().__init__(**kwargs)
        self._agent = agent

    def _run(
        self,
        merchant: str,
        group_by_category: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Execute the analyze_merchant tool"""
        return self._agent.analyze_merchant(
            merchant, group_by_category, start_date, end_date
        )

    async def _arun(
        self,
        merchant: str,
        group_by_category: bool = False,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> str:
        """Async execution (not implemented)"""
        raise NotImplementedError("Async not supported")

