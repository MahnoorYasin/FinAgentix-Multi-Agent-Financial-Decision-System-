"""
Approval Logic Test for FinAgentix - Lab 5 Task 2
Tests Human-in-the-Loop (HITL) with safety breakpoints
FIXED: Added message serialization and custom query support
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.graph.graph import graph
from src.graph.state import create_initial_state
import datetime
import time
import os
import json
import re
from langchain_core.messages import HumanMessage, AIMessage, FunctionMessage

# Create logs directory for lab5
LOG_DIR = Path(__file__).parent.parent / "logs" / "lab5"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================
# MESSAGE SERIALIZATION FIX
# ============================================
def message_serializer(obj):
    """Convert LangChain messages to serializable dicts"""
    if isinstance(obj, (HumanMessage, AIMessage, FunctionMessage)):
        return {
            "__type__": obj.__class__.__name__,
            "content": obj.content,
            "additional_kwargs": getattr(obj, 'additional_kwargs', {})
        }
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def message_deserializer(dct):
    """Reconstruct messages from serialized dicts"""
    if "__type__" in dct:
        if dct["__type__"] == "HumanMessage":
            return HumanMessage(content=dct["content"], additional_kwargs=dct.get("additional_kwargs", {}))
        elif dct["__type__"] == "AIMessage":
            return AIMessage(content=dct["content"], additional_kwargs=dct.get("additional_kwargs", {}))
        elif dct["__type__"] == "FunctionMessage":
            return FunctionMessage(content=dct["content"], name=dct.get("name", ""))
    return dct

# Patch JSON encoder to handle messages
original_default = json.JSONEncoder.default

def safe_default(self, obj):
    try:
        return message_serializer(obj)
    except TypeError:
        return original_default(self, obj)

json.JSONEncoder.default = safe_default

def log_message(message: str, to_file_only: bool = False):
    """Log message to file and optionally print"""
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    
    log_file = LOG_DIR / "approval_logic.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    if not to_file_only:
        print(message)

# ============================================
# TICKER EXTRACTION FUNCTION
# ============================================
def extract_ticker_from_query(query: str) -> str:
    """Extract ticker symbol from query"""
    query_lower = query.lower()
    
    # Direct ticker matches
    words = query.split()
    for word in words:
        clean_word = re.sub(r'[^A-Za-z]', '', word).upper()
        known_tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'NFLX']
        if clean_word in known_tickers:
            return clean_word
    
    # Company name mapping
    ticker_map = {
        'apple': 'AAPL',
        'microsoft': 'MSFT',
        'google': 'GOOGL',
        'amazon': 'AMZN',
        'nvidia': 'NVDA',
        'meta': 'META',
        'facebook': 'META',
        'tesla': 'TSLA',
        'netflix': 'NFLX'
    }
    
    for name, ticker in ticker_map.items():
        if name in query_lower:
            return ticker
    
    return "NVDA"  # Default

def display_proposed_action(state):
    """Display the proposed action for user approval"""
    print("\n" + "="*60)
    print("🔴 HUMAN APPROVAL REQUIRED")
    print("="*60)
    
    print("\n📊 PROPOSED INVESTMENT DECISION:")
    print("-" * 40)
    
    # Get ticker from state
    ticker = state.get("tickers", ["NVDA"])[0] if state.get("tickers") else "NVDA"
    print(f"📌 Stock: {ticker}")
    
    # Show market data
    if state.get("market_data") and state["market_data"].get("quotes"):
        quote = state["market_data"]["quotes"]
        print(f"💰 Current Price: ${quote.get('price', 'N/A')} ({quote.get('change_percent', 0):+.2f}%)")
    
    # Show sentiment
    if state.get("news_data") and state["news_data"].get("analyze_news_sentiment"):
        sentiment = state["news_data"]["analyze_news_sentiment"]
        print(f"📰 News Sentiment: {sentiment.get('sentiment', 'N/A')} ({sentiment.get('sentiment_score', 0):+.2f})")
    
    # Show risk
    if state.get("risk_data") and state["risk_data"].get("calculate_value_at_risk"):
        var = state["risk_data"]["calculate_value_at_risk"]
        print(f"⚠️ Value at Risk: {var.get('var_percent', 'N/A')}%")
    
    # Show compliance
    if state.get("compliance_data") and state["compliance_data"].get("check_finra_compliance"):
        comp = state["compliance_data"]["check_finra_compliance"]
        status = "✅ COMPLIANT" if comp.get('compliant') else "❌ NON-COMPLIANT"
        print(f"⚖️ Compliance: {status}")
    
    print("\n📝 Portfolio Agent will generate investment thesis based on this data.")
    print("-" * 40)

def test_approval_workflow():
    """Test HITL approval workflow with custom query"""
    
    print("\n" + "="*70)
    print("📋 LAB 5 TASK 2: HUMAN-IN-THE-LOOP (HITL) TEST")
    print("="*70 + "\n")
    
    # ============================================
    # GET CUSTOM QUERY FROM USER
    # ============================================
    print("\n📝 Enter your investment question (or press Enter for default):")
    custom_query = input("> ").strip()
    
    if not custom_query:
        custom_query = "Should I invest $10,000 in NVDA?"
        ticker = "NVDA"
    else:
        ticker = extract_ticker_from_query(custom_query)
    
    print(f"\n🔍 Processing query: '{custom_query}'")
    print(f"📊 Detected ticker: {ticker}")
    
    log_message("🚀 Starting HITL approval test...")
    log_message(f"📝 Query: {custom_query}")
    log_message(f"📊 Ticker: {ticker}")
    
    # Create thread_id
    thread_id = f"hitl_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initial state with custom query
    initial_state = create_initial_state(
        query=custom_query,
        query_type="investment decision"
    )
    
    initial_state["portfolio"] = {
        "risk_tolerance": "moderate",
        "cash": 10000,
        "holdings": []
    }
    initial_state["tickers"] = [ticker]
    
    # Configure with thread_id
    config = {
        "configurable": {
            "thread_id": thread_id,
            "recursion_limit": 30
        }
    }
    
    try:
        log_message("\n📌 STEP 1: Running agents (will pause before portfolio)...")
        
        # First invocation - runs all agents except portfolio
        for step in graph.stream(initial_state, config=config):
            # Just process the stream, don't try to display here
            pass
        
        # Get the current state after interruption
        state = graph.get_state(config)
        
        log_message("\n✅ Agents completed data collection")
        log_message("⏸️ Graph paused at portfolio_node (high-risk node)")
        
        # Display proposed action for approval
        display_proposed_action(state.values)
        
        # Ask for approval
        print("\n" + "="*60)
        choice = input("❓ Approve this investment decision? (yes/no): ").strip().lower()
        
        if choice == 'yes' or choice == 'y':
            log_message(f"\n✅ User APPROVED. Resuming execution...")
            
            # Resume execution - this will run portfolio agent
            for step in graph.stream(None, config=config):
                # Process the stream
                pass
            
            # Get final result
            result = graph.invoke(None, config=config)
            
            # Show final result
            if result.get("final_output"):
                print("\n" + "="*60)
                print("📊 FINAL INVESTMENT THESIS")
                print("="*60)
                print(result["final_output"])
            else:
                print("\n⚠️ No final output generated")
            
            log_message("\n✅ Investment thesis generated and approved")
            
        else:
            log_message(f"\n❌ User REJECTED. Cancelling execution...")
            print("\n❌ Investment decision cancelled by user.")
        
        log_message("\n✅ HITL test completed")
        log_message(f"📝 Log file: logs/lab5/approval_logic.log")
        
    except Exception as e:
        log_message(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_approval_workflow()