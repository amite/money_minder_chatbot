# Response Quality Testing

This directory contains test results and quality reports for the Financial Agent.

## Running Tests

### Generate realistic data first:
```bash
python generate_sample.py
```

### Generate complex scenarios with ground truth:
```bash
python -c "
from complex_test_scenarios import ComplexTestScenarios
import pandas as pd
df = pd.read_csv('data/transactions.csv')
gen = ComplexTestScenarios(df)
gen.export_test_suite()
"
```

### Run all scenarios:
```bash
python test_complex_scenarios.py
```

### Run only hard scenarios:
```bash
python test_complex_scenarios.py --difficulty hard
```

### Run specific scenario:
```bash
python test_complex_scenarios.py --scenario-id complex_001
```

## Test Coverage

The test suite includes 15 diverse questions covering:

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
   - Multi-parameter queries combining merchant, category, and date

## Output Files

Each test run generates:

1. **`complex_test_results_YYYYMMDD_HHMMSS.json`** - Complete test data in JSON format
   - All responses, timing, tool usage, errors
   - Suitable for programmatic analysis

2. **`complex_quality_report_YYYYMMDD_HHMMSS.md`** - Human-readable quality report
   - Executive summary with key metrics
   - Performance analysis
   - Detailed results for each question
   - Recommendations for improvement

## Evaluating Quality

### Key Metrics to Review

1. **Success Rate**: Percentage of questions answered successfully
2. **Tool Selection Accuracy**: Whether the correct tool was selected
3. **Response Time**: Average and distribution of response times
4. **Response Quality**: Review actual responses for accuracy and completeness

### Quality Criteria

- ✅ **Excellent**: >95% success rate, <3s average response time, correct tool selection
- ✅ **Good**: >85% success rate, <5s average response time, mostly correct tool selection
- ⚠️ **Needs Improvement**: <85% success rate, >5s response time, frequent tool mismatches

## Interpreting Results

### Response Quality Indicators

- **Accurate Data**: Responses contain correct numbers and facts
- **Complete Answers**: Responses address the full question
- **Appropriate Tool Usage**: Correct tool selected for each query type
- **Error Handling**: Graceful handling of edge cases

### Common Issues

1. **Tool Mismatches**: LLM selects wrong tool for query
   - Solution: Improve tool descriptions or add examples

2. **Slow Responses**: High response times
   - Solution: Optimize vector store queries, consider caching

3. **Incomplete Answers**: Responses miss important information
   - Solution: Review tool outputs and LLM prompts

4. **Date Parsing Errors**: Incorrect date range extraction
   - Solution: Improve date parsing logic or add validation

## Continuous Testing

For ongoing quality monitoring:

1. Run tests after significant changes
2. Compare metrics across test runs
3. Track improvements over time
4. Set up automated testing in CI/CD if possible

## Notes

- Tests require Ollama with `llama3.1:8b-instruct-q4_K_M` model
- Tests require Qdrant vector store to be running
- Test data is loaded from `data/transactions.csv`
- All queries are logged using the structured logger
- Create Comparison report with the last comparison_report_v[x]

