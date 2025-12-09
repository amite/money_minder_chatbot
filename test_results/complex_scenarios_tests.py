"""
15 Complex Test Scenarios for Financial Agent Robustness Testing

These scenarios test:
- Multi-step reasoning
- Comparative analysis
- Temporal patterns
- Edge cases
- Ambiguous queries
- Complex aggregations
"""

from typing import List, Dict, Any, Optional
import pandas as pd
from datetime import datetime
import json


class ComplexTestScenarios:
    """Generate complex test scenarios for robust agent evaluation"""

    def __init__(self, transactions_df: pd.DataFrame):
        self.df = transactions_df.copy()
        self.df["date"] = pd.to_datetime(self.df["date"])
        self.df["amount"] = pd.to_numeric(self.df["amount"])

    def generate_all_scenarios(self) -> List[Dict[str, Any]]:
        """Generate all 15 complex test scenarios"""

        scenarios = [
            # 1. Multi-step comparative analysis
            {
                "id": "complex_001",
                "query": "Which category did I spend more on in February: food or shopping?",
                "difficulty": "hard",
                "requires_tools": ["analyze_by_category"],  # Need to call twice
                "requires_reasoning": "comparison",
                "expected_steps": [
                    "Get food spending in February",
                    "Get shopping spending in February",
                    "Compare totals",
                    "Answer which is higher",
                ],
                "ground_truth": self._calculate_category_comparison(
                    "food", "shopping", "2024-02-01", "2024-02-29"
                ),
                "evaluation_criteria": {
                    "tool_calls": "Must call analyze_by_category twice with correct dates",
                    "comparison": "Must explicitly compare the two amounts",
                    "answer": "Must state which category is higher",
                },
            },
            # 2. Trend analysis across time periods
            {
                "id": "complex_002",
                "query": "Did my food spending increase or decrease from January to February?",
                "difficulty": "hard",
                "requires_tools": ["analyze_by_category"],
                "requires_reasoning": "temporal_comparison",
                "expected_steps": [
                    "Get food spending in January",
                    "Get food spending in February",
                    "Calculate change",
                    "Determine trend (increase/decrease/same)",
                ],
                "ground_truth": self._calculate_monthly_trend(
                    "food", "2024-01", "2024-02"
                ),
                "evaluation_criteria": {
                    "tool_calls": "Must call analyze_by_category twice with different date ranges",
                    "calculation": "Must calculate the difference",
                    "trend": "Must state increase/decrease with amount or percentage",
                },
            },
            # 3. Top N analysis with filtering
            {
                "id": "complex_003",
                "query": "What were my 3 largest shopping purchases at Amazon?",
                "difficulty": "medium",
                "requires_tools": ["analyze_merchant", "search_transactions"],
                "requires_reasoning": "filtering_and_ranking",
                "expected_steps": [
                    "Get all Amazon transactions",
                    "Filter to shopping category",
                    "Sort by amount descending",
                    "Return top 3",
                ],
                "ground_truth": self._get_top_n_merchant_category(
                    "Amazon", "shopping", 3
                ),
                "evaluation_criteria": {
                    "filtering": "Must filter to shopping category only",
                    "ranking": "Must return exactly 3 transactions",
                    "ordering": "Must be in descending order by amount",
                },
            },
            # 4. Percentage/proportion analysis
            {
                "id": "complex_004",
                "query": "What percentage of my total spending went to subscriptions?",
                "difficulty": "hard",
                "requires_tools": ["get_spending_summary", "search_transactions"],
                "requires_reasoning": "calculation",
                "expected_steps": [
                    "Identify subscription merchants (Netflix, Spotify, etc.)",
                    "Get total spending",
                    "Get subscription spending",
                    "Calculate percentage",
                ],
                "ground_truth": self._calculate_subscription_percentage(),
                "evaluation_criteria": {
                    "identification": "Must correctly identify subscription merchants",
                    "calculation": "Must calculate percentage correctly",
                    "format": "Should present as percentage (e.g., 15.3%)",
                },
            },
            # 5. Average with outlier consideration
            {
                "id": "complex_005",
                "query": "What's my average grocery spending per week, excluding any trips over $100?",
                "difficulty": "hard",
                "requires_tools": ["search_transactions", "analyze_by_category"],
                "requires_reasoning": "filtering_and_aggregation",
                "expected_steps": [
                    "Identify grocery merchants (Whole Foods, Walmart, Target)",
                    "Filter transactions under $100",
                    "Calculate weekly average",
                ],
                "ground_truth": self._calculate_filtered_weekly_average(
                    ["Whole Foods", "Walmart", "Target"], max_amount=100
                ),
                "evaluation_criteria": {
                    "filtering": "Must exclude transactions over $100",
                    "time_grouping": "Must calculate weekly average correctly",
                    "accuracy": "Answer within $5 of ground truth",
                },
            },
            # 6. Multi-merchant aggregation
            {
                "id": "complex_006",
                "query": "How much did I spend at coffee shops (Starbucks and Dunkin) in total?",
                "difficulty": "medium",
                "requires_tools": ["analyze_merchant"],
                "requires_reasoning": "aggregation",
                "expected_steps": [
                    "Get Starbucks spending",
                    "Get Dunkin spending",
                    "Sum both amounts",
                ],
                "ground_truth": self._calculate_multi_merchant_total(
                    ["Starbucks", "Dunkin"]
                ),
                "evaluation_criteria": {
                    "tool_calls": "Must call analyze_merchant for both merchants",
                    "aggregation": "Must sum the totals correctly",
                    "completeness": "Must include both merchants",
                },
            },
            # 7. Conditional analysis
            {
                "id": "complex_007",
                "query": "Show me all entertainment expenses over $20",
                "difficulty": "medium",
                "requires_tools": ["analyze_by_category"],
                "requires_reasoning": "filtering",
                "expected_steps": [
                    "Get all entertainment transactions",
                    "Filter to amounts > $20",
                    "Return filtered list",
                ],
                "ground_truth": self._get_category_above_threshold("entertainment", 20),
                "evaluation_criteria": {
                    "filtering": "Must filter to entertainment category",
                    "threshold": "Must only show transactions > $20",
                    "completeness": "Must return all matching transactions",
                },
            },
            # 8. Frequency analysis
            {
                "id": "complex_008",
                "query": "How many times per week do I go to Starbucks on average?",
                "difficulty": "hard",
                "requires_tools": ["analyze_merchant"],
                "requires_reasoning": "frequency_calculation",
                "expected_steps": [
                    "Get all Starbucks transactions",
                    "Calculate date range in weeks",
                    "Divide transaction count by weeks",
                ],
                "ground_truth": self._calculate_visit_frequency("Starbucks"),
                "evaluation_criteria": {
                    "calculation": "Must calculate average per week",
                    "accuracy": "Answer within 0.5 visits/week",
                    "format": "Should present as 'X times per week'",
                },
            },
            # 9. Category within merchant analysis
            {
                "id": "complex_009",
                "query": "At Amazon, did I spend more on shopping or entertainment?",
                "difficulty": "medium",
                "requires_tools": ["analyze_merchant"],
                "requires_reasoning": "comparison",
                "expected_steps": [
                    "Get Amazon transactions grouped by category",
                    "Compare shopping vs entertainment totals",
                    "State which is higher",
                ],
                "ground_truth": self._compare_merchant_categories(
                    "Amazon", ["shopping", "entertainment"]
                ),
                "evaluation_criteria": {
                    "tool_usage": "Should use analyze_merchant with group_by_category=true",
                    "comparison": "Must compare the two categories",
                    "answer": "Must state which category is higher",
                },
            },
            # 10. Negative/absence detection
            {
                "id": "complex_010",
                "query": "Did I make any purchases at Target in January?",
                "difficulty": "easy",
                "requires_tools": ["analyze_merchant"],
                "requires_reasoning": "existence_check",
                "expected_steps": [
                    "Get Target transactions in January",
                    "Check if any exist",
                    "Return yes/no answer",
                ],
                "ground_truth": self._check_merchant_in_period(
                    "Target", "2024-01-01", "2024-01-31"
                ),
                "evaluation_criteria": {
                    "date_filtering": "Must filter to January only",
                    "existence": "Must correctly state yes/no",
                    "detail": "If yes, should provide count or amount",
                },
            },
            # 11. Budget/threshold analysis
            {
                "id": "complex_011",
                "query": "Which months did I spend over $300 on food?",
                "difficulty": "hard",
                "requires_tools": ["analyze_by_category"],
                "requires_reasoning": "temporal_filtering",
                "expected_steps": [
                    "Get food spending for each month",
                    "Filter months where total > $300",
                    "Return list of months",
                ],
                "ground_truth": self._get_months_above_threshold("food", 300),
                "evaluation_criteria": {
                    "grouping": "Must group by month",
                    "filtering": "Must apply $300 threshold",
                    "completeness": "Must check all months in dataset",
                },
            },
            # 12. Rate/ratio analysis
            {
                "id": "complex_012",
                "query": "What's the ratio of my dining out expenses to grocery expenses?",
                "difficulty": "hard",
                "requires_tools": ["search_transactions", "analyze_by_category"],
                "requires_reasoning": "calculation",
                "expected_steps": [
                    "Identify dining merchants (restaurants vs grocery stores)",
                    "Calculate dining total",
                    "Calculate grocery total",
                    "Calculate ratio",
                ],
                "ground_truth": self._calculate_dining_to_grocery_ratio(),
                "evaluation_criteria": {
                    "categorization": "Must correctly identify dining vs grocery",
                    "calculation": "Must calculate ratio correctly",
                    "format": "Should present as ratio (e.g., '1.5:1' or '1.5x')",
                },
            },
            # 13. Ambiguous temporal reference
            {
                "id": "complex_013",
                "query": "How much have I spent on health this quarter?",
                "difficulty": "medium",
                "requires_tools": ["analyze_by_category"],
                "requires_reasoning": "temporal_interpretation",
                "expected_steps": [
                    "Interpret 'this quarter' (Q1 2024: Jan-Mar)",
                    "Get health spending for Q1",
                    "Return total",
                ],
                "ground_truth": self._calculate_quarter_spending("health", 1, 2024),
                "evaluation_criteria": {
                    "interpretation": "Must correctly interpret quarter (Jan-Mar)",
                    "date_range": "Must use correct date range",
                    "calculation": "Must sum correctly",
                },
            },
            # 14. Complex merchant pattern
            {
                "id": "complex_014",
                "query": "Show me all gas station transactions where I also bought food",
                "difficulty": "hard",
                "requires_tools": ["search_transactions", "analyze_merchant"],
                "requires_reasoning": "pattern_matching",
                "expected_steps": [
                    "Identify gas stations (Shell, Exxon)",
                    "Get transactions from these merchants",
                    "Filter to those in food category (convenience store purchases)",
                    "Return matching transactions",
                ],
                "ground_truth": self._get_gas_station_food_purchases(),
                "evaluation_criteria": {
                    "merchant_identification": "Must identify gas station merchants",
                    "category_filtering": "Must filter to food category",
                    "accuracy": "Must return only matching transactions",
                },
            },
            # 15. Multi-constraint query
            {
                "id": "complex_015",
                "query": "Find all shopping transactions over $50 at either Amazon or Target in February",
                "difficulty": "hard",
                "requires_tools": ["analyze_merchant"],
                "requires_reasoning": "multi_constraint_filtering",
                "expected_steps": [
                    "Get Amazon transactions in February",
                    "Get Target transactions in February",
                    "Filter both to shopping category",
                    "Filter both to amount > $50",
                    "Combine and return results",
                ],
                "ground_truth": self._get_multi_constraint_transactions(
                    merchants=["Amazon", "Target"],
                    category="shopping",
                    min_amount=50,
                    start_date="2024-02-01",
                    end_date="2024-02-29",
                ),
                "evaluation_criteria": {
                    "merchant_filtering": "Must include both merchants",
                    "category_filtering": "Must filter to shopping only",
                    "amount_filtering": "Must filter to > $50",
                    "date_filtering": "Must filter to February only",
                },
            },
        ]

        return scenarios

    # Helper methods for ground truth calculations

    def _calculate_category_comparison(
        self, cat1: str, cat2: str, start_date: str, end_date: str
    ) -> Dict:
        """Compare two categories in date range"""
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        filtered = self.df[(self.df["date"] >= start) & (self.df["date"] <= end)]

        cat1_total = filtered[filtered["category"] == cat1]["amount"].sum()
        cat2_total = filtered[filtered["category"] == cat2]["amount"].sum()

        return {
            cat1: float(cat1_total),
            cat2: float(cat2_total),
            "higher": cat1 if cat1_total > cat2_total else cat2,
            "difference": float(abs(cat1_total - cat2_total)),
        }

    def _calculate_monthly_trend(self, category: str, month1: str, month2: str) -> Dict:
        """Calculate trend between two months"""
        df1 = self.df[self.df["date"].dt.strftime("%Y-%m") == month1]
        df2 = self.df[self.df["date"].dt.strftime("%Y-%m") == month2]

        total1 = df1[df1["category"] == category]["amount"].sum()
        total2 = df2[df2["category"] == category]["amount"].sum()

        change = total2 - total1
        pct_change = (change / total1 * 100) if total1 > 0 else 0

        return {
            month1: float(total1),
            month2: float(total2),
            "change": float(change),
            "percent_change": float(pct_change),
            "trend": (
                "increase" if change > 0 else "decrease" if change < 0 else "no change"
            ),
        }

    def _get_top_n_merchant_category(
        self, merchant: str, category: str, n: int
    ) -> Dict:
        """Get top N transactions for merchant in category"""
        filtered_df = self.df[
            (self.df["merchant"] == merchant) & (self.df["category"] == category)
        ]
        filtered = filtered_df.sort_values(by="amount", ascending=False).head(n)  # type: ignore

        return {
            "count": len(filtered),
            "transactions": [
                {
                    "date": (
                        str(pd.to_datetime(row["date"]).date())  # type: ignore
                        if not pd.isna(row["date"])  # type: ignore
                        else ""
                    ),
                    "amount": float(row["amount"]),
                    "description": str(row["description"]),
                }
                for _, row in filtered.iterrows()
            ],
        }

    def _calculate_subscription_percentage(self) -> Dict:
        """Calculate subscription percentage of total spending"""
        subscription_merchants = [
            "Netflix",
            "Spotify",
            "YouTube Premium",
            "Disney+",
            "Planet Fitness",
            "Equinox",
        ]

        subscription_total = self.df[self.df["merchant"].isin(subscription_merchants)][
            "amount"
        ].sum()

        total_spending = self.df["amount"].sum()
        percentage = (
            (subscription_total / total_spending * 100) if total_spending > 0 else 0
        )

        return {
            "subscription_total": float(subscription_total),
            "total_spending": float(total_spending),
            "percentage": float(percentage),
        }

    def _calculate_filtered_weekly_average(
        self, merchants: List[str], max_amount: float
    ) -> Dict:
        """Calculate weekly average excluding outliers"""
        filtered = self.df[
            (self.df["merchant"].isin(merchants)) & (self.df["amount"] <= max_amount)
        ]

        if filtered.empty:
            return {"weekly_average": 0.0, "total_weeks": 0}

        date_range = (filtered["date"].max() - filtered["date"].min()).days
        weeks = max(1, date_range / 7)

        weekly_avg = filtered["amount"].sum() / weeks

        return {
            "weekly_average": float(weekly_avg),
            "total_weeks": float(weeks),
            "transaction_count": len(filtered),
            "excluded_count": len(
                self.df[
                    (self.df["merchant"].isin(merchants))
                    & (self.df["amount"] > max_amount)
                ]
            ),
        }

    def _calculate_multi_merchant_total(self, merchants: List[str]) -> Dict:
        """Calculate total across multiple merchants"""
        totals = {}
        for merchant in merchants:
            merchant_total = self.df[self.df["merchant"] == merchant]["amount"].sum()
            totals[merchant] = float(merchant_total)

        return {"merchants": totals, "combined_total": float(sum(totals.values()))}

    def _get_category_above_threshold(self, category: str, threshold: float) -> Dict:
        """Get transactions in category above threshold"""
        filtered = self.df[
            (self.df["category"] == category) & (self.df["amount"] > threshold)
        ]

        return {
            "count": len(filtered),
            "total": float(filtered["amount"].sum()),
            "transactions": [
                {
                    "date": (
                        str(pd.to_datetime(row["date"]).date())  # type: ignore
                        if not pd.isna(row["date"])  # type: ignore
                        else ""
                    ),
                    "merchant": str(row["merchant"]),
                    "amount": float(row["amount"]),
                }
                for _, row in filtered.iterrows()
            ],
        }

    def _calculate_visit_frequency(self, merchant: str) -> Dict:
        """Calculate average visits per week"""
        merchant_df = self.df[self.df["merchant"] == merchant]

        if merchant_df.empty:
            return {"visits_per_week": 0.0}

        date_range = (merchant_df["date"].max() - merchant_df["date"].min()).days
        weeks = max(1, date_range / 7)

        visits_per_week = len(merchant_df) / weeks

        return {
            "total_visits": len(merchant_df),
            "total_weeks": float(weeks),
            "visits_per_week": float(visits_per_week),
        }

    def _compare_merchant_categories(
        self, merchant: str, categories: List[str]
    ) -> Dict:
        """Compare categories within a merchant"""
        merchant_df = self.df[self.df["merchant"] == merchant]

        totals = {}
        for cat in categories:
            cat_total = merchant_df[merchant_df["category"] == cat]["amount"].sum()
            totals[cat] = float(cat_total)

        higher = max(totals, key=lambda x: totals[x]) if totals else None

        return {"categories": totals, "higher": higher}

    def _check_merchant_in_period(
        self, merchant: str, start_date: str, end_date: str
    ) -> Dict:
        """Check if merchant has transactions in period"""
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        filtered = self.df[
            (self.df["merchant"] == merchant)
            & (self.df["date"] >= start)
            & (self.df["date"] <= end)
        ]

        return {
            "exists": len(filtered) > 0,
            "count": len(filtered),
            "total": float(filtered["amount"].sum()) if not filtered.empty else 0.0,
        }

    def _get_months_above_threshold(self, category: str, threshold: float) -> Dict:
        """Get months where category spending exceeded threshold"""
        cat_df = self.df[self.df["category"] == category].copy()
        date_series: pd.Series = pd.to_datetime(cat_df["date"])  # type: ignore
        cat_df["month"] = date_series.dt.strftime("%Y-%m")  # type: ignore

        monthly: pd.Series = cat_df.groupby("month")["amount"].sum()  # type: ignore
        above_threshold: pd.Series = monthly[monthly > threshold]  # type: ignore

        return {
            "months": above_threshold.index.tolist(),  # type: ignore
            "amounts": {
                str(month): float(amt) for month, amt in above_threshold.items()  # type: ignore
            },
        }

    def _calculate_dining_to_grocery_ratio(self) -> Dict:
        """Calculate dining vs grocery ratio"""
        # Dining merchants (restaurants)
        dining_merchants = ["Chipotle", "McDonald's", "Uber"]  # Uber Eats
        # Grocery merchants
        grocery_merchants = ["Whole Foods", "Walmart", "Target"]

        dining_total = self.df[
            self.df["merchant"].isin(dining_merchants) & (self.df["category"] == "food")
        ]["amount"].sum()

        grocery_total = self.df[
            self.df["merchant"].isin(grocery_merchants)
            & (self.df["category"] == "food")
        ]["amount"].sum()

        ratio = dining_total / grocery_total if grocery_total > 0 else 0

        return {
            "dining_total": float(dining_total),
            "grocery_total": float(grocery_total),
            "ratio": float(ratio),
        }

    def _calculate_quarter_spending(
        self, category: str, quarter: int, year: int
    ) -> Dict:
        """Calculate spending for a quarter"""
        quarter_months = {
            1: ["01", "02", "03"],
            2: ["04", "05", "06"],
            3: ["07", "08", "09"],
            4: ["10", "11", "12"],
        }

        months = quarter_months[quarter]
        quarter_df = self.df[
            (self.df["date"].dt.year == year)
            & (self.df["date"].dt.month.isin([int(m) for m in months]))
            & (self.df["category"] == category)
        ]

        return {
            "quarter": f"Q{quarter} {year}",
            "total": float(quarter_df["amount"].sum()),
            "transaction_count": len(quarter_df),
        }

    def _get_gas_station_food_purchases(self) -> Dict:
        """Get gas station convenience store food purchases"""
        gas_stations = ["Shell", "Exxon"]

        filtered = self.df[
            (self.df["merchant"].isin(gas_stations)) & (self.df["category"] == "food")
        ]

        return {
            "count": len(filtered),
            "total": float(filtered["amount"].sum()),
            "transactions": [
                {
                    "date": (
                        str(pd.to_datetime(row["date"]).date())  # type: ignore
                        if not pd.isna(row["date"])  # type: ignore
                        else ""
                    ),
                    "merchant": str(row["merchant"]),
                    "amount": float(row["amount"]),
                }
                for _, row in filtered.iterrows()
            ],
        }

    def _get_multi_constraint_transactions(
        self,
        merchants: List[str],
        category: str,
        min_amount: float,
        start_date: str,
        end_date: str,
    ) -> Dict:
        """Get transactions matching multiple constraints"""
        start = pd.to_datetime(start_date)
        end = pd.to_datetime(end_date)

        filtered = self.df[
            (self.df["merchant"].isin(merchants))
            & (self.df["category"] == category)
            & (self.df["amount"] > min_amount)
            & (self.df["date"] >= start)
            & (self.df["date"] <= end)
        ]

        return {
            "count": len(filtered),
            "total": float(filtered["amount"].sum()),
            "transactions": [
                {
                    "date": (
                        str(pd.to_datetime(row["date"]).date())  # type: ignore
                        if not pd.isna(row["date"])  # type: ignore
                        else ""
                    ),
                    "merchant": str(row["merchant"]),
                    "amount": float(row["amount"]),
                    "description": str(row["description"]),
                }
                for _, row in filtered.iterrows()
            ],
        }

    def export_test_suite(self, filename: str = "tests/complex_scenarios.json"):
        """Export all scenarios to JSON"""
        import os

        scenarios = self.generate_all_scenarios()

        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            json.dump(scenarios, f, indent=2)

        print(f"✓ Exported {len(scenarios)} complex scenarios to {filename}")

        # Print summary
        print(f"\nScenario Difficulty Distribution:")
        difficulties = {}
        for s in scenarios:
            diff = s["difficulty"]
            difficulties[diff] = difficulties.get(diff, 0) + 1
        for diff, count in difficulties.items():
            print(f"  {diff}: {count}")

        return scenarios

    def create_evaluation_framework(self) -> Dict:
        """Create evaluation framework for complex scenarios"""
        return {
            "scoring": {
                "tool_selection": {
                    "weight": 0.25,
                    "criteria": "Correct tools selected for task",
                },
                "reasoning": {
                    "weight": 0.25,
                    "criteria": "Proper multi-step reasoning demonstrated",
                },
                "accuracy": {
                    "weight": 0.30,
                    "criteria": "Answer matches ground truth (with tolerance)",
                },
                "completeness": {
                    "weight": 0.20,
                    "criteria": "All aspects of query addressed",
                },
            },
            "difficulty_multipliers": {"easy": 1.0, "medium": 1.5, "hard": 2.0},
            "pass_thresholds": {
                "excellent": 0.90,
                "good": 0.75,
                "acceptable": 0.60,
                "failing": 0.60,
            },
        }


