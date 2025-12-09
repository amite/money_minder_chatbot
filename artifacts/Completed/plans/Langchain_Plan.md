# LangChain Migration Implementation Plan & Execution Log

## Overview

This document tracks the complete LangChain migration from manual Ollama tool calling to a modern LangChain/LangGraph architecture. The migration eliminates hard-coded conditionals in `app.py` and creates a scalable, maintainable system using LangChain's agent framework.

## Original Plan

### Objectives

1. **Eliminate conditional logic**: Remove all if/elif chains for tool handling in `app.py`
2. **Create scalable architecture**: Make it easy to add new tools without modifying core logic
3. **Maintain existing functionality**: Preserve all current features (dataframes, titles, visualizations)
4. **Use modern LangChain**: Leverage LangChain 0.1.0+ and LangGraph for agent orchestration

### Implementation Phases

#### Phase 1: Dependencies and Setup
- Add LangChain dependencies to `pyproject.toml`
- Dependencies: `langchain`, `langchain-core`, `langchain-community`, `langchain-ollama`, `langgraph`

#### Phase 2: Create Tool Result Handlers
- Create `tool_handlers.py` with:
  - `ToolResultHandler` base class
  - Concrete handlers for each tool (SearchTransactionsHandler, AnalyzeByCategoryHandler, GetSpendingSummaryHandler, AnalyzeMerchantHandler)
  - `HandlerRegistry` for mapping tool names to handlers

#### Phase 3: Create LangChain Tools
- Create `langchain_tools.py` with:
  - `BaseTool` classes wrapping each `FinancialAgent` method
  - Proper Pydantic input schemas for each tool
  - Tool descriptions for LLM tool selection

#### Phase 4: Refactor Agent Class
- Add `get_langchain_tools()` method to `FinancialAgent`
- Maintain backward compatibility with existing `get_tools()` method

#### Phase 5: Refactor App with LangChain Agent
- Replace manual Ollama tool calling with LangChain agent
- Implement callback system to intercept tool execution
- Use handler registry to process results
- Update session state with dataframes and titles

#### Phase 6: Testing and Validation
- Test all 4 tools
- Verify dataframe extraction
- Verify title generation
- Verify UI display

## Challenges Faced & Bugs Fixed

### Challenge 1: Import Path Errors

**Error**: `ModuleNotFoundError: No module named 'langchain.callbacks'`

**Root Cause**: LangChain 0.1.0+ reorganized module structure. Callbacks moved to `langchain_core`.

**Fix**:
- Changed `from langchain.callbacks.base import BaseCallbackHandler` to `from langchain_core.callbacks import BaseCallbackHandler`
- Changed `from langchain.schema import AgentAction, AgentFinish` to `from langchain_core.agents import AgentAction, AgentFinish`
- Added `langchain-core>=0.1.0` to dependencies

**Files Modified**: `app.py`, `pyproject.toml`

---

### Challenge 2: Pydantic v2 Field Override Error

**Error**: `Field 'name' defined on a base class was overridden by a non-annotated attribute. All field definitions, including overrides, require a type annotation.`

**Root Cause**: Pydantic v2 requires type annotations when overriding fields from base classes.

**Fix**:
- Added type annotations to all tool class fields:
  - `name: str = "tool_name"`
  - `description: str = "tool description"`
  - `args_schema: type[BaseModel] = InputSchema`

**Files Modified**: `langchain_tools.py`

---

### Challenge 3: Agent Field Not Recognized

**Error**: `"SearchTransactionsTool" object has no field "agent"`

**Root Cause**: Pydantic v2 doesn't allow arbitrary attributes. The `agent` field needs to be declared as a private attribute.

**Fix**:
- Used `PrivateAttr()` from Pydantic to store the agent:
  - `_agent: FinancialAgent = PrivateAttr()`
  - Changed `self.agent` to `self._agent` throughout
  - Updated `__init__` to accept `**kwargs` and pass to parent

**Files Modified**: `langchain_tools.py`

---

### Challenge 4: RunnableConfig Type Error

**Error**: `Argument of type "dict[str, list[ToolExecutionCallback]]" cannot be assigned to parameter "config" of type "RunnableConfig | None"`

**Root Cause**: Type checker needed explicit type annotation for the config dictionary.

**Fix**:
- Added import: `from langchain_core.runnables import RunnableConfig`
- Added type annotation: `config: RunnableConfig = {"callbacks": [callback]}`

**Files Modified**: `app.py`

---

### Challenge 5: DataFrame Not Updating

**Issue**: DataFrame showed all transactions instead of filtered/grouped results.

**Root Cause**: Callback was trying to update Streamlit session state from a background thread, which doesn't work (caused "missing ScriptRunContext" warnings).

