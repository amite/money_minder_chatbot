Now let me create the test runner that integrates with your existing testing infrastructure:Perfect! Now let me create a summary document showing how these 15 scenarios will test your agent's robustness:## Summary

I've created **15 complex test scenarios** that will thoroughly test your agent's robustness across 8 critical dimensions:

### What Makes These Scenarios Complex:

1. **Multi-Step Reasoning** (3 scenarios)
   - Requires multiple tool calls and holding results in memory
   - Example: "Which category did I spend more on: food or shopping?" (needs 2 calls + comparison)

2. **Filtering & Ranking** (4 scenarios)
   - Multiple constraints, sorting, outlier handling
   - Example: "Top 3 shopping purchases at Amazon" or "Weekly average excluding trips over $100"

3. **Percentage & Ratios** (2 scenarios)
   - Mathematical calculations beyond simple sums
   - Example: "What percentage went to subscriptions?" or "Ratio of dining to groceries"

4. **Frequency & Patterns** (2 scenarios)
   - Temporal frequency calculations, pattern recognition
   - Example: "How many times per week do I go to Starbucks?" or "Gas stations where I bought food"

5. **Comparisons** (2 scenarios)
   - Comparing within merchants, across merchants
   - Example: "At Amazon, did I spend more on shopping or entertainment?"

6. **Existence & Negatives** (2 scenarios)
   - Yes/no questions, threshold detection, handling empty results
   - Example: "Did I make purchases at Target in January?"

7. **Temporal Intelligence** (2 scenarios)
   - Understanding "this quarter", trend analysis over time
   - Example: "Did food spending increase from January to February?"

8. **Multi-Constraint** (1 scenario)
   - Maximum complexity: 4+ constraints simultaneously
   - Example: "Shopping > $50 at Amazon OR Target in February"

### Files Created:

1. **`complex_test_scenarios.py`** - Generates 15 scenarios with ground truth
2. **`test_complex_scenarios.py`** - Test runner with evaluation framework
3. **Scenario summary document** - Explains rationale and benchmarks

### How to Use:

```bash
# 1. Generate realistic data (using improved generator)
python generate_sample.py

# 2. Generate complex scenarios
python -c "from complex_test_scenarios import ComplexTestScenarios; import pandas as pd; gen = ComplexTestScenarios(pd.read_csv('data/transactions.csv')); gen.export_test_suite()"

# 3. Run all scenarios
python test_results/test_complex_scenarios.py

# 4. Or run by difficulty
python test_results/test_complex_scenarios.py --difficulty hard
```

### Expected Pass Rates:
- **Easy:** ≥90%
- **Medium:** ≥75%  
- **Hard:** ≥60%
- **Overall Target:** ≥70%

These scenarios will expose real weaknesses in your agent that your current 15 basic tests miss. They're designed to mirror real-world user queries that require true reasoning, not just simple tool calling!