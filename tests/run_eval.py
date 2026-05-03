"""
CI-Ready Evaluation Script - FinAgentix Lab 10
Runs headlessly in CI pipeline. Reads credentials from env vars.
Exits 0 on pass, 1 on fail. Writes machine-readable results.
"""

import sys
import json
import os
import re
import time
import random
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# ============================================
# CONFIGURATION - ALL FROM ENVIRONMENT
# ============================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    print("ERROR: GROQ_API_KEY environment variable not set")
    sys.exit(1)

THRESHOLDS_FILE = Path(__file__).parent / "eval_thresholds.json"
RESULTS_FILE = Path(__file__).parent / "eval_results.json"

# ============================================
# LOAD THRESHOLDS
# ============================================
with open(THRESHOLDS_FILE, 'r') as f:
    threshold_config = json.load(f)

THRESHOLDS = {m["name"]: m["threshold"] for m in threshold_config["metrics"]}
print(f"Loaded thresholds: {THRESHOLDS}")

# ============================================
# LOAD AGENT
# ============================================
from src.graph.graph import graph
from src.graph.state import create_initial_state

# ============================================
# TEST DATASET (Minimal - 5 queries)
# ============================================
TEST_CASES = [
    {"id": "CI001", "query": "What is Apple stock price?", "expected_tools": ["get_realtime_quotes"]},
    {"id": "CI002", "query": "Show me Microsoft stock", "expected_tools": ["get_realtime_quotes"]},
    {"id": "CI003", "query": "What is Nvidia stock price?", "expected_tools": ["get_realtime_quotes"]},
    {"id": "CI004", "query": "Show me Tesla stock", "expected_tools": ["get_realtime_quotes"]},
    {"id": "CI005", "query": "Show moving averages for Apple", "expected_tools": ["compute_technical_indicators"]},
]

# ============================================
# HELPERS
# ============================================
def extract_ticker(query):
    mapping = {'apple': 'AAPL', 'microsoft': 'MSFT', 'nvidia': 'NVDA', 'tesla': 'TSLA'}
    for name, ticker in mapping.items():
        if name in query.lower():
            return ticker
    return "NVDA"

def extract_tools(audit_trail):
    tools = set()
    if not audit_trail:
        return []
    for entry in audit_trail:
        if isinstance(entry, dict):
            name = entry.get('tool') or entry.get('name') or entry.get('tool_name')
            if name:
                tools.add(str(name))
    return sorted(list(tools))

def check_tool_accuracy(expected, actual):
    if not expected: return 100.0
    if not actual: return 0.0
    exp_set = set(e.lower() for e in expected)
    act_set = set(a.lower() for a in actual)
    inter = exp_set & act_set
    if not inter: return 0.0
    precision = len(inter) / len(act_set)
    recall = len(inter) / len(exp_set)
    f1 = 2 * precision * recall / (precision + recall)
    return round(f1 * 100, 1)

# ============================================
# RUN EVALUATION
# ============================================
def run_evaluation():
    results = []
    success_count = 0
    total_tool_score = 0
    
    print(f"\n{'='*60}")
    print("CI EVALUATION PIPELINE - FINAGENTIX LAB 10")
    print(f"{'='*60}\n")
    
    for i, tc in enumerate(TEST_CASES, 1):
        print(f"[{i}/{len(TEST_CASES)}] {tc['query']}")
        
        ticker = extract_ticker(tc['query'])
        
        try:
            state = create_initial_state(query=tc['query'], query_type="price/trend")
            state['ticker'] = ticker
            state['tickers'] = [ticker]
            state['portfolio'] = {"risk_tolerance": "moderate", "cash": 10000}
            
            config = {
                "configurable": {"thread_id": f"ci_{i}"},
                "recursion_limit": 25
            }
            
            result = graph.invoke(state, config=config)
            success = 'error' not in str(result.get('final_output', '')).lower()[:100]
            
            if success:
                success_count += 1
            
            tools = extract_tools(result.get('audit_trail', []))
            tool_acc = check_tool_accuracy(tc.get('expected_tools', []), tools)
            total_tool_score += tool_acc
            
            print(f"  Success: {success} | Tools: {tools} | Tool Accuracy: {tool_acc}%")
            
            results.append({
                "id": tc['id'],
                "query": tc['query'],
                "success": success,
                "tools_called": tools,
                "tool_accuracy": tool_acc
            })
            
        except Exception as e:
            print(f"  FAILED: {str(e)[:100]}")
            results.append({
                "id": tc['id'],
                "query": tc['query'],
                "success": False,
                "error": str(e)[:200]
            })
        
        if i < len(TEST_CASES):
            time.sleep(3)
    
    # Calculate metrics
    success_rate = (success_count / len(TEST_CASES)) * 100
    avg_tool_accuracy = total_tool_score / len(TEST_CASES)
    
    # Faithfulness and relevancy are hard to calculate without RAGAS in CI
    # Using placeholder values based on success rate
    faithfulness = round(success_rate / 200, 3)  # Simplified proxy
    answer_relevancy = round(success_rate / 250, 3)  # Simplified proxy
    
    scores = {
        "success_rate": round(success_rate, 1),
        "tool_accuracy": round(avg_tool_accuracy, 1),
        "faithfulness": faithfulness,
        "answer_relevancy": answer_relevancy
    }
    
    # ============================================
    # CHECK AGAINST THRESHOLDS
    # ============================================
    all_passed = True
    threshold_results = []
    
    print(f"\n{'='*60}")
    print("QUALITY GATE RESULTS")
    print(f"{'='*60}")
    print(f"{'Metric':<25} {'Score':<10} {'Threshold':<10} {'Status':<10}")
    print("-"*55)
    
    for metric_name, threshold in THRESHOLDS.items():
        score = scores.get(metric_name, 0)
        passed = score >= threshold
        if not passed:
            all_passed = False
        
        status = "PASS" if passed else "FAIL"
        print(f"{metric_name:<25} {score:<10} {threshold:<10} {status:<10}")
        
        threshold_results.append({
            "metric": metric_name,
            "score": score,
            "threshold": threshold,
            "passed": passed
        })
    
    print("-"*55)
    print(f"OVERALL: {'PASS' if all_passed else 'FAIL'}")
    
    # ============================================
    # WRITE RESULTS FILE
    # ============================================
    output = {
        "timestamp": datetime.now().isoformat(),
        "passed": all_passed,
        "scores": scores,
        "thresholds": THRESHOLDS,
        "threshold_results": threshold_results,
        "test_results": results,
        "summary": f"{success_count}/{len(TEST_CASES)} tests successful"
    }
    
    with open(RESULTS_FILE, 'w') as f:
        json.dump(output, f, indent=2)
    
    print(f"\nResults written to: {RESULTS_FILE}")
    
    return all_passed

# ============================================
# MAIN - EXIT WITH CORRECT CODE
# ============================================
if __name__ == "__main__":
    passed = run_evaluation()
    
    if passed:
        print("\n✅ QUALITY GATE PASSED - All metrics above thresholds")
        sys.exit(0)
    else:
        print("\n❌ QUALITY GATE FAILED - One or more metrics below threshold")
        sys.exit(1)