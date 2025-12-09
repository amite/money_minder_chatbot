# Structured Logging Implementation Plan

**Created**: December 9, 2025  
**Issue**: [#1 - Add structured logging and query/response visibility](https://github.com/amite/money_minder_chatbot/issues/1)

## Overview

This document outlines the implementation plan for adding comprehensive structured logging to the Money Minder Chatbot application. The goal is to provide full visibility into user queries, server responses, tool execution, and system errors.

## Objectives

1. **Query Visibility**: Log all user queries with metadata
2. **Response Tracking**: Log all server responses with performance metrics
3. **Tool Execution**: Log tool calls, arguments, and results
4. **Error Tracking**: Comprehensive error logging with context
5. **Structured Format**: JSON logging for easy parsing and analysis
6. **Production Ready**: Log rotation, file management, and monitoring support

## Architecture

### Logging Module Structure

```
logger.py
├── StructuredLogger (main logger class)
│   ├── log_query() - User query logging
│   ├── log_response() - Server response logging
│   ├── log_tool_execution() - Tool execution logging
│   ├── log_error() - Error logging with context
│   └── log_metric() - Performance metrics
├── LogFormatter (JSON formatter)
└── LogConfig (Configuration management)
```

### Log Levels

- **DEBUG**: Detailed diagnostic information
- **INFO**: General informational messages (queries, responses)
- **WARNING**: Warning messages (tool failures, edge cases)
- **ERROR**: Error messages with full context
- **CRITICAL**: Critical errors requiring immediate attention

### Log Structure

All logs will be in JSON format with the following base structure:

```json
{
  "timestamp": "2025-12-09T10:30:45.123456Z",
  "level": "INFO",
  "event_type": "user_query",
  "session_id": "abc123",
  "data": {
    "query": "Find my coffee purchases",
    "query_length": 25
  },
  "metadata": {
    "user_agent": "...",
    "ip_address": "..."
  }
}
```

## Implementation Details

### 1. Core Logging Module (`logger.py`)

**Features**:
- Structured JSON logging
- Multiple handlers (file, console)
- Log rotation (size-based and time-based)
- Contextual logging (session IDs, request IDs)
- Performance metrics tracking

**Key Classes**:
- `StructuredLogger`: Main logger with specialized methods
- `JSONFormatter`: Custom formatter for structured logs
- `LogConfig`: Configuration management

### 2. Integration Points

#### A. User Query Logging (`app.py`)
- Log when user submits query (line ~252, ~231)
- Include: query text, timestamp, session ID
- Log query processing start

#### B. Response Logging (`app.py`)
- Log after response generation (line ~183)
- Include: response text, response time, tool used, response length
- Log response display completion

#### C. Tool Execution Logging (`app.py`)
- Log in `ToolExecutionCallback.on_tool_start()` (line ~62)
- Log in `ToolExecutionCallback.on_tool_end()` (line ~89)
- Include: tool name, arguments, execution time, result summary

#### D. Error Logging (`app.py`)
- Log in `process_query()` exception handler (line ~185)
- Log in `load_sample_data()` error handler (line ~107)
- Include: full exception, stack trace, context

### 3. Log File Management

**File Structure**:
```
logs/
├── app.log              # Current log file
├── app.log.2025-12-09   # Rotated logs (date-based)
├── errors.log           # Error-only log file
└── queries.log          # Query/response log file (optional)
```

**Rotation Strategy**:
- Size-based: Rotate when file reaches 10MB
- Time-based: Rotate daily at midnight
- Retention: Keep last 30 days of logs
- Compression: Compress rotated logs after 7 days

### 4. Log Events

#### Event Types

1. **user_query**
   - Triggered: When user submits query
   - Data: query text, session_id, timestamp

2. **query_processing_start**
   - Triggered: When query processing begins
   - Data: query_id, query_text, session_id

3. **tool_execution_start**
   - Triggered: When tool starts executing
   - Data: tool_name, tool_args, query_id

4. **tool_execution_end**
   - Triggered: When tool finishes
   - Data: tool_name, execution_time, result_summary, success

5. **response_generated**
   - Triggered: When LLM generates response
   - Data: response_text, response_time, tool_used, query_id

6. **response_displayed**
   - Triggered: When response shown to user
   - Data: response_id, display_time, query_id

7. **error**
   - Triggered: On any exception
   - Data: error_type, error_message, stack_trace, context

8. **performance_metric**
   - Triggered: For performance tracking
   - Data: metric_name, value, unit, timestamp

### 5. Configuration

**Environment Variables**:
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_DIR`: Directory for log files (default: `logs/`)
- `LOG_FILE`: Main log file name (default: `app.log`)
- `LOG_ROTATION_SIZE`: Max file size in MB (default: 10)
- `LOG_RETENTION_DAYS`: Days to keep logs (default: 30)
- `LOG_TO_CONSOLE`: Enable console logging (default: True)
- `LOG_TO_FILE`: Enable file logging (default: True)

### 6. Performance Considerations

- **Async Logging**: Use async handlers for file I/O to avoid blocking
- **Buffering**: Buffer logs and flush periodically
- **Sampling**: For high-volume scenarios, sample DEBUG logs
- **Filtering**: Allow filtering by event type or session ID

## Implementation Steps

### Phase 1: Core Infrastructure
1. ✅ Create `logger.py` with structured logging classes
2. ✅ Implement JSON formatter
3. ✅ Add log rotation and file management
4. ✅ Create logs directory structure

### Phase 2: Integration
1. ✅ Integrate logging into `app.py`
2. ✅ Add query logging
3. ✅ Add response logging
4. ✅ Add tool execution logging
5. ✅ Add error logging

### Phase 3: Enhancement
1. ✅ Add performance metrics
2. ✅ Add session tracking
3. ✅ Add request ID correlation
4. ✅ Configure log rotation

### Phase 4: Documentation
1. ✅ Document logging usage
2. ✅ Add log analysis examples
3. ✅ Create troubleshooting guide

## Usage Examples

### Basic Query Logging
```python
from logger import get_logger

logger = get_logger()
logger.log_query(
    query="Find my coffee purchases",
    session_id=st.session_state.session_id
)
```

### Response Logging
```python
start_time = time.time()
response = agent.invoke(...)
response_time = time.time() - start_time

logger.log_response(
    query="Find my coffee purchases",
    response=response,
    response_time=response_time,
    tool_used="search_transactions",
    session_id=st.session_state.session_id
)
```

### Tool Execution Logging
```python
def on_tool_start(self, serialized, input_str, **kwargs):
    logger.log_tool_execution_start(
        tool_name=serialized.get("name"),
        tool_args=input_str,
        session_id=self.session_id
    )
```

### Error Logging
```python
try:
    # ... code ...
except Exception as e:
    logger.log_error(
        error=e,
        context={"function": "process_query", "user_query": user_query},
        session_id=st.session_state.session_id
    )
```

## Log Analysis

### Query Patterns
```bash
# Find all queries containing "coffee"
grep -i "coffee" logs/app.log | jq '.data.query'

# Count queries by type
cat logs/app.log | jq -r '.event_type' | sort | uniq -c

# Find slow responses (>5 seconds)
cat logs/app.log | jq 'select(.event_type == "response_generated" and .data.response_time > 5)'
```

### Error Analysis
```bash
# Find all errors
cat logs/errors.log | jq 'select(.level == "ERROR")'

# Group errors by type
cat logs/errors.log | jq -r '.data.error_type' | sort | uniq -c
```

### Performance Metrics
```bash
# Average response time
cat logs/app.log | jq 'select(.event_type == "response_generated") | .data.response_time' | awk '{sum+=$1; count++} END {print sum/count}'
```

## Testing

### Unit Tests
- Test JSON formatting
- Test log rotation
- Test log levels
- Test error handling

### Integration Tests
- Test query logging flow
- Test response logging flow
- Test tool execution logging
- Test error logging

## Future Enhancements

1. **External Logging Services**: Integration with CloudWatch, Datadog, etc.
2. **Real-time Monitoring**: Dashboard for live log viewing
3. **Alerting**: Alerts for errors or performance issues
4. **Log Aggregation**: Centralized log collection
5. **Analytics**: Query pattern analysis and insights
6. **Privacy**: PII redaction in logs
7. **Compliance**: GDPR-compliant logging

## Success Metrics

- ✅ All user queries are logged
- ✅ All responses are logged with metrics
- ✅ All tool executions are logged
- ✅ All errors are logged with context
- ✅ Logs are structured and parseable
- ✅ Log rotation works correctly
- ✅ No performance degradation from logging

## Timeline

- **Phase 1**: 1-2 hours (Core infrastructure)
- **Phase 2**: 1-2 hours (Integration)
- **Phase 3**: 1 hour (Enhancement)
- **Phase 4**: 30 minutes (Documentation)

**Total Estimated Time**: 3.5 - 5.5 hours

