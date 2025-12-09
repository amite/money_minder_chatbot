# Architectural Approaches for Tool-Based LLM Systems

## Current Architecture Issues

### The Problem

As the system grows, we're accumulating conditional logic that doesn't scale:

1. **Hard-coded conditionals** for each tool (if/elif chains in `app.py`)
2. **Query pattern matching** for title generation and UI behavior
3. **Manual dataframe extraction** for each tool type
4. **Scattered UI logic** mixed with business logic

**Example of current approach:**
```python
if tool_name == "search_transactions":
    df = agent.search_transactions_df(...)
    title = f"📊 Search Results: '{query}'"
elif tool_name == "analyze_by_category":
    df = agent.analyze_by_category_df(...)
    title = f"📊 Category Analysis: {category}"
elif tool_name == "get_spending_summary":
    df = agent.get_spending_summary_df(...)
    # Check if query is about listing categories
    is_category_listing = any(word in query_lower for word in [...])
    if is_category_listing:
        title = "📊 Spending Categories"
    else:
        title = f"📊 Spending Summary: {period}"
elif tool_name == "analyze_merchant":
    df = agent.analyze_merchant_df(...)
    if group_by_category:
        title = f"📊 {merchant} Spending by Category"
    else:
        title = f"📊 {merchant} Transactions"
# ... and so on for each new tool
```

**Problems:**
- Adding 10 more tools = 10 more `elif` blocks
- Query pattern matching is brittle and hard to maintain
- UI logic is tightly coupled to tool implementation
- Difficult to test and refactor
- Code duplication across similar tools

## Real-World Architectural Patterns

### 1. Agent Frameworks (LangChain, LlamaIndex, AutoGen)

Production systems use frameworks that provide:

- **Tool Registry Pattern**: Centralized tool registration and discovery
- **Plugin Architecture**: Extensible tool system with standardized interfaces
- **Result Formatting Pipeline**: Generic handlers for different result types
- **Orchestration**: Multi-tool query handling and tool chaining

**Example (LangChain-style):**
```python
from langchain.tools import BaseTool
from langchain.agents import AgentExecutor

class AnalyzeMerchantTool(BaseTool):
    name = "analyze_merchant"
    description = "Analyze merchant spending"
    
    def _run(self, merchant: str, group_by_category: bool = False):
        # Tool implementation
        return result
    
    def _arun(self, merchant: str):
        raise NotImplementedError

# Framework handles:
# - Tool registration
# - Result formatting
# - Error handling
# - Multi-tool orchestration
```

**Pros:**
- Battle-tested patterns
- Handles complexity automatically
- Good documentation and community
- Built-in error handling and retries

**Cons:**
- Learning curve
- More dependencies
- Might be overkill for smaller systems
- Less control over internals

### 2. Structured Tool Result Schemas

Define metadata for each tool, then use generic renderers:

```python
TOOL_METADATA = {
    "analyze_merchant": {
        "result_type": "merchant_analysis",
        "has_dataframe": True,
        "dataframe_method": "analyze_merchant_df",
        "title_template": "📊 {merchant} {mode}",
        "title_logic": lambda args: (
            f"📊 {args['merchant']} Spending by Category"
            if args.get("group_by_category")
            else f"📊 {args['merchant']} Transactions"
        ),
        "visualization": {
            "type": "conditional",
            "condition": lambda args: args.get("group_by_category"),
            "chart_type": "bar_chart"
        }
    },
    "get_spending_summary": {
        "result_type": "summary",
        "has_dataframe": True,
        "dataframe_method": "get_spending_summary_df",
        "title_template": "📊 Spending Summary: {period}",
        "query_detection": {
            "category_listing": {
                "keywords": ["list", "types", "kinds", "categories"],
                "title_override": "📊 Spending Categories"
            }
        },
        "visualization": "bar_chart"
    }
}

# Generic handler
def handle_tool_result(tool_name, result, tool_args, user_query):
    metadata = TOOL_METADATA.get(tool_name, {})
    
    # Get dataframe if available
    df = None
    if metadata.get("has_dataframe"):
        df_method = getattr(agent, metadata["dataframe_method"])
        df = df_method(**tool_args)
    
    # Generate title
    title = generate_title(metadata, tool_args, user_query)
    
    return {"dataframe": df, "title": title, "visualization": metadata.get("visualization")}
```

