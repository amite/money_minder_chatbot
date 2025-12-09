# Tool Selection Mechanism

## Overview

The Money Minder Chatbot uses a **function calling** (tool calling) approach where the LLM autonomously decides which tool to use based on the user's query. This document explains how the LLM makes these decisions and the mechanisms that enable tool selection.

## Architecture

The tool selection process follows this flow:

```
User Query → LLM with Tool Definitions → Tool Selection Decision → Tool Execution → Results → Natural Language Response
```

## Tool Definitions

The system defines three tools in the `FinancialAgent` class (`agent.py`), each with structured metadata that helps the LLM understand when and how to use them:

### 1. `search_transactions`
- **Purpose**: Search for transactions by description, category, or merchant using vector similarity
- **When to use**: User asks to "find", "show", "search for" specific transactions or mentions specific merchants/descriptions
- **Parameters**:
  - `query` (required): Natural language search query
  - `limit` (optional, default: 10): Maximum number of results

### 2. `analyze_by_category`
- **Purpose**: Analyze spending by category within optional date ranges
- **When to use**: User asks about spending in a specific category (food, shopping, entertainment, etc.) or wants category-based analysis
- **Parameters**:
  - `category` (required): Transaction category
  - `start_date` (optional): Start date in YYYY-MM-DD format
  - `end_date` (optional): End date in YYYY-MM-DD format

### 3. `get_spending_summary`
- **Purpose**: Get summary statistics of spending over a time period
- **When to use**: User asks for "summary", "overview", "total spending", or wants period-based statistics
- **Parameters**:
  - `period` (optional, default: "last_month"): Time period (last_week, last_month, last_3_months, all_time)

## How the LLM Receives Tool Information

When a user query is processed (`app.py`, `process_query()` function):

1. **System Prompt**: The LLM receives a system message that instructs it to:
   - Act as a financial assistant
   - Use appropriate tools based on the user's query
   - Provide clear, natural language explanations after tool execution

2. **Tool Definitions**: The LLM receives the complete tool schema via:
   ```python
   tools=st.session_state.agent.get_tools()
   ```
   This passes the full JSON schema for all three tools, including:
   - Tool names
   - Descriptions (what each tool does)
   - Parameter definitions (what inputs each tool accepts)
   - Parameter types and requirements

3. **Conversation History**: The LLM also receives the full conversation history, providing context for follow-up questions and multi-turn conversations.

## LLM Decision-Making Process

The LLM (using `llama3.1:8b-instruct-q4_K_M` model via Ollama) makes tool selection decisions through:

### 1. **Semantic Understanding**
The LLM analyzes the user's query to understand:
- **Intent**: What is the user trying to accomplish?
- **Entities**: What specific information is mentioned? (categories, dates, merchants, etc.)
- **Query Type**: Is this a search, analysis, or summary request?

### 2. **Tool Matching**
The LLM compares the query against each tool's description and parameters:

- **`search_transactions`** is selected when:
  - Query contains search-related verbs: "find", "show", "search", "look for"
  - Query mentions specific merchants, descriptions, or transaction details
  - User wants to see specific transactions matching criteria
  - Example: "Find my coffee purchases" → `search_transactions(query="coffee purchases")`

- **`analyze_by_category`** is selected when:
  - Query mentions a specific category: "food", "shopping", "entertainment", etc.
  - Query asks "how much" for a category
  - Query requests category-based analysis
  - Example: "How much did I spend on shopping?" → `analyze_by_category(category="shopping")`

- **`get_spending_summary`** is selected when:
  - Query asks for "summary", "overview", "total spending"
  - Query mentions time periods without specific categories
  - Query requests general statistics
  - Example: "What's my spending summary for last month?" → `get_spending_summary(period="last_month")`

### 3. **Parameter Extraction**
Once a tool is selected, the LLM extracts relevant parameters from the user's query:
- Extracts category names from natural language
- Parses date references ("last month", "January", "Q1") into appropriate date formats
- Determines appropriate limits for search results
- Handles optional parameters intelligently

## Execution Flow

The complete execution flow in `process_query()`:

```python
# Step 1: Build conversation context
messages = [system_prompt] + conversation_history + [user_query]

# Step 2: LLM makes tool selection decision
response = ollama.chat(
    model="llama3.1:8b-instruct-q4_K_M",
    messages=messages,
    tools=st.session_state.agent.get_tools(),  # Tool definitions
)

# Step 3: Check if LLM decided to use a tool
if response.message.tool_calls:
    tool_call = response.message.tool_calls[0]
    tool_name = tool_call.function.name
    tool_args = dict(tool_call.function.arguments)
    
    # Step 4: Execute the selected tool
    result = st.session_state.agent.execute_tool(tool_name, **tool_args)
    
    # Step 5: Send results back to LLM for natural language explanation
    tool_result_context = f"""I executed the {tool_name} tool...
    The tool returned these results: {result}
    Please provide a clear, natural language explanation..."""
    
    # Step 6: LLM generates user-friendly response
    final_response = ollama.chat(
        model="llama3.1:8b-instruct-q4_K_M",
        messages=messages + [{"role": "user", "content": tool_result_context}],
    )
```

