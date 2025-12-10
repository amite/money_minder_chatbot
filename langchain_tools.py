from typing import Optional
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr
from agent import FinancialAgent


class SearchTransactionsInput(BaseModel):
    """Input schema for search_transactions tool"""

    query: str = Field(description="Search query describing what to look for")
    limit: int = Field(default=10, description="Maximum number of results to return")
    category: Optional[str] = Field(
        default=None,
        description="Optional: Filter by category (food, shopping, entertainment, transport, utilities, health)",
    )
    sort_by: Optional[str] = Field(
        default=None,
        description="Optional: Sort results - 'amount_desc' (largest first), 'amount_asc' (smallest first), 'date_desc' (newest first), 'date_asc' (oldest first)",
    )


class SearchTransactionsTool(BaseTool):
    """Tool for searching transactions by description, category, or merchant"""

    name: str = "search_transactions"
    description: str = """Search for transactions by description keywords or text, with optional filtering and sorting.

USE THIS WHEN:
- User searches by description keywords (e.g., "coffee", "subscription", "gas")
- User wants to find transactions matching text in descriptions
- User asks "Find my [item] purchases" or "Show me [keyword] transactions"
- User asks for "top N", "largest", "smallest", "most expensive" transactions
- User wants to search across all merchants/categories by description

ESPECIALLY USE FOR "TOP N" QUERIES:
✓ "What were my 3 largest shopping purchases at Amazon?" 
  → search_transactions(query="Amazon", category="shopping", sort_by="amount_desc", limit=3)
✓ "Show me my 5 most expensive food purchases"
  → search_transactions(query="food", sort_by="amount_desc", limit=5)
✓ "Find my smallest transport expenses"
  → search_transactions(query="transport", sort_by="amount_asc", limit=5)

FOR MULTI-STEP QUERIES (call this tool MULTIPLE TIMES):
✓ Multiple keyword searches: "Find all coffee shops (Starbucks and Dunkin)"
  → Call #1: search_transactions(query="Starbucks")
  → Call #2: search_transactions(query="Dunkin")
  → Then combine results in your response

DO NOT USE FOR:
- Queries about total spending (use analyze_merchant or analyze_by_category)
- Queries about spending summaries (use get_spending_summary)

Examples:
✓ "Find my coffee purchases"
✓ "Show me all my Spotify transactions"
✓ "What were my 3 largest purchases at Amazon?" (use sort_by="amount_desc", limit=3)
✗ "How much did I spend on food?" (use analyze_by_category - asking for total)"""
    args_schema: type[BaseModel] = SearchTransactionsInput
    _agent: FinancialAgent = PrivateAttr()

    def __init__(self, agent: FinancialAgent, **kwargs):
        super().__init__(**kwargs)
        self._agent = agent

    def _run(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> str:
        """Execute the search_transactions tool"""
        return self._agent.search_transactions(query, limit, category, sort_by)

    async def _arun(
        self,
        query: str,
        limit: int = 10,
        category: Optional[str] = None,
        sort_by: Optional[str] = None,
    ) -> str:
        """Async execution (not implemented)"""
        raise NotImplementedError("Async not supported")


class AnalyzeByCategoryInput(BaseModel):
    """Input schema for analyze_by_category tool"""

    category: str = Field(
        description="Transaction category (food, shopping, entertainment, transport, utilities, health). Example queries: 'How much did I spend on shopping?', 'What were my food expenses in February?', 'Show me entertainment spending'."
    )
    start_date: Optional[str] = Field(
        default=None,
        description="Start date in YYYY-MM-DD format. When user mentions a month (e.g., 'February 2024'), use the first day of that month (e.g., '2024-02-01'). When user mentions a quarter (e.g., 'Q1 2024'), use the first day of that quarter (e.g., '2024-01-01'). When user mentions a specific date range, use the start of that range. Examples: 'February 2024' → '2024-02-01', 'in March' → '2024-03-01', 'from January 1st' → '2024-01-01', 'Q1 2024' → '2024-01-01'.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format. When user mentions a month (e.g., 'February 2024'), use the last day of that month (e.g., '2024-02-29' for February 2024, '2024-02-28' for non-leap years). When user mentions a quarter, use the last day of that quarter. When user mentions a specific date range, use the end of that range. Examples: 'February 2024' → '2024-02-29', 'through March 15th' → '2024-03-15', 'Q1 2024' → '2024-03-31'.",
    )


class AnalyzeByCategoryTool(BaseTool):
    """Tool for analyzing spending by category within a date range"""

    name: str = "analyze_by_category"
    description: str = """Analyze spending for a SPECIFIC single category.

USE THIS WHEN:
- User asks about spending in ONE specific category (food, shopping, entertainment, transport, utilities, health)
- User mentions category WITHOUT mentioning a specific merchant
- User asks "How much did I spend on [category]?"

FOR MULTI-STEP QUERIES (call this tool MULTIPLE TIMES):
✓ Comparative queries: "Compare food vs shopping in February"
  → Call #1: analyze_by_category(category="food", start_date="2024-02-01", end_date="2024-02-29")
  → Call #2: analyze_by_category(category="shopping", start_date="2024-02-01", end_date="2024-02-29")
  → Then compare the totals in your response

✓ Trend analysis: "Did food spending increase from January to February?"
  → Call #1: analyze_by_category(category="food", start_date="2024-01-01", end_date="2024-01-31")
  → Call #2: analyze_by_category(category="food", start_date="2024-02-01", end_date="2024-02-29")
  → Then calculate the change and report the trend

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
✗ "Show me my health expenses at Uber" (use analyze_merchant - merchant mentioned)"""
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
        description="Time period (last_week, last_month, last_3_months, all_time). Example queries: 'Give me an overview of all my spending', 'What's my spending summary for last month?', 'Show me all my spending categories'.",
    )