**Pros:**
- Declarative configuration
- Easy to add new tools
- Centralized logic
- Testable

**Cons:**
- Requires upfront design
- Can become complex with many edge cases

### 3. LLM-Based Result Formatting

Let the LLM format results instead of hard-coding:

```python
def format_tool_result(tool_name, result, tool_args, user_query):
    formatting_prompt = f"""
    Tool: {tool_name}
    Result: {result}
    User Query: {user_query}
    Tool Arguments: {tool_args}
    
    Generate:
    1. A natural, descriptive title for this result
    2. What type of visualization would be helpful (bar_chart, line_chart, table, none)
    3. Key insights to highlight in the response
    
    Return JSON:
    {{
        "title": "...",
        "visualization": "...",
        "insights": ["...", "..."]
    }}
    """
    
    response = llm.chat(formatting_prompt)
    formatted = json.loads(response)
    return formatted
```

**Pros:**
- Adapts to new tools automatically
- Natural language titles
- Context-aware formatting

**Cons:**
- Extra LLM call (latency + cost)
- Less predictable
- May need validation

### 4. Chain of Responsibility Pattern

Process results through a pipeline of handlers:

```python
class ResultHandler:
    def handle(self, tool_name, result, context, output):
        raise NotImplementedError

class DataFrameExtractor(ResultHandler):
    def handle(self, tool_name, result, context, output):
        metadata = context.get("metadata", {})
        if metadata.get("has_dataframe"):
            df_method = getattr(agent, metadata["dataframe_method"])
            output["dataframe"] = df_method(**context["tool_args"])
        return output

class TitleGenerator(ResultHandler):
    def handle(self, tool_name, result, context, output):
        metadata = context.get("metadata", {})
        if "title_logic" in metadata:
            output["title"] = metadata["title_logic"](context["tool_args"])
        elif "title_template" in metadata:
            output["title"] = metadata["title_template"].format(**context["tool_args"])
        return output

class VisualizationSelector(ResultHandler):
    def handle(self, tool_name, result, context, output):
        metadata = context.get("metadata", {})
        viz_config = metadata.get("visualization")
        if viz_config:
            output["visualization"] = determine_visualization(viz_config, context)
        return output

class ResultProcessor:
    def __init__(self):
        self.handlers = [
            DataFrameExtractor(),
            TitleGenerator(),
            VisualizationSelector(),
            InsightExtractor()
        ]
    
    def process(self, tool_name, result, context):
        output = {}
        for handler in self.handlers:
            output = handler.handle(tool_name, result, context, output)
        return output
```

**Pros:**
- Highly extensible
- Single responsibility per handler
- Easy to test individual components
- Can add/remove handlers dynamically

**Cons:**
- More complex setup
- Overhead for simple cases
- Requires careful design

## Recommended Approaches for This System

### Option 1: Tool Metadata Registry (Recommended for Current Scale)

**Best for:** 4-15 tools, need quick refactoring, want to maintain control

**Implementation:**

