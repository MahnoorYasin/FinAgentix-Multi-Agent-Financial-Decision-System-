"""
Market Agent - Handles all market data operations
UPDATED with force tool calling and retry logic
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from src.agents.base_agent import BaseAgent
from src.tools.tools import (
    get_realtime_quotes,
    get_historical_data,
    search_sec_filings,
    compute_technical_indicators,
    identify_support_resistance
)

class MarketAgent(BaseAgent):
    """Agent specialized in market data"""
    
    def __init__(self):
        tools = [
            get_realtime_quotes,
            get_historical_data,
            search_sec_filings,
            compute_technical_indicators,
            identify_support_resistance
        ]
        super().__init__("market", tools)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print(f"\n📈 MARKET AGENT working...")
        
        # Get existing messages or start fresh
        messages = state.get("messages", [])
        
        # Build message list with VERY strong tool instructions
        force_messages = []
        
        # 1. Start with system prompt if no messages
        if not messages:
            force_messages.append(HumanMessage(content=self.get_system_prompt()))
        else:
            # Keep conversation history but add fresh instructions
            force_messages.extend(messages[-3:] if len(messages) > 3 else messages)
        
        # 2. Add user query if present
        if state.get("query"):
            force_messages.append(HumanMessage(content=f"QUERY: {state['query']}"))
        
        # 3. Add EXTREMELY STRONG tool instruction
        force_messages.append(HumanMessage(content="""
███████████████████████████████████████████████████████████████████████████
CRITICAL INSTRUCTION - YOU MUST CALL A TOOL NOW:

You have the following tools available for market data:
- get_realtime_quotes(ticker) - Get current stock price
- get_historical_data(ticker, start_date, end_date) - Get historical prices
- compute_technical_indicators(ticker) - Calculate RSI, MACD, etc.
- identify_support_resistance(ticker, days) - Find support/resistance
- search_sec_filings(ticker, filing_type) - Search SEC filings

YOU MUST CALL AT LEAST ONE OF THESE TOOLS IMMEDIATELY.
DO NOT RESPOND WITH TEXT. CALL A TOOL FIRST.

Your response should contain ONLY tool calls in JSON format.
Example: {"tool_calls": [{"name": "get_realtime_quotes", "args": {"ticker": "NVDA"}}]}
███████████████████████████████████████████████████████████████████████████
"""))
        
        print(f"🔍 Calling LLM with {len(force_messages)} messages")
        
        # Try up to 2 times to get a tool call
        for attempt in range(2):
            try:
                response = self.llm_with_tools.invoke(force_messages)
                
                # Check if tools were called
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    tools_called = [tc['name'] for tc in response.tool_calls]
                    print(f"✅ TOOL CALLED (attempt {attempt+1}): {tools_called}")
                    
                    # Store which tools were called for audit trail
                    if "audit_trail" not in state:
                        state["audit_trail"] = []
                    state["audit_trail"].append({
                        "agent": "market",
                        "tools_called": tools_called,
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    })
                    
                    # Return with the response
                    return {
                        "messages": state.get("messages", []) + force_messages + [response],
                        "market_data": state.get("market_data", {}),
                        "current_agent": "market"
                    }
                else:
                    print(f"⚠️ No tools called on attempt {attempt+1}")
                    if attempt == 0:
                        # Add even stronger instruction for retry
                        force_messages.append(HumanMessage(content="""
❌❌❌ YOU FAILED TO CALL A TOOL. THIS IS YOUR FINAL WARNING ❌❌❌

You MUST call a tool. Call get_realtime_quotes with ticker="NVDA" immediately.
Do not respond with any text. Only output the tool call in JSON format.
"""))
                    else:
                        # After second failure, create a fallback tool call
                        print("⚠️ Creating fallback tool call")
                        
                        # Create a synthetic tool call for get_realtime_quotes
                        from langchain_core.messages import AIMessage
                        import json
                        
                        # Create a message with tool calls
                        fallback_response = AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "get_realtime_quotes",
                                    "args": {"ticker": "NVDA"},
                                    "id": "fallback_1"
                                }
                            ]
                        )
                        
                        print(f"✅ Using fallback tool call for get_realtime_quotes")
                        
                        return {
                            "messages": state.get("messages", []) + force_messages + [fallback_response],
                            "market_data": state.get("market_data", {}),
                            "current_agent": "market"
                        }
                        
            except Exception as e:
                print(f"❌ Error on attempt {attempt+1}: {e}")
                if attempt == 1:
                    # On final error, return empty but don't crash
                    return {
                        "messages": state.get("messages", []),
                        "market_data": state.get("market_data", {}),
                        "current_agent": "market",
                        "errors": state.get("errors", []) + [str(e)]
                    }
        
        return {
            "messages": state.get("messages", []) + force_messages,
            "market_data": state.get("market_data", {}),
            "current_agent": "market"
        }