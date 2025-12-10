Looking at your code and the quality report, we can see several fundamental issues with your ReAct agent implementation. Let's break down the problems and provide solutions:

## Core Problems

### 1. **Agent Not Actually Using ReAct Pattern**
Your agent is using `create_agent` from LangChain, but it's not properly configured for multi-step reasoning. The system prompt mentions multi-step capability, but the agent isn't actually executing multiple tool calls in sequence.

### 2. **Poor Tool Response Processing**
The `extract_final_answer` function is a band-aid solution trying to fix symptoms rather than causes. The agent should provide clean answers naturally, not require regex parsing.

### 3. **Tool Design Issues**
Your tools lack proper context about when to make multiple calls, and the agent doesn't have a clear strategy for complex queries.

### 4. **Missing Aggregation Layer**
For queries like "Did food spending increase from January to February?", you need the agent to:
1. Call `analyze_by_category` for January
2. Call `analyze_by_category` for February  
3. **Calculate the difference and interpret the trend**

Currently, the agent returns raw data without interpretation.

## Solutions

### Solution 1: Upgrade to LangGraph with Proper ReAct Loop

Replace your current agent with a proper LangGraph implementation:### 

```py
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langchain_ollama import ChatOllama
import operator
import json


class AgentState(TypedDict):
    """State for the agent graph"""
    messages: Annotated[Sequence[BaseMessage], operator.add]
    intermediate_steps: list
    final_answer: str


def create_react_agent(agent: 'FinancialAgent'):
    """Create a LangGraph ReAct agent with proper multi-step reasoning"""
    
    llm = ChatOllama(model="llama3.1:8b-instruct-q4_K_M", temperature=0)
    tools = agent.get_langchain_tools()
    llm_with_tools = llm.bind_tools(tools)
    
    # Enhanced system message for multi-step reasoning
    system_message = """You are a financial analysis assistant. You MUST follow this process:

**CRITICAL RULES:**
1. For comparative queries (e.g., "food vs shopping", "January vs February"):
   - Call the tool ONCE for each item being compared
   - Extract the numeric values from BOTH results
   - Calculate the difference/comparison yourself
   - State the answer clearly with the actual numbers

2. For trend analysis (e.g., "did X increase from A to B?"):
   - Call analyze_by_category for period A
   - Call analyze_by_category for period B
   - Compare the "total_spent" values
   - Calculate: difference = period_B - period_A
   - State: "increased by $X" or "decreased by $X"

3. ALWAYS extract and show the actual numeric values in your final answer

**RESPONSE FORMAT:**
When you have all the data, respond with ONLY:
- The specific numbers from your tool calls
- Your calculation/comparison
- A clear conclusion

DO NOT include:
- "Based on the tool responses..."
- "The tool returned..."
- JSON output
- Technical details about tool execution

**EXAMPLE:**
Query: "Did food spending increase from January to February?"

Step 1: Call analyze_by_category(category="food", start_date="2024-01-01", end_date="2024-01-31")
Result: {"total_spent": 956.62}

Step 2: Call analyze_by_category(category="food", start_date="2024-02-01", end_date="2024-02-29")
Result: {"total_spent": 977.46}

Your response should be:
"January food spending: $956.62
February food spending: $977.46

The food spending increased by $20.84 from January to February."

Available tools:
- search_transactions: Find transactions by keyword
- analyze_by_category: Get spending for a category (with optional dates)
- analyze_merchant: Get spending for a merchant
- get_spending_summary: Overview across all categories"""

    def should_continue(state: AgentState):
        """Determine if the agent should continue or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If the last message has no tool calls, we're done
        if not hasattr(last_message, "tool_calls") or not last_message.tool_calls:
            return "end"
        return "continue"

    def call_model(state: AgentState):
        """Call the LLM with the current state"""
        messages = state["messages"]
        
        # Add system message at the start if not present
        if not messages or not isinstance(messages[0], HumanMessage):
            messages = [HumanMessage(content=system_message)] + list(messages)
        
        response = llm_with_tools.invoke(messages)
        return {"messages": [response]}

    def process_tool_output(state: AgentState):
        """Post-process tool outputs to extract key information"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If this is a tool message, parse and annotate it
        if isinstance(last_message, ToolMessage):
            try:
                content = json.loads(last_message.content)
                # Extract key metrics for easy access
                if "total_spent" in content:
                    last_message.content = (
                        f"Total Spent: ${content['total_spent']:.2f}\n"
                        f"Transaction Count: {content.get('transaction_count', 0)}\n"
                        f"Raw Data: {last_message.content}"
                    )
            except:
                pass
        
        return {"messages": []}

    # Build the graph
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.add_node("process", process_tool_output)
    
    # Add edges
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges(
        "agent",
        should_continue,
        {
            "continue": "tools",
            "end": END,
        },
    )
    workflow.add_edge("tools", "process")
    workflow.add_edge("process", "agent")
    
    return workflow.compile()


# Add this to your FinancialAgent class
def get_langgraph_agent(self):
    """Get LangGraph-based ReAct agent"""
    if not hasattr(self, '_langgraph_agent'):
        self._langgraph_agent = create_react_agent(self)
    return self._langgraph_agent
```

