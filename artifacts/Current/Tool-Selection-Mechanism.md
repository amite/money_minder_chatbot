# Tool Selection Mechanism

## Overview

The Money Minder Chatbot uses a **LangChain agent-based** approach where the LLM autonomously decides which tool to use based on the user's query. The system leverages LangChain's `create_agent` function with LangGraph to orchestrate tool selection and execution, eliminating manual conditional logic.

## Architecture

The tool selection process follows this flow:

```
User Query → LangChain Agent → Tool Selection Decision → Tool Execution → Callback Interception → Handler Registry → Results Processing → Natural Language Response
```

## Current Implementation (LangChain-Based)

### Agent Setup

The system uses LangChain's `create_agent` function to create a ReAct agent:

```python
from langchain.agents import create_agent
from langchain_ollama import ChatOllama

llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M", temperature=0)
tools = agent.get_langchain_tools()  # Returns LangChain BaseTool instances
agent = create_agent(llm, tools)
```

### Tool Definitions

Tools are now defined as LangChain `BaseTool` classes in `langchain_tools.py`, each with:

1. **Pydantic Input Schema**: Defines parameters with types and descriptions
2. **Tool Metadata**: Name, description, and args_schema
3. **Execution Method**: `_run()` method that calls the corresponding `FinancialAgent` method

#### Available Tools

### 1. `SearchTransactionsTool`
- **Purpose**: Search for transactions by description, category, or merchant using vector similarity
- **When to use**: User asks to "find", "show", "search for" specific transactions or mentions specific merchants/descriptions
- **Parameters**:
  - `query` (required): Natural language search query
  - `limit` (optional, default: 10): Maximum number of results
- **Implementation**: `langchain_tools.py::SearchTransactionsTool`

### 2. `AnalyzeByCategoryTool`
- **Purpose**: Analyze spending by category within optional date ranges
- **When to use**: User asks about spending in a specific category (food, shopping, entertainment, etc.) or wants category-based analysis
- **Parameters**:
  - `category` (required): Transaction category
  - `start_date` (optional): Start date in YYYY-MM-DD format
  - `end_date` (optional): End date in YYYY-MM-DD format
- **Implementation**: `langchain_tools.py::AnalyzeByCategoryTool`

### 3. `GetSpendingSummaryTool`
- **Purpose**: Get summary statistics of spending over a time period
- **When to use**: User asks for "summary", "overview", "total spending", or wants period-based statistics. Also used to list all available categories.
- **Parameters**:
  - `period` (optional, default: "last_month"): Time period (last_week, last_month, last_3_months, all_time)
- **Implementation**: `langchain_tools.py::GetSpendingSummaryTool`

### 4. `AnalyzeMerchantTool`
- **Purpose**: Analyze spending for a specific merchant, optionally grouped by category
- **When to use**: User asks about spending at a specific merchant, wants to see merchant transactions grouped by category, or needs merchant-specific analysis
- **Parameters**:
  - `merchant` (required): Merchant name (e.g., Amazon, Starbucks, Walmart)
  - `group_by_category` (optional, default: False): Whether to group results by category
  - `start_date` (optional): Start date in YYYY-MM-DD format
  - `end_date` (optional): End date in YYYY-MM-DD format
- **Implementation**: `langchain_tools.py::AnalyzeMerchantTool`

## How the LLM Receives Tool Information

The LangChain agent automatically provides tool information to the LLM:

1. **Tool Registration**: Tools are registered with the agent during initialization:
   ```python
   tools = st.session_state.agent.get_langchain_tools()
   agent = create_agent(llm, tools)
   ```

2. **Tool Schemas**: Each `BaseTool` class provides:
   - Tool name (via `name` attribute)
   - Tool description (via `description` attribute)
   - Parameter schema (via `args_schema` Pydantic model)
   - LangChain automatically converts these to function calling format for the LLM

3. **Conversation History**: The agent maintains conversation history using LangChain's message format:
   - `HumanMessage` for user queries
   - `AIMessage` for assistant responses
   - Tool messages are automatically handled by the agent

## LLM Decision-Making Process

