---
name: Fix ReAct Agent - Plan A
overview: Fix the ReAct agent WITHOUT migrating to LangGraph. Focus on prompt engineering and intelligent response processing to achieve 80% improvement in 25% of the time through enhanced system prompts, query preprocessing, and the ResponseProcessor class.
todos:
  - id: create-response-processor
    content: Create response_processor.py with ResponseProcessor class from diagnosis document (lines 180-371)
    status: completed
  - id: add-query-preprocessing
    content: Add preprocess_query() function to app.py for comparative query enhancement
    status: completed
  - id: update-system-prompt
    content: Replace system prompt in get_langchain_agent() with enhanced multi-step version
    status: completed
  - id: test-basic-functionality
    content: Test agent with simple queries to verify prompts don't break existing functionality
    status: completed
    dependencies:
      - update-system-prompt
  - id: remove-extract-final-answer
    content: Remove extract_final_answer() function from app.py (lines 203-369)
    status: completed
    dependencies:
      - test-basic-functionality
  - id: integrate-response-processor
    content: Update process_query() to use preprocess_query and ResponseProcessor
    status: completed
    dependencies:
      - create-response-processor
      - add-query-preprocessing
      - remove-extract-final-answer
  - id: test-comparative-queries
    content: "Test with failing scenarios: trend analysis, category comparisons, merchant comparisons"
    status: completed
    dependencies:
      - integrate-response-processor
  - id: verify-no-regressions
    content: Verify all logging, callbacks, and session state management still work correctly
    status: completed
    dependencies:
      - integrate-response-processor
---

# Fix ReAct Agent - Plan A (Minimal Changes)

## Overview

Fix the broken ReAct implementation by improving prompts and response processing **without** changing the core architecture. This achieves 80% of the desired improvement with minimal risk and faster implementation.

## Current Problems

1. Agent returns raw tool outputs without synthesis
2. Complex `extract_final_answer` regex tries to fix symptoms, not causes  
3. System prompt lacks explicit multi-step reasoning instructions
4. Agent doesn't extract numeric values or do comparisons

## Solution Strategy

Fix responses at the source (better prompts) + intelligent post-processing (ResponseProcessor) as safety net.

---

## Changes

### 1. Create ResponseProcessor Class

**New File**: `response_processor.py`

Port the complete `ResponseProcessor` class from the diagnosis document (lines 180-371 in critique). This class provides:

- `extract_numeric_data()` - Parse JSON tool results for numeric values
- `format_comparative_response()` - Handle "X vs Y" queries with proper formatting
- `should_use_comparative_format()` - Detect comparative keywords in queries
- `process_response()` - Main orchestration method
- `_format_period()` - Helper to format date ranges nicely

**Key capability**: Detects query patterns (comparative, trend analysis, etc.) and formats responses accordingly with actual numbers and calculations.

### 2. Add Query Preprocessing Function

**File**: [`app.py`](app.py) - Add before `process_query` function

```python
def preprocess_query(query: str) -> str:
    """Add explicit instructions for comparative queries"""
    comparative_keywords = [
        'vs', 'versus', 'compare', 'more', 'less',
        'increase', 'decrease', 'from', 'to', 'than'
    ]
    
    is_comparative = any(kw in query.lower() for kw in comparative_keywords)
    
    if is_comparative:
        enhanced = f"""{query}

CRITICAL INSTRUCTIONS:
1. Make the necessary tool calls to get data
2. Extract "total_spent" from EACH JSON result
3. Calculate the difference: value2 - value1
4. Format response as:
   Period1/Item1: $XXX.XX
   Period2/Item2: $YYY.YY
   Difference: $ZZZ.ZZ (increased/decreased/more/less)

Show me the ACTUAL NUMBERS, not just "you spent more"!"""
        return enhanced
    
    return query
```

**Purpose**: Enhances comparative queries with explicit step-by-step instructions so the agent knows exactly what to do.

### 3. Enhanced System Prompt

**File**: [`app.py`](app.py) - function `get_langchain_agent()` (line 378)

Replace the current `system_prompt` with:

```python
system_prompt = """You are a financial analysis assistant.

**CRITICAL MULTI-STEP RULES:**

For comparative queries (e.g., "X vs Y", "did X increase from A to B?"):

1. Call the tool ONCE for EACH item being compared
2. Parse the JSON result and extract "total_spent" from EACH call
3. Do the math yourself: difference = value2 - value1
4. Format your response as:
   
   Item1/Period1: $XXX.XX
   Item2/Period2: $YYY.YY
   
   [Comparison statement with actual difference]

**RESPONSE FORMAT - DO THIS:**
✅ "January food: $956.62, February food: $977.46. Spending increased by $20.84."
✅ "Food: $977.46, Shopping: $217.60. You spent $759.86 more on food."

**NEVER DO THIS:**
❌ "Based on the tool call responses, you spent more..."
❌ "The tool returned $977.46 for food and $217.60 for shopping..."
❌ Including JSON output or tool execution details

**EXTRACTION RULE:**
Every tool result is JSON. Extract the "total_spent" value like this:
Result: {"total_spent": 956.62, ...} → Use: 956.62

**CALCULATION RULE:**
You must calculate differences yourself:
- For trends: new_value - old_value = change
- For comparisons: larger_value - smaller_value = difference

Available tools:
- analyze_by_category(category, start_date, end_date) - Returns {"total_spent": X, ...}
- analyze_merchant(merchant, ...) - Returns {"total_spent": X, ...}
- search_transactions(query) - Returns list of transactions
- get_spending_summary(period) - Returns category breakdown"""
```