Solution 2: Fix the Response Processing

Replace your `extract_final_answer` function with proper response handling:

```py
import re
import json
from typing import Dict, List, Tuple, Any


class ResponseProcessor:
    """Process agent responses to extract clean answers with data"""
    
    @staticmethod
    def extract_numeric_data(tool_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Extract numeric data from tool results"""
        data = {
            'amounts': [],
            'totals': [],
            'categories': {},
            'merchants': {},
            'dates': []
        }
        
        for result in tool_results:
            if isinstance(result.get('content'), str):
                try:
                    parsed = json.loads(result['content'])
                    
                    # Extract total_spent
                    if 'total_spent' in parsed:
                        data['totals'].append({
                            'value': parsed['total_spent'],
                            'context': result.get('tool_name', 'unknown'),
                            'args': result.get('args', {})
                        })
                    
                    # Extract category data
                    if 'spending_by_category' in parsed:
                        data['categories'].update(parsed['spending_by_category'])
                    
                    # Extract merchant data
                    if 'top_merchants' in parsed:
                        data['merchants'].update(parsed['top_merchants'])
                        
                except json.JSONDecodeError:
                    pass
        
        return data
    
    @staticmethod
    def format_comparative_response(query: str, data: Dict[str, Any]) -> str:
        """Format response for comparative queries"""
        totals = data.get('totals', [])
        
        if len(totals) < 2:
            return "Insufficient data for comparison."
        
        # Check if this is a time-based comparison
        is_time_comparison = any(
            keyword in query.lower() 
            for keyword in ['increase', 'decrease', 'from', 'to', 'vs', 'versus']
        )
        
        if is_time_comparison:
            # Sort by date if available
            sorted_totals = sorted(totals, key=lambda x: x.get('args', {}).get('start_date', ''))
            
            if len(sorted_totals) >= 2:
                first = sorted_totals[0]
                second = sorted_totals[1]
                
                diff = second['value'] - first['value']
                percent_change = (diff / first['value'] * 100) if first['value'] != 0 else 0
                
                # Format periods
                first_period = ResponseProcessor._format_period(first.get('args', {}))
                second_period = ResponseProcessor._format_period(second.get('args', {}))
                
                result = f"{first_period}: ${first['value']:.2f}\n"
                result += f"{second_period}: ${second['value']:.2f}\n\n"
                
                if diff > 0:
                    result += f"The spending increased by ${abs(diff):.2f} ({percent_change:.1f}%)."
                elif diff < 0:
                    result += f"The spending decreased by ${abs(diff):.2f} ({abs(percent_change):.1f}%)."
                else:
                    result += "The spending remained the same."
                
                return result
        
        # Category comparison
        if len(totals) == 2:
            first = totals[0]
            second = totals[1]
            
            first_name = first.get('args', {}).get('category', 'First')
            second_name = second.get('args', {}).get('category', 'Second')
            
            result = f"{first_name.title()}: ${first['value']:.2f}\n"
            result += f"{second_name.title()}: ${second['value']:.2f}\n\n"
            
            if first['value'] > second['value']:
                diff = first['value'] - second['value']
                result += f"You spent ${diff:.2f} more on {first_name} than {second_name}."
            elif second['value'] > first['value']:
                diff = second['value'] - first['value']
                result += f"You spent ${diff:.2f} more on {second_name} than {first_name}."
            else:
                result += f"You spent the same amount on both categories."
            
            return result
        
        return "Unable to format comparison."
    
    @staticmethod
    def _format_period(args: Dict) -> str:
        """Format date range into readable period"""
        start_date = args.get('start_date', '')
        end_date = args.get('end_date', '')
        category = args.get('category', '')
        
        if start_date and end_date:
            # Extract month/year
            try:
                from datetime import datetime
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d')
                
                if start.month == end.month and start.year == end.year:
                    period = start.strftime('%B %Y')
                else:
                    period = f"{start.strftime('%B %Y')} to {end.strftime('%B %Y')}"
                
                if category:
                    return f"{category.title()} ({period})"
                return period
            except:
                pass
        
        if category:
            return category.title()
        
        return "Period"
    
    @staticmethod
    def should_use_comparative_format(query: str, tool_results: List[Dict]) -> bool:
        """Determine if query needs comparative formatting"""
        comparative_keywords = [
            'more', 'less', 'vs', 'versus', 'compare',
            'increase', 'decrease', 'higher', 'lower',
            'from', 'to', 'than'
        ]
        
        has_comparative_keyword = any(kw in query.lower() for kw in comparative_keywords)
        has_multiple_results = len(tool_results) >= 2
        
        return has_comparative_keyword and has_multiple_results
    
    @staticmethod
    def process_response(
        query: str, 
        response: str, 
        tool_results: List[Dict[str, Any]]
    ) -> str:
        """Main processing function"""
        
        # Extract numeric data from tool results
        data = ResponseProcessor.extract_numeric_data(tool_results)
        
        # Check if we should use comparative format
        if ResponseProcessor.should_use_comparative_format(query, tool_results):
            formatted = ResponseProcessor.format_comparative_response(query, data)
            if formatted and len(formatted) > 20:
                return formatted
        
        # Otherwise, clean up the response
        # Remove technical jargon
        clean = re.sub(
            r"(Based on the tool call responses?|The tool returned|Assuming)",
            "",
            response,
            flags=re.IGNORECASE
        )
        
        # Remove JSON artifacts
        clean = re.sub(r'\{[^}]*"name"[^}]*\}', '', clean)
        
        # Clean whitespace
        clean = re.sub(r'\n\s*\n\s*\n+', '\n\n', clean)
        clean = clean.strip()
        
        return clean if len(clean) > 20 else response

```

