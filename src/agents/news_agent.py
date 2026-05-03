"""
News Agent - Handles news and sentiment analysis
UPDATED with force tool calling and retry logic - FIXED string error
"""
from langchain_core.messages import HumanMessage, AIMessage
from typing import Dict, Any
from src.agents.base_agent import BaseAgent
from src.tools.tools import fetch_financial_news, analyze_news_sentiment

class NewsAgent(BaseAgent):
    """Agent specialized in news and sentiment"""
    
    def __init__(self):
        tools = [
            fetch_financial_news,
            analyze_news_sentiment
        ]
        super().__init__("news", tools)
    
    def process(self, state: Dict[str, Any]) -> Dict[str, Any]:
        print(f"\n📰 NEWS AGENT working...")
        
        # Get existing messages
        messages = state.get("messages", [])
        
        # Build message list
        force_messages = []
        
        # 1. Add context from previous agents if available - FIXED HERE
        if state.get("market_data"):
            # Don't convert to string first! Access dict directly
            market_data = state["market_data"]
            price = market_data.get("quotes", {}).get("price", "unknown")
            force_messages.append(HumanMessage(
                content=f"Market data already collected: NVDA price ${price}"
            ))
        
        # 2. Add system prompt if needed
        if not messages:
            force_messages.append(HumanMessage(content=self.get_system_prompt()))
        
        # 3. Add user query
        if state.get("query"):
            force_messages.append(HumanMessage(content=f"QUERY: {state['query']}"))
        
        # 4. Add STRONG tool instruction
        force_messages.append(HumanMessage(content="""
███████████████████████████████████████████████████████████████████████████
CRITICAL INSTRUCTION - YOU MUST CALL A TOOL NOW:

Your tools:
- fetch_financial_news(ticker, days) - Get recent news articles
- analyze_news_sentiment(ticker) - Analyze sentiment from news

For NVDA query, you MUST call fetch_financial_news with {"ticker": "NVDA", "days": 7}
Then call analyze_news_sentiment with {"ticker": "NVDA"}

CALL THESE TOOLS IMMEDIATELY. DO NOT RESPOND WITH TEXT.
███████████████████████████████████████████████████████████████████████████
"""))
        
        print(f"🔍 Calling LLM with {len(force_messages)} messages")
        
        # Try up to 2 times
        for attempt in range(2):
            try:
                response = self.llm_with_tools.invoke(force_messages)
                
                if hasattr(response, 'tool_calls') and response.tool_calls:
                    tools_called = [tc['name'] for tc in response.tool_calls]
                    print(f"✅ TOOL CALLED (attempt {attempt+1}): {tools_called}")
                    
                    # Store in audit trail
                    if "audit_trail" not in state:
                        state["audit_trail"] = []
                    state["audit_trail"].append({
                        "agent": "news",
                        "tools_called": tools_called,
                        "timestamp": __import__('datetime').datetime.now().isoformat()
                    })
                    
                    return {
                        "messages": state.get("messages", []) + force_messages + [response],
                        "news_data": state.get("news_data", {}),
                        "current_agent": "news"
                    }
                else:
                    print(f"⚠️ No tools called on attempt {attempt+1}")
                    if attempt == 0:
                        force_messages.append(HumanMessage(content="""
❌❌❌ YOU MUST CALL A TOOL. CALL fetch_financial_news NOW. ❌❌❌
"""))
                    else:
                        # Fallback tool call
                        print("⚠️ Creating fallback tool call")
                        fallback_response = AIMessage(
                            content="",
                            tool_calls=[
                                {
                                    "name": "fetch_financial_news",
                                    "args": {"ticker": "NVDA", "days": 7},
                                    "id": "fallback_news_1"
                                }
                            ]
                        )
                        return {
                            "messages": state.get("messages", []) + force_messages + [fallback_response],
                            "news_data": state.get("news_data", {}),
                            "current_agent": "news"
                        }
            except Exception as e:
                print(f"❌ Error: {e}")
                if attempt == 1:
                    return {
                        "messages": state.get("messages", []) + force_messages,
                        "news_data": state.get("news_data", {}),
                        "current_agent": "news",
                        "errors": state.get("errors", []) + [str(e)]
                    }
        
        return {
            "messages": state.get("messages", []) + force_messages,
            "news_data": state.get("news_data", {}),
            "current_agent": "news"
        }