**Fix**:
- Removed session state updates from `on_tool_end()` callback (runs in background thread)
- Added `tool_executed` flag to track tool execution
- Moved session state updates to main thread after `agent.invoke()` completes
- Process tool results using handler registry in main thread

**Files Modified**: `app.py`

---

### Challenge 6: Deprecated Function Warning

**Warning**: `create_react_agent has been moved to langchain.agents. Please update your import to from langchain.agents import create_agent`

**Root Cause**: LangChain moved the function from `langgraph.prebuilt` to `langchain.agents` and renamed it.

**Fix**:
- Changed import: `from langgraph.prebuilt import create_react_agent` → `from langchain.agents import create_agent`
- Changed function call: `create_react_agent(llm, tools)` → `create_agent(llm, tools)`

**Files Modified**: `app.py`

---

### Challenge 7: Using Context7 for Modern LangChain

**Issue**: Initial implementation used older LangChain patterns that didn't match current best practices.

**Solution**: Used Context7 to get latest LangChain documentation and updated to:
- Use `langchain_core.callbacks.BaseCallbackHandler` instead of deprecated paths
- Use `create_agent` from `langchain.agents` instead of `create_react_agent` from `langgraph.prebuilt`
- Use proper message format with `HumanMessage` and `AIMessage`
- Use `agent.invoke()` with messages format instead of `agent.run()`

**Files Modified**: `app.py`

---

## Final Architecture

### File Structure

```
money_minder_chatbot/
├── agent.py                 # FinancialAgent with get_langchain_tools() method
├── app.py                   # Refactored with LangChain agent and callbacks
├── vector_store.py          # No changes
├── langchain_tools.py       # LangChain BaseTool wrappers (NEW)
├── tool_handlers.py         # Result handler registry (NEW)
└── pyproject.toml           # Updated with LangChain dependencies
```

### Key Components

1. **LangChain Tools** (`langchain_tools.py`):
   - `SearchTransactionsTool`
   - `AnalyzeByCategoryTool`
   - `GetSpendingSummaryTool`
   - `AnalyzeMerchantTool`
   - Each tool uses Pydantic v2 compatible field definitions
   - Uses `PrivateAttr()` for agent reference

2. **Tool Handlers** (`tool_handlers.py`):
   - `ToolResultHandler` base class
   - Concrete handlers for each tool
   - `HandlerRegistry` for mapping tool names to handlers
   - Eliminates all conditional logic

3. **Agent Integration** (`app.py`):
   - Uses `create_agent` from `langchain.agents`
   - `ToolExecutionCallback` to intercept tool execution
   - Processes results in main thread after agent execution
   - Updates session state with dataframes and titles

### Benefits Achieved

✅ **No conditional logic**: Handler registry replaces all if/elif chains  
✅ **Scalable**: Adding new tools = add tool class + handler class  
✅ **Maintainable**: Clear separation of concerns  
✅ **Testable**: Each component can be tested independently  
✅ **Modern**: Uses latest LangChain/LangGraph patterns  
✅ **Type-safe**: Proper type annotations throughout  

## Dependencies Added

```toml
"langchain>=0.1.0",
"langchain-core>=0.1.0",
"langchain-community>=0.0.20",
"langchain-ollama>=0.0.1",
"langgraph>=0.0.1",
```

## Testing Status

- ✅ All 4 tools execute correctly through LangChain agent
- ✅ Dataframes are extracted properly
- ✅ Titles are generated correctly
- ✅ UI displays results as before
- ✅ Conversation history persists
- ✅ Error handling works

## Known Issues (Non-Critical)

1. **Pandas SettingWithCopyWarning**: Appears in `agent.py` when filtering DataFrames. Low priority, doesn't affect functionality.
2. **Qdrant Insecure Connection Warning**: API key used with HTTP instead of HTTPS. Intentional for local development.
3. **Streamlit ScriptRunContext Warning**: Appears when callbacks run in background threads. Expected behavior, warnings can be ignored.

## Lessons Learned

1. **Pydantic v2 is strict**: All field overrides require type annotations
2. **Private attributes**: Use `PrivateAttr()` for non-serializable attributes
3. **Streamlit thread safety**: Session state updates must happen in main thread
4. **LangChain evolution**: Always check latest documentation - APIs change frequently
5. **Context7 is valuable**: Using up-to-date documentation prevents compatibility issues

## Success Criteria - All Met ✅

- [x] All 4 tools work through LangChain agent
- [x] No if/elif chains in `app.py` for tool handling
- [x] Dataframes and titles generated correctly
- [x] UI displays results as before
- [x] Code is more maintainable and extensible
- [x] All existing functionality preserved

## Next Steps (Optional Improvements)

1. Fix pandas SettingWithCopyWarning by using `.loc` or `.copy()`
2. Add unit tests for tool handlers
3. Add integration tests for agent execution
4. Consider adding streaming responses for better UX
5. Add error recovery mechanisms for tool failures

