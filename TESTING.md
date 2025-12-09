# Response Quality Testing Guide

## Quick Start

Run the response quality test suite:

```bash
python test_response_quality.py
```

## Prerequisites

1. **Ollama** must be running with the model:
   ```bash
   ollama pull llama3.1:8b-instruct-q4_K_M
   ```

2. **Qdrant** vector store must be running:
   - Local: `qdrant` (default localhost:6333)
   - Or set `QDRANT_URL` and `QDRANT_API_KEY` environment variables

3. **Transaction Data**: `data/transactions.csv` must exist

## What Gets Tested

The test suite includes 15 questions covering:

- ✅ Category analysis (simple and with dates)
- ✅ Merchant analysis (simple, grouped, with dates)
- ✅ Spending summaries (different time periods)
- ✅ Semantic search queries
- ✅ Complex multi-parameter queries

## Output

After running, you'll get:

1. **JSON Results** (`test_results/test_results_*.json`)
   - Complete test data for programmatic analysis
   - All responses, timings, tool usage, errors

2. **Markdown Report** (`test_results/quality_report_*.md`)
   - Human-readable quality evaluation
   - Executive summary with key metrics
   - Detailed results for each question
   - Performance analysis
   - Recommendations

## Evaluating Results

### Key Metrics

- **Success Rate**: Should be >90%
- **Average Response Time**: Should be <5 seconds
- **Tool Selection Accuracy**: Correct tool should be used
- **Response Quality**: Answers should be accurate and complete

### Review Checklist

- [ ] All questions answered successfully
- [ ] Response times are reasonable (<5s average)
- [ ] Correct tools are selected for each query type
- [ ] Responses contain accurate data
- [ ] Responses are complete and address the question
- [ ] Error handling works for edge cases

## Example Output

```
======================================================================
FINANCIAL AGENT RESPONSE QUALITY TEST
======================================================================

Loading test data...
✓ Loaded 150 transactions

[1/15] Testing: How much did I spend on shopping?
Category: category_analysis
✓ Success (2.34s)
  Tool used: analyze_by_category

...

======================================================================
TEST COMPLETE
======================================================================

✓ Successful: 15/15
✓ Success Rate: 100.0%
✓ Average Response Time: 2.45s

📄 Results: test_results/test_results_20241209_143022.json
📊 Report: test_results/quality_report_20241209_143022.md
```

## Troubleshooting

### "Model not found"
- Run: `ollama pull llama3.1:8b-instruct-q4_K_M`

### "Qdrant connection error"
- Ensure Qdrant is running: `docker run -p 6333:6333 qdrant/qdrant`
- Or set `QDRANT_URL` environment variable

### "No transactions found"
- Check that `data/transactions.csv` exists
- Verify the file has the correct format

### Slow responses
- Check Ollama is running and responsive
- Verify Qdrant is accessible
- Consider using a faster model or optimizing queries

## Continuous Improvement

1. Run tests after code changes
2. Compare metrics across runs
3. Track improvements over time
4. Use results to guide optimization efforts

## Integration with Logging

All test queries are logged using the structured logger:
- Queries logged to `logs/app.log`
- Errors logged to `logs/errors.log`
- Use log analysis tools to review detailed execution traces

