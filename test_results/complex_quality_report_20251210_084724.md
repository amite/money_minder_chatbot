# Complex Scenario Test Results

**Generated:** 2025-12-10 08:47:24
**Report Version:** 20251210_084724

---

## Executive Summary

- **Total Scenarios Tested:** 15
- **Passed:** 0 (0.0%)
- **Failed:** 15
- **Average Response Time:** 2.36s
- **Average Final Score:** 0.21/1.0

### Overall Performance

**Performance Rating:** ❌ **Needs Improvement**

---

## Performance by Difficulty

| Difficulty | Count | Passed | Pass Rate | Avg Score | Avg Time |
|-----------|-------|--------|----------|----------|----------|
| EASY | 1 | 0 | 0.0% | 0.36 | 2.40s |
| HARD | 9 | 0 | 0.0% | 0.18 | 2.50s |
| MEDIUM | 5 | 0 | 0.0% | 0.25 | 2.10s |

---

## Score Breakdown by Metric

| Metric | Average Score |
|--------|---------------|
| Tool Selection | 0.62/1.0 |
| Reasoning | 0.41/1.0 |
| Accuracy | 0.32/1.0 |
| Completeness | 0.47/1.0 |

---

## Detailed Results

### 1. Which category did I spend more on in February: food or shopping?

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_001
**Response Time:** 3.24s

**Scores:**
- Tool Selection: 1.00/1.0
- Reasoning: 0.52/1.0
- Accuracy: 0.75/1.0
- Completeness: 0.67/1.0

**Final Score:** 0.37/1.0

**Response:**
```
Based on the tool call responses, it appears that you spent more on food in February than shopping. The total amount spent on food was $977.46, while the total amount spent on shopping was $217.60. Therefore, your category of choice for spending in February is food.
```

**Tools Used:** analyze_by_category, analyze_by_category

---

### 2. Did my food spending increase or decrease from January to February?

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_002
**Response Time:** 0.56s

**Scores:**
- Tool Selection: 1.00/1.0
- Reasoning: 0.55/1.0
- Accuracy: 0.80/1.0
- Completeness: 0.33/1.0

**Final Score:** 0.35/1.0

**Response:**
```
Based on the tool call responses, it appears that your food spending increased from January to February. In January, you spent a total of $956.62, while in February, you spent a total of $977.46. This represents an increase of approximately $20.84 over the two-month period.
```

**Tools Used:** analyze_by_category, analyze_by_category

---

### 3. What were my 3 largest shopping purchases at Amazon?

**Status:** ❌ FAIL
**Difficulty:** medium
**Scenario ID:** complex_003
**Response Time:** 1.40s

**Scores:**
- Tool Selection: 0.00/1.0
- Reasoning: 0.25/1.0
- Accuracy: 0.00/1.0
- Completeness: 0.33/1.0

**Final Score:** 0.09/1.0

**Response:**
```
{"name": "analyze_merchant", "parameters": {"merchant": "Amazon", "group_by_category": False, "start_date": "all_time", "end_date": "all_time"}}
```

---

### 4. What percentage of my total spending went to subscriptions?

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_004
**Response Time:** 2.05s

**Scores:**
- Tool Selection: 0.50/1.0
- Reasoning: 0.80/1.0
- Accuracy: 0.00/1.0
- Completeness: 1.00/1.0

**Final Score:** 0.26/1.0

**Response:**
```
Based on the spending summary, we can calculate the percentage of total spending that went to subscriptions.

The total spent is $8,761.65 and the amount spent on subscriptions (entertainment) is $496.29.

To find the percentage, divide the amount spent on subscriptions by the total spent and multiply by 100:

($496.29 ÷ $8,761.65) x 100 = 5.66%

So, approximately 5.66% of your total spending went to subscriptions.
```

**Tools Used:** get_spending_summary

---

### 5. What's my average grocery spending per week, excluding any trips over $100?

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_005
**Response Time:** 1.90s

**Final Score:** 0.00/1.0

**Error:**
```
Unknown datetime string format, unable to parse: last_week, at position 0
```

---

### 6. How much did I spend at coffee shops (Starbucks and Dunkin) in total?

**Status:** ❌ FAIL
**Difficulty:** medium
**Scenario ID:** complex_006
**Response Time:** 2.20s

**Scores:**
- Tool Selection: 1.00/1.0
- Reasoning: 0.58/1.0
- Accuracy: 0.50/1.0
- Completeness: 0.33/1.0

**Final Score:** 0.41/1.0