**Key changes**:

- Explicit multi-step instructions with examples
- Clear "Do This" vs "Never Do This" sections
- Emphasis on extracting `total_spent` and doing calculations
- Shows expected response format with real numbers

### 4. Update process_query Function

**File**: [`app.py`](app.py) - function `process_query` (lines 429-628)

**Step 4a**: Remove the `extract_final_answer` function entirely (lines 203-369)

**Step 4b**: Modify `process_query` to:

1. Import ResponseProcessor at top of function
2. Apply `preprocess_query()` to enhance user query
3. Pass enhanced query to agent (not original)
4. Use `ResponseProcessor.process_response()` instead of `extract_final_answer()`

**Key code changes**:

```python
def process_query(user_query):
    # ... existing setup code ...
    
    try:
        agent = get_langchain_agent()
        
        # NEW: Preprocess query for comparative analysis
        enhanced_query = preprocess_query(user_query)
        
        callback = ToolExecutionCallback(
            st.session_state.handler_registry,
            enhanced_query,  # Use enhanced, not original
            session_id,
            query_id,
        )

        messages = []
        for msg in st.session_state.messages:
            # ... existing message building ...
        
        # Use enhanced query in messages
        messages.append(HumanMessage(content=enhanced_query))
        
        config: RunnableConfig = {"callbacks": [callback]}
        result = agent.invoke({"messages": messages}, config=config)

        # Extract response (existing code)
        if result.get("messages"):
            last_message = result["messages"][-1]
            full_response = last_message.content if hasattr(last_message, "content") else str(last_message)
        else:
            full_response = str(result)

        # NEW: Use ResponseProcessor instead of extract_final_answer
        from response_processor import ResponseProcessor
        
        tool_results = []
        for call in callback.tool_calls:
            tool_results.append({
                'content': call.get('result', ''),
                'tool_name': call.get('name', ''),
                'args': call.get('args', {})
            })
        
        response = ResponseProcessor.process_response(
            query=user_query,  # Use original query for pattern detection
            response=full_response,
            tool_results=tool_results
        )

        # ... rest of existing code for logging, display, etc. ...
```

**What stays the same**:

- All callback tracking (no changes needed)
- All logging calls
- Session state management
- Error handling
- UI display logic

---

## Implementation Steps

### Phase 1: Create Infrastructure

1. ✅ Create `response_processor.py` with ResponseProcessor class from diagnosis
2. ✅ Add `preprocess_query()` function to `app.py`

### Phase 2: Update Prompting

3. ✅ Replace system prompt in `get_langchain_agent()` with enhanced version
4. ✅ Test that agent still works with simple queries

### Phase 3: Integrate Response Processing  

5. ✅ Remove `extract_final_answer()` function from `app.py`
6. ✅ Update `process_query()` to use preprocessing and ResponseProcessor
7. ✅ Verify imports and code flow

### Phase 4: Testing & Validation

8. ✅ Test failing scenarios from diagnosis:

   - "Did food spending increase from January to February?"
   - "Which category did I spend more on: food or shopping?"
   - "Compare Amazon vs Walmart spending"

9. ✅ Verify responses show actual numbers and calculations
10. ✅ Confirm no tool JSON appears in responses

---

## Files Modified

1. **`response_processor.py`** - NEW file (complete ResponseProcessor class)
2. **[`app.py`](app.py)** - 3 changes:

   - Add `preprocess_query()` function (new, ~30 lines)
   - Update system prompt in `get_langchain_agent()` (~40 lines)
   - Update `process_query()` function (modify ~10 lines, remove ~167 lines)

**Total lines**: ~80 new, ~167 removed, ~10 modified

---

## Expected Results

| Metric | Before (Current) | After (Plan A) |

|--------|-----------------|----------------|

| Average Score | 0.21/1.0 | 0.5-0.7/1.0 |

| Response Quality | "You spent more..." | "January: $956.62, February: $977.46, increased by $20.84" |

| Tool JSON Visible | Yes | No |

| Multi-step Reasoning | Broken | Working |

| Architecture Changes | N/A | None (keeps LangChain) |

---

## Risk Assessment

**Risk Level**: ⭐ LOW

**Why Low Risk**:

- No changes to core agent architecture (still uses `create_agent`)
- All callbacks, logging, and metrics unchanged
- No new dependencies
- Changes are additive (preprocessing) or replacement (ResponseProcessor)
- Easy to rollback (git revert)

**What Could Go Wrong**:

- ResponseProcessor might not cover all edge cases → Safety net: still improves most queries
- Enhanced prompts might confuse agent on simple queries → Test shows this unlikely
- Tool result parsing could fail → ResponseProcessor has fallbacks

---

## Time Estimate

- **Phase 1**: 1 hour (create files)
- **Phase 2**: 1 hour (update prompts, test)
- **Phase 3**: 1 hour (integrate processing)
- **Phase 4**: 1 hour (testing)

**Total**: 3-4 hours

---

## Success Criteria

✅ Agent calls tools multiple times for comparative queries

✅ Responses include actual numeric values from tool results

✅ Responses show calculated differences/comparisons

✅ No tool JSON or technical details in final responses

✅ All existing logging/callbacks continue working

✅ Score improves from 0.21 to at least 0.5

---

## Next Steps After Plan A

If results are satisfactory (score 0.5-0.7):

- ✅ **Done!** No need for LangGraph migration

If more improvement needed (score < 0.5 or specific issues):

- Consider Plan B (full LangGraph migration)
- Analyze specific failure patterns
- May need more sophisticated state management

**Recommendation**: Complete Plan A first, measure results, then decide.