# Usage and testing
if __name__ == "__main__":
    import sys

    # Load transaction data
    try:
        df = pd.read_csv("data/transactions.csv")
        print(f"Loaded {len(df)} transactions")
    except FileNotFoundError:
        print("Error: Please generate transaction data first using:")
        print("  python generate_sample.py")
        sys.exit(1)

    # Generate complex scenarios
    scenario_gen = ComplexTestScenarios(df)
    scenarios = scenario_gen.export_test_suite()

    # Export evaluation framework
    framework = scenario_gen.create_evaluation_framework()
    with open("tests/evaluation_framework.json", "w") as f:
        json.dump(framework, f, indent=2)
    print("✓ Exported evaluation framework")

    # Print sample scenarios
    print("\n" + "=" * 80)
    print("SAMPLE COMPLEX SCENARIOS")
    print("=" * 80)

    for i, scenario in enumerate(scenarios[:3], 1):
        print(f"\n{i}. {scenario['query']}")
        print(f"   Difficulty: {scenario['difficulty']}")
        print(f"   Requires: {', '.join(scenario['requires_tools'])}")
        print(f"   Reasoning: {scenario['requires_reasoning']}")
        print(f"   Ground Truth: {json.dumps(scenario['ground_truth'], indent=6)}")

    print("\n" + "=" * 80)
    print(f"Total scenarios generated: {len(scenarios)}")
    print("Run these scenarios using: python test_complex_scenarios.py")
    print("=" * 80)