```python
# agent.py
class FinancialAgent:
    def __init__(self):
        # ... existing code ...
        self.tool_metadata = {
            "analyze_merchant": {
                "dataframe_method": "analyze_merchant_df",
                "title_generator": self._generate_merchant_title,
                "visualization": lambda args: "category_chart" if args.get("group_by_category") else None
            },
            "get_spending_summary": {
                "dataframe_method": "get_spending_summary_df",
                "title_generator": self._generate_summary_title,
                "visualization": "bar_chart",
                "query_detection": {
                    "category_listing": {
                        "keywords": ["list", "types", "kinds", "categories", "expenditures", "spendings"],
                        "title_override": "📊 Spending Categories"
                    }
                }
            },
            "analyze_by_category": {
                "dataframe_method": "analyze_by_category_df",
                "title_generator": lambda args, query: f"📊 Category Analysis: {args.get('category', '').title()}",
                "visualization": "bar_chart"
            },
            "search_transactions": {
                "dataframe_method": "search_transactions_df",
                "title_generator": lambda args, query: f"📊 Search Results: '{args.get('query', '')}'",
                "visualization": None
            }
        }
    
    def _generate_merchant_title(self, tool_args, user_query):
        merchant = tool_args.get("merchant", "")
        if tool_args.get("group_by_category"):
            return f"📊 {merchant} Spending by Category"
        return f"📊 {merchant} Transactions"
    
    def _generate_summary_title(self, tool_args, user_query):
        # Check for category listing query
        query_lower = user_query.lower()
        metadata = self.tool_metadata["get_spending_summary"]
        if "query_detection" in metadata:
            detection = metadata["query_detection"].get("category_listing", {})
            keywords = detection.get("keywords", [])
            if any(word in query_lower for word in keywords):
                return detection.get("title_override", "📊 Spending Categories")
        
        period = tool_args.get("period", "last_month").replace("_", " ").title()
        return f"📊 Spending Summary: {period}"
    
    def get_tool_metadata(self, tool_name):
        return self.tool_metadata.get(tool_name, {})

# app.py - Generic handler
def handle_tool_result(tool_name, tool_args, result, user_query):
    metadata = agent.get_tool_metadata(tool_name)
    
    # Get dataframe
    df = None
    if "dataframe_method" in metadata:
        df_method = getattr(agent, metadata["dataframe_method"])
        df = df_method(**tool_args)
        st.session_state.query_dataframe = df
    
    # Generate title
    if "title_generator" in metadata:
        title_generator = metadata["title_generator"]
        if callable(title_generator):
            title = title_generator(tool_args, user_query)
        else:
            title = title_generator
        st.session_state.query_title = title
    
    # Handle visualization
    if "visualization" in metadata:
        viz_config = metadata["visualization"]
        if callable(viz_config):
            viz_type = viz_config(tool_args)
        else:
            viz_type = viz_config
        # Use viz_type to render appropriate chart
```

**Benefits:**
- Removes all if/elif chains
- Easy to add new tools (just add metadata)
- Centralized logic
- Minimal refactoring required
- Maintains full control

**Implementation Time:** 1-2 hours

### Option 2: Plugin System (More Extensible)

**Best for:** 10+ tools, need maximum flexibility, team development

