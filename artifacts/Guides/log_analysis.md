# Log Analysis Guide: User Behavior & Performance Optimization

**Created**: December 9, 2025  
**Purpose**: Comprehensive guide for analyzing structured logs to understand user behavior and optimize performance

## Table of Contents

1. [User Behavior Analysis](#user-behavior-analysis)
2. [Performance Optimization](#performance-optimization)
3. [Advanced Analysis Scripts](#advanced-analysis-scripts)
4. [Key Metrics to Track](#key-metrics-to-track)
5. [Actionable Insights](#actionable-insights)
6. [Quick Reference Commands](#quick-reference-commands)

---

## User Behavior Analysis

### Query Pattern Analysis

#### Most Common Queries

Find the most frequently asked questions:

```bash
# Extract all user queries and count frequency
cat logs/app.log | jq -r 'select(.event_type == "user_query") | .data.query' | \
  sort | uniq -c | sort -rn | head -20
```

This helps identify:
- Popular use cases
- Features users want most
- Potential areas for UI improvements

#### Query Categories

Identify what types of queries users are making:

```bash
# Group queries by keywords (categories, merchants, time periods)
cat logs/app.log | jq -r 'select(.event_type == "user_query") | .data.query' | \
  grep -iE "(category|categories|merchant|spending|summary|last|month|week)" | \
  wc -l
```

#### Query Length Distribution

Analyze query complexity:

```bash
# Analyze query complexity
cat logs/app.log | jq 'select(.event_type == "user_query") | .data.query_length' | \
  awk '{sum+=$1; sumsq+=$1*$1; count++} END {
    mean=sum/count; 
    stddev=sqrt(sumsq/count - mean*mean); 
    print "Mean:", mean, "StdDev:", stddev, "Count:", count
  }'
```

**Insights:**
- Short queries (<20 chars): Users want quick answers
- Medium queries (20-50 chars): Standard usage
- Long queries (>50 chars): Complex analysis requests

#### Session Analysis

Understand user engagement:

```bash
# Average queries per session
cat logs/app.log | jq -r 'select(.event_type == "user_query") | .session_id' | \
  sort | uniq -c | awk '{sum+=$1; count++} END {print "Avg queries per session:", sum/count}'

# Most active sessions
cat logs/app.log | jq -r 'select(.event_type == "user_query") | .session_id' | \
  sort | uniq -c | sort -rn | head -10
```

**Metrics to track:**
- Average queries per session
- Session duration
- Most engaged users
- Drop-off points

### Tool Usage Patterns

#### Most Used Tools

Identify which tools are most popular:

```bash
# Which tools are used most frequently
cat logs/app.log | jq -r 'select(.event_type == "tool_execution_start") | .data.tool_name' | \
  sort | uniq -c | sort -rn
```

**Action items:**
- Optimize frequently used tools
- Add caching for popular operations
- Consider UI shortcuts for common tools

#### Tool-Query Correlation

Understand what queries trigger which tools:

```bash
# What types of queries trigger which tools
cat logs/app.log | jq -r 'select(.event_type == "user_query" or .event_type == "tool_execution_start") | 
  {query_id, event: .event_type, data: .data} | 
  @json' | jq -s 'group_by(.query_id) | 
  map({query: .[0].data.query, tool: .[1].data.tool_name}) | 
  group_by(.tool) | map({tool: .[0].tool, count: length, sample_queries: [.[0:3].query]})'
```

This helps:
- Validate tool selection logic
- Identify misrouted queries
- Improve tool descriptions

---

## Performance Optimization

### Response Time Analysis

#### Average Response Time

**Overall average:**
```bash
cat logs/app.log | jq 'select(.event_type == "response_generated") | .data.response_time' | \
  awk '{sum+=$1; count++} END {print "Average:", sum/count, "seconds"}'
```

**By tool:**
```bash
cat logs/app.log | jq -r 'select(.event_type == "response_generated") | 
  "\(.data.tool_used // "none") \(.data.response_time)"' | \
  awk '{sum[$1]+=$2; count[$1]++} END {for (tool in sum) print tool, sum[tool]/count[tool]}'
```

**Target metrics:**
- Average < 2 seconds: Excellent
- Average 2-5 seconds: Good
- Average > 5 seconds: Needs optimization

#### Slow Query Identification

Find queries that need optimization:

```bash
# Queries taking >3 seconds
cat logs/app.log | jq 'select(.event_type == "response_generated" and .data.response_time > 3) | 
  {query: .data.query, time: .data.response_time, tool: .data.tool_used}'
```

**Percentile analysis:**
```bash
# P95 and P99 response times
cat logs/app.log | jq 'select(.event_type == "response_generated") | .data.response_time' | \
  sort -n | awk '{
    a[NR]=$1
  } END {
    p95=int(NR*0.95); p99=int(NR*0.99);
    print "P50:", a[int(NR*0.5)], "P95:", a[p95], "P99:", a[p99]
  }'
```

**Optimization strategies:**
- Cache results for slow queries
- Optimize tool execution
- Pre-compute common aggregations
- Add database indexes if needed

### Tool Performance Analysis

#### Tool Execution Times

Identify slow tools:

```bash
# Average execution time per tool
cat logs/app.log | jq -r 'select(.event_type == "tool_execution_end") | 
  "\(.data.tool_name) \(.data.execution_time)"' | \
  awk '{sum[$1]+=$2; count[$1]++; max[$1]=($2>max[$1]?$2:max[$1])} 
  END {for (tool in sum) print tool, "avg:", sum[tool]/count[tool], "max:", max[tool]}'
```

**Action items:**
- Focus optimization on slowest tools
- Add caching for expensive operations
- Consider async execution for long-running tools

#### Tool Failure Rate

Monitor tool reliability:

```bash
# Success vs failure rate
cat logs/app.log | jq -r 'select(.event_type == "tool_execution_end") | 
  "\(.data.tool_name) \(.data.success)"' | \
  awk '{total[$1]++; if ($2=="true") success[$1]++} 
  END {for (tool in total) print tool, success[tool]/total[tool]*100, "% success"}'
```

**Target:**
- Success rate > 99%: Excellent
- Success rate 95-99%: Good
- Success rate < 95%: Needs investigation

---

## Advanced Analysis Scripts

### Python Analysis Script

Create a comprehensive analysis script (`scripts/analyze_logs.py`):

```python
#!/usr/bin/env python3
"""
Log Analysis Script for Money Minder Chatbot
Analyzes user behavior and performance metrics from structured logs
"""

import json
import sys
from collections import defaultdict, Counter
from statistics import mean, median, stdev
from datetime import datetime

def load_logs(log_file):
    """Load and parse JSON logs"""
    logs = []
    with open(log_file, 'r') as f:
        for line in f:
            try:
                logs.append(json.loads(line.strip()))
            except json.JSONDecodeError:
                continue
    return logs

def analyze_user_behavior(logs):
    """Analyze user query patterns"""
    queries = [log for log in logs if log.get('event_type') == 'user_query']
    
    print("\n=== USER BEHAVIOR ANALYSIS ===\n")
    
    # Most common queries
    query_texts = [q['data']['query'] for q in queries]
    query_counts = Counter(query_texts)
    print("Top 10 Most Common Queries:")
    for query, count in query_counts.most_common(10):
        print(f"  {count:3d}x: {query}")
    
    # Query length stats
    lengths = [q['data']['query_length'] for q in queries]
    print(f"\nQuery Length Statistics:")
    print(f"  Mean: {mean(lengths):.1f} characters")
    print(f"  Median: {median(lengths):.1f} characters")
    print(f"  StdDev: {stdev(lengths):.1f} characters")
    
    # Sessions
    sessions = set(q.get('session_id') for q in queries if q.get('session_id'))
    queries_per_session = defaultdict(int)
    for q in queries:
        if q.get('session_id'):
            queries_per_session[q['session_id']] += 1
    
    print(f"\nSession Statistics:")
    print(f"  Total sessions: {len(sessions)}")
    if queries_per_session:
        print(f"  Avg queries per session: {mean(queries_per_session.values()):.1f}")
        print(f"  Max queries in one session: {max(queries_per_session.values())}")

def analyze_performance(logs):
    """Analyze performance metrics"""
    responses = [log for log in logs if log.get('event_type') == 'response_generated']
    tool_executions = [log for log in logs if log.get('event_type') == 'tool_execution_end']
    
    print("\n=== PERFORMANCE ANALYSIS ===\n")
    
    # Response times
    response_times = [r['data']['response_time'] for r in responses]
    if response_times:
        print("Response Time Statistics:")
        print(f"  Mean: {mean(response_times):.3f} seconds")
        print(f"  Median: {median(response_times):.3f} seconds")
        print(f"  P95: {sorted(response_times)[int(len(response_times)*0.95)]:.3f} seconds")
        print(f"  P99: {sorted(response_times)[int(len(response_times)*0.99)]:.3f} seconds")
        print(f"  Max: {max(response_times):.3f} seconds")
        
        # Slow queries
        slow_threshold = 3.0
        slow_queries = [r for r in responses if r['data']['response_time'] > slow_threshold]
        print(f"\nSlow Queries (>={slow_threshold}s): {len(slow_queries)}")
        for r in sorted(slow_queries, key=lambda x: x['data']['response_time'], reverse=True)[:5]:
            print(f"  {r['data']['response_time']:.2f}s: {r['data']['query'][:60]}...")
    
    # Tool performance
    tool_times = defaultdict(list)
    for tool_log in tool_executions:
        tool_name = tool_log['data']['tool_name']
        exec_time = tool_log['data']['execution_time']
        tool_times[tool_name].append(exec_time)
    
    print("\nTool Execution Times:")
    for tool, times in sorted(tool_times.items()):
        print(f"  {tool}:")
        print(f"    Avg: {mean(times):.3f}s, Median: {median(times):.3f}s, Max: {max(times):.3f}s")
        print(f"    Count: {len(times)}")

def analyze_tool_usage(logs):
    """Analyze tool usage patterns"""
    tool_starts = [log for log in logs if log.get('event_type') == 'tool_execution_start']
    
    print("\n=== TOOL USAGE ANALYSIS ===\n")
    
    # Tool frequency
    tool_counts = Counter(t['data']['tool_name'] for t in tool_starts)
    print("Tool Usage Frequency:")
    for tool, count in tool_counts.most_common():
        print(f"  {tool}: {count} times")
    
    # Tool-query correlation
    query_tool_map = {}
    for log in logs:
        if log.get('event_type') == 'user_query':
            query_tool_map[log.get('query_id')] = {
                'query': log['data']['query'],
                'tool': None
            }
        elif log.get('event_type') == 'tool_execution_start':
            query_id = log.get('query_id')
            if query_id in query_tool_map:
                query_tool_map[query_id]['tool'] = log['data']['tool_name']
    
    print("\nQuery-Tool Patterns:")
    tool_query_patterns = defaultdict(list)
    for qid, info in query_tool_map.items():
        if info['tool']:
            tool_query_patterns[info['tool']].append(info['query'])
    
    for tool, queries in tool_query_patterns.items():
        print(f"\n  {tool}:")
        # Show sample queries
        for query in queries[:3]:
            print(f"    - {query[:70]}...")

def analyze_errors(logs):
    """Analyze error patterns"""
    errors = [log for log in logs if log.get('level') == 'ERROR']
    
    print("\n=== ERROR ANALYSIS ===\n")
    
    if not errors:
        print("No errors found! 🎉")
        return
    
    error_types = Counter(e['data']['error_type'] for e in errors if 'data' in e)
    print(f"Total Errors: {len(errors)}")
    print("\nError Types:")
    for error_type, count in error_types.most_common():
        print(f"  {error_type}: {count}")
    
    # Recent errors
    print("\nRecent Errors (last 5):")
    for error in errors[-5:]:
        print(f"  {error.get('timestamp', 'unknown')}: {error.get('data', {}).get('error_message', 'unknown')}")

def main():
    if len(sys.argv) < 2:
        print("Usage: python analyze_logs.py <log_file>")
        sys.exit(1)
    
    log_file = sys.argv[1]
    print(f"Analyzing logs from: {log_file}\n")
    
    logs = load_logs(log_file)
    print(f"Loaded {len(logs)} log entries\n")
    
    analyze_user_behavior(logs)
    analyze_performance(logs)
    analyze_tool_usage(logs)
    analyze_errors(logs)
    
    print("\n=== SUMMARY ===\n")
    total_queries = len([l for l in logs if l.get('event_type') == 'user_query'])
    total_responses = len([l for l in logs if l.get('event_type') == 'response_generated'])
    total_errors = len([l for l in logs if l.get('level') == 'ERROR'])
    
    print(f"Total Queries: {total_queries}")
    print(f"Total Responses: {total_responses}")
    print(f"Total Errors: {total_errors}")
    if total_queries > 0:
        print(f"Error Rate: {total_errors/total_queries*100:.2f}%")

if __name__ == '__main__':
    main()
```

**Usage:**
```bash
python3 scripts/analyze_logs.py logs/app.log
```

### Real-time Monitoring Script

Monitor logs in real-time:

```bash
#!/bin/bash
# real_time_monitor.sh

tail -f logs/app.log | while read line; do
  event=$(echo "$line" | jq -r '.event_type // "unknown"')
  level=$(echo "$line" | jq -r '.level // "INFO"')
  
  case "$event" in
    "user_query")
      query=$(echo "$line" | jq -r '.data.query')
      echo "[QUERY] $query"
      ;;
    "response_generated")
      time=$(echo "$line" | jq -r '.data.response_time')
      echo "[RESPONSE] ${time}s"
      ;;
    "error")
      error=$(echo "$line" | jq -r '.data.error_message')
      echo "[ERROR] $error"
      ;;
  esac
done
```

---

## Key Metrics to Track

### User Behavior Metrics

| Metric | Command | Target |
|--------|---------|--------|
| Query frequency | `jq -r 'select(.event_type == "user_query") | .data.query' \| sort \| uniq -c` | Identify trends |
| Queries per session | `jq -r 'select(.event_type == "user_query") \| .session_id' \| sort \| uniq -c` | > 2 queries/session |
| Query length | `jq 'select(.event_type == "user_query") \| .data.query_length'` | Mean: 20-50 chars |
| Tool usage frequency | `jq -r 'select(.event_type == "tool_execution_start") \| .data.tool_name' \| sort \| uniq -c` | Identify popular tools |

### Performance Metrics

| Metric | Command | Target |
|--------|---------|--------|
| Average response time | `jq 'select(.event_type == "response_generated") \| .data.response_time' \| awk '{sum+=$1; count++} END {print sum/count}'` | < 2 seconds |
| P95 response time | Percentile calculation | < 5 seconds |
| Tool execution time | `jq -r 'select(.event_type == "tool_execution_end") \| "\(.data.tool_name) \(.data.execution_time)"'` | Tool-specific |
| Error rate | `jq 'select(.level == "ERROR")' \| wc -l` | < 1% |

### Health Metrics

| Metric | Description | Target |
|--------|-------------|--------|
| Error rate | Errors per total queries | < 1% |
| Tool success rate | Successful tool executions | > 99% |
| Session retention | Users returning | Track over time |
| Query success rate | Successful responses | > 95% |

---

## Actionable Insights

### 1. If Certain Queries Are Slow

**Symptoms:**
- Response time > 5 seconds for specific query types
- High P95/P99 percentiles

**Actions:**
- ✅ Cache results for common queries
- ✅ Optimize the tool being used
- ✅ Pre-compute common aggregations
- ✅ Add database indexes
- ✅ Consider async processing for long operations

**Example:**
```bash
# Find slow queries
cat logs/app.log | jq 'select(.event_type == "response_generated" and .data.response_time > 5) | 
  {query: .data.query, time: .data.response_time, tool: .data.tool_used}' | \
  jq -s 'group_by(.tool) | map({tool: .[0].tool, count: length, avg_time: (map(.time) | add / length)})'
```

### 2. If a Tool Is Frequently Used

**Symptoms:**
- Tool appears in >30% of queries
- High execution count

**Actions:**
- ✅ Optimize that tool's performance
- ✅ Add caching layer
- ✅ Monitor for bottlenecks
- ✅ Consider dedicated infrastructure

**Example:**
```bash
# Find most used tools
cat logs/app.log | jq -r 'select(.event_type == "tool_execution_start") | .data.tool_name' | \
  sort | uniq -c | sort -rn | head -5
```

### 3. If Error Rates Are High

**Symptoms:**
- Error rate > 1%
- Specific error types recurring

**Actions:**
- ✅ Fix most common error types first
- ✅ Add better error handling
- ✅ Improve input validation
- ✅ Add retry logic for transient errors
- ✅ Monitor error trends

**Example:**
```bash
# Analyze errors
cat logs/errors.log | jq -r '.data.error_type' | sort | uniq -c | sort -rn
```

### 4. If Query Patterns Show Trends

**Symptoms:**
- Similar queries repeated frequently
- Clear use case patterns emerging

**Actions:**
- ✅ Add features for common use cases
- ✅ Create shortcuts for frequent queries
- ✅ Improve tool descriptions to guide users
- ✅ Add query suggestions/autocomplete
- ✅ Build dashboards for common analyses

**Example:**
```bash
# Find query patterns
cat logs/app.log | jq -r 'select(.event_type == "user_query") | .data.query' | \
  sort | uniq -c | sort -rn | head -20
```

### 5. If Tool Selection Is Inefficient

**Symptoms:**
- Wrong tools being selected for queries
- Users asking follow-up questions to get correct results

**Actions:**
- ✅ Improve tool descriptions
- ✅ Add examples to tool descriptions
- ✅ Review tool selection logic
- ✅ Add tool selection feedback mechanism

**Example:**
```bash
# Analyze tool-query mismatches
cat logs/app.log | jq -r 'select(.event_type == "user_query" or .event_type == "tool_execution_start") | 
  {query_id, event: .event_type, data: .data} | @json' | \
  jq -s 'group_by(.query_id) | map({query: .[0].data.query, tool: .[1].data.tool_name})'
```

---

## Quick Reference Commands

### Daily Monitoring

```bash
# Quick health check
echo "=== Daily Health Check ==="
echo "Total queries today:"
cat logs/app.log | jq -r 'select(.event_type == "user_query")' | wc -l
echo "Errors today:"
cat logs/errors.log | jq -r 'select(.level == "ERROR")' | wc -l
echo "Average response time:"
cat logs/app.log | jq 'select(.event_type == "response_generated") | .data.response_time' | \
  awk '{sum+=$1; count++} END {print sum/count " seconds"}'
```

### Weekly Analysis

```bash
# Weekly report
echo "=== Weekly Report ==="
echo "Top queries:"
cat logs/app.log | jq -r 'select(.event_type == "user_query") | .data.query' | \
  sort | uniq -c | sort -rn | head -10
echo "Tool usage:"
cat logs/app.log | jq -r 'select(.event_type == "tool_execution_start") | .data.tool_name' | \
  sort | uniq -c | sort -rn
echo "Error summary:"
cat logs/errors.log | jq -r '.data.error_type' | sort | uniq -c | sort -rn
```

### Performance Investigation

```bash
# Find performance issues
echo "=== Performance Issues ==="
echo "Slow queries (>3s):"
cat logs/app.log | jq 'select(.event_type == "response_generated" and .data.response_time > 3) | 
  {query: .data.query, time: .data.response_time}' | head -10
echo "Slow tools:"
cat logs/app.log | jq -r 'select(.event_type == "tool_execution_end") | 
  "\(.data.tool_name) \(.data.execution_time)"' | \
  awk '{sum[$1]+=$2; count[$1]++; max[$1]=($2>max[$1]?$2:max[$1])} 
  END {for (tool in sum) if (sum[tool]/count[tool] > 1) print tool, "avg:", sum[tool]/count[tool], "max:", max[tool]}'
```

### Debugging Specific Issues

```bash
# Track a specific query through the system
QUERY_ID="your-query-id-here"
cat logs/app.log | jq "select(.query_id == \"$QUERY_ID\")"

# Find all events for a session
SESSION_ID="your-session-id-here"
cat logs/app.log | jq "select(.session_id == \"$SESSION_ID\")"

# Find queries that led to errors
cat logs/app.log | jq -s 'map(select(.level == "ERROR")) | 
  map(.query_id) | unique | 
  map(. as $qid | [inputs | select(.query_id == $qid and .event_type == "user_query")])'
```

---

## Best Practices

1. **Regular Monitoring**: Check logs daily for errors and performance issues
2. **Set Alerts**: Configure alerts for error rate spikes or slow response times
3. **Trend Analysis**: Track metrics over time to identify patterns
4. **User Feedback**: Correlate log data with user feedback
5. **Continuous Optimization**: Use insights to continuously improve the system

## Tools and Integrations

### Log Aggregation Services

Consider integrating with:
- **CloudWatch** (AWS)
- **Datadog**
- **Splunk**
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Grafana Loki**

### Visualization

Create dashboards for:
- Query volume over time
- Response time trends
- Error rates
- Tool usage distribution
- User engagement metrics

---

## Conclusion

Regular log analysis provides valuable insights into:
- How users interact with the system
- Performance bottlenecks
- Error patterns
- Optimization opportunities

Use this guide to establish a regular log analysis routine and continuously improve the Money Minder Chatbot based on real usage data.

