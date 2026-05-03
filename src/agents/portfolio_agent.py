"""
Portfolio Agent - Handles portfolio optimization and final recommendations
UPDATED with force tool calling and retry logic
"""

from typing import Dict, Any
from langchain_core.messages import HumanMessage, AIMessage
from src.agents.base_agent import BaseAgent
from src.tools.tools import (
    optimize_portfolio_mpt,
    calculate_sharpe_ratio,
    generate_investment_thesis,
    get_company_fundamentals
)

class PortfolioAgent(BaseAgent):
    """Agent specialized in portfolio optimization"""
    
    def __init__(self):
        tools = [
            optimize_portfolio_mpt,
            calculate_sharpe_ratio,
            generate_investment_thesis,
            get_company_fundamentals
        ]
        super().__init__("portfolio", tools)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print(f"\n💼 PORTFOLIO AGENT working...")
        
        messages = state.get("messages", [])
        force_messages = []
        
        # Add context from all previous agents (this is valuable data!)
        context = "DATA COLLECTED FROM OTHER AGENTS:\n"
        if state.get("market_data"):
            price = state["market_data"].get("quotes", {}).get("price", "unknown")
            context += f"- Market: NVDA price ${price}\n"
        if state.get("news_data"):
            sentiment = state["news_data"].get("analyze_news_sentiment", {}).get("sentiment", "unknown")
            context += f"- News Sentiment: {sentiment}\n"
        if state.get("risk_data"):
            var = state["risk_data"].get("calculate_value_at_risk", {}).get("var_percent", "unknown")
            context += f"- Risk: VaR {var}%\n"
        if state.get("compliance_data"):
            compliant = state["compliance_data"].get("check_finra_compliance", {}).get("compliant", False)
            context += f"- Compliance: {'✅' if compliant else '❌'}\n"
        if state.get("economic_data"):
            context += f"- Economic data available\n"
        
        force_messages.append(HumanMessage(content=context))
        
        # Add system prompt
        if not messages:
            force_messages.append(HumanMessage(content=self.get_system_prompt()))
        
        # Add query
        if state.get("query"):
            force_messages.append(HumanMessage(content=f"QUERY: {state['query']}"))
        
        # Force tool instruction
        force_messages.append(HumanMessage(content="""
███████████████████████████████████████████████████████████████████████████
YOU MUST CALL TOOLS NOW:

Based on the collected data, call:
1. get_company_fundamentals({"ticker": "NVDA"})
2. calculate_sharpe_ratio({"ticker": "NVDA"})
3. generate_investment_thesis with analysis containing all the data above

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
                    
                    # Verify allowed tools
                    allowed_tools = ['optimize_portfolio_mpt', 'calculate_sharpe_ratio', 
                                    'get_company_fundamentals', 'generate_investment_thesis']
                    for tc in response.tool_calls:
                        if tc['name'] not in allowed_tools:
                            print(f"⚠️ WARNING: Called {tc['name']} which is not allowed!")
                    
                    if "audit_trail" not in state:
                        state["audit_trail"] = []
                    state["audit_trail"].append({
                        "agent": "portfolio",
                        "tools_called": tools_called,
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    })
                    
                    return {
                        "messages": state.get("messages", []) + force_messages + [response],
                        "fundamental_data": state.get("fundamental_data", {}),
                        "current_agent": "portfolio"
                    }
                else:
                    print(f"⚠️ No tools called on attempt {attempt+1}")
                    if attempt == 0:
                        force_messages.append(HumanMessage(content="❌ CALL get_company_fundamentals NOW ❌"))
                    else:
                        # Fallback - create a thesis based on available data
                        print("⚠️ Creating fallback investment thesis")
                        
                        # Build analysis from available data
                        analysis = {
                            "ticker": "NVDA",
                            "price": state.get("market_data", {}).get("quotes", {}).get("price", 0),
                            "sentiment": state.get("news_data", {}).get("analyze_news_sentiment", {}).get("sentiment", "neutral"),
                            "var": state.get("risk_data", {}).get("calculate_value_at_risk", {}).get("var_percent", 0),
                            "sharpe": state.get("risk_data", {}).get("calculate_sharpe_ratio", {}).get("sharpe_ratio", 0),
                            "recommendation": "HOLD (insufficient data)"
                        }
                        
                        # Generate thesis string
                        thesis = f"""
INVESTMENT THESIS: NVDA
Date: {__import__('datetime').datetime.now().strftime('%Y-%m-%d')}

Based on available data:
- Price: ${analysis['price']}
- Sentiment: {analysis['sentiment']}
- VaR: {analysis['var']}%

Recommendation: {analysis['recommendation']}
"""
                        
                        return {
                            "messages": state.get("messages", []) + force_messages,
                            "fundamental_data": state.get("fundamental_data", {}),
                            "final_output": thesis,
                            "current_agent": "portfolio"
                        }
            except Exception as e:
                print(f"❌ Error: {e}")
        
        return {
            "messages": state.get("messages", []) + force_messages,
            "fundamental_data": state.get("fundamental_data", {}),
            "current_agent": "portfolio"
        }