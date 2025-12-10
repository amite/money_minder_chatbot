---
name: Fix ReAct Agent Architecture
overview: Migrate from LangChain's create_agent to LangGraph's create_react_agent with proper multi-step reasoning, implement ResponseProcessor for intelligent answer formatting, enhance system prompts, and adapt the callback system for LangGraph streaming.
todos:
  - id: create-response-processor
    content: Create response_processor.py with ResponseProcessor class from diagnosis
    status: pending
  - id: add-query-preprocessing
    content: Add preprocess_query() function to app.py for comparative query enhancement
    status: pending
  - id: update-imports
    content: Update imports in app.py to use langgraph.prebuilt.create_react_agent
    status: pending
  - id: migrate-agent-function
    content: Replace get_langchain_agent() to use create_react_agent with enhanced prompt
    status: pending
    dependencies:
      - update-imports
  - id: remove-extract-final-answer
    content: Remove extract_final_answer() function from app.py
    status: pending
    dependencies:
      - migrate-agent-function
  - id: integrate-response-processor
    content: Update process_query() to use ResponseProcessor instead of extract_final_answer
    status: pending
    dependencies:
      - create-response-processor
      - remove-extract-final-answer
  - id: adapt-callbacks
    content: Modify ToolExecutionCallback to work with LangGraph streaming events
    status: pending
    dependencies:
      - migrate-agent-function
  - id: test-implementation
    content: "Test with failing scenarios: trend analysis, comparisons, multi-merchant queries"
    status: pending
    dependencies:
      - integrate-response-processor
      - adapt-callbacks
---

# Fix ReAct Agent Architecture

## Overview

Transform the broken ReAct implementation from LangChain's basic agent to LangGraph's proper ReAct agent with intelligent response processing and multi-step reasoning capabilities.

## Core Problem

Current implementation uses `langchain.agents.create_agent` which lacks proper ReAct loop execution. The agent doesn't synthesize multi-tool results, requiring complex regex post-processing (`extract_final_answer`) to clean responses.

## Architecture Changes

### 1. Upgrade to LangGraph ReAct Agent

**Files**: [`app.py`](app.py) (lines 372-426)

Replace `create_agent` with `create_react_agent` from `langgraph.prebuilt`:

```python
from langgraph.prebuilt import create_react_agent
```

**Key Benefits**:

- Built-in ReAct loop with proper state management
- Automatic multi-tool call support
- Better message history handling
- Streaming support for real-time updates

### 2. Implement ResponseProcessor Class

**Create**: `response_processor.py`

Port the `ResponseProcessor` from diagnosis document (lines 180-371) with these capabilities:

- Extract numeric data from tool results
- Format comparative responses (A vs B)
- Format trend analysis (increase/decrease)
- Clean technical jargon from responses
- Pattern detection for query types

**Key Methods**:

- `extract_numeric_data()` - Parse JSON tool outputs
- `format_comparative_response()` - Handle "X vs Y" queries
- `should_use_comparative_format()` - Detect comparative keywords
- `process_response()` - Main orchestration

### 3. Enhanced System Prompt

**Files**: [`app.py`](app.py) (line 378)

Replace current system prompt with multi-step reasoning instructions:

**Critical Elements**:

- Explicit patterns for comparative analysis
- Examples showing: Call tool 1 → Call tool 2 → Extract values → Calculate → State answer
- Emphasis on extracting numeric `total_spent` values
- Clear "Good vs Bad" response examples
- Instructions to NOT show tool JSON or reasoning process

### 4. Query Preprocessing

**Files**: [`app.py`](app.py) - new function before `process_query`

Add `preprocess_query()` function to enhance comparative queries with explicit instructions:

```python
def preprocess_query(query: str) -> str:
    """Enhance comparative queries with explicit multi-step instructions"""
    comparative_keywords = ['vs', 'versus', 'compare', 'increase', 'decrease']
    if any(kw in query.lower() for kw in comparative_keywords):
        return f"""{query}

IMPORTANT: Call tools to get data, extract 'total_spent' from EACH result,
calculate difference, show actual amounts and difference."""
    return query
```

### 5. Adapt Callback System

**Files**: [`app.py`](app.py) (lines 59-165)

Modify `ToolExecutionCallback` to work with LangGraph streaming:

- Keep existing tool tracking (for logging/metrics)
- Add LangGraph streaming event handlers
- Capture tool results from stream events
- Maintain compatibility with existing logger calls

### 6. Update Process Query Function

**Files**: [`app.py`](app.py) (lines 429-628)

**Changes**:

1. Remove `extract_final_answer` function (lines 203-369) - no longer needed
2. Use `create_react_agent` instead of `create_agent`
3. Apply `preprocess_query` to enhance user input
4. Pass enhanced query to agent
5. Stream results with callback tracking
6. Use `ResponseProcessor.process_response()` for final formatting
7. Keep existing logging and session state management

**Flow**:

```
User Query → preprocess_query → create_react_agent
  → Stream with callbacks → Extract tool results
  → ResponseProcessor.process_response → Display
```

### 7. Update Agent Initialization

**Files**: [`app.py`](app.py) (function `get_langchain_agent`)

**Changes**:

- Import from `langgraph.prebuilt` instead of `langchain.agents`
- Pass enhanced system prompt
- Return compiled graph from `create_react_agent`
- Remove unnecessary StateGraph setup (handled by prebuilt)

## Implementation Sequence

### Phase 1: Core Infrastructure

1. Create `response_processor.py` with ResponseProcessor class
2. Add query preprocessing function to `app.py`
3. Update imports in `app.py`

### Phase 2: Agent Migration

4. Replace `get_langchain_agent()` to use `create_react_agent`
5. Enhance system prompt with multi-step instructions
6. Test basic single-tool queries

### Phase 3: Response Processing

7. Remove `extract_final_answer` function
8. Integrate ResponseProcessor in `process_query`
9. Test comparative queries (should now work correctly)

### Phase 4: Callback Integration

10. Adapt ToolExecutionCallback for LangGraph streaming
11. Verify logging and metrics still work
12. Test multi-tool execution tracking

### Phase 5: Validation

13. Test against failing scenarios from diagnosis:

    - "Did food spending increase from January to February?"
    - "Which category did I spend more on: food or shopping?"
    - "Compare Amazon vs Walmart spending"

14. Verify responses show actual numbers and calculations
15. Confirm no tool JSON in final responses

## Expected Improvements

**Before** (current):

- Score: 0.21/1.0 average
- Responses: "Based on tool responses, you spent more..."
- No numeric details
- Tool JSON visible

**After** (target):

- Score: 0.6-0.8/1.0 average
- Responses: "January: $956.62, February: $977.46. Food spending increased by $20.84."
- Clear numeric comparisons
- Clean, professional answers

## Files to Modify

1. **[app.py](app.py)** - Main changes (agent, processing, prompts)
2. **response_processor.py** - New file (ResponseProcessor class)
3. **[agent.py](agent.py)** - No changes needed (tools already have good descriptions)
4. **[langchain_tools.py](langchain_tools.py)** - No changes needed (multi-step examples already present)

## Risk Mitigation

- Keep old `extract_final_answer` in git history for reference
- Test incrementally after each phase
- Maintain backward compatibility with existing logging
- LangGraph's `create_react_agent` is stable/production-ready