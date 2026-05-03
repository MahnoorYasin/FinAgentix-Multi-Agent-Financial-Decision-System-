"""
Conditional Router for LangGraph
Decides next step based on current state
UPDATED: Fixed routing to ensure portfolio node runs before conflict check
"""

from typing import Literal
from langgraph.graph import END
from src.graph.state import AgentState

def router(state: AgentState) -> Literal["market_node", "news_node", "risk_node", 
                                         "compliance_node", "economic_node", 
                                         "portfolio_node", "tool_node",
                                         "conflict_check_node", 
                                         "resolve_conflicts_node", "__end__"]:
    """
    Route to next node based on current state and LLM response
    
    Args:
        state: Current agent state
    
    Returns:
        Next node to execute (must match graph node names exactly)
    """
    
    # Check query type to determine which agents to run
    query_type = state.get("query_type", "")
    
    # Track which agents have completed
    completed = state.get("agents_completed", [])
    
    # IMPORTANT: For investment decision, we MUST run portfolio agent
    # after all other agents are complete
    if query_type == "investment decision":
        # Check if we have a final output already (means we're done)
        if state.get("final_output"):
            return "conflict_check_node"
        
        # Run all agents in sequence
        if "market" not in completed:
            return "market_node"
        elif "news" not in completed:
            return "news_node"
        elif "risk" not in completed:
            return "risk_node"
        elif "compliance" not in completed:
            return "compliance_node"
        elif "economic" not in completed:
            return "economic_node"
        elif "portfolio" not in completed:
            # Portfolio must run before conflict check
            return "portfolio_node"
        else:
            # All agents including portfolio are done, go to conflict check
            return "conflict_check_node"
    
    elif query_type == "price/trend":
        if "market" not in completed:
            return "market_node"
        else:
            return "conflict_check_node"
    
    elif query_type == "risk/volatility":
        if "market" not in completed:
            return "market_node"
        elif "risk" not in completed:
            return "risk_node"
        else:
            return "conflict_check_node"
    
    elif query_type == "regulation":
        if "compliance" not in completed:
            return "compliance_node"
        else:
            return "conflict_check_node"
    
    elif query_type == "economic":
        if "economic" not in completed:
            return "economic_node"
        else:
            return "conflict_check_node"
    
    elif query_type == "allocation":
        if "market" not in completed:
            return "market_node"
        elif "risk" not in completed:
            return "risk_node"
        elif "economic" not in completed:
            return "economic_node"
        else:
            return "conflict_check_node"
    
    # Default
    return "conflict_check_node"

def tool_router(state: AgentState) -> Literal["tool_node", "next_agent"]:
    """Router that checks if tools were called"""
    messages = state.get("messages", [])
    
    if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
        print(f"🔄 Routing to tool_node ({len(messages[-1].tool_calls)} tool calls)")
        return "tool_node"
    
    return "next_agent"

def conflict_router(state: AgentState) -> Literal["resolve_conflicts_node", "generate_report_node"]:
    """Router for conflict resolution"""
    if state.get("conflicts"):
        print(f"⚠️ Conflicts found: {len(state['conflicts'])}")
        return "resolve_conflicts_node"
    
    print("✅ No conflicts found, generating report")
    return "generate_report_node"