The LLM (using `llama3.1:8b-instruct-q4_K_M` model via Ollama through LangChain) makes tool selection decisions through LangChain's ReAct agent pattern:

### 1. **Semantic Understanding**
The agent analyzes the user's query to understand:
- **Intent**: What is the user trying to accomplish?
- **Entities**: What specific information is mentioned? (categories, dates, merchants, etc.)
- **Query Type**: Is this a search, analysis, or summary request?

### 2. **Tool Matching**
The agent compares the query against each tool's description and parameters:

- **`SearchTransactionsTool`** is selected when:
  - Query contains search-related verbs: "find", "show", "search", "look for"
  - Query mentions specific merchants, descriptions, or transaction details
  - User wants to see specific transactions matching criteria
  - Example: "Find my coffee purchases" → `search_transactions(query="coffee purchases")`

- **`AnalyzeByCategoryTool`** is selected when:
  - Query mentions a specific category: "food", "shopping", "entertainment", etc.
  - Query asks "how much" for a category
  - Query requests category-based analysis
  - Example: "How much did I spend on shopping?" → `analyze_by_category(category="shopping")`

- **`GetSpendingSummaryTool`** is selected when:
  - Query asks for "summary", "overview", "total spending"
  - Query mentions time periods without specific categories
  - Query requests general statistics
  - Query asks about available categories
  - Example: "What's my spending summary for last month?" → `get_spending_summary(period="last_month")`

- **`AnalyzeMerchantTool`** is selected when:
  - Query mentions a specific merchant name
  - Query asks about merchant spending
  - Query requests merchant analysis with optional category grouping
  - Example: "Can you group my Amazon transactions by category?" → `analyze_merchant(merchant="Amazon", group_by_category=True)`

### 3. **Parameter Extraction**
Once a tool is selected, the agent extracts relevant parameters from the user's query:
- Extracts category names from natural language
- Parses date references ("last month", "January", "Q1") into appropriate date formats
- Determines appropriate limits for search results
- Handles optional parameters intelligently
- Extracts boolean flags (e.g., `group_by_category=True` from "group by category")

## Execution Flow

The complete execution flow in `process_query()`:

```python
# Step 1: Get or create LangChain agent
agent = get_langchain_agent()

# Step 2: Create callback to intercept tool execution
callback = ToolExecutionCallback(handler_registry, user_query)

# Step 3: Build messages from conversation history
messages = []
for msg in st.session_state.messages:
    if msg["role"] == "user":
        messages.append(HumanMessage(content=msg["content"]))
    elif msg["role"] == "assistant":
        messages.append(AIMessage(content=msg["content"]))

# Step 4: Add current user query
messages.append(HumanMessage(content=user_query))

# Step 5: Agent makes tool selection and executes
config = {"callbacks": [callback]}
result = agent.invoke({"messages": messages}, config=config)

# Step 6: Callback captures tool execution info
# - on_tool_start(): Captures tool_name and tool_args
# - on_tool_end(): Marks tool_executed flag

# Step 7: Process tool results using handler registry (in main thread)
if callback.tool_executed and callback.tool_name and callback.tool_args:
    result_info = callback.handler_registry.handle_result(
        callback.tool_name, callback.tool_args, user_query
    )
    # Update session state with dataframe and title
    st.session_state.query_dataframe = result_info["dataframe"]
    st.session_state.query_title = result_info["title"]

# Step 8: Extract and display response
last_message = result["messages"][-1]
response = last_message.content
```

## Callback System

The `ToolExecutionCallback` class intercepts tool execution:

### `on_tool_start()`
- Called when a tool starts running
- Captures `tool_name` from serialized tool info
- Parses `input_str` to extract `tool_args` (handles dict, string, or JSON formats)

### `on_tool_end()`
- Called when a tool finishes running
- Sets `tool_executed` flag to True
- Note: Session state updates happen in main thread after agent execution completes

## Handler Registry Pattern

The `HandlerRegistry` eliminates all conditional logic by mapping tool names to handlers:

