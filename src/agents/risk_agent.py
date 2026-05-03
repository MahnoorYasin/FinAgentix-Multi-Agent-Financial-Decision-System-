"""
Risk Agent - Handles risk assessment
UPDATED with force tool calling and retry logic
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.base_agent import BaseAgent
from src.tools.tools import (
    calculate_value_at_risk,
    compute_portfolio_volatility,
    stress_test_portfolio
)

class RiskAgent(BaseAgent):
    """Agent specialized in risk assessment"""
    
    def __init__(self):
        tools = [
            calculate_value_at_risk,
            compute_portfolio_volatility,
            stress_test_portfolio
        ]
        super().__init__("risk", tools)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print(f"\n⚠️ RISK AGENT working...")
        
        messages = state.get("messages", [])
        force_messages = []
        
        # Add context from previous agents
        if state.get("market_data"):
            price = state["market_data"].get("quotes", {}).get("price", "unknown")
            force_messages.append(HumanMessage(content=f"Current NVDA price: ${price}"))
        
        # Add system prompt
        if not messages:
            force_messages.append(HumanMessage(content=self.get_system_prompt()))
        
        # Add query
        if state.get("query"):
            force_messages.append(HumanMessage(content=f"QUERY: {state['query']}"))
        
        # Force tool instruction
        force_messages.append(HumanMessage(content="""
███████████████████████████████████████████████████████████████████████████
YOU MUST CALL A TOOL NOW:

Call calculate_value_at_risk with {"ticker": "NVDA", "confidence": 0.95}
Then call stress_test_portfolio with {"tickers": ["NVDA"], "scenario": "market_crash"}

CALL THESE TOOLS IMMEDIATELY. DO NOT RESPOND WITH TEXT.
███████████████████████████████████████████████████████████████████████████
"""))
        
        print(f"🔍 Calling LLM with {len(force_messages)} messages")
        
        for attempt in range(2):
            try:
                response = self.llm_with_tools.invoke(force_messages)
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    tools_called = [tc['name'] for tc in response.tool_calls]
                    print(f"✅ TOOL CALLED (attempt {attempt+1}): {tools_called}")
                    
                    if "audit_trail" not in state:
                        state["audit_trail"] = []
                    state["audit_trail"].append({
                        "agent": "risk",
                        "tools_called": tools_called,
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    })
                    
                    return {
                        "messages": state.get("messages", []) + force_messages + [response],
                        "risk_data": state.get("risk_data", {}),
                        "current_agent": "risk"
                    }
                else:
                    print(f"⚠️ No tools called on attempt {attempt+1}")
                    if attempt == 0:
                        force_messages.append(HumanMessage(content="❌ CALL calculate_value_at_risk NOW ❌"))
                    else:
                        # Fallback
                        fallback_response = AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "calculate_value_at_risk",
                                    "args": {"ticker": "NVDA", "confidence": 0.95},
                                    "id": "fallback_risk_1"
                                }
                            ]
                        )
                        return {
                            "messages": state.get("messages", []) + force_messages + [fallback_response],
                            "risk_data": state.get("risk_data", {}),
                            "current_agent": "risk"
                        }
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return {
            "messages": state.get("messages", []) + force_messages,
            "risk_data": state.get("risk_data", {}),
            "current_agent": "risk"
        }