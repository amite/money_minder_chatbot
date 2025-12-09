# money_minder_chatbot

## Project Idea: Financial Transaction Query Agent

### **Tech Stack**
- **Ollama**: Mistral or llama3.1:8b-instruct-q4_K_M (good at tool calling)
- **Qdrant**: Store transaction embeddings
- **Python**: FastAPI/LangChain for orchestration
- **Data**: Bank transaction CSV/JSON

### **Environment Variables**

You can set environment variables either in your shell or in a `.env` file in the project root.

For **Qdrant Cloud** (remote instance), create a `.env` file with:
```bash
QDRANT_API_KEY=your-api-key-here
QDRANT_URL=https://your-cluster-id.qdrant.io
```

For **Local Qdrant behind reverse proxy** (e.g., Traefik), create a `.env` file with:
```bash
QDRANT_URL=https://qdrant.local
# No API key needed for local instances
```

For **Local Qdrant** (default):
- No environment variables needed - will connect to `localhost:6333` automatically

### Boot up the app
```bash
streamlit run app
```


### **Data Structure Example (transactions.csv)**
```csv
date,description,category,amount,merchant
2024-01-15,Starbucks Coffee,food,5.50,Starbucks
2024-01-16,Amazon Purchase,shopping,89.99,Amazon
2024-01-17,Netflix Subscription,entertainment,15.99,Netflix
```



### **Tool Calling Setup**
Create 3 tools for structured queries:

1. **Search Transactions Tool** - Vector search on descriptions
2. **Categorical Analysis Tool** - Filter by category/date ranges
3. **Summary Statistics Tool** - Calculate totals, averages

### **Limited Query Set (6-8 focused queries)**

1. **Descriptive Search**: 
   - "Find my coffee purchases last month"
   - "Show transactions at Amazon in January"

2. **Categorical Analysis**:
   - "What did I spend on groceries in Q1?"
   - "How much for entertainment vs shopping?"

3. **Statistical Queries**:
   - "What's my average food spending?"
   - "Show total by category last 3 months"
   - "What's my largest purchase this year?"

### **Implementation Steps**

```python
# Simplified architecture
1. Load CSV → Embed descriptions → Store in Qdrant
2. Create tool functions for 3 operations above
3. Set up Ollama with tool calling
4. Build agent that:
   - Classifies query type
   - Calls appropriate tool(s)
   - Formats structured response
```

### **Project Scope**
- **Focused scope**: 3 tools, limited query types
- **Structured data**: Easy to parse/embed
- **Clear evaluation**: You can test with sample queries
- **Extensible**: Add more categories/tools later

### **Sample Output Format**
```
Query: "How much did I spend on food in January?"
Agent Action:
- Calls categorical analysis tool (food, Jan 1-31)
- Returns: {"total": 245.50, "transactions": 12, "average": 20.46}
```

### **Test Questions (15 Questions for Quality Evaluation)**

The following 15 questions are used for response quality testing and cover various query types:

**Category Analysis:**
1. How much did I spend on shopping?
2. What were my food expenses in February 2024?
3. Analyze my transportation expenses
4. What's my total spending on entertainment?

**Merchant Analysis:**
5. Show me my Amazon spending
6. Analyze my Whole Foods spending grouped by category
7. How much did I spend at Walmart in March 2024?
8. What categories have I spent money on at Apple?
9. How much did I spend at CVS from January 1st to February 15th, 2024?
10. Show me my health expenses at Uber in February

**Spending Summary:**
11. What's my spending summary for last month?
12. Give me an overview of all my spending
13. Show me my spending breakdown for the last 3 months

**Search Queries:**
14. Find my coffee purchases
15. Show me all my Spotify transactions

Run quality tests with: `python test_response_quality.py`

