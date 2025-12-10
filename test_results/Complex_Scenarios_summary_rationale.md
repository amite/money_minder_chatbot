# Complex Test Scenarios for Agent Robustness

## Overview
These 15 scenarios test critical capabilities beyond simple tool calling:
- **Multi-step reasoning** (requires chaining multiple tool calls)
- **Comparative analysis** (requires comparing results)
- **Temporal intelligence** (understands time periods and trends)
- **Edge case handling** (negative results, missing data)
- **Complex filtering** (multiple constraints simultaneously)

---

## Scenarios by Testing Category

### 1. Multi-Step Reasoning (Scenarios 1, 2, 6)

#### Scenario 1: Category Comparison
**Query:** "Which category did I spend more on in February: food or shopping?"

**Why it's critical:**
- Requires TWO tool calls (analyze_by_category for each)
- Must hold first result in memory while getting second
- Must perform comparison logic
- Tests: Can agent break down complex questions?

**What you'll learn:**
- Does agent make single call expecting one tool to do both?
- Does it correctly compare numerical results?
- Does it provide clear answer format?

---

#### Scenario 2: Trend Analysis
**Query:** "Did my food spending increase or decrease from January to February?"

**Why it's critical:**
- Requires temporal reasoning across two periods
- Must calculate percentage/absolute change
- Must interpret trend direction

**What you'll learn:**
- Can agent understand temporal comparisons?
- Does it provide context (how much increase/decrease)?
- Does it handle edge case where spending is equal?

---

### 2. Filtering & Ranking (Scenarios 3, 5, 7, 15)

#### Scenario 3: Top N with Multiple Constraints
**Query:** "What were my 3 largest shopping purchases at Amazon?"

**Why it's critical:**
- Requires filtering by merchant AND category
- Must sort by amount
- Must limit to N results

**What you'll learn:**
- Does agent correctly apply multiple filters?
- Can it rank/sort results?
- Does it return exactly N items (not all)?

---

#### Scenario 5: Outlier Filtering
**Query:** "What's my average grocery spending per week, excluding any trips over $100?"

**Why it's critical:**
- Tests negative filtering (excluding, not including)
- Requires weekly aggregation
- Real-world scenario (removing outliers from averages)

**What you'll learn:**
- Can agent understand exclusion logic?
- Does it correctly identify grocery merchants?
- Can it calculate weekly averages?

---

### 3. Percentage & Ratio Analysis (Scenarios 4, 12)

#### Scenario 4: Percentage Calculation
**Query:** "What percentage of my total spending went to subscriptions?"

**Why it's critical:**
- Must identify subscription pattern (not explicit in data)
- Requires two totals (subscriptions vs all)
- Must calculate percentage correctly

**What you'll learn:**
- Can agent identify subscriptions without being told?
- Does it include all subscription types (streaming, gym)?
- Is percentage calculation accurate?

---

#### Scenario 12: Ratio Analysis
**Query:** "What's the ratio of my dining out expenses to grocery expenses?"

**Why it's critical:**
- Must categorize merchants into dining vs grocery
- Calculate ratio (not just difference)
- Present in meaningful format

**What you'll learn:**
- Can agent infer dining vs grocery from merchant names?
- Does it understand ratio vs percentage vs difference?
- How does it present ratios (1.5:1 vs 1.5x)?

---

### 4. Frequency & Pattern Detection (Scenarios 8, 14)

#### Scenario 8: Visit Frequency
**Query:** "How many times per week do I go to Starbucks on average?"

**Why it's critical:**
- Must calculate time period in weeks
- Divide transaction count by weeks
- Real metric users want to track

**What you'll learn:**
- Can agent calculate temporal averages?
- Does it handle edge case of irregular patterns?
- Does it present in user-friendly format?

---

#### Scenario 14: Pattern Recognition
**Query:** "Show me all gas station transactions where I also bought food"

**Why it's critical:**
- Must identify gas station merchants
- Understand that food at gas station = convenience store
- Real-world scenario (tracking combined purchases)

**What you'll learn:**
- Can agent understand implicit patterns?
- Does it correctly identify gas stations?
- Can it filter by category within merchant?

---

### 5. Comparison & Benchmarking (Scenarios 6, 9)

#### Scenario 6: Multi-Merchant Aggregation
**Query:** "How much did I spend at coffee shops (Starbucks and Dunkin) in total?"

**Why it's critical:**
- User groups merchants by category (coffee shops)
- Must aggregate multiple merchants
- Tests semantic understanding

**What you'll learn:**
- Can agent understand category groupings?
- Does it include all relevant merchants?
- Does it sum correctly?

---

#### Scenario 9: Within-Merchant Category Comparison
**Query:** "At Amazon, did I spend more on shopping or entertainment?"

**Why it's critical:**
- Requires merchant analysis WITH category breakdown
- Must compare within single merchant
- Tests group_by_category parameter usage

**What you'll learn:**
- Does agent use analyze_merchant with group_by_category=true?
- Can it compare categories within one merchant?
- Does it provide clear comparison?

---