class GetSpendingSummaryTool(BaseTool):
    """Tool for getting summary statistics of spending"""

    name: str = "get_spending_summary"
    description: str = (
        "Get summary statistics showing spending breakdown across ALL categories. Use this tool when users want an overview of spending across multiple/all categories, want to see all available categories, or ask for general spending summaries. DO NOT use this for queries about a single specific category - use analyze_by_category instead. Examples: 'Give me an overview of all my spending', 'What's my spending summary?', 'Show me all my spending categories'."
    )
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
        description="Start date in YYYY-MM-DD format. Only include if user explicitly mentions a specific date or time period (e.g., 'in January', 'this year', 'from 2024-01-01'). Do not infer or guess dates. When user mentions a month (e.g., 'in February', 'February 2024'), use the first day of that month (e.g., '2024-02-01'). When user mentions a quarter, use the first day of that quarter. Examples: 'in February' → '2024-02-01', 'from January 1st' → '2024-01-01', 'Q1 2024' → '2024-01-01'.",
    )
    end_date: Optional[str] = Field(
        default=None,
        description="End date in YYYY-MM-DD format. Only include if user explicitly mentions a specific date or time period. Do not infer or guess dates. When user mentions a month (e.g., 'in February', 'February 2024'), use the last day of that month (e.g., '2024-02-29' for February 2024). When user mentions a quarter, use the last day of that quarter. Examples: 'in February' → '2024-02-29', 'through March 15th' → '2024-03-15', 'Q1 2024' → '2024-03-31'.",
    )


class AnalyzeMerchantTool(BaseTool):
    """Tool for analyzing spending for a specific merchant"""

    name: str = "analyze_merchant"
    description: str = """Analyze spending for a specific merchant.

USE THIS WHEN:
- User mentions a specific merchant name (Amazon, Walmart, Starbucks, Whole Foods, CVS, Uber, Spotify, etc.)
- User wants merchant spending grouped by category
- User asks "How much at [merchant]?" or "Show me [merchant] spending"
- User mentions BOTH merchant AND category (prioritize merchant)
- User asks about merchant transactions with date filters

FOR MULTI-STEP QUERIES (call this tool MULTIPLE TIMES):
✓ Comparative merchant analysis: "Compare my Amazon vs Walmart spending in Q1"
  → Call #1: analyze_merchant(merchant="Amazon", start_date="2024-01-01", end_date="2024-03-31")
  → Call #2: analyze_merchant(merchant="Walmart", start_date="2024-01-01", end_date="2024-03-31")
  → Then compare the totals in your response

✓ Category breakdown at merchant: "At Amazon, did I spend more on shopping or entertainment?"
  → Call #1: analyze_merchant(merchant="Amazon", group_by_category=True)
  → Then compare the category totals from the results

✓ Multiple merchants: "Show me spending at Starbucks and Dunkin in February"
  → Call #1: analyze_merchant(merchant="Starbucks", start_date="2024-02-01", end_date="2024-02-29")
  → Call #2: analyze_merchant(merchant="Dunkin", start_date="2024-02-01", end_date="2024-02-29")
  → Then present both results

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
✗ "How much did I spend on shopping?" (use analyze_by_category - no merchant)"""
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