```python
class HandlerRegistry:
    def __init__(self, agent: FinancialAgent):
        self.handlers = {
            "search_transactions": SearchTransactionsHandler(agent),
            "analyze_by_category": AnalyzeByCategoryHandler(agent),
            "get_spending_summary": GetSpendingSummaryHandler(agent),
            "analyze_merchant": AnalyzeMerchantHandler(agent),
        }
    
    def handle_result(self, tool_name, tool_args, user_query):
        handler = self.handlers.get(tool_name)
        # Handler extracts dataframe, generates title, determines visualization
        return handler.get_dataframe(), handler.generate_title(), ...
```

Each handler implements:
- `get_dataframe()`: Extracts appropriate DataFrame from tool result
- `generate_title()`: Generates display title based on tool args and user query
- `get_visualization()`: Returns visualization type if applicable

## Factors Influencing Tool Selection

### 1. **Query Keywords**
- Search-related: "find", "show", "search" → `SearchTransactionsTool`
- Category mentions: "food", "shopping", "entertainment" → `AnalyzeByCategoryTool`
- Summary requests: "summary", "overview", "total" → `GetSpendingSummaryTool`
- Merchant mentions: "Amazon", "Starbucks", etc. → `AnalyzeMerchantTool`
- Grouping requests: "group by category" → `AnalyzeMerchantTool` with `group_by_category=True`

### 2. **Query Structure**
- Questions about specific items → `SearchTransactionsTool`
- Questions about categories → `AnalyzeByCategoryTool`
- Questions about overall spending → `GetSpendingSummaryTool`
- Questions about merchants → `AnalyzeMerchantTool`

### 3. **Conversation Context**
- Follow-up questions may reference previous tool results
- The agent maintains context across the conversation using message history
- Previous tool calls inform subsequent decisions

### 4. **Tool Descriptions**
The quality of tool descriptions directly impacts selection accuracy:
- Clear, specific descriptions help the agent understand tool purposes
- Parameter descriptions guide the agent in extracting correct values
- Comprehensive descriptions improve matching accuracy

## Example Query Mappings

| User Query | Selected Tool | Extracted Parameters |
|------------|--------------|---------------------|
| "Find my coffee purchases" | `SearchTransactionsTool` | `query="coffee purchases"` |
| "Show my Amazon transactions" | `SearchTransactionsTool` | `query="Amazon"` |
| "How much did I spend on shopping?" | `AnalyzeByCategoryTool` | `category="shopping"` |
| "Analyze my food expenses" | `AnalyzeByCategoryTool` | `category="food"` |
| "What's my spending summary for last month?" | `GetSpendingSummaryTool` | `period="last_month"` |
| "Show me my total spending" | `GetSpendingSummaryTool` | `period="all_time"` (default) |
| "Can you group my Amazon transactions by category?" | `AnalyzeMerchantTool` | `merchant="Amazon", group_by_category=True` |
| "What did I spend at Starbucks?" | `AnalyzeMerchantTool` | `merchant="Starbucks", group_by_category=False` |

## System Prompt Role

The LangChain agent uses implicit system prompts built into the `create_agent` function. The agent is configured to:
- Act as a helpful assistant
- Use tools when appropriate
- Provide clear, natural language explanations
- Maintain conversation context

## Advantages of LangChain Approach

### 1. **No Conditional Logic**
- Handler registry replaces all if/elif chains
- Adding new tools = add tool class + handler class
- No need to modify core processing logic

### 2. **Automatic Tool Management**
- LangChain handles tool registration and discovery
- Automatic parameter validation via Pydantic schemas
- Built-in error handling and retries

### 3. **Message-Based Architecture**
- Uses standard LangChain message format
- Automatic conversation history management
- Support for multi-turn conversations

### 4. **Callback System**
- Intercept tool execution without modifying tool code
- Capture tool arguments for result processing
- Thread-safe result handling

### 5. **Type Safety**
- Pydantic schemas ensure type correctness
- Type annotations throughout
- Better IDE support and error detection

## Limitations and Considerations