## Factors Influencing Tool Selection

### 1. **Query Keywords**
- Search-related: "find", "show", "search" → `search_transactions`
- Category mentions: "food", "shopping", "entertainment" → `analyze_by_category`
- Summary requests: "summary", "overview", "total" → `get_spending_summary`

### 2. **Query Structure**
- Questions about specific items → `search_transactions`
- Questions about categories → `analyze_by_category`
- Questions about overall spending → `get_spending_summary`

### 3. **Conversation Context**
- Follow-up questions may reference previous tool results
- The LLM maintains context across the conversation
- Previous tool calls inform subsequent decisions

### 4. **Tool Descriptions**
The quality of tool descriptions directly impacts selection accuracy:
- Clear, specific descriptions help the LLM understand tool purposes
- Parameter descriptions guide the LLM in extracting correct values
- Examples in descriptions (if present) improve matching

## Example Query Mappings

| User Query | Selected Tool | Extracted Parameters |
|------------|--------------|---------------------|
| "Find my coffee purchases" | `search_transactions` | `query="coffee purchases"` |
| "Show my Amazon transactions" | `search_transactions` | `query="Amazon"` |
| "How much did I spend on shopping?" | `analyze_by_category` | `category="shopping"` |
| "Analyze my food expenses" | `analyze_by_category` | `category="food"` |
| "What's my spending summary for last month?" | `get_spending_summary` | `period="last_month"` |
| "Show me my total spending" | `get_spending_summary` | `period="all_time"` (default) |

## System Prompt Role

The system prompt (`app.py`, lines 60-64) plays a crucial role in tool selection:

```python
"You are a financial assistant that helps users analyze their transactions.
You have access to tools that can search transactions, analyze by category, and provide spending summaries.
Always use the appropriate tool based on the user's query. After getting tool results, provide a clear, 
natural language explanation of the findings."
```

This prompt:
- Establishes the assistant's role
- Mentions available tools (implicitly guiding selection)
- Instructs the LLM to use tools appropriately
- Sets expectations for response format

## Limitations and Considerations

### 1. **Single Tool Selection**
Currently, the system only supports selecting one tool per query. Multi-tool queries (e.g., "Compare my food spending to shopping spending") would require:
- Multiple tool calls in sequence
- Result aggregation logic
- Enhanced system prompt guidance

### 2. **Parameter Extraction Accuracy**
The LLM must correctly extract parameters from natural language:
- Date parsing can be ambiguous ("last month" vs "January")
- Category names must match exactly (case-insensitive matching helps)
- Search queries may need refinement

### 3. **Tool Description Quality**
Tool selection accuracy depends on:
- Clear, unambiguous tool descriptions
- Comprehensive parameter documentation
- Examples of appropriate use cases

### 4. **Model Capabilities**
The `llama3.1:8b-instruct-q4_K_M` model:
- Has good tool calling capabilities
- May occasionally select incorrect tools for ambiguous queries
- Benefits from clear, specific user queries

## Improving Tool Selection

To improve tool selection accuracy:

1. **Enhance Tool Descriptions**: Add more specific use cases and examples
2. **Improve System Prompt**: Provide more explicit guidance on when to use each tool
3. **Add Tool Examples**: Include example queries in tool descriptions
4. **Implement Fallback Logic**: Handle cases where no tool is appropriate
5. **Add Validation**: Validate extracted parameters before tool execution
6. **Support Multi-Tool Queries**: Allow chaining multiple tools for complex queries

## Technical Implementation Details

### Tool Definition Format
Tools are defined using the OpenAI-compatible function calling format:
```python
{
    "type": "function",
    "function": {
        "name": "tool_name",
        "description": "What the tool does",
        "parameters": {
            "type": "object",
            "properties": {
                "param_name": {
                    "type": "string",
                    "description": "Parameter description"
                }
            },
            "required": ["param_name"]
        }
    }
}
```

### Tool Execution
The `execute_tool()` method in `FinancialAgent` maps tool names to implementation methods:
```python
def execute_tool(self, tool_name: str, **kwargs) -> str:
    if tool_name == "search_transactions":
        return self.search_transactions(**kwargs)
    elif tool_name == "analyze_by_category":
        return self.analyze_by_category(**kwargs)
    elif tool_name == "get_spending_summary":
        return self.get_spending_summary(**kwargs)
```

## Conclusion

The tool selection mechanism relies on:
1. **Well-defined tool schemas** that clearly describe each tool's purpose
2. **Semantic understanding** by the LLM to match queries to tools
3. **Parameter extraction** to convert natural language to structured inputs
4. **System prompt guidance** to direct the LLM's behavior
5. **Two-step LLM interaction** for both tool selection and response generation

This approach provides a flexible, natural language interface while maintaining structured data access through well-defined tools.

