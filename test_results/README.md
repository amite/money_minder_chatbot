# Response Quality Testing

This directory contains test results and quality reports for the Financial Agent.

## Running Tests

To run the response quality tests:

```bash
python test_response_quality.py
```

## Test Coverage

The test suite includes 15 diverse questions covering:

1. **Category Analysis** (3 questions)
   - Simple category queries
   - Category queries with date ranges

2. **Merchant Analysis** (5 questions)
   - Simple merchant queries
   - Merchant queries with category grouping
   - Merchant queries with date ranges

3. **Spending Summary** (3 questions)
   - Last month summary
   - All-time summary
   - Last 3 months summary

4. **Search Queries** (2 questions)
   - Semantic search for specific items
   - Merchant-specific searches

5. **Complex Queries** (2 questions)
   - Multi-parameter queries combining merchant, category, and date

## Output Files

Each test run generates:

1. **`test_results_YYYYMMDD_HHMMSS.json`** - Complete test data in JSON format
   - All responses, timing, tool usage, errors
   - Suitable for programmatic analysis

2. **`quality_report_YYYYMMDD_HHMMSS.md`** - Human-readable quality report
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