```python
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any
import pandas as pd

class ToolPlugin(ABC):
    """Base class for tool plugins"""
    
    @property
    @abstractmethod
    def tool_name(self) -> str:
        """Return the tool name"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> str:
        """Execute tool and return JSON result"""
        pass
    
    @abstractmethod
    def get_dataframe(self, **kwargs) -> pd.DataFrame:
        """Get result as DataFrame"""
        pass
    
    def generate_title(self, tool_args: Dict, user_query: str) -> str:
        """Generate display title - can be overridden"""
        return f"📊 {self.tool_name.replace('_', ' ').title()}"
    
    def get_visualization(self, result: Dict, tool_args: Dict) -> Optional[str]:
        """Return visualization type if applicable"""
        return None
    
    def should_visualize(self, result: Dict, tool_args: Dict) -> bool:
        """Determine if visualization should be shown"""
        return False

class AnalyzeMerchantPlugin(ToolPlugin):
    tool_name = "analyze_merchant"
    
    def __init__(self, agent):
        self.agent = agent
    
    def execute(self, **kwargs):
        return self.agent.analyze_merchant(**kwargs)
    
    def get_dataframe(self, **kwargs):
        return self.agent.analyze_merchant_df(**kwargs)
    
    def generate_title(self, tool_args, user_query):
        merchant = tool_args.get("merchant", "")
        if tool_args.get("group_by_category"):
            return f"📊 {merchant} Spending by Category"
        return f"📊 {merchant} Transactions"
    
    def get_visualization(self, result, tool_args):
        if tool_args.get("group_by_category"):
            return "bar_chart"
        return None

class SpendingSummaryPlugin(ToolPlugin):
    tool_name = "get_spending_summary"
    
    def __init__(self, agent):
        self.agent = agent
    
    def execute(self, **kwargs):
        return self.agent.get_spending_summary(**kwargs)
    
    def get_dataframe(self, **kwargs):
        return self.agent.get_spending_summary_df(**kwargs)
    
    def generate_title(self, tool_args, user_query):
        query_lower = user_query.lower()
        category_keywords = ["list", "types", "kinds", "categories", "expenditures", "spendings"]
        
        if any(word in query_lower for word in category_keywords):
            return "📊 Spending Categories"
        
        period = tool_args.get("period", "last_month").replace("_", " ").title()
        return f"📊 Spending Summary: {period}"

# Plugin Registry
class PluginRegistry:
    def __init__(self):
        self.plugins = {}
    
    def register(self, plugin: ToolPlugin):
        self.plugins[plugin.tool_name] = plugin
    
    def get_plugin(self, tool_name: str) -> Optional[ToolPlugin]:
        return self.plugins.get(tool_name)
    
    def handle_tool_result(self, tool_name: str, tool_args: Dict, result: str, user_query: str):
        plugin = self.get_plugin(tool_name)
        if not plugin:
            return None
        
        df = plugin.get_dataframe(**tool_args)
        title = plugin.generate_title(tool_args, user_query)
        visualization = plugin.get_visualization(json.loads(result), tool_args)
        
        return {
            "dataframe": df,
            "title": title,
            "visualization": visualization
        }

# Usage
registry = PluginRegistry()
registry.register(AnalyzeMerchantPlugin(agent))
registry.register(SpendingSummaryPlugin(agent))
# ... register all plugins

# In app.py
result_info = registry.handle_tool_result(tool_name, tool_args, result, user_query)
if result_info:
    st.session_state.query_dataframe = result_info["dataframe"]
    st.session_state.query_title = result_info["title"]
```

**Benefits:**
- Maximum flexibility
- Each tool is self-contained
- Easy to test individual plugins
- Can add plugin-specific logic easily
- Supports inheritance and composition

**Implementation Time:** 3-4 hours

### Option 3: LangChain Integration (Most Robust)

**Best for:** Production systems, 15+ tools, need advanced features

```python
from langchain.tools import BaseTool
from langchain.agents import initialize_agent, AgentType
from langchain.llms import OllamaLLM

class AnalyzeMerchantTool(BaseTool):
    name = "analyze_merchant"
    description = "Analyze spending for a specific merchant, optionally grouped by category"
    
    def _run(self, merchant: str, group_by_category: bool = False, 
             start_date: str = None, end_date: str = None):
        return agent.analyze_merchant(
            merchant=merchant,
            group_by_category=group_by_category,
            start_date=start_date,
            end_date=end_date
        )
    
    def _arun(self, merchant: str):
        raise NotImplementedError("Async not supported")

# LangChain handles:
# - Tool registration
# - Result formatting
# - Error handling
# - Multi-tool queries
# - Streaming responses

tools = [
    AnalyzeMerchantTool(),
    AnalyzeByCategoryTool(),
    GetSpendingSummaryTool(),
    SearchTransactionsTool()
]

agent_executor = initialize_agent(
    tools=tools,
    llm=OllamaLLM(model="llama3.1:8b-instruct-q4_K_M"),
    agent=AgentType.OPENAI_FUNCTIONS,
    verbose=True
)

result = agent_executor.run(user_query)
```

