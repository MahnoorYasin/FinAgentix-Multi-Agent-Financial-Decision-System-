"""
Economic Agent - Handles economic indicators
UPDATED with force tool calling and retry logic
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.base_agent import BaseAgent
from src.tools.tools import get_economic_indicator, get_fred_data

class EconomicAgent(BaseAgent):
    """Agent specialized in economic data"""
    
    def __init__(self):
        tools = [
            get_economic_indicator,
            get_fred_data
        ]
        super().__init__("economic", tools)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print(f"\n📊 ECONOMIC AGENT working...")
        
        messages = state.get("messages", [])
        force_messages = []
        
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

Call get_economic_indicator with {"indicator": "GDP"}
Call get_economic_indicator with {"indicator": "FEDFUNDS"}

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
                        "agent": "economic",
                        "tools_called": tools_called,
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    })
                    
                    return {
                        "messages": state.get("messages", []) + force_messages + [response],
                        "economic_data": state.get("economic_data", {}),
                        "current_agent": "economic"
                    }
                else:
                    print(f"⚠️ No tools called on attempt {attempt+1}")
                    if attempt == 0:
                        force_messages.append(HumanMessage(content="❌ CALL get_economic_indicator NOW ❌"))
                    else:
                        # Fallback
                        fallback_response = AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "get_economic_indicator",
                                    "args": {"indicator": "GDP"},
                                    "id": "fallback_econ_1"
                                }
                            ]
                        )
                        return {
                            "messages": state.get("messages", []) + force_messages + [fallback_response],
                            "economic_data": state.get("economic_data", {}),
                            "current_agent": "economic"
                        }
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return {
            "messages": state.get("messages", []) + force_messages,
            "economic_data": state.get("economic_data", {}),
            "current_agent": "economic"
        }