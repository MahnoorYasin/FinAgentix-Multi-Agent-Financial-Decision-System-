"""
Base Agent Class for all FinAgentix agents
"""

from typing import Dict, Any, List
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langchain_core.tools import BaseTool
from src.llm.llm_config import get_llm_for_agent

class BaseAgent:
    """Base class for all agents"""
    
    def __init__(self, agent_type: str, tools: List[BaseTool]):
        self.agent_type = agent_type
        self.tools = tools
        self.llm = get_llm_for_agent(agent_type)
        self.llm_with_tools = self.llm.bind_tools(tools, tool_choice="auto")
        print(f"   🔧 Tools bound for {agent_type}: {[t.name for t in tools]}")
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        """Process current state and decide next action"""
        raise NotImplementedError
    
    def get_system_prompt(self) -> str:
        """Get system prompt for this agent"""
        return """You are a financial AI agent. 
Always use the available tools to get real data. 
Never make up answers or prices.
Call the appropriate tool for the user's query."""
    
    def invoke_llm(self, messages: List, config: Dict = None) -> AIMessage:
        """
        Invoke the LLM with tool calling.
        """
        max_retries = 2
        
        for attempt in range(max_retries):
            try:
                full_messages = [SystemMessage(content=self.get_system_prompt())] + list(messages)
                response = self.llm_with_tools.invoke(full_messages, config=config or {})
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    print(f"✅ TOOL CALLED (attempt {attempt + 1}): {[tc.get('name') for tc in response.tool_calls]}")
                    return response
                
                print(f"⚠️ No tools called on attempt {attempt + 1}")
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg or "rate_limit" in error_msg.lower():
                    print(f"❌ Rate limit error: {e}")
                    raise
                print(f"❌ Error on attempt {attempt + 1}: {e}")
        
        # Fallback to first tool
        if self.tools:
            tool = self.tools[0]
            print(f"⚠️ Creating fallback tool call for {tool.name}")
            return AIMessage(
                content="",
                tool_calls=[{
                    "name": tool.name,
                    "args": {},
                    "id": f"fallback_{tool.name}"
                }]
            )
        
        return AIMessage(content="Error: Unable to process request")