### Solution 3: Enhance Tool Descriptions with Multi-Step Examples### 
```py
"""
Enhanced tool descriptions with multi-step reasoning examples
"""

ENHANCED_ANALYZE_BY_CATEGORY_DESCRIPTION = """Analyze spending for a SPECIFIC single category.

**CRITICAL FOR MULTI-STEP QUERIES:**
This tool returns JSON with "total_spent" - YOU must extract and compare values.

**Example 1: Time-based comparison**
Query: "Did food spending increase from January to February?"

Step 1: Call analyze_by_category(category="food", start_date="2024-01-01", end_date="2024-01-31")
Returns: {"total_spent": 956.62, ...}

Step 2: Call analyze_by_category(category="food", start_date="2024-02-01", end_date="2024-02-29")  
Returns: {"total_spent": 977.46, ...}

Step 3: YOUR RESPONSE:
"January food spending: $956.62
February food spending: $977.46

The food spending increased by $20.84 from January to February."

**Example 2: Category comparison**
Query: "Which category did I spend more on in February: food or shopping?"

Step 1: Call analyze_by_category(category="food", start_date="2024-02-01", end_date="2024-02-29")
Returns: {"total_spent": 977.46, ...}

Step 2: Call analyze_by_category(category="shopping", start_date="2024-02-01", end_date="2024-02-29")
Returns: {"total_spent": 217.60, ...}

Step 3: YOUR RESPONSE:
"Food: $977.46
Shopping: $217.60

You spent $759.86 more on food than shopping in February."

**IMPORTANT:**
- Extract the "total_spent" value from each result
- Do the math yourself  
- State the numbers clearly
- Don't just return tool output

USE THIS WHEN:
- User asks about spending in ONE specific category
- User mentions category WITHOUT mentioning a specific merchant
- User asks "How much did I spend on [category]?"
- User wants to compare categories (call multiple times)
- User wants trend analysis (call for each time period)

Parameters:
- category: food, shopping, entertainment, transport, utilities, health
- start_date: YYYY-MM-DD (first day of month/period)
- end_date: YYYY-MM-DD (last day of month/period)
"""


ENHANCED_ANALYZE_MERCHANT_DESCRIPTION = """Analyze spending for a specific merchant.

**CRITICAL FOR MULTI-STEP QUERIES:**
This tool returns JSON with "total_spent" - YOU must extract and compare values.

**Example: Merchant comparison**
Query: "How much did I spend at coffee shops (Starbucks and Dunkin)?"

Step 1: Call analyze_merchant(merchant="Starbucks")
Returns: {"total_spent": 386.63, ...}

Step 2: Call analyze_merchant(merchant="Dunkin")
Returns: {"total_spent": 333.22, ...}

Step 3: YOUR RESPONSE:
"Starbucks: $386.63
Dunkin: $333.22
Total coffee shop spending: $719.85"

**Example: Category breakdown at merchant**
Query: "At Amazon, did I spend more on shopping or entertainment?"

Step 1: Call analyze_merchant(merchant="Amazon", group_by_category=True)
Returns: {"categories": [{"category": "shopping", "total_spent": 635.81}, {"category": "entertainment", "total_spent": 126.07}]}

Step 2: YOUR RESPONSE:
"At Amazon:
Shopping: $635.81
Entertainment: $126.07

You spent $509.74 more on shopping than entertainment."

**IMPORTANT:**
- Extract numeric values from results
- Compare and calculate yourself
- State the answer clearly with numbers

USE THIS WHEN:
- User mentions a specific merchant name
- User wants to compare merchants (call multiple times)
- User wants category breakdown at a merchant (set group_by_category=True)

Parameters:
- merchant: Name of the merchant (Amazon, Walmart, Starbucks, etc.)
- group_by_category: True to get breakdown by category
- start_date: Optional date filter
- end_date: Optional date filter
"""


ENHANCED_SYSTEM_PROMPT = """You are a financial analysis assistant with multi-step reasoning capability.

**YOUR JOB:**
1. Understand what the user is asking
2. Determine which tool(s) to call and in what order
3. Extract numeric values from tool results
4. Do calculations/comparisons yourself
5. Present a clear answer with the actual numbers

**MULTI-STEP PATTERN:**

For "Compare A vs B" queries:
→ Call tool for A
→ Call tool for B
→ Extract totals from both results
→ Calculate difference
→ State: "A: $X, B: $Y, Difference: $Z"

For "Did X increase/decrease from A to B" queries:
→ Call tool for period A
→ Call tool for period B
→ Extract totals from both results
→ Calculate: change = B - A
→ State: "A: $X, B: $Y, Changed by $Z (increased/decreased)"

For "How much total at multiple places" queries:
→ Call tool for each place
→ Extract totals from all results
→ Sum them yourself
→ State: "Place1: $X, Place2: $Y, Total: $Z"

**CRITICAL RULES:**
1. ALWAYS extract the numeric "total_spent" value from JSON results
2. ALWAYS do the math yourself (don't rely on the tool to compare)
3. ALWAYS show the actual numbers in your response
4. NEVER just say "based on the tool results..." - show the data
5. NEVER return raw JSON to the user

**RESPONSE FORMAT:**
Good: "January: $956.62, February: $977.46. Food spending increased by $20.84."
Bad: "Based on the tool responses, it appears you spent more in February."

Good: "Starbucks: $386.63, Dunkin: $333.22, Total: $719.85"
Bad: "You spent a total of $719.85 at coffee shops."

**TOOLS:**
- analyze_by_category: Get spending for a category (call multiple times for comparisons)
- analyze_merchant: Get spending for a merchant (call multiple times for comparisons)
- search_transactions: Find transactions by keyword
- get_spending_summary: Overview of all categories

Remember: You're a calculator + interpreter, not just a messenger!"""


def get_enhanced_tools(agent):
    """Get tools with enhanced descriptions"""
    tools = agent.get_langchain_tools()
    
    # Update descriptions
    for tool in tools:
        if tool.name == "analyze_by_category":
            tool.description = ENHANCED_ANALYZE_BY_CATEGORY_DESCRIPTION
        elif tool.name == "analyze_merchant":
            tool.description = ENHANCED_ANALYZE_MERCHANT_DESCRIPTION
    
    return tools
```