**Response:**
```
Based on the tool call responses, you spent a total of $386.63 at Starbucks and $333.22 at Dunkin. Therefore, your total spending at these two coffee shops is $719.85.
```

**Tools Used:** analyze_merchant, analyze_merchant

---

### 7. Show me all entertainment expenses over $20

**Status:** ❌ FAIL
**Difficulty:** medium
**Scenario ID:** complex_007
**Response Time:** 3.89s

**Scores:**
- Tool Selection: 0.00/1.0
- Reasoning: 0.25/1.0
- Accuracy: 0.33/1.0
- Completeness: 0.33/1.0

**Final Score:** 0.15/1.0

**Response:**
```
Based on the search results, here are all entertainment expenses over $20:

1. Date: 2024-01-12 | Description: iTunes | Category: entertainment | Amount: $96.55 | Merchant: Apple
2. Date: 2024-02-26 | Description: Music subscription | Category: entertainment | Amount: $10.99 | Merchant: Spotify
3. Date: 2024-03-26 | Description: Subscription | Category: entertainment | Amount: $15.49 | Merchant: Netflix
4. Date: 2024-01-20 | Description: Online shopping | Category: entertainment | Amount: $126.0...
```

**Tools Used:** search_transactions

---

### 8. How many times per week do I go to Starbucks on average?

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_008
**Response Time:** 1.33s

**Final Score:** 0.00/1.0

**Error:**
```
Unknown datetime string format, unable to parse: all_time, at position 0
```

---

### 9. At Amazon, did I spend more on shopping or entertainment?

**Status:** ❌ FAIL
**Difficulty:** medium
**Scenario ID:** complex_009
**Response Time:** 1.12s

**Scores:**
- Tool Selection: 1.00/1.0
- Reasoning: 0.48/1.0
- Accuracy: 0.50/1.0
- Completeness: 0.00/1.0

**Final Score:** 0.35/1.0

**Response:**
```
Based on the tool call response, it appears that you spent more on shopping ($635.81) than entertainment ($126.07) at Amazon.
```

**Tools Used:** analyze_merchant

---

### 10. Did I make any purchases at Target in January?

**Status:** ❌ FAIL
**Difficulty:** easy
**Scenario ID:** complex_010
**Response Time:** 2.40s

**Scores:**
- Tool Selection: 1.00/1.0
- Reasoning: 0.17/1.0
- Accuracy: 0.00/1.0
- Completeness: 0.33/1.0

**Final Score:** 0.36/1.0

**Response:**
```
Based on the tool call response, it appears that you made 7 purchases at Target in January, with a total spend of $676.73 and an average transaction value of $96.68. The minimum transaction was $52.58 and the maximum transaction was $136.90. The categories of your purchases included health, food, and shopping.
```

**Tools Used:** analyze_merchant

---

### 11. Which months did I spend over $300 on food?

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_011
**Response Time:** 1.45s

**Final Score:** 0.00/1.0

**Error:**
```
Out of bounds nanosecond timestamp: 9999-12-31, at position 0
```

---

### 12. What's the ratio of my dining out expenses to grocery expenses?

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_012
**Response Time:** 2.57s

**Scores:**
- Tool Selection: 0.50/1.0
- Reasoning: 0.60/1.0
- Accuracy: 0.00/1.0
- Completeness: 1.00/1.0

**Final Score:** 0.24/1.0

**Response:**
```
Based on the tool call responses, it appears that there are no transactions in either the "dining out" or "grocery" categories. Therefore, we cannot calculate a ratio of your dining out expenses to grocery expenses.

However, if you provide more information about your transaction history or categorization, I can try to help you with the calculation.
```

**Tools Used:** analyze_by_category, analyze_by_category

---

### 13. How much have I spent on health this quarter?

**Status:** ❌ FAIL
**Difficulty:** medium
**Scenario ID:** complex_013
**Response Time:** 1.87s

**Scores:**
- Tool Selection: 1.00/1.0
- Reasoning: 0.17/1.0
- Accuracy: 0.00/1.0
- Completeness: 0.33/1.0

**Final Score:** 0.24/1.0

**Response:**
```
Since there are no transactions in the 'health' category, you have spent $0 on health this quarter.
```

**Tools Used:** analyze_by_category

---

### 14. Show me all gas station transactions where I also bought food

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_014
**Response Time:** 9.22s

**Scores:**
- Tool Selection: 0.50/1.0
- Reasoning: 0.38/1.0
- Accuracy: 0.67/1.0
- Completeness: 0.67/1.0

**Final Score:** 0.28/1.0

