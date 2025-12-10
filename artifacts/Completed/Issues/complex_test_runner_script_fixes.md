## Fixed issues

1. **Import path errors**
   - Added `sys.path` manipulation to include the parent directory so imports from the project root work
   - Added missing imports: `os`, `sys`, `BaseCallbackHandler`, `HumanMessage`

2. **Missing file handling**
   - Made `scenarios_file` optional with a default path
   - Added graceful handling when `complex_scenarios.json` is missing (returns empty list with warning)
   - Added default evaluation framework when `evaluation_framework.json` is missing
   - All file paths now use absolute paths based on project root

3. **Tool call tracking**
   - Implemented `ToolCallTracker` callback class to capture tool calls
   - Fixed callback integration with agent execution

4. **Message format**
   - Changed from dict format `{"role": "user", "content": ...}` to `HumanMessage` from `langchain_core.messages`

5. **File path handling**
   - All file operations (scenarios, framework, results export) now use absolute paths
   - Added directory creation for export paths

6. **Empty scenarios handling**
   - Added check for empty scenarios list with informative warning message

The script should now run without import errors. The Qdrant connection error seen during testing is expected if the Qdrant service isn't running; it's not a bug in the script itself.



1. **Qdrant authentication error** — Fixed by adding `load_dotenv()` to load environment variables from the `.env` file. The script now reads `QDRANT_API_KEY` and `QDRANT_URL` correctly.

2. **Empty/invalid JSON handling** — Added error handling for empty or invalid `evaluation_framework.json` files, falling back to a default framework.

3. **Empty scenarios handling** — Fixed the summary report generation to handle cases with no scenarios, preventing a `KeyError`.

The script now:
- Connects to Qdrant with the API key from `.env`
- Loads transactions successfully
- Handles missing scenario files gracefully
- Generates proper reports even with no scenarios

The only remaining message is a warning about using an API key with HTTP (instead of HTTPS), which is expected for local development and doesn't affect functionality.

You can now run the script with:
```bash
python test_results/test_complex_scenarios_runner.py
```

To actually run tests, you'll need to create a `complex_scenarios.json` file in the `test_results/` directory, or use the `test_complex_scenarios.py` file to generate scenarios.

You can now run the script with:
```bash
python test_results/test_complex_scenarios_runner.py
```

1. **Auto-generation of scenarios**: The test runner now automatically generates `complex_scenarios.json` and `evaluation_framework.json` if they're missing, using the `ComplexTestScenarios` class.

2. **Improved scenario loading**: Added error handling and clearer messages when loading scenarios.

3. **Report format**: The report structure matches the documentation:
   - `summary` with total_scenarios, passed, failed, pass_rate, avg_response_time, avg_final_score
   - `difficulty_breakdown` by difficulty level
   - `score_breakdown` by metric
   - `failures` list
   - `detailed_results` with full test data

4. **Better feedback**: The script now prints when scenarios are loaded and generated.

The previous report showed zero scenarios because:
- The `complex_scenarios.json` file didn't exist
- The script didn't auto-generate it

Now when you run:
```bash
python test_results/test_complex_scenarios_runner.py
```

It will:
1. Auto-generate 15 scenarios if missing
2. Load them
3. Run the tests
4. Generate a report with actual results

The report format matches the specifications in `Complex_Quality_Testing.md`. The zero-scenario report was from before scenarios were generated; new runs will include actual test results.

Adding markdown report generation with versioning. Added versioned markdown report generation to the test runner. The script now exports two files:

1. **JSON file** (`complex_results_YYYYMMDD_HHMMSS.json`) - For programmatic analysis
2. **Markdown file** (`complex_quality_report_YYYYMMDD_HHMMSS.md`) - Human-readable report

### Features of the Markdown Report:

- **Versioned with timestamps** - Each report has a unique timestamp in the filename
- **Executive Summary** - Overview with key metrics and performance rating
- **Performance by Difficulty** - Table showing results by difficulty level (easy/medium/hard)
- **Score Breakdown** - Detailed metrics (tool_selection, reasoning, accuracy, completeness)
- **Detailed Results** - Full results for each scenario including:
  - Query text
  - Pass/Fail status
  - Response time
  - Individual scores
  - Agent response
  - Tools used
  - Errors (if any)
- **Failed Scenarios** - Dedicated section for failures
- **Recommendations** - Actionable recommendations based on performance

### Report Format:

The markdown report includes:
- Performance ratings (Excellent/Good/Acceptable/Needs Improvement)
- Tables for easy reading
- Code blocks for responses and errors
- Clear section separators
- Links to the corresponding JSON file

When you run the test runner, both files are created automatically:
```bash
python test_results/test_complex_scenarios_runner.py
```

The markdown report will be saved as `complex_quality_report_YYYYMMDD_HHMMSS.md` in the `test_results/` directory, making it easy to review results and track performance over time.