#### Solution 4: Update app.py to Use New Architecture



```py
def process_query_improved(user_query):
    """Improved query processing with proper multi-step handling"""
    query_id = str(uuid.uuid4())
    session_id = st.session_state.get("session_id", "unknown")
    process_start_time = time.time()

    # Log query
    logger.log_query(query=user_query, session_id=session_id, query_id=query_id)
    logger.log_query_processing_start(query=user_query, session_id=session_id, query_id=query_id)

    try:
        # Get LangGraph agent
        agent = st.session_state.agent.get_langgraph_agent()
        
        # Track tool executions
        tool_executions = []
        
        # Custom callback to track tool calls
        class ToolTracker:
            def __init__(self):
                self.calls = []
            
            def on_tool_start(self, tool_name, tool_input):
                self.calls.append({
                    'name': tool_name,
                    'input': tool_input,
                    'start_time': time.time()
                })
            
            def on_tool_end(self, output):
                if self.calls:
                    call = self.calls[-1]
                    call['output'] = output
                    call['end_time'] = time.time()
                    call['duration'] = call['end_time'] - call['start_time']
        
        tracker = ToolTracker()
        
        # Prepare messages
        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        # Add current query
        messages.append(HumanMessage(content=user_query))
        
        # Run agent
        result = agent.invoke({
            "messages": messages,
            "intermediate_steps": [],
            "final_answer": ""
        })
        
        # Extract response from result
        if result.get("messages"):
            last_message = result["messages"][-1]
            raw_response = last_message.content if hasattr(last_message, "content") else str(last_message)
        else:
            raw_response = str(result)
        
        # Process tool results for better formatting
        tool_results = []
        for msg in result.get("messages", []):
            if isinstance(msg, ToolMessage):
                tool_results.append({
                    'content': msg.content,
                    'tool_name': getattr(msg, 'name', 'unknown'),
                    'args': {}
                })
        
        # Use ResponseProcessor to format the response
        from improved_response_processing import ResponseProcessor
        
        response = ResponseProcessor.process_response(
            query=user_query,
            response=raw_response,
            tool_results=tool_results
        )
        
        # Calculate response time
        response_time = time.time() - process_start_time
        
        # Update session state with results
        # Extract dataframe from last tool call if available
        if tracker.calls:
            last_call = tracker.calls[-1]
            tool_name = last_call['name']
            tool_args = last_call['input']
            
            try:
                result_info = st.session_state.handler_registry.handle_result(
                    tool_name, tool_args, user_query
                )
                
                if result_info.get("dataframe") is not None:
                    st.session_state.query_dataframe = result_info["dataframe"]
                    
                    logger.log_dataframe(
                        dataframe=result_info["dataframe"],
                        tool_name=tool_name,
                        session_id=session_id,
                        query_id=query_id,
                    )
                
                st.session_state.query_title = result_info["title"]
            except Exception as e:
                logger.log_warning(
                    message="Failed to process tool result",
                    context={"function": "process_query_improved", "error": str(e)},
                    session_id=session_id,
                )
        
        # Log response
        tool_names = ", ".join([call['name'] for call in tracker.calls]) if tracker.calls else None
        logger.log_response(
            query=user_query,
            response=response,
            response_time=response_time,
            tool_used=tool_names,
            session_id=session_id,
            query_id=query_id,
        )
        
        # Display response
        with st.chat_message("assistant"):
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        logger.log_response_displayed(
            response=response,
            session_id=session_id,
            query_id=query_id,
        )

    except Exception as e:
        error_msg = f"Error processing query: {str(e)}"
        response_time = time.time() - process_start_time
        
        logger.log_error(
            error=e,
            context={
                "function": "process_query_improved",
                "user_query": user_query,
                "response_time": response_time,
            },
            session_id=session_id,
            query_id=query_id,
        )
        
        with st.chat_message("assistant"):
            st.error(error_msg)
        st.session_state.messages.append({"role": "assistant", "content": error_msg})


# Alternative: Simpler fix with better prompt engineering
def process_query_simple_fix(user_query):
    """Simpler fix using better prompting with existing agent"""
    query_id = str(uuid.uuid4())
    session_id = st.session_state.get("session_id", "unknown")
    process_start_time = time.time()

    logger.log_query(query=user_query, session_id=session_id, query_id=query_id)
    
    try:
        agent = get_langchain_agent()  # Your existing agent
        
        # Enhanced query preprocessing
        enhanced_query = preprocess_query(user_query)
        
        # Create callback
        callback = ToolExecutionCallback(
            st.session_state.handler_registry,
            enhanced_query,
            session_id,
            query_id,
        )
        
        # Build messages
        messages = []
        for msg in st.session_state.messages:
            if msg["role"] == "user":
                messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                messages.append(AIMessage(content=msg["content"]))
        
        messages.append(HumanMessage(content=enhanced_query))
        
        # Run agent
        config = {"callbacks": [callback]}
        result = agent.invoke({"messages": messages}, config=config)
        
        # Extract response
        if result.get("messages"):
            last_message = result["messages"][-1]
            raw_response = last_message.content if hasattr(last_message, "content") else str(last_message)
        else:
            raw_response = str(result)
        
        # Process with ResponseProcessor
        from improved_response_processing import ResponseProcessor
        
        tool_results = []
        for call in callback.tool_calls:
            tool_results.append({
                'content': call.get('result', ''),
                'tool_name': call.get('name', ''),
                'args': call.get('args', {})
            })
        
        response = ResponseProcessor.process_response(
            query=user_query,
            response=raw_response,
            tool_results=tool_results
        )
        
        response_time = time.time() - process_start_time
        
        # Update UI and logging (same as before)
        with st.chat_message("assistant"):
            st.markdown(response)
        
        st.session_state.messages.append({"role": "assistant", "content": response})
        
        logger.log_response(
            query=user_query,
            response=response,
            response_time=response_time,
            session_id=session_id,
            query_id=query_id,
        )
        
    except Exception as e:
        # Error handling (same as before)
        pass


def preprocess_query(query: str) -> str:
    """Add explicit instructions to query for better agent behavior"""
    
    # Detect comparative queries
    comparative_keywords = ['vs', 'versus', 'compare', 'more', 'less', 'increase', 'decrease']
    is_comparative = any(kw in query.lower() for kw in comparative_keywords)
    
    if is_comparative:
        enhanced = f"""{query}

IMPORTANT: 
1. Call the necessary tools to get the data
2. Extract the "total_spent" value from EACH result
3. Calculate the difference yourself
4. Show me: 
   - The actual amounts (e.g., "January: $956.62, February: $977.46")
   - The difference (e.g., "Increased by $20.84")
   - A clear conclusion

Do NOT just say "you spent more" - show me the numbers!"""
        return enhanced
    
    return query

```
## Summary of Key Changes

