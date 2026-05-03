"""
State Editing Test for FinAgentix - Lab 5 Task 3
Tests human editing of agent's proposed plan before execution
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
    
    log_file = LOG_DIR / "state_editing.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    
    if not to_file_only:
        print(message)

# ============================================
# TICKER EXTRACTION FUNCTION
# ============================================
def extract_ticker_from_query(query: str) -> str:
    """Extract ticker symbol from query"""
    if not query:
        return "NVDA"
    
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
        'alphabet': 'GOOGL',
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

def display_current_plan(state):
    """Display the current plan for editing"""
    print("\n" + "="*60)
    print("📝 CURRENT AGENT PLAN")
    print("="*60)
    
    # Show ticker
    ticker = state.get("tickers", ["NVDA"])[0] if state.get("tickers") else "NVDA"
    print(f"📌 Stock: {ticker}")
    
    # Show collected data
    if state.get("market_data") and state["market_data"].get("quotes"):
        quote = state["market_data"]["quotes"]
        print(f"\n💰 Current Price: ${quote.get('price', 'N/A')}")
    
    if state.get("risk_data") and state["risk_data"].get("calculate_value_at_risk"):
        var = state["risk_data"]["calculate_value_at_risk"]
        print(f"⚠️ Risk (VaR): {var.get('var_percent', 'N/A')}%")
    
    # Show current portfolio settings
    portfolio = state.get("portfolio", {})
    print(f"\n📊 Current Portfolio Settings:")
    print(f"   • Risk Tolerance: {portfolio.get('risk_tolerance', 'moderate')}")
    print(f"   • Available Cash: ${portfolio.get('cash', 10000):,}")
    
    return portfolio

def test_state_editing():
    """Test state editing workflow with custom query"""
    
    print("\n" + "="*70)
    print("📋 LAB 5 TASK 3: STATE EDITING TEST")
    print("="*70 + "\n")
    
    # ============================================
    # GET CUSTOM QUERY FROM USER
    # ============================================
    print("\n📝 Enter your investment question (or press Enter for default):")
    custom_query = input("> ").strip()
    
    if not custom_query:
        custom_query = "Should I invest in NVDA?"
        ticker = "NVDA"
    else:
        ticker = extract_ticker_from_query(custom_query)
    
    print(f"\n🔍 Processing query: '{custom_query}'")
    print(f"📊 Detected ticker: {ticker}")
    
    log_message("🚀 Starting state editing test...")
    log_message(f"📝 Query: {custom_query}")
    log_message(f"📊 Ticker: {ticker}")
    
    # Create thread_id
    thread_id = f"editing_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Initial state with custom query
    initial_state = create_initial_state(
        query=custom_query,
        query_type="investment decision"
    )
    
    initial_state["portfolio"] = {
        "risk_tolerance": "moderate",  # Default
        "cash": 10000,                  # Default
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
        
        # Use stream() instead of invoke() to avoid serialization issues
        for step in graph.stream(initial_state, config=config):
            # Process stream without storing
            pass
        
        # Get the current state from the checkpoint
        state = graph.get_state(config)
        
        log_message("\n✅ Agents completed data collection")
        log_message("⏸️ Graph paused at portfolio_node")
        
        # Display current plan
        current_portfolio = display_current_plan(state.values)
        
        # ============================================
        # STATE EDITING SECTION
        # ============================================
        print("\n" + "="*60)
        print("✏️ HUMAN INTERVENTION - EDIT PLAN")
        print("="*60)
        
        print("\nYou can edit the investment parameters:")
        
        # Edit risk tolerance
        print(f"\nCurrent Risk Tolerance: {current_portfolio.get('risk_tolerance', 'moderate')}")
        risk_choice = input("New risk tolerance (conservative/moderate/aggressive) [Enter to keep]: ").strip().lower()
        
        # Edit investment amount
        print(f"\nCurrent Investment Amount: ${current_portfolio.get('cash', 10000):,}")
        amount_input = input("New investment amount [Enter to keep]: ").strip()
        
        # ============================================
        # APPLY EDITS TO STATE
        # ============================================
        updates = {}
        
        if risk_choice and risk_choice in ['conservative', 'moderate', 'aggressive']:
            updates["portfolio"] = state.values.get("portfolio", {}).copy()
            updates["portfolio"]["risk_tolerance"] = risk_choice
            log_message(f"\n✅ Risk tolerance updated to: {risk_choice}")
        
        if amount_input:
            try:
                new_amount = int(amount_input.replace(',', ''))
                if "portfolio" not in updates:
                    updates["portfolio"] = state.values.get("portfolio", {}).copy()
                updates["portfolio"]["cash"] = new_amount
                log_message(f"✅ Investment amount updated to: ${new_amount:,}")
            except:
                log_message("❌ Invalid amount, keeping original")
        
        # Apply updates if any
        if updates:
            log_message("\n📌 Applying edits to state...")
            state = graph.update_state(config, updates)
            log_message("✅ State updated with human edits")
        else:
            log_message("\n📌 No edits applied, continuing with original plan")
        
        # ============================================
        # RESUME EXECUTION
        # ============================================
        print("\n" + "="*60)
        choice = input("❓ Resume execution with these settings? (yes/no): ").strip().lower()
        
        if choice == 'yes' or choice == 'y':
            log_message(f"\n✅ User APPROVED. Resuming execution with edited state...")
            
            # Resume execution using stream
            for step in graph.stream(None, config=config):
                pass
            
            # Get final result
            result = graph.invoke(None, config=config)
            
            # Show final result
            if result.get("final_output"):
                print("\n" + "="*60)
                print("📊 FINAL INVESTMENT THESIS (WITH EDITED PARAMETERS)")
                print("="*60)
                print(result["final_output"])
            else:
                print("\n⚠️ No final output generated")
            
            log_message("\n✅ Investment thesis generated with human edits")
            
        else:
            log_message(f"\n❌ User REJECTED. Cancelling execution...")
            print("\n❌ Execution cancelled by user.")
        
        log_message("\n✅ State editing test completed")
        log_message(f"📝 Log file: logs/lab5/state_editing.log")
        
    except Exception as e:
        log_message(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_state_editing()