### 6. Existence & Negative Cases (Scenarios 10, 11)

#### Scenario 10: Existence Check
**Query:** "Did I make any purchases at Target in January?"

**Why it's critical:**
- Simple yes/no question
- Must handle empty result gracefully
- Common user question type

**What you'll learn:**
- Does agent provide clear yes/no answer?
- If yes, does it provide useful details?
- If no, does it confirm (not just error)?

---

#### Scenario 11: Threshold Detection
**Query:** "Which months did I spend over $300 on food?"

**Why it's critical:**
- Requires grouping by month
- Apply threshold filter
- Return list of matches

**What you'll learn:**
- Can agent group by temporal units?
- Does it correctly apply threshold?
- Does it return all matching months?

---

### 7. Temporal Interpretation (Scenarios 2, 13)

#### Scenario 13: Ambiguous Time Reference
**Query:** "How much have I spent on health this quarter?"

**Why it's critical:**
- "This quarter" is ambiguous (Q1 2024)
- Must interpret based on data date range
- Real users use relative time references

**What you'll learn:**
- Can agent interpret "this quarter"?
- Does it calculate correct date range (Jan-Mar)?
- Does it handle edge cases (current date outside data)?

---

### 8. Multi-Constraint Filtering (Scenario 15)

#### Scenario 15: Complex Filter Combination
**Query:** "Find all shopping transactions over $50 at either Amazon or Target in February"

**Why it's critical:**
- FOUR constraints simultaneously:
  - Merchant: Amazon OR Target
  - Category: shopping
  - Amount: > $50
  - Date: February
- Tests maximum complexity

**What you'll learn:**
- Can agent apply multiple filters correctly?
- Does it handle OR logic (Amazon OR Target)?
- Does it maintain all constraints?

---

## Expected Performance Benchmarks

### By Difficulty Level

**Easy Scenarios (3 scenarios):**
- Expected Pass Rate: **≥ 90%**
- Single tool call, clear intent
- Examples: Scenario 10 (existence check)

**Medium Scenarios (5 scenarios):**
- Expected Pass Rate: **≥ 75%**
- 2-3 tool calls or moderate complexity
- Examples: Scenarios 3, 6, 7, 9, 13

**Hard Scenarios (7 scenarios):**
- Expected Pass Rate: **≥ 60%**
- Multi-step reasoning, calculations, complex filtering
- Examples: Scenarios 1, 2, 4, 5, 8, 11, 12, 14, 15

### Overall Target
- **Minimum Pass Rate: 70%** across all scenarios
- **Excellent Performance: 85%+** pass rate

---

## What Each Failure Teaches You

### Low Tool Selection Score
**Problem:** Agent choosing wrong tools for the task
**Fix:** Improve tool descriptions with more examples

### Low Reasoning Score
**Problem:** Agent not demonstrating multi-step logic
**Fix:** Add reasoning examples to system prompt, use ReAct pattern

### Low Accuracy Score
**Problem:** Wrong numbers or facts in response
**Fix:** Review tool implementation, check date filtering bugs

### Low Completeness Score
**Problem:** Partial answers, missing aspects
**Fix:** Improve prompts to address all parts of question

---

## Running the Tests

### Generate realistic data first:
```bash
python generate_sample.py
```

### Generate complex scenarios with ground truth:
```bash
python -c "
from complex_test_scenarios import ComplexTestScenarios
import pandas as pd
df = pd.read_csv('data/transactions.csv')
gen = ComplexTestScenarios(df)
gen.export_test_suite()
"
```

### Run all scenarios:
```bash
python test_complex_scenarios.py
```

### Run only hard scenarios:
```bash
python test_complex_scenarios.py --difficulty hard
```

### Run specific scenario:
```bash
python test_complex_scenarios.py --scenario-id complex_001
```

---

## Integration with Existing Tests

These complex scenarios complement your existing 15 basic tests:

**Basic Tests (existing):**
- Simple single-tool operations
- Direct category/merchant queries
- Basic date filtering

**Complex Tests (new):**
- Multi-step reasoning
- Comparative analysis
- Pattern recognition
- Complex filtering

**Together they provide:**
- **30 total scenarios**
- **Comprehensive coverage** of agent capabilities
- **Clear performance benchmarks** for improvements

---

## Success Metrics

Track these over time as you improve your agent:

1. **Pass Rate by Difficulty**
   - Target improvement: +10% per iteration

2. **Average Response Time**
   - Target: < 5s for hard scenarios

3. **Score Breakdown**
   - Tool selection: 0.85+
   - Reasoning: 0.75+
   - Accuracy: 0.80+
   - Completeness: 0.80+

4. **Failure Categories**
   - Identify patterns in failures
   - Prioritize fixes by frequency

---

## Next Steps After Running Tests

1. **Analyze failures** by category
2. **Fix highest-impact issues** first (tool descriptions, date bugs)
3. **Re-run test suite** to measure improvement
4. **Add golden dataset** for regression prevention (ignore for now)
5. **Set up CI/CD** to run on every change

These scenarios will push your agent to its limits and reveal exactly where improvements are needed!