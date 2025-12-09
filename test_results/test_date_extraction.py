"""
Date Extraction Test Script

Tests date extraction for month-based queries similar to Q2.
Focuses on verifying that improved tool descriptions help LLM extract correct dates.

Usage:
    python test_results/test_date_extraction.py
"""

import json
import time
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from agent import FinancialAgent
from vector_store import TransactionVectorStore
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain.agents import create_agent
from langchain_core.callbacks import BaseCallbackHandler

# Test questions focused on date extraction (similar to Q2)
DATE_EXTRACTION_TESTS = [
    {
        "id": 1,
        "question": "What were my food expenses in February 2024?",
        "expected_start": "2024-02-01",
        "expected_end": "2024-02-29",
        "category": "food",
    },
    {
        "id": 2,
        "question": "Show me my shopping expenses in March 2024",
        "expected_start": "2024-03-01",
        "expected_end": "2024-03-31",
        "category": "shopping",
    },
    {
        "id": 3,
        "question": "How much did I spend on entertainment in January 2024?",
        "expected_start": "2024-01-01",
        "expected_end": "2024-01-31",
        "category": "entertainment",
    },
    {
        "id": 4,
        "question": "What were my transport expenses in February?",
        "expected_start": "2024-02-01",
        "expected_end": "2024-02-29",
        "category": "transport",
    },
    {
        "id": 5,
        "question": "Show me my health spending in April 2024",
        "expected_start": "2024-04-01",
        "expected_end": "2024-04-30",
        "category": "health",
    },
]


class ToolCaptureCallback(BaseCallbackHandler):
    """Callback to capture tool calls"""

    def __init__(self):
        super().__init__()
        self.tool_name = None
        self.tool_args = None

    def on_tool_start(
        self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
    ) -> None:
        """Capture tool name and arguments"""
        self.tool_name = serialized.get("name")
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


def test_date_extraction():
    """Test date extraction for various month-based queries"""
    print("\n" + "=" * 70)
    print("DATE EXTRACTION TEST - Q2 Style Queries")
    print("=" * 70 + "\n")

    # Load data
    print("Loading test data...")
    vector_store = TransactionVectorStore()

    # Load transactions
    csv_path = os.path.join(project_root, "data", "transactions.csv")
    if not os.path.exists(csv_path):
        print(f"❌ Error: {csv_path} not found")
        return

    import pandas as pd

    df = pd.read_csv(csv_path)
    transactions = df.to_dict("records")
    vector_store.add_transactions(transactions)
    print(f"✓ Loaded {len(transactions)} transactions\n")

    # Create agent
    financial_agent = FinancialAgent()
    financial_agent.vector_store = vector_store

    # Create LangChain agent (same pattern as test_response_quality.py)
    llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M", temperature=0)
    tools = financial_agent.get_langchain_tools()
    langchain_agent = create_agent(llm, tools)

    results = []
    total_tests = len(DATE_EXTRACTION_TESTS)
    passed = 0

    for test_case in DATE_EXTRACTION_TESTS:
        question = test_case["question"]
        expected_start = test_case["expected_start"]
        expected_end = test_case["expected_end"]
        category = test_case["category"]

        print(f"[{test_case['id']}/{total_tests}] Testing: {question}")
        print(f"  Expected: start_date={expected_start}, end_date={expected_end}")

        callback = ToolCaptureCallback()
        start_time = time.time()

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

            # Check tool call
            tool_name = callback.tool_name
            tool_args = callback.tool_args or {}

            # Analyze results
            extracted_start = tool_args.get("start_date")
            extracted_end = tool_args.get("end_date")
            extracted_category = tool_args.get("category")

            # Check if correct
            start_correct = extracted_start == expected_start
            end_correct = extracted_end == expected_end
            category_correct = (
                extracted_category and category.lower() in extracted_category.lower()
            )
            tool_correct = tool_name == "analyze_by_category"

            all_correct = (
                start_correct and end_correct and category_correct and tool_correct
            )

            if all_correct:
                passed += 1
                status = "✅ PASS"
            else:
                status = "❌ FAIL"

            print(f"  Tool: {tool_name} {'✅' if tool_correct else '❌'}")
            print(
                f"  Category: {extracted_category} {'✅' if category_correct else '❌'}"
            )
            print(
                f"  Start Date: {extracted_start} {'✅' if start_correct else f'❌ (expected {expected_start})'}"
            )
            print(
                f"  End Date: {extracted_end} {'✅' if end_correct else f'❌ (expected {expected_end})'}"
            )
            print(f"  Response Time: {response_time:.2f}s")
            print(f"  Status: {status}\n")

            results.append(
                {
                    "question": question,
                    "expected_start": expected_start,
                    "expected_end": expected_end,
                    "extracted_start": extracted_start,
                    "extracted_end": extracted_end,
                    "tool_name": tool_name,
                    "tool_args": tool_args,
                    "start_correct": start_correct,
                    "end_correct": end_correct,
                    "all_correct": all_correct,
                    "response_time": response_time,
                    "response": (
                        response[:200] + "..." if len(response) > 200 else response
                    ),
                }
            )

        except Exception as e:
            print(f"  ❌ Error: {str(e)}\n")
            results.append(
                {
                    "question": question,
                    "error": str(e),
                    "all_correct": False,
                }
            )

    # Summary
    print("=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"Total Tests: {total_tests}")
    print(f"Passed: {passed}")
    print(f"Failed: {total_tests - passed}")
    print(f"Success Rate: {passed/total_tests*100:.1f}%")
    print()

    # Detailed breakdown
    print("Date Extraction Accuracy:")
    start_correct_count = sum(1 for r in results if r.get("start_correct", False))
    end_correct_count = sum(1 for r in results if r.get("end_correct", False))
    print(
        f"  Start Date Correct: {start_correct_count}/{total_tests} ({start_correct_count/total_tests*100:.1f}%)"
    )
    print(
        f"  End Date Correct: {end_correct_count}/{total_tests} ({end_correct_count/total_tests*100:.1f}%)"
    )
    print()

    # Save results
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_file = os.path.join(
        project_root, "test_results", f"date_extraction_test_{timestamp}.json"
    )
    os.makedirs(os.path.dirname(results_file), exist_ok=True)

    with open(results_file, "w") as f:
        json.dump(
            {
                "timestamp": timestamp,
                "summary": {
                    "total_tests": total_tests,
                    "passed": passed,
                    "failed": total_tests - passed,
                    "success_rate": passed / total_tests * 100,
                    "start_date_accuracy": start_correct_count / total_tests * 100,
                    "end_date_accuracy": end_correct_count / total_tests * 100,
                },
                "results": results,
            },
            f,
            indent=2,
        )

    print(f"📄 Results saved to: {results_file}")
    print()

    return results


if __name__ == "__main__":
    test_date_extraction()
