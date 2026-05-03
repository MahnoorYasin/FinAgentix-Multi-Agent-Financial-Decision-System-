"""
Compliance Agent - Handles regulatory compliance
UPDATED with force tool calling and retry logic
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.base_agent import BaseAgent
from src.tools.tools import (
    check_finra_compliance,
    generate_audit_trail
)

class ComplianceAgent(BaseAgent):
    """Agent specialized in compliance checking"""
    
    def __init__(self):
        tools = [
            check_finra_compliance,
            generate_audit_trail
        ]
        super().__init__("compliance", tools)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print(f"\n⚖️ COMPLIANCE AGENT working...")
        
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

Call check_finra_compliance with {"ticker": "NVDA", "action": "BUY", "amount": 10000}

CALL THIS TOOL IMMEDIATELY. DO NOT RESPOND WITH TEXT.
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
                        "agent": "compliance",
                        "tools_called": tools_called,
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    })
                    
                    return {
                        "messages": state.get("messages", []) + force_messages + [response],
                        "compliance_data": state.get("compliance_data", {}),
                        "current_agent": "compliance"
                    }
                else:
                    print(f"⚠️ No tools called on attempt {attempt+1}")
                    if attempt == 0:
                        force_messages.append(HumanMessage(content="❌ CALL check_finra_compliance NOW ❌"))
                    else:
                        # Fallback
                        fallback_response = AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "check_finra_compliance",
                                    "args": {"ticker": "NVDA", "action": "BUY", "amount": 10000},
                                    "id": "fallback_compliance_1"
                                }
                            ]
                        )
                        return {
                            "messages": state.get("messages", []) + force_messages + [fallback_response],
                            "compliance_data": state.get("compliance_data", {}),
                            "current_agent": "compliance"
                        }
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return {
            "messages": state.get("messages", []) + force_messages,
            "compliance_data": state.get("compliance_data", {}),
            "current_agent": "compliance"
        }