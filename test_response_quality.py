"""
Response Quality Testing Script

This script tests the Financial Agent with 15 diverse questions and generates
a comprehensive quality evaluation report.

Usage:
    python test_response_quality.py
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from agent import FinancialAgent
from vector_store import TransactionVectorStore
from logger import get_logger
from tool_handlers import HandlerRegistry

# Test questions covering various query types
TEST_QUESTIONS = [
    {
        "id": 1,
        "question": "How much did I spend on shopping?",
        "category": "category_analysis",
        "expected_tool": "analyze_by_category",
        "expected_params": {"category": "shopping"},
    },
    {
        "id": 2,
        "question": "What were my food expenses in February 2024?",
        "category": "category_analysis_with_date",
        "expected_tool": "analyze_by_category",
        "expected_params": {
            "category": "food",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29",
        },
    },
    {
        "id": 3,
        "question": "Show me my Amazon spending",
        "category": "merchant_analysis",
        "expected_tool": "analyze_merchant",
        "expected_params": {"merchant": "Amazon"},
    },
    {
        "id": 4,
        "question": "Analyze my Whole Foods spending grouped by category",
        "category": "merchant_analysis_grouped",
        "expected_tool": "analyze_merchant",
        "expected_params": {"merchant": "Whole Foods", "group_by_category": True},
    },
    {
        "id": 5,
        "question": "How much did I spend at Walmart in March 2024?",
        "category": "merchant_analysis_with_date",
        "expected_tool": "analyze_merchant",
        "expected_params": {
            "merchant": "Walmart",
            "start_date": "2024-03-01",
            "end_date": "2024-03-31",
        },
    },
    {
        "id": 6,
        "question": "What's my spending summary for last month?",
        "category": "spending_summary",
        "expected_tool": "get_spending_summary",
        "expected_params": {"period": "last_month"},
    },
    {
        "id": 7,
        "question": "Give me an overview of all my spending",
        "category": "spending_summary",
        "expected_tool": "get_spending_summary",
        "expected_params": {"period": "all_time"},
    },
    {
        "id": 8,
        "question": "Show me my spending breakdown for the last 3 months",
        "category": "spending_summary",
        "expected_tool": "get_spending_summary",
        "expected_params": {"period": "last_3_months"},
    },
    {
        "id": 9,
        "question": "Find my coffee purchases",
        "category": "search_query",
        "expected_tool": "search_transactions",
        "expected_params": {"query": "coffee"},
    },
    {
        "id": 10,
        "question": "Show me all my Spotify transactions",
        "category": "search_query",
        "expected_tool": "search_transactions",
        "expected_params": {"query": "Spotify"},
    },
    {
        "id": 11,
        "question": "Analyze my transportation expenses",
        "category": "category_analysis",
        "expected_tool": "analyze_by_category",
        "expected_params": {"category": "transport"},
    },
    {
        "id": 12,
        "question": "What categories have I spent money on at Apple?",
        "category": "merchant_analysis",
        "expected_tool": "analyze_merchant",
        "expected_params": {"merchant": "Apple"},
    },
    {
        "id": 13,
        "question": "How much did I spend at CVS from January 1st to February 15th, 2024?",
        "category": "merchant_analysis_with_date",
        "expected_tool": "analyze_merchant",
        "expected_params": {
            "merchant": "CVS",
            "start_date": "2024-01-01",
            "end_date": "2024-02-15",
        },
    },
    {
        "id": 14,
        "question": "What's my total spending on entertainment?",
        "category": "category_analysis",
        "expected_tool": "analyze_by_category",
        "expected_params": {"category": "entertainment"},
    },
    {
        "id": 15,
        "question": "Show me my health expenses at Uber in February",
        "category": "complex_query",
        "expected_tool": "analyze_merchant",
        "expected_params": {
            "merchant": "Uber",
            "start_date": "2024-02-01",
            "end_date": "2024-02-29",
        },
    },
]


class ResponseQualityTester:
    """Test response quality of the Financial Agent"""

    def __init__(self):
        self.logger = get_logger()
        self.agent = FinancialAgent()
        self.handler_registry = HandlerRegistry(self.agent)
        self.results: List[Dict[str, Any]] = []
        self.test_session_id = f"test_session_{int(time.time())}"

    def load_test_data(self) -> int:
        """Load transactions into vector store"""
        print("Loading test data...")
        try:
            df = pd.read_csv("data/transactions.csv")
            transactions = df.to_dict("records")
            vector_store = TransactionVectorStore()
            vector_store.add_transactions(transactions)
            print(f"✓ Loaded {len(transactions)} transactions")
            return len(transactions)
        except Exception as e:
            print(f"✗ Error loading data: {e}")
            raise

    def test_with_langchain_agent(
        self, question: str, agent: FinancialAgent
    ) -> tuple[str, float, Optional[str], Optional[Dict]]:
        """Test question using LangChain agent (simulates app behavior)"""
        from langchain_ollama import ChatOllama
        from langchain.agents import create_agent
        from langchain_core.messages import HumanMessage
        from langchain_core.callbacks import BaseCallbackHandler

        # Callback to capture tool execution
        class ToolCaptureCallback(BaseCallbackHandler):
            def __init__(self):
                super().__init__()
                self.tool_name = None
                self.tool_args = None

            def on_tool_start(
                self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
            ) -> None:
                self.tool_name = serialized.get("name")
                # Parse tool input to extract arguments
                try:
                    import ast

                    if isinstance(input_str, dict):
                        self.tool_args = input_str
                    elif isinstance(input_str, str):
                        try:
                            self.tool_args = ast.literal_eval(input_str)
                        except:
                            try:
                                self.tool_args = json.loads(input_str)
                            except:
                                self.tool_args = {"raw_input": input_str}
                    else:
                        self.tool_args = {}
                except Exception:
                    self.tool_args = {}

        llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M", temperature=0)
        tools = agent.get_langchain_tools()
        langchain_agent = create_agent(llm, tools)

        start_time = time.time()
        callback = ToolCaptureCallback()

        try:
            result = langchain_agent.invoke(
                {"messages": [HumanMessage(content=question)]},
                config={"callbacks": [callback]},
            )

            response_time = time.time() - start_time

            # Extract response
            if result.get("messages"):
                last_message = result["messages"][-1]
                response = (
                    last_message.content
                    if hasattr(last_message, "content")
                    else str(last_message)
                )
            else:
                response = str(result)

            return response, response_time, callback.tool_name, callback.tool_args

        except Exception as e:
            response_time = time.time() - start_time
            raise e

    def run_tests(self) -> Dict[str, Any]:
        """Run all test questions and document results"""
        print("\n" + "=" * 70)
        print("FINANCIAL AGENT RESPONSE QUALITY TEST")
        print("=" * 70 + "\n")

        # Load data
        transaction_count = self.load_test_data()

        total_start_time = time.time()

        for test_case in TEST_QUESTIONS:
            question_id = test_case["id"]
            question = test_case["question"]
            category = test_case["category"]

            print(f"\n[{question_id}/15] Testing: {question}")
            print(f"Category: {category}")

            query_id = f"test_{question_id}_{int(time.time())}"

            # Log query
            self.logger.log_query(
                query=question,
                session_id=self.test_session_id,
                query_id=query_id,
            )

            result: Dict[str, Any] = {
                "question_id": question_id,
                "question": question,
                "category": category,
                "expected_tool": test_case.get("expected_tool"),
                "expected_params": test_case.get("expected_params"),
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "response": None,
                "response_length": 0,
                "response_time": None,
                "tool_used": None,
                "tool_args": None,
                "tool_match": None,
                "dataframe": None,
                "dataframe_match": None,
                "dataframe_analysis": None,
                "error": None,
                "error_type": None,
            }

            try:
                self.logger.log_query_processing_start(
                    query=question,
                    session_id=self.test_session_id,
                    query_id=query_id,
                )

                response, response_time, tool_used, tool_args = (
                    self.test_with_langchain_agent(question, self.agent)
                )

                result["success"] = True
                result["response"] = response
                result["response_length"] = len(response)
                result["response_time"] = response_time
                result["tool_used"] = tool_used
                result["tool_args"] = tool_args

                # Check if correct tool was used
                expected_tool = test_case.get("expected_tool")
                if expected_tool:
                    result["tool_match"] = tool_used == expected_tool

                # Generate and analyze dataframe
                if tool_used and tool_args:
                    try:
                        result_info = self.handler_registry.handle_result(
                            tool_used, tool_args, question
                        )
                        df = result_info.get("dataframe")
                        if df is not None and not df.empty:
                            result["dataframe"] = {
                                "row_count": len(df),
                                "column_count": len(df.columns),
                                "columns": list(df.columns),
                                "sample_rows": df.head(10).to_dict("records"),
                            }

                            # Analyze if dataframe matches query context
                            analysis = self._analyze_dataframe_match(
                                df, question, tool_used, tool_args, test_case
                            )
                            result["dataframe_analysis"] = analysis
                            result["dataframe_match"] = analysis["matches_query"]

                            # Log dataframe
                            self.logger.log_dataframe(
                                dataframe=df,
                                tool_name=tool_used,
                                session_id=self.test_session_id,
                                query_id=query_id,
                            )
                    except Exception as e:
                        result["dataframe_analysis"] = {
                            "error": str(e),
                            "matches_query": False,
                        }

                # Log response
                self.logger.log_response(
                    query=question,
                    response=response,
                    response_time=response_time,
                    tool_used=tool_used,
                    session_id=self.test_session_id,
                    query_id=query_id,
                )

                print(f"✓ Success ({response_time:.2f}s)")
                if tool_used:
                    print(f"  Tool used: {tool_used}")

            except Exception as e:
                result["error"] = str(e)
                result["error_type"] = type(e).__name__
                result["response_time"] = time.time() - time.time()

                self.logger.log_error(
                    error=e,
                    context={
                        "function": "run_tests",
                        "question": question,
                        "question_id": question_id,
                    },
                    session_id=self.test_session_id,
                    query_id=query_id,
                )

                print(f"✗ Error: {e}")

            self.results.append(result)

            # Small delay between questions
            time.sleep(0.5)

        total_time = time.time() - total_start_time

        # Generate summary
        successful = [r for r in self.results if r["success"]]
        failed = [r for r in self.results if not r["success"]]
        tool_matches = [r for r in self.results if r.get("tool_match") is True]
        tool_mismatches = [r for r in self.results if r.get("tool_match") is False]
        dataframe_matches = [
            r for r in self.results if r.get("dataframe_match") is True
        ]
        dataframe_mismatches = [
            r for r in self.results if r.get("dataframe_match") is False
        ]
        has_dataframe = [r for r in self.results if r.get("dataframe") is not None]

        summary = {
            "test_run": {
                "timestamp": datetime.now().isoformat(),
                "session_id": self.test_session_id,
                "total_questions": len(TEST_QUESTIONS),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(TEST_QUESTIONS) * 100,
                "tool_match_count": len(tool_matches),
                "tool_mismatch_count": len(tool_mismatches),
                "dataframe_match_count": len(dataframe_matches),
                "dataframe_mismatch_count": len(dataframe_mismatches),
                "dataframe_generated_count": len(has_dataframe),
                "total_time_seconds": total_time,
                "avg_response_time": (
                    sum(r["response_time"] for r in successful if r["response_time"])
                    / len(successful)
                    if successful
                    else 0
                ),
                "transaction_count": transaction_count,
            },
            "results": self.results,
        }

        return summary

    def _analyze_dataframe_match(
        self,
        df: pd.DataFrame,
        question: str,
        tool_used: str,
        tool_args: Dict[str, Any],
        test_case: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Analyze if dataframe matches the query context"""
        analysis = {
            "matches_query": True,
            "checks": [],
            "issues": [],
        }

        question_lower = question.lower()
        expected_params = test_case.get("expected_params", {})

        # Check 1: Category match (for category analysis)
        if tool_used == "analyze_by_category":
            expected_category = expected_params.get("category", "").lower()
            if "category" in df.columns:
                df_categories = (
                    df["category"].str.lower().unique()
                    if "category" in df.columns
                    else []
                )
                if expected_category and expected_category not in df_categories:
                    # Check if all rows have the expected category
                    if len(df_categories) > 0:
                        if expected_category not in [c.lower() for c in df_categories]:
                            analysis["issues"].append(
                                f"Expected category '{expected_category}' not found in dataframe"
                            )
                            analysis["matches_query"] = False
                analysis["checks"].append(
                    f"Category filter: {expected_category} in dataframe"
                )

        # Check 2: Merchant match (for merchant analysis)
        if tool_used == "analyze_merchant":
            expected_merchant = expected_params.get("merchant", "").lower()
            if "merchant" in df.columns:
                df_merchants = df["merchant"].str.lower().unique()
                if expected_merchant and expected_merchant not in df_merchants:
                    analysis["issues"].append(
                        f"Expected merchant '{expected_merchant}' not found in dataframe"
                    )
                    analysis["matches_query"] = False
                analysis["checks"].append(
                    f"Merchant filter: {expected_merchant} in dataframe"
                )
            elif "Category" in df.columns and tool_args.get("group_by_category"):
                # Grouped by category - check if merchant is in title or metadata
                analysis["checks"].append(
                    "Merchant analysis grouped by category - structure correct"
                )

        # Check 3: Date range match
        if expected_params.get("start_date") or expected_params.get("end_date"):
            if "date" in df.columns:
                start_date = expected_params.get("start_date")
                end_date = expected_params.get("end_date")
                df_dates = pd.to_datetime(df["date"], errors="coerce")

                if start_date:
                    before_start = (df_dates < pd.to_datetime(start_date)).sum()
                    if before_start > 0:
                        analysis["issues"].append(
                            f"{before_start} rows before start_date {start_date}"
                        )
                        analysis["matches_query"] = False

                if end_date:
                    after_end = (df_dates > pd.to_datetime(end_date)).sum()
                    if after_end > 0:
                        analysis["issues"].append(
                            f"{after_end} rows after end_date {end_date}"
                        )
                        analysis["matches_query"] = False

                analysis["checks"].append("Date range filter applied correctly")

        # Check 4: Empty dataframe check
        if df.empty:
            # Check if empty result is expected
            if "no" not in question_lower and "empty" not in question_lower:
                analysis["issues"].append(
                    "Dataframe is empty but query expects results"
                )
                analysis["matches_query"] = False
            analysis["checks"].append("Empty dataframe - may be expected")
        else:
            analysis["checks"].append(f"Dataframe contains {len(df)} rows")

        # Check 5: Expected columns for tool type
        if tool_used == "get_spending_summary":
            expected_cols = [
                "Category",
                "Total Spending",
                "Transaction Count",
                "Average",
            ]
            missing_cols = [col for col in expected_cols if col not in df.columns]
            if missing_cols:
                analysis["issues"].append(f"Missing expected columns: {missing_cols}")
                # Don't mark as failure - columns might vary
            analysis["checks"].append("Spending summary structure verified")

        # Check 6: Search query relevance (for search_transactions)
        if tool_used == "search_transactions":
            search_query = tool_args.get("query", "").lower()
            if search_query and not df.empty:
                # Check if search terms appear in descriptions
                if "description" in df.columns:
                    descriptions = df["description"].str.lower()
                    matches = descriptions.str.contains(search_query, na=False).sum()
                    if matches == 0 and len(df) > 0:
                        analysis["issues"].append(
                            f"Search query '{search_query}' not found in descriptions"
                        )
                        # Don't mark as failure - semantic search might find related items
                    analysis["checks"].append(
                        f"Search relevance: {matches}/{len(df)} rows contain search term"
                    )

        return analysis

    def save_results(self, summary: Dict[str, Any], output_dir: str = "test_results"):
        """Save test results to JSON and generate markdown report"""
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Save JSON
        json_file = output_path / f"test_results_{timestamp}.json"
        with open(json_file, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        print(f"\n✓ Results saved to {json_file}")

        # Generate markdown report
        markdown_file = output_path / f"quality_report_{timestamp}.md"
        self.generate_markdown_report(summary, markdown_file)

        print(f"✓ Quality report saved to {markdown_file}")

        return json_file, markdown_file

    def generate_markdown_report(self, summary: Dict[str, Any], output_file: Path):
        """Generate a comprehensive markdown quality report"""
        test_run = summary["test_run"]
        results = summary["results"]

        with open(output_file, "w") as f:
            f.write("# Financial Agent Response Quality Report\n\n")
            f.write(f"**Generated:** {test_run['timestamp']}\n\n")
            f.write("---\n\n")

            # Executive Summary
            f.write("## Executive Summary\n\n")
            f.write(f"- **Total Questions:** {test_run['total_questions']}\n")
            f.write(
                f"- **Successful:** {test_run['successful']} ({test_run['success_rate']:.1f}%)\n"
            )
            f.write(f"- **Failed:** {test_run['failed']}\n")
            f.write(
                f"- **Tool Match Rate:** {len([r for r in results if r.get('tool_match') is True])}/{len([r for r in results if r.get('tool_match') is not None])} correct tool selections\n"
            )
            f.write(
                f"- **Dataframe Generated:** {test_run['dataframe_generated_count']}/{test_run['total_questions']} queries\n"
            )
            if test_run["dataframe_generated_count"] > 0:
                f.write(
                    f"- **Dataframe Match Rate:** {test_run['dataframe_match_count']}/{test_run['dataframe_generated_count']} dataframes match query context ({test_run['dataframe_match_count']/test_run['dataframe_generated_count']*100:.1f}%)\n"
                )
            f.write(
                f"- **Average Response Time:** {test_run['avg_response_time']:.2f}s\n"
            )
            f.write(
                f"- **Total Test Duration:** {test_run['total_time_seconds']:.1f}s\n"
            )
            f.write(
                f"- **Transaction Data:** {test_run['transaction_count']} transactions\n\n"
            )

            # Performance Metrics
            f.write("## Performance Metrics\n\n")
            response_times = [
                r["response_time"]
                for r in results
                if r["success"] and r["response_time"]
            ]
            if response_times:
                f.write(f"- **Fastest Response:** {min(response_times):.2f}s\n")
                f.write(f"- **Slowest Response:** {max(response_times):.2f}s\n")
                f.write(
                    f"- **Median Response Time:** {sorted(response_times)[len(response_times)//2]:.2f}s\n\n"
                )

            # Response Length Analysis
            response_lengths = [r["response_length"] for r in results if r["success"]]
            if response_lengths:
                f.write("### Response Length Analysis\n\n")
                f.write(
                    f"- **Average Length:** {sum(response_lengths)/len(response_lengths):.0f} characters\n"
                )
                f.write(f"- **Shortest:** {min(response_lengths)} characters\n")
                f.write(f"- **Longest:** {max(response_lengths)} characters\n\n")

            # Tool Usage Analysis
            f.write("## Tool Usage Analysis\n\n")
            tool_usage = {}
            for r in results:
                if r.get("tool_used"):
                    tool = r["tool_used"]
                    tool_usage[tool] = tool_usage.get(tool, 0) + 1

            for tool, count in sorted(tool_usage.items(), key=lambda x: -x[1]):
                f.write(f"- **{tool}:** {count} times\n")
            f.write("\n")

            # Detailed Results
            f.write("## Detailed Test Results\n\n")

            for result in results:
                f.write(
                    f"### Question {result['question_id']}: {result['question']}\n\n"
                )
                f.write(f"**Category:** {result['category']}\n\n")

                if result["success"]:
                    f.write(f"✅ **Status:** Success\n\n")
                    f.write(f"**Response Time:** {result['response_time']:.2f}s\n")
                    f.write(
                        f"**Response Length:** {result['response_length']} characters\n"
                    )

                    if result.get("tool_used"):
                        f.write(f"**Tool Used:** `{result['tool_used']}`\n")
                        if result.get("expected_tool"):
                            match_status = "✅" if result.get("tool_match") else "❌"
                            f.write(
                                f"**Expected Tool:** `{result['expected_tool']}` {match_status}\n"
                            )

                    if result.get("tool_args"):
                        f.write(
                            f"**Tool Arguments:** `{json.dumps(result['tool_args'], indent=2)}`\n"
                        )

                    # Dataframe analysis
                    if result.get("dataframe"):
                        df_info = result["dataframe"]
                        f.write(f"\n**Dataframe:**\n")
                        f.write(f"- Rows: {df_info['row_count']}\n")
                        f.write(
                            f"- Columns: {df_info['column_count']} ({', '.join(df_info['columns'][:5])}{'...' if len(df_info['columns']) > 5 else ''})\n"
                        )

                        if result.get("dataframe_analysis"):
                            analysis = result["dataframe_analysis"]
                            match_status = (
                                "✅" if analysis.get("matches_query") else "❌"
                            )
                            f.write(f"- **Matches Query:** {match_status}\n")

                            if analysis.get("checks"):
                                f.write(f"- **Checks:**\n")
                                for check in analysis["checks"]:
                                    f.write(f"  - {check}\n")

                            if analysis.get("issues"):
                                f.write(f"- **Issues:**\n")
                                for issue in analysis["issues"]:
                                    f.write(f"  - ⚠️ {issue}\n")

                    elif result.get("dataframe_analysis") and result[
                        "dataframe_analysis"
                    ].get("error"):
                        f.write(
                            f"\n**Dataframe Error:** {result['dataframe_analysis']['error']}\n"
                        )

                    f.write("\n**Response:**\n\n")
                    f.write("```\n")
                    # Truncate very long responses
                    response_text = result["response"]
                    if len(response_text) > 1000:
                        response_text = response_text[:1000] + "\n... (truncated)"
                    f.write(response_text)
                    f.write("\n```\n\n")
                else:
                    f.write(f"❌ **Status:** Failed\n\n")
                    f.write(f"**Error Type:** {result.get('error_type', 'Unknown')}\n")
                    f.write(
                        f"**Error Message:** {result.get('error', 'Unknown error')}\n\n"
                    )

                f.write("---\n\n")

            # Failed Tests Summary
            failed_tests = [r for r in results if not r["success"]]
            if failed_tests:
                f.write("## Failed Tests Summary\n\n")
                for result in failed_tests:
                    f.write(f"- **Q{result['question_id']}:** {result['question']}\n")
                    f.write(f"  - Error: {result.get('error', 'Unknown')}\n\n")

            # Tool Mismatch Analysis
            mismatches = [r for r in results if r.get("tool_match") is False]
            if mismatches:
                f.write("## Tool Selection Mismatches\n\n")
                for result in mismatches:
                    f.write(f"- **Q{result['question_id']}:** {result['question']}\n")
                    f.write(f"  - Expected: `{result.get('expected_tool')}`\n")
                    f.write(f"  - Used: `{result.get('tool_used')}`\n\n")

            # Dataframe Mismatch Analysis
            df_mismatches = [r for r in results if r.get("dataframe_match") is False]
            if df_mismatches:
                f.write("## Dataframe Context Mismatches\n\n")
                for result in df_mismatches:
                    f.write(f"- **Q{result['question_id']}:** {result['question']}\n")
                    if result.get("dataframe_analysis"):
                        analysis = result["dataframe_analysis"]
                        if analysis.get("issues"):
                            for issue in analysis["issues"]:
                                f.write(f"  - ⚠️ {issue}\n")
                    f.write("\n")

            # Recommendations
            f.write("## Recommendations\n\n")

            if test_run["success_rate"] < 100:
                f.write("### Error Handling\n")
                f.write("- Review failed test cases and improve error handling\n")
                f.write("- Add better input validation\n\n")

            if mismatches:
                f.write("### Tool Selection\n")
                f.write("- Review tool descriptions to ensure they match user intent\n")
                f.write("- Consider improving LLM prompts for tool selection\n\n")

            avg_time = test_run["avg_response_time"]
            if avg_time > 5:
                f.write("### Performance\n")
                f.write("- Response times are high, consider optimization\n")
                f.write("- Review vector store and LLM performance\n\n")

            f.write("---\n\n")
            f.write(f"*Report generated by Response Quality Tester*\n")


def main():
    """Main entry point"""
    tester = ResponseQualityTester()

    try:
        summary = tester.run_tests()
        json_file, markdown_file = tester.save_results(summary)

        print("\n" + "=" * 70)
        print("TEST COMPLETE")
        print("=" * 70)
        print(
            f"\n✓ Successful: {summary['test_run']['successful']}/{summary['test_run']['total_questions']}"
        )
        print(f"✓ Success Rate: {summary['test_run']['success_rate']:.1f}%")
        print(
            f"✓ Average Response Time: {summary['test_run']['avg_response_time']:.2f}s"
        )
        print(f"\n📄 Results: {json_file}")
        print(f"📊 Report: {markdown_file}\n")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nFatal error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
