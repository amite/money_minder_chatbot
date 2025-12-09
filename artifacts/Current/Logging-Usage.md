# Logging Usage Guide

## Overview

The Money Minder Chatbot now includes comprehensive structured logging for all user queries, server responses, tool execution, and errors. All logs are in JSON format for easy parsing and analysis.

## Log Files

Logs are stored in the `logs/` directory:

- `logs/app.log` - Main application log (all events)
- `logs/errors.log` - Error-only log file

## Log Structure

All logs are in JSON format with the following structure:

```json
{
  "timestamp": "2025-12-09T10:30:45.123456Z",
  "level": "INFO",
  "logger": "money_minder",
  "message": "User query received",
  "event_type": "user_query",
  "session_id": "abc-123-def-456",
  "query_id": "xyz-789-uvw-012",
  "data": {
    "query": "Find my coffee purchases",
    "query_length": 25
  }
}
```

## Event Types

### 1. `user_query`
Logged when a user submits a query.

**Data fields:**
- `query`: The user's query text
- `query_length`: Length of the query

### 2. `query_processing_start`
Logged when query processing begins.

**Data fields:**
- `query`: The user's query text

### 3. `tool_execution_start`
Logged when a tool starts executing.

**Data fields:**
- `tool_name`: Name of the tool being executed
- `tool_args`: Arguments passed to the tool

### 4. `tool_execution_end`
Logged when a tool finishes executing.

**Data fields:**
- `tool_name`: Name of the tool
- `execution_time`: Time taken in seconds
- `success`: Whether execution was successful
- `result_summary`: Summary of the result (truncated if long)

### 5. `response_generated`
Logged when the LLM generates a response.

**Data fields:**
- `query`: Original user query
- `response`: Generated response text
- `response_length`: Length of the response
- `response_time`: Time taken to generate response (seconds)
- `tool_used`: Tool that was used (if any)

### 6. `response_displayed`
Logged when response is displayed to the user.

**Data fields:**
- `response_length`: Length of the response

### 7. `error`
Logged when an error occurs.

**Data fields:**
- `error_type`: Type of the error
- `error_message`: Error message
- `context`: Additional context about where the error occurred
- `exception`: Full exception details including traceback

### 8. `performance_metric`
Logged for performance tracking.

**Data fields:**
- `metric_name`: Name of the metric
- `value`: Metric value
- `unit`: Unit of measurement

## Configuration

Logging can be configured via environment variables:

```bash
# Log directory (default: logs)
export LOG_DIR=logs

# Log file name (default: app.log)
export LOG_FILE=app.log

# Log level (default: INFO)
export LOG_LEVEL=INFO

# Enable/disable console logging (default: true)
export LOG_TO_CONSOLE=true

# Enable/disable file logging (default: true)
export LOG_TO_FILE=true

# Log rotation size in MB (default: 10)
export LOG_ROTATION_SIZE=10

# Log retention in days (default: 30)
export LOG_RETENTION_DAYS=30
```

## Log Analysis Examples

### Find all queries containing "coffee"
```bash
grep -i "coffee" logs/app.log | jq -r '.data.query'
```

### Count queries by event type
```bash
cat logs/app.log | jq -r '.event_type' | sort | uniq -c
```

### Find slow responses (>5 seconds)
```bash
cat logs/app.log | jq 'select(.event_type == "response_generated" and .data.response_time > 5)'
```

### Find all errors
```bash
cat logs/errors.log | jq 'select(.level == "ERROR")'
```

### Group errors by type
```bash
cat logs/errors.log | jq -r '.data.error_type' | sort | uniq -c
```

### Average response time
```bash
cat logs/app.log | jq 'select(.event_type == "response_generated") | .data.response_time' | awk '{sum+=$1; count++} END {print sum/count}'
```

### Track a specific query through the system
```bash
QUERY_ID="your-query-id"
cat logs/app.log | jq "select(.query_id == \"$QUERY_ID\")"
```

### Find all tool executions for a specific tool
```bash
cat logs/app.log | jq 'select(.event_type == "tool_execution_start" and .data.tool_name == "search_transactions")'
```

## Session Tracking

Each Streamlit session gets a unique `session_id` that persists for the duration of the session. Each query within a session gets a unique `query_id`. This allows you to:

- Track all queries from a single user session
- Correlate queries with their responses and tool executions
- Debug issues by following a query through the entire processing pipeline

## Best Practices

1. **Monitor Error Logs**: Regularly check `logs/errors.log` for issues
2. **Track Performance**: Monitor `response_time` metrics to identify slow queries
3. **Analyze Query Patterns**: Use log analysis to understand common user queries
4. **Debug Issues**: Use `query_id` to trace a specific query through the system
5. **Log Rotation**: Ensure log rotation is working to prevent disk space issues

## Privacy Considerations

Currently, all user queries and responses are logged. For production use, consider:

- Adding PII redaction for sensitive data
- Implementing log filtering for sensitive queries
- Adding user consent for logging
- Complying with GDPR and other privacy regulations

