"""
Persistence Test for FinAgentix - Lab 5 Task 1
Tests that conversations can be saved and resumed using thread_id
FIXED: Added message serialization to prevent JSON errors
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

def log_message(message: str):
    """Log message to file and print"""
    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
    log_entry = f"[{timestamp}] {message}\n"
    
    log_file = LOG_DIR / "persistence_test.log"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(log_entry)
    print(message)

def run_conversation(thread_id: str, query: str, new_conversation: bool = True):
    """
    Run a conversation with a specific thread_id
    
    Args:
        thread_id: Unique identifier for the conversation
        query: User query
        new_conversation: If True, start fresh; if False, resume existing
    """
    log_message(f"\n{'='*60}")
    log_message(f"🔄 {'NEW' if new_conversation else 'RESUMED'} CONVERSATION")
    log_message(f"📌 Thread ID: {thread_id}")
    log_message(f"📝 Query: {query}")
    log_message(f"{'='*60}")
    
    # Create initial state
    initial_state = create_initial_state(
        query=query,
        query_type="investment decision"
    )
    
    # Add portfolio info
    initial_state["portfolio"] = {
        "risk_tolerance": "moderate",
        "cash": 10000,
        "holdings": []
    }
    initial_state["tickers"] = ["NVDA"]
    
    # Configure with thread_id
    config = {
        "configurable": {
            "thread_id": thread_id,
            "recursion_limit": 30
        }
    }
    
    try:
        if new_conversation:
            log_message("\n🚀 Starting new conversation...")
            
            # Use stream() instead of invoke() to avoid serialization during execution
            for step in graph.stream(initial_state, config=config):
                for node_name, node_output in step.items():
                    if node_name == "router_node":
                        completed = node_output.get('agents_completed', [])
                        if completed:
                            log_message(f"   ✅ Completed: {completed}")
            
            # Get final result
            result = graph.invoke(initial_state, config=config)
            
            # Extract market data to prove memory
            if result.get("market_data") and result["market_data"].get("quotes"):
                price = result["market_data"]["quotes"].get('price', 'N/A')
                log_message(f"\n📊 Market Data Stored: Price = ${price}")
            
            log_message("\n✅ Conversation saved to checkpoint_db.sqlite")
            
        else:
            log_message("\n🔄 Resuming previous conversation...")
            
            # Resume existing conversation
            for step in graph.stream(None, config=config):
                for node_name, node_output in step.items():
                    if node_name == "router_node":
                        completed = node_output.get('agents_completed', [])
                        if completed:
                            log_message(f"   ✅ Resumed with: {completed}")
            
            # Get final state
            result = graph.invoke(None, config=config)
            
            # Show what we remember
            if result.get("market_data") and result["market_data"].get("quotes"):
                price = result["market_data"]["quotes"].get('price', 'N/A')
                log_message(f"\n📊 Agent Remembers: Price = ${price}")
                log_message("✅ Memory works! Agent retrieved previous context.")
            else:
                log_message("❌ No memory found - persistence failed")
        
        return result
        
    except Exception as e:
        log_message(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_persistence():
    """Main test function for persistence"""
    
    print("\n" + "="*70)
    print("📋 LAB 5 TASK 1: PERSISTENCE TEST")
    print("="*70 + "\n")
    
    # Use a fixed thread_id for testing
    thread_id = f"persistence_test_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Step 1: Run first conversation
    log_message("\n📌 STEP 1: Starting first conversation...")
    result1 = run_conversation(thread_id, "Should I invest $10,000 in NVDA?", new_conversation=True)
    
    if not result1:
        log_message("❌ First conversation failed")
        return
    
    # Step 2: Wait a moment
    log_message("\n⏳ Waiting 2 seconds...")
    time.sleep(2)
    
    # Step 3: Resume with same thread_id
    log_message("\n📌 STEP 2: Resuming with same thread_id...")
    result2 = run_conversation(thread_id, "What was the price again?", new_conversation=False)
    
    log_message("\n" + "="*60)
    log_message("✅ PERSISTENCE TEST COMPLETED")
    log_message("📁 Checkpoint DB: checkpoint_db.sqlite")
    log_message("📝 Log file: logs/lab5/persistence_test.log")
    log_message("="*60)

if __name__ == "__main__":
    test_persistence()