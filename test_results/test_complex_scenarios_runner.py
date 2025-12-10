"""
Test Runner for Complex Scenarios
Integrates with your existing test infrastructure
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Any, Optional
import pandas as pd
from agent import FinancialAgent
from langchain_ollama import ChatOllama
from langchain.agents import create_agent


class ComplexScenarioEvaluator:
    """Evaluate agent performance on complex scenarios"""

    def __init__(
        self,
        agent: FinancialAgent,
        scenarios_file: str = "tests/complex_scenarios.json",
    ):
        self.agent = agent
        self.scenarios = self._load_scenarios(scenarios_file)
        self.results = []

        # Load evaluation framework
        with open("tests/evaluation_framework.json") as f:
            self.framework = json.load(f)

    def _load_scenarios(self, filename: str) -> List[Dict]:
        """Load test scenarios"""
        with open(filename) as f:
            return json.load(f)

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
            agent_executor = create_agent(llm, tools)

            # Track tool calls
            tool_calls = []

            # Execute query
            result = agent_executor.invoke(
                {"messages": [{"role": "user", "content": scenario["query"]}]}
            )
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
            return {}

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
        """Export detailed results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"tests/complex_results_{timestamp}.json"

        report = self._generate_summary_report()

        export_data = {
            "report": report,
            "detailed_results": self.results,
            "timestamp": datetime.now().isoformat(),
        }

        with open(filename, "w") as f:
            json.dump(export_data, f, indent=2)

        print(f"\n✓ Results exported to {filename}")

        # Print summary
        self._print_summary_report(report)

        return filename

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

    # Load transaction data
    try:
        df = pd.read_csv("data/transactions.csv")
        print(f"Loaded {len(df)} transactions")
    except FileNotFoundError:
        print("Error: Transaction data not found. Run generate_sample.py first.")
        sys.exit(1)

    # Initialize agent with data
    agent = FinancialAgent()
    transactions = df.to_dict("records")
    agent.vector_store.add_transactions(transactions)

    # Run evaluator
    evaluator = ComplexScenarioEvaluator(agent)

    if args.scenario_id:
        # Run single scenario
        scenario = next(
            (s for s in evaluator.scenarios if s["id"] == args.scenario_id), None
        )
        if scenario:
            evaluator.evaluate_single_scenario(scenario)
            evaluator.export_results()
        else:
            print(f"Scenario {args.scenario_id} not found")
    else:
        # Run all or filtered scenarios
        evaluator.run_all_scenarios(difficulty_filter=args.difficulty)
        evaluator.export_results()

    print("\n" + "=" * 80)
    print("Testing complete!")
    print("=" * 80)