**Benefits:**
- Production-ready patterns
- Handles complexity automatically
- Built-in error handling
- Multi-tool orchestration
- Good documentation

**Cons:**
- Learning curve
- More dependencies
- Less control
- Might be overkill

**Implementation Time:** 1-2 days (including learning curve)

## Ollama vs OpenAI: Impact Analysis

### Current Issues That LLM Choice Affects

1. **Date Parameter Extraction**
   - **Ollama**: Sometimes incorrectly infers dates
   - **OpenAI**: Better at following "only extract if explicit" instructions
   - **Impact**: Medium - can be mitigated with better prompts

2. **Tool Selection Accuracy**
   - **Ollama**: Generally good, occasional mistakes
   - **OpenAI**: More consistent, better at edge cases
   - **Impact**: Low - current tool selection works well

3. **Response Formatting**
   - **Ollama**: Sometimes includes tool call JSON in responses
   - **OpenAI**: More consistent response formatting
   - **Impact**: Low - can be handled with filters

4. **Structured Output**
   - **Ollama**: Limited structured output support
   - **OpenAI**: Native JSON mode and structured outputs
   - **Impact**: Medium - could simplify result formatting

### Cost Comparison

**Ollama:**
- Free (runs locally)
- No API costs
- Requires local GPU/CPU resources

**OpenAI:**
- ~$0.002-0.01 per 1K tokens (depending on model)
- For 100 queries/day: ~$5-20/month
- No local resources needed

### Recommendation

**Stick with Ollama for now if:**
- You're in development/early stage
- Cost is a concern
- You have local compute resources
- Current reliability is acceptable

**Consider OpenAI if:**
- You need production-grade reliability
- You want structured outputs
- Cost is acceptable
- You need better instruction following

**Key Insight:** Architecture improvements will help more than switching LLMs. Fix the structure first, then evaluate LLM choice.

## Migration Path

### Phase 1: Quick Win (1-2 hours)
Implement **Tool Metadata Registry** to remove conditional logic:
- Add metadata dictionary to `FinancialAgent`
- Create generic `handle_tool_result()` function
- Replace all if/elif chains with metadata lookup

### Phase 2: Refinement (2-4 hours)
Enhance metadata system:
- Add visualization configuration
- Implement query detection patterns
- Add error handling

### Phase 3: Evaluation (1-2 weeks)
- Monitor system with new architecture
- Collect metrics on tool usage
- Identify pain points

### Phase 4: Decision Point
**If system is working well:**
- Continue with metadata registry
- Add more tools as needed

**If you need more features:**
- Consider migrating to Plugin System
- Or evaluate LangChain for advanced features

**If reliability becomes critical:**
- Evaluate OpenAI for better instruction following
- Consider hybrid approach (Ollama for dev, OpenAI for prod)

## Best Practices

### 1. Separation of Concerns
- **Agent**: Tool execution logic only
- **Metadata/Plugins**: Result formatting and UI concerns
- **App**: Orchestration and UI rendering

### 2. Declarative Over Imperative
- Define what tools do, not how to handle them
- Use metadata/configuration over conditionals

### 3. Extensibility
- Design for adding new tools easily
- Avoid hard-coding tool-specific logic in generic handlers

### 4. Testability
- Each component should be testable in isolation
- Mock tool results for testing handlers

### 5. Error Handling
- Graceful degradation when tools fail
- Clear error messages for users
- Logging for debugging

## Conclusion

The current conditional approach doesn't scale. Real-world systems use:

1. **Declarative metadata** (Tool Metadata Registry) - Best for your current scale
2. **Plugin architectures** - Best for larger, more complex systems
3. **Agent frameworks** - Best for production systems needing advanced features

**Recommended Next Step:** Implement Tool Metadata Registry (Option 1) to immediately improve maintainability while keeping the system simple and under your control.