**Response:**
```
Here is a summary of the transactions:

**Food and Beverage**

* Starbucks: 14 transactions, total amount: $234.41
* Whole Foods: 1 transaction, total amount: $80.49
* CVS: 1 transaction, total amount: $55.50
* Walgreens: 2 transactions, total amount: $87.18

**Transportation**

* Lyft: 3 transactions, total amount: $113.08
* Uber: 4 transactions, total amount: $97.19
* Exxon: 6 transactions, total amount: $261.41
* Con Edison (electric bill): 2 transactions, total amount: $223.10

**Shopping**
...
```

**Tools Used:** search_transactions

---

### 15. Find all shopping transactions over $50 at either Amazon or Target in February

**Status:** ❌ FAIL
**Difficulty:** hard
**Scenario ID:** complex_015
**Response Time:** 0.19s

**Scores:**
- Tool Selection: 0.00/1.0
- Reasoning: 0.20/1.0
- Accuracy: 0.33/1.0
- Completeness: 0.25/1.0

**Final Score:** 0.10/1.0

**Response:**
```
{"name": "analyze_merchant", "parameters": {"merchant": "Amazon", "start_date": "2024-02-01", "end_date": "2024-02-29", "group_by_category": True}} 
{"name": "analyze_merchant", "parameters": {"merchant": "Target", "start_date": "2024-02-01", "end_date": "2024-02-29", "group_by_category": True}}
{"name": "search_transactions", "parameters": {"query": "shopping", "limit": 50}}
```

---

## Failed Scenarios

### Which category did I spend more on in February: food or shopping?
- **ID:** complex_001
- **Difficulty:** hard
- **Score:** 0.37/1.0
- **Error:** None

### Did my food spending increase or decrease from January to February?
- **ID:** complex_002
- **Difficulty:** hard
- **Score:** 0.35/1.0
- **Error:** None

### What were my 3 largest shopping purchases at Amazon?
- **ID:** complex_003
- **Difficulty:** medium
- **Score:** 0.09/1.0
- **Error:** None

### What percentage of my total spending went to subscriptions?
- **ID:** complex_004
- **Difficulty:** hard
- **Score:** 0.26/1.0
- **Error:** None

### What's my average grocery spending per week, excluding any trips over $100?
- **ID:** complex_005
- **Difficulty:** hard
- **Score:** 0.00/1.0
- **Error:** Unknown datetime string format, unable to parse: last_week, at position 0

### How much did I spend at coffee shops (Starbucks and Dunkin) in total?
- **ID:** complex_006
- **Difficulty:** medium
- **Score:** 0.41/1.0
- **Error:** None

### Show me all entertainment expenses over $20
- **ID:** complex_007
- **Difficulty:** medium
- **Score:** 0.15/1.0
- **Error:** None

### How many times per week do I go to Starbucks on average?
- **ID:** complex_008
- **Difficulty:** hard
- **Score:** 0.00/1.0
- **Error:** Unknown datetime string format, unable to parse: all_time, at position 0

### At Amazon, did I spend more on shopping or entertainment?
- **ID:** complex_009
- **Difficulty:** medium
- **Score:** 0.35/1.0
- **Error:** None

### Did I make any purchases at Target in January?
- **ID:** complex_010
- **Difficulty:** easy
- **Score:** 0.36/1.0
- **Error:** None

### Which months did I spend over $300 on food?
- **ID:** complex_011
- **Difficulty:** hard
- **Score:** 0.00/1.0
- **Error:** Out of bounds nanosecond timestamp: 9999-12-31, at position 0

### What's the ratio of my dining out expenses to grocery expenses?
- **ID:** complex_012
- **Difficulty:** hard
- **Score:** 0.24/1.0
- **Error:** None

### How much have I spent on health this quarter?
- **ID:** complex_013
- **Difficulty:** medium
- **Score:** 0.24/1.0
- **Error:** None

### Show me all gas station transactions where I also bought food
- **ID:** complex_014
- **Difficulty:** hard
- **Score:** 0.28/1.0
- **Error:** None

### Find all shopping transactions over $50 at either Amazon or Target in February
- **ID:** complex_015
- **Difficulty:** hard
- **Score:** 0.10/1.0
- **Error:** None

---

## Recommendations

- **Critical:** Pass rate is below acceptable threshold (70%)
- Review failed scenarios and improve tool selection logic
- Check LLM responses for accuracy and completeness
- Consider improving tool descriptions and examples

---

*Report generated by test_complex_scenarios_runner.py*
*For detailed JSON data, see the corresponding complex_results_20251210_084724.json file*