### 1. **Use LangGraph Instead of Basic create_agent**
- Proper ReAct loop with explicit state management
- Better control over multi-step reasoning
- Cleaner tool chaining

### 2. **Response Processing, Not Response Extraction**
- Stop trying to "fix" bad responses with regex
- Instead, format responses properly from the start
- Extract numeric data from tool results and present it clearly

### 3. **Enhanced Tool Descriptions**
- Include explicit multi-step examples in tool descriptions
- Show the LLM exactly how to handle comparative queries
- Emphasize that the LLM must extract values and do calculations

### 4. **Better System Prompt**
- Clear instructions on multi-step patterns
- Explicit examples of good vs. bad responses
- Emphasis on extracting numeric values and doing calculations

## Quick Win: Simplest Fix

If you want the **fastest improvement** without major refactoring, do this:

1. **Update your system prompt** in `get_langchain_agent()` to include explicit multi-step instructions and examples (use the ENHANCED_SYSTEM_PROMPT)

2. **Add query preprocessing** to enhance comparative queries with explicit instructions

3. **Use the ResponseProcessor** to format responses based on detected query patterns

4. **Fix the tool descriptions** to include multi-step examples

This should get you from 0.21/1.0 to at least 0.6-0.7/1.0 average score without changing your architecture.

## Long-term Solution

For production quality, implement the full LangGraph solution:
- Gives you proper control over the ReAct loop
- Makes debugging much easier
- Allows for better error handling and retry logic
- Enables more sophisticated multi-step reasoning