### 1. **Single Tool Selection Per Query**
Currently, the agent selects one tool per query. Multi-tool queries (e.g., "Compare my food spending to shopping spending") would require:
- Multiple tool calls in sequence (supported by LangChain)
- Result aggregation logic
- Enhanced prompt guidance

### 2. **Parameter Extraction Accuracy**
The agent must correctly extract parameters from natural language:
- Date parsing can be ambiguous ("last month" vs "January")
- Category names must match exactly (case-insensitive matching helps)
- Search queries may need refinement
- Boolean flags must be correctly inferred

### 3. **Tool Description Quality**
Tool selection accuracy depends on:
- Clear, unambiguous tool descriptions
- Comprehensive parameter documentation
- Examples of appropriate use cases (can be added to descriptions)

### 4. **Model Capabilities**
The `llama3.1:8b-instruct-q4_K_M` model:
- Has good tool calling capabilities through LangChain
- May occasionally select incorrect tools for ambiguous queries
- Benefits from clear, specific user queries
- Works well with LangChain's structured tool definitions

### 5. **Thread Safety**
- Callbacks run in background threads
- Session state updates must happen in main thread
- Tool result processing is deferred until after agent execution

## Improving Tool Selection

To improve tool selection accuracy:

1. **Enhance Tool Descriptions**: Add more specific use cases and examples in tool descriptions
2. **Improve System Prompt**: Configure agent with more explicit guidance (via agent configuration)
3. **Add Tool Examples**: Include example queries in tool descriptions
4. **Implement Fallback Logic**: Handle cases where no tool is appropriate
5. **Add Validation**: Validate extracted parameters before tool execution (Pydantic handles this)
6. **Support Multi-Tool Queries**: LangChain supports this - add aggregation logic
7. **Fine-tune Descriptions**: Test and refine tool descriptions based on actual usage patterns

## Technical Implementation Details

### Tool Definition Format
Tools are defined as LangChain `BaseTool` classes:

```python
from langchain.tools import BaseTool
from pydantic import BaseModel, Field, PrivateAttr

class SearchTransactionsInput(BaseModel):
    query: str = Field(description="Search query describing what to look for")
    limit: int = Field(default=10, description="Maximum number of results")

class SearchTransactionsTool(BaseTool):
    name: str = "search_transactions"
    description: str = "Search for transactions by description, category, or merchant"
    args_schema: type[BaseModel] = SearchTransactionsInput
    _agent: FinancialAgent = PrivateAttr()
    
    def _run(self, query: str, limit: int = 10) -> str:
        return self._agent.search_transactions(query, limit)
```

### Tool Execution
Tools are executed by the LangChain agent:
- Agent selects tool based on query
- Agent extracts parameters using Pydantic validation
- Tool's `_run()` method executes
- Results are returned to agent for response generation

### Result Processing
Results are processed through the handler registry:

```python
# In main thread after agent execution
result_info = handler_registry.handle_result(
    tool_name, tool_args, user_query
)
# Returns: {"dataframe": df, "title": str, "visualization": str}
```

## Comparison: Old vs New Approach

### Old Approach (Manual Ollama Tool Calling)
- Manual `ollama.chat()` calls with tool definitions
- Manual tool execution via `execute_tool()`
- Hard-coded if/elif chains for result processing
- Manual conversation history management
- Two separate LLM calls (tool selection + response generation)

### New Approach (LangChain Agent)
- LangChain agent handles tool selection and execution
- Automatic tool registration and discovery
- Handler registry eliminates conditionals
- Automatic conversation history management
- Single agent invocation handles everything
- Callback system for result interception
- Type-safe with Pydantic schemas

## Conclusion

The tool selection mechanism now relies on:
1. **LangChain agent framework** for orchestration and tool management
2. **Well-defined tool schemas** using Pydantic models that clearly describe each tool's purpose
3. **Semantic understanding** by the LLM to match queries to tools
4. **Automatic parameter extraction** with Pydantic validation
5. **Handler registry pattern** for result processing without conditionals
6. **Callback system** for intercepting tool execution
7. **Message-based architecture** for conversation management

This approach provides a flexible, natural language interface while maintaining structured data access through well-defined tools, all without hard-coded conditional logic.
