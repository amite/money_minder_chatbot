"""
Test Runner for Complex Scenarios
Integrates with your existing test infrastructure
"""

import json
import time
import sys
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agent import FinancialAgent
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage


class ComplexScenarioEvaluator:
    """Evaluate agent performance on complex scenarios"""

    def __init__(
        self,
        agent: FinancialAgent,
        scenarios_file: Optional[str] = None,
    ):
        self.agent = agent
        # Get project root directory
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        # Default to test_results directory if scenarios_file not provided
        if scenarios_file is None:
            scenarios_file = os.path.join(
                self.project_root, "test_results", "complex_scenarios.json"
            )
        elif not os.path.isabs(scenarios_file):
            scenarios_file = os.path.join(self.project_root, scenarios_file)

        self.scenarios = self._load_scenarios(scenarios_file)
        if self.scenarios:
            print(f"✓ Loaded {len(self.scenarios)} test scenarios")
        self.results = []

        # Load evaluation framework
        framework_file = os.path.join(
            self.project_root, "test_results", "evaluation_framework.json"
        )
        if os.path.exists(framework_file):
            try:
                with open(framework_file) as f:
                    content = f.read().strip()
                    if content:
                        self.framework = json.loads(content)
                    else:
                        # File exists but is empty, use default
                        print(
                            f"Warning: {framework_file} is empty, using default framework"
                        )
                        self.framework = self._get_default_framework()
            except json.JSONDecodeError as e:
                # Invalid JSON, use default
                print(
                    f"Warning: {framework_file} contains invalid JSON ({e}), using default framework"
                )
                self.framework = self._get_default_framework()
        else:
            # Use default framework if file doesn't exist
            self.framework = self._get_default_framework()

    def _load_scenarios(self, filename: str) -> List[Dict]:
        """Load test scenarios"""
        if not os.path.exists(filename):
            return []
        try:
            with open(filename) as f:
                scenarios = json.load(f)
                if not isinstance(scenarios, list):
                    print(f"Warning: Scenarios file {filename} does not contain a list")
                    return []
                return scenarios
        except json.JSONDecodeError as e:
            print(f"Warning: Could not parse scenarios file {filename}: {e}")
            return []

    def _get_default_framework(self) -> Dict:
        """Return default evaluation framework if file doesn't exist"""
        return {
            "scoring": {
                "tool_selection": {"weight": 0.25},
                "reasoning": {"weight": 0.25},
                "accuracy": {"weight": 0.30},
                "completeness": {"weight": 0.20},
            },
            "difficulty_multipliers": {
                "easy": 1.0,
                "medium": 1.2,
                "hard": 1.5,
            },
            "pass_thresholds": {
                "acceptable": 0.7,
                "good": 0.85,
                "excellent": 0.95,
            },
        }

    def evaluate_single_scenario(self, scenario: Dict) -> Dict:
        """Evaluate agent on a single scenario"""
        print(f"\n{'='*80}")
        print(f"Testing: {scenario['query']}")
        print(f"Difficulty: {scenario['difficulty']}")
        print(f"{'='*80}")

        start_time = time.time()

        try:
            # Run agent query
            llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M", temperature=0)
            tools = self.agent.get_langchain_tools()

            # Track tool calls with callback
            class ToolCallTracker(BaseCallbackHandler):
                def __init__(self):
                    super().__init__()
                    self.tool_calls = []

                def on_tool_start(
                    self, serialized: Dict[str, Any], input_str: str, **kwargs: Any
                ) -> None:
                    tool_name = serialized.get("name", "unknown")
                    self.tool_calls.append(tool_name)

            callback = ToolCallTracker()
            agent_executor = create_react_agent(llm, tools)

            # Execute query
            result = agent_executor.invoke(
                {"messages": [HumanMessage(content=scenario["query"])]},
                config={"callbacks": [callback]},
            )

            # Get tracked tool calls
            tool_calls = callback.tool_calls
            response = (
                result.get("messages", [])[-1].content
                if result.get("messages")
                else str(result)
            )

            response_time = time.time() - start_time

            # Evaluate response
            scores = self._evaluate_response(scenario, response, tool_calls)

            # Calculate weighted score
            weighted_score = sum(
                scores[metric] * self.framework["scoring"][metric]["weight"]
                for metric in [
                    "tool_selection",
                    "reasoning",
                    "accuracy",
                    "completeness",
                ]
                if metric in scores
            )

            # Apply difficulty multiplier
            difficulty_mult = self.framework["difficulty_multipliers"][
                scenario["difficulty"]
            ]
            final_score = weighted_score / difficulty_mult

            result_entry = {
                "scenario_id": scenario["id"],
                "query": scenario["query"],
                "difficulty": scenario["difficulty"],
                "response": response,
                "response_time": response_time,
                "scores": scores,
                "weighted_score": weighted_score,
                "final_score": final_score,
                "passed": final_score
                >= self.framework["pass_thresholds"]["acceptable"],
                "ground_truth": scenario["ground_truth"],
                "tool_calls": tool_calls,
                "timestamp": datetime.now().isoformat(),
            }

            self.results.append(result_entry)

            # Print evaluation
            print(f"\n✓ Response: {response[:200]}...")
            print(f"⏱  Response Time: {response_time:.2f}s")
            print(f"📊 Scores:")
            for metric, score in scores.items():
                print(f"   {metric}: {score:.2f}")
            print(f"🎯 Final Score: {final_score:.2f}")
            print(f"{'✅ PASS' if result_entry['passed'] else '❌ FAIL'}")

            return result_entry

        except Exception as e:
            print(f"❌ Error: {str(e)}")
            error_result = {
                "scenario_id": scenario["id"],
                "query": scenario["query"],
                "difficulty": scenario["difficulty"],
                "error": str(e),
                "response_time": time.time() - start_time,
                "passed": False,
                "timestamp": datetime.now().isoformat(),
            }
            self.results.append(error_result)
            return error_result

    def _evaluate_response(
        self, scenario: Dict, response: str, tool_calls: List
    ) -> Dict[str, float]:
        """Evaluate response against scenario criteria"""
        scores = {}

        # 1. Tool Selection Score
        scores["tool_selection"] = self._score_tool_selection(
            scenario["requires_tools"], tool_calls
        )

        # 2. Reasoning Score (using LLM-as-judge)
        scores["reasoning"] = self._score_reasoning(
            scenario["requires_reasoning"], response, scenario["expected_steps"]
        )

        # 3. Accuracy Score (comparing to ground truth)
        scores["accuracy"] = self._score_accuracy(response, scenario["ground_truth"])

        # 4. Completeness Score
        scores["completeness"] = self._score_completeness(
            scenario["query"], response, scenario["evaluation_criteria"]
        )

        return scores

    def _score_tool_selection(
        self, required_tools: List[str], actual_tools: List[str]
    ) -> float:
        """Score tool selection (1.0 = perfect, 0.0 = wrong tools)"""
        if not required_tools:
            return 1.0

        # Simple matching for now
        # In production, this would track actual tool calls
        score = 0.0
        for tool in required_tools:
            if tool in str(actual_tools):  # Simple contains check
                score += 1.0 / len(required_tools)

        return score

    def _score_reasoning(
        self, reasoning_type: str, response: str, expected_steps: List[str]
    ) -> float:
        """Score multi-step reasoning quality"""
        # Check if response demonstrates the reasoning type
        reasoning_indicators = {
            "comparison": [
                "more",
                "less",
                "higher",
                "lower",
                "compared",
                "versus",
                "than",
            ],
            "temporal_comparison": ["increased", "decreased", "change", "from", "to"],
            "calculation": ["total", "sum", "percentage", "average", "ratio"],
            "filtering": ["only", "excluding", "over", "under", "above", "below"],
            "aggregation": ["combined", "total", "sum", "all"],
            "frequency": ["times", "per week", "per month", "average", "frequency"],
        }

        indicators = reasoning_indicators.get(reasoning_type, [])
        response_lower = response.lower()

        found_indicators = sum(1 for ind in indicators if ind in response_lower)

        # Score based on indicator presence and expected steps
        indicator_score = min(1.0, found_indicators / max(1, len(indicators)))

        # Check if mentions key numbers from expected steps
        step_score = 0.0
        for step in expected_steps:
            if any(word in response_lower for word in step.lower().split()[:3]):
                step_score += 1.0 / len(expected_steps)

        return (indicator_score + step_score) / 2

    def _score_accuracy(self, response: str, ground_truth: Dict) -> float:
        """Score factual accuracy against ground truth"""
        if not ground_truth:
            return 1.0

        score = 0.0
        checks = 0

        # Extract numbers from response
        import re

        numbers_in_response = [float(n) for n in re.findall(r"\d+\.?\d*", response)]

        # Check each ground truth value
        for key, expected_value in ground_truth.items():
            checks += 1

            if isinstance(expected_value, (int, float)):
                # Numeric comparison with 10% tolerance
                tolerance = abs(expected_value * 0.10)
                if any(
                    abs(n - expected_value) <= tolerance for n in numbers_in_response
                ):
                    score += 1.0

            elif isinstance(expected_value, str):
                # String matching
                if expected_value.lower() in response.lower():
                    score += 1.0

            elif isinstance(expected_value, list):
                # List matching
                matches = sum(
                    1
                    for item in expected_value
                    if str(item).lower() in response.lower()
                )
                score += matches / len(expected_value)

        return score / checks if checks > 0 else 0.0

    def _score_completeness(self, query: str, response: str, criteria: Dict) -> float:
        """Score how completely the query was answered"""
        if not criteria:
            return 1.0

        score = 0.0

        for criterion, requirement in criteria.items():
            # Simple keyword-based checking
            # In production, use more sophisticated NLP
            keywords = requirement.lower().split()
            response_lower = response.lower()

            if any(kw in response_lower for kw in keywords if len(kw) > 3):
                score += 1.0 / len(criteria)

        return score

    def run_all_scenarios(self, difficulty_filter: Optional[str] = None) -> Dict:
        """Run all scenarios, optionally filtering by difficulty"""
        scenarios_to_run = self.scenarios

        if difficulty_filter:
            scenarios_to_run = [
                s for s in scenarios_to_run if s["difficulty"] == difficulty_filter
            ]

        if not scenarios_to_run:
            print(f"\n{'='*80}")
            print("WARNING: No scenarios to run!")
            print(
                "Create a scenarios JSON file or use test_complex_scenarios.py to generate scenarios."
            )
            print(f"{'='*80}")
            return self._generate_summary_report()

        print(f"\n{'='*80}")
        print(f"RUNNING {len(scenarios_to_run)} COMPLEX SCENARIOS")
        if difficulty_filter:
            print(f"Filtered to: {difficulty_filter} difficulty")
        print(f"{'='*80}")

        for i, scenario in enumerate(scenarios_to_run, 1):
            print(f"\n[{i}/{len(scenarios_to_run)}]")
            self.evaluate_single_scenario(scenario)

        return self._generate_summary_report()

    def _generate_summary_report(self) -> Dict:
        """Generate comprehensive summary report"""
        if not self.results:
            return {
                "summary": {
                    "total_scenarios": 0,
                    "passed": 0,
                    "failed": 0,
                    "pass_rate": 0.0,
                    "avg_response_time": 0.0,
                    "avg_final_score": 0.0,
                },
                "difficulty_breakdown": {},
                "score_breakdown": {
                    "tool_selection": 0.0,
                    "reasoning": 0.0,
                    "accuracy": 0.0,
                    "completeness": 0.0,
                },
                "failures": [],
            }

        total = len(self.results)
        passed = sum(1 for r in self.results if r.get("passed", False))

        # Calculate average scores by difficulty
        difficulty_stats = {}
        for difficulty in ["easy", "medium", "hard"]:
            diff_results = [
                r for r in self.results if r.get("difficulty") == difficulty
            ]
            if diff_results:
                difficulty_stats[difficulty] = {
                    "count": len(diff_results),
                    "passed": sum(1 for r in diff_results if r.get("passed", False)),
                    "avg_score": sum(r.get("final_score", 0) for r in diff_results)
                    / len(diff_results),
                    "avg_time": sum(r.get("response_time", 0) for r in diff_results)
                    / len(diff_results),
                }

        # Calculate score breakdown
        score_breakdown = {
            "tool_selection": [],
            "reasoning": [],
            "accuracy": [],
            "completeness": [],
        }

        for result in self.results:
            if "scores" in result:
                for metric in score_breakdown:
                    if metric in result["scores"]:
                        score_breakdown[metric].append(result["scores"][metric])

        avg_scores = {
            metric: sum(scores) / len(scores) if scores else 0.0
            for metric, scores in score_breakdown.items()
        }

        report = {
            "summary": {
                "total_scenarios": total,
                "passed": passed,
                "failed": total - passed,
                "pass_rate": passed / total if total > 0 else 0,
                "avg_response_time": sum(
                    r.get("response_time", 0) for r in self.results
                )
                / total,
                "avg_final_score": sum(r.get("final_score", 0) for r in self.results)
                / total,
            },
            "difficulty_breakdown": difficulty_stats,
            "score_breakdown": avg_scores,
            "failures": [
                {
                    "id": r["scenario_id"],
                    "query": r["query"],
                    "difficulty": r.get("difficulty"),
                    "final_score": r.get("final_score", 0),
                    "error": r.get("error"),
                }
                for r in self.results
                if not r.get("passed", False)
            ],
        }

        return report

    def export_results(self, filename: Optional[str] = None):
        """Export detailed results to JSON and Markdown files"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if filename is None:
            json_filename = os.path.join(
                self.project_root, "test_results", f"complex_results_{timestamp}.json"
            )
            md_filename = os.path.join(
                self.project_root,
                "test_results",
                f"complex_quality_report_{timestamp}.md",
            )
        else:
            # If custom filename provided, derive both from it
            base = os.path.splitext(filename)[0]
            json_filename = f"{base}.json"
            md_filename = f"{base}.md"
            if not os.path.isabs(json_filename):
                json_filename = os.path.join(self.project_root, json_filename)
                md_filename = os.path.join(self.project_root, md_filename)

        # Ensure directory exists
        os.makedirs(os.path.dirname(json_filename), exist_ok=True)

        report = self._generate_summary_report()

        # Export JSON
        export_data = {
            "report": report,
            "detailed_results": self.results,
            "timestamp": datetime.now().isoformat(),
        }

        with open(json_filename, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"\n✓ JSON results exported to {json_filename}")

        # Export Markdown
        md_content = self._generate_markdown_report(report, timestamp)
        with open(md_filename, "w") as f:
            f.write(md_content)

        print(f"✓ Markdown report exported to {md_filename}")

        # Print summary
        self._print_summary_report(report)

        return json_filename, md_filename

    def _print_summary_report(self, report: Dict):
        """Print formatted summary report"""
        print(f"\n{'='*80}")
        print("COMPLEX SCENARIO TEST RESULTS")
        print(f"{'='*80}")

        summary = report["summary"]
        print(f"\n📊 OVERALL PERFORMANCE")
        print(f"   Total Scenarios: {summary['total_scenarios']}")
        print(f"   Passed: {summary['passed']} ({summary['pass_rate']:.1%})")
        print(f"   Failed: {summary['failed']}")
        print(f"   Avg Response Time: {summary['avg_response_time']:.2f}s")
        print(f"   Avg Final Score: {summary['avg_final_score']:.2f}")

        print(f"\n📈 BY DIFFICULTY")
        for difficulty, stats in report["difficulty_breakdown"].items():
            pass_rate = stats["passed"] / stats["count"] if stats["count"] > 0 else 0
            print(f"   {difficulty.upper()}:")
            print(
                f"      Pass Rate: {pass_rate:.1%} ({stats['passed']}/{stats['count']})"
            )
            print(f"      Avg Score: {stats['avg_score']:.2f}")
            print(f"      Avg Time: {stats['avg_time']:.2f}s")

        print(f"\n🎯 SCORE BREAKDOWN")
        for metric, score in report["score_breakdown"].items():
            print(f"   {metric}: {score:.2f}")

        if report["failures"]:
            print(f"\n❌ FAILURES ({len(report['failures'])})")
            for failure in report["failures"][:5]:  # Show first 5
                print(f"   - {failure['query']}")
                print(
                    f"     Difficulty: {failure['difficulty']}, Score: {failure['final_score']:.2f}"
                )
                if "error" in failure:
                    print(f"     Error: {failure['error']}")

    def _generate_markdown_report(self, report: Dict, timestamp: str) -> str:
        """Generate a comprehensive markdown report"""
        summary = report["summary"]
        timestamp_readable = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        md_lines = [
            "# Complex Scenario Test Results",
            "",
            f"**Generated:** {timestamp_readable}",
            f"**Report Version:** {timestamp}",
            "",
            "---",
            "",
            "## Executive Summary",
            "",
            f"- **Total Scenarios Tested:** {summary['total_scenarios']}",
            f"- **Passed:** {summary['passed']} ({summary['pass_rate']:.1%})",
            f"- **Failed:** {summary['failed']}",
            f"- **Average Response Time:** {summary['avg_response_time']:.2f}s",
            f"- **Average Final Score:** {summary['avg_final_score']:.2f}/1.0",
            "",
            "### Overall Performance",
            "",
        ]

        # Performance rating
        pass_rate = summary["pass_rate"]
        if pass_rate >= 0.95:
            rating = "✅ **Excellent**"
        elif pass_rate >= 0.85:
            rating = "✅ **Good**"
        elif pass_rate >= 0.70:
            rating = "⚠️ **Acceptable**"
        else:
            rating = "❌ **Needs Improvement**"

        md_lines.extend(
            [
                f"**Performance Rating:** {rating}",
                "",
                "---",
                "",
                "## Performance by Difficulty",
                "",
            ]
        )

        # Difficulty breakdown
        if report["difficulty_breakdown"]:
            md_lines.append(
                "| Difficulty | Count | Passed | Pass Rate | Avg Score | Avg Time |"
            )
            md_lines.append(
                "|-----------|-------|--------|----------|----------|----------|"
            )
            for difficulty, stats in sorted(report["difficulty_breakdown"].items()):
                pass_rate = (
                    stats["passed"] / stats["count"] if stats["count"] > 0 else 0
                )
                md_lines.append(
                    f"| {difficulty.upper()} | {stats['count']} | {stats['passed']} | "
                    f"{pass_rate:.1%} | {stats['avg_score']:.2f} | {stats['avg_time']:.2f}s |"
                )
        else:
            md_lines.append("*No scenarios were run.*")

        md_lines.extend(
            [
                "",
                "---",
                "",
                "## Score Breakdown by Metric",
                "",
            ]
        )

        # Score breakdown
        md_lines.append("| Metric | Average Score |")
        md_lines.append("|--------|---------------|")
        for metric, score in report["score_breakdown"].items():
            metric_name = metric.replace("_", " ").title()
            md_lines.append(f"| {metric_name} | {score:.2f}/1.0 |")

        # Detailed results
        if self.results:
            md_lines.extend(
                [
                    "",
                    "---",
                    "",
                    "## Detailed Results",
                    "",
                ]
            )

            for i, result in enumerate(self.results, 1):
                status = "✅ PASS" if result.get("passed", False) else "❌ FAIL"
                md_lines.extend(
                    [
                        f"### {i}. {result.get('query', 'Unknown Query')}",
                        "",
                        f"**Status:** {status}",
                        f"**Difficulty:** {result.get('difficulty', 'unknown')}",
                        f"**Scenario ID:** {result.get('scenario_id', 'unknown')}",
                        f"**Response Time:** {result.get('response_time', 0):.2f}s",
                        "",
                    ]
                )

                if "scores" in result:
                    md_lines.append("**Scores:**")
                    for metric, score in result["scores"].items():
                        metric_name = metric.replace("_", " ").title()
                        md_lines.append(f"- {metric_name}: {score:.2f}/1.0")
                    md_lines.append("")

                md_lines.extend(
                    [
                        f"**Final Score:** {result.get('final_score', 0):.2f}/1.0",
                        "",
                    ]
                )

                if "response" in result:
                    response_preview = result["response"][:500]
                    if len(result["response"]) > 500:
                        response_preview += "..."
                    md_lines.extend(
                        [
                            "**Response:**",
                            "```",
                            response_preview,
                            "```",
                            "",
                        ]
                    )

                if "tool_calls" in result and result["tool_calls"]:
                    md_lines.extend(
                        [
                            f"**Tools Used:** {', '.join(result['tool_calls'])}",
                            "",
                        ]
                    )

                if "error" in result:
                    md_lines.extend(
                        [
                            "**Error:**",
                            "```",
                            result["error"],
                            "```",
                            "",
                        ]
                    )

                md_lines.append("---")
                md_lines.append("")

        # Failures section
        if report["failures"]:
            md_lines.extend(
                [
                    "## Failed Scenarios",
                    "",
                ]
            )

            for failure in report["failures"]:
                md_lines.extend(
                    [
                        f"### {failure['query']}",
                        f"- **ID:** {failure['id']}",
                        f"- **Difficulty:** {failure.get('difficulty', 'unknown')}",
                        f"- **Score:** {failure['final_score']:.2f}/1.0",
                    ]
                )
                if "error" in failure:
                    md_lines.append(f"- **Error:** {failure['error']}")
                md_lines.append("")

        # Recommendations
        md_lines.extend(
            [
                "---",
                "",
                "## Recommendations",
                "",
            ]
        )

        if summary["total_scenarios"] == 0:
            md_lines.append(
                "- No scenarios were run. Generate scenarios using `test_complex_scenarios.py`"
            )
        elif summary["pass_rate"] < 0.70:
            md_lines.extend(
                [
                    "- **Critical:** Pass rate is below acceptable threshold (70%)",
                    "- Review failed scenarios and improve tool selection logic",
                    "- Check LLM responses for accuracy and completeness",
                    "- Consider improving tool descriptions and examples",
                ]
            )
        elif summary["pass_rate"] < 0.85:
            md_lines.extend(
                [
                    "- Pass rate is good but could be improved",
                    "- Focus on scenarios with low scores",
                    "- Review tool selection accuracy",
                    "- Optimize response times for better user experience",
                ]
            )
        else:
            md_lines.extend(
                [
                    "- Excellent performance!",
                    "- Continue monitoring for regression",
                    "- Consider adding more complex scenarios to test edge cases",
                ]
            )

        if summary["avg_response_time"] > 5.0:
            md_lines.append(
                "- **Performance:** Average response time is high. Consider optimizing queries or caching."
            )

        md_lines.extend(
            [
                "",
                "---",
                "",
                f"*Report generated by test_complex_scenarios_runner.py*",
                f"*For detailed JSON data, see the corresponding complex_results_{timestamp}.json file*",
            ]
        )

        return "\n".join(md_lines)


# Main execution
if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser(description="Run complex scenario tests")
    parser.add_argument(
        "--difficulty",
        choices=["easy", "medium", "hard"],
        help="Filter scenarios by difficulty",
    )
    parser.add_argument("--scenario-id", help="Run specific scenario by ID")

    args = parser.parse_args()

    # Get project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Load transaction data
    transactions_file = os.path.join(project_root, "data", "transactions.csv")
    try:
        df = pd.read_csv(transactions_file)
        print(f"Loaded {len(df)} transactions")
    except FileNotFoundError:
        print(f"Error: Transaction data not found at {transactions_file}")
        print("Run generate_sample.py first or ensure data/transactions.csv exists.")
        sys.exit(1)

    # Check if scenarios file exists, generate if missing
    scenarios_file = os.path.join(
        project_root, "test_results", "complex_scenarios.json"
    )
    if not os.path.exists(scenarios_file):
        print("\n" + "=" * 80)
        print("Scenarios file not found. Generating scenarios...")
        print("=" * 80)
        try:
            # Import and use ComplexTestScenarios to generate scenarios
            sys.path.insert(0, os.path.join(project_root, "test_results"))
            from test_complex_scenarios import ComplexTestScenarios

            scenario_gen = ComplexTestScenarios(df)
            scenarios = scenario_gen.export_test_suite(filename=scenarios_file)
            print(f"✓ Generated {len(scenarios)} scenarios")

            # Also generate evaluation framework if missing
            framework_file = os.path.join(
                project_root, "test_results", "evaluation_framework.json"
            )
            if (
                not os.path.exists(framework_file)
                or os.path.getsize(framework_file) == 0
            ):
                framework = scenario_gen.create_evaluation_framework()
                with open(framework_file, "w") as f:
                    json.dump(framework, f, indent=2)
                print(f"✓ Generated evaluation framework")
        except Exception as e:
            print(f"Warning: Could not auto-generate scenarios: {e}")
            print("You can manually generate scenarios by running:")
            print("  python test_results/test_complex_scenarios.py")
            print("\nContinuing with empty scenarios list...")

    # Initialize agent with data
    try:
        agent = FinancialAgent()
        transactions = df.to_dict("records")
        agent.vector_store.add_transactions(transactions)
    except Exception as e:
        error_msg = str(e)
        if "401" in error_msg or "Unauthorized" in error_msg or "API key" in error_msg:
            print("\n" + "=" * 80)
            print("❌ QDRANT AUTHENTICATION ERROR")
            print("=" * 80)
            print(
                "\nThe Qdrant connection requires authentication but the API key is missing or incorrect."
            )
            print("\nPossible solutions:")
            print("1. For LOCAL Qdrant (no auth needed):")
            print("   - Remove QDRANT_API_KEY from .env file")
            print("   - Keep only: QDRANT_URL=http://localhost:6333")
            print("   - Or remove both to use default localhost:6333")
            print("\n2. For REMOTE Qdrant Cloud:")
            print("   - Ensure QDRANT_API_KEY is set correctly in .env")
            print("   - Ensure QDRANT_URL points to your Qdrant Cloud instance")
            print("   - Format: QDRANT_URL=https://your-cluster-id.qdrant.io")
            print("\n3. Check if Qdrant is running:")
            print("   - Local: docker run -p 6333:6333 qdrant/qdrant")
            print("   - Or check your remote Qdrant instance status")
            print("\n" + "=" * 80)
        else:
            print(f"\n❌ Error initializing agent: {error_msg}")
            print("\nTroubleshooting:")
            print("- Ensure Qdrant is running (local or remote)")
            print("- Check your .env file configuration")
            print("- Verify network connectivity to Qdrant instance")
        sys.exit(1)

    # Run evaluator
    evaluator = ComplexScenarioEvaluator(agent)

    if args.scenario_id:
        # Run single scenario
        scenario = next(
            (s for s in evaluator.scenarios if s["id"] == args.scenario_id), None
        )
        if scenario:
            evaluator.evaluate_single_scenario(scenario)
            json_file, md_file = evaluator.export_results()
        else:
            print(f"Scenario {args.scenario_id} not found")
            sys.exit(1)
    else:
        # Run all or filtered scenarios
        evaluator.run_all_scenarios(difficulty_filter=args.difficulty)
        json_file, md_file = evaluator.export_results()

    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)
