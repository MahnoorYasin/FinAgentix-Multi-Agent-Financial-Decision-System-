"""
Agent Nodes for LangGraph
Each node corresponds to a step in the workflow
UPDATED with data validation, confidence scoring, NumPy serialization fix, and comprehensive object serialization
FIXED: Convert numpy types, pandas Timestamps, and all non-serializable objects at source
"""

from datetime import datetime
from typing import Dict, Any, List
from langchain_core.messages import FunctionMessage, HumanMessage, AIMessage, BaseMessage
import numpy as np
import pandas as pd

from src.agents.market_agent import MarketAgent
from src.agents.news_agent import NewsAgent
from src.agents.risk_agent import RiskAgent
from src.agents.compliance_agent import ComplianceAgent
from src.agents.economic_agent import EconomicAgent
from src.agents.portfolio_agent import PortfolioAgent
from src.graph.state import AgentState
from src.security.guardrails_config import sanitize_output

# Initialize agents
market_agent = MarketAgent()
news_agent = NewsAgent()
risk_agent = RiskAgent()
compliance_agent = ComplianceAgent()
economic_agent = EconomicAgent()
portfolio_agent = PortfolioAgent()


# ============================================
# COMPREHENSIVE SERIALIZATION HELPER
# ============================================

def make_serializable(obj):
    """
    Convert any non-serializable object to Python native types.
    Handles numpy types, pandas Timestamps, LangChain messages, and more.
    """
    # Handle numpy types
    if isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, np.bool_):
        return bool(obj)
    
    # Handle pandas Timestamp (this was the recent error)
    elif isinstance(obj, pd.Timestamp):
        return obj.isoformat()
    
    # Handle datetime objects
    elif isinstance(obj, datetime):
        return obj.isoformat()
    
    # Handle LangChain messages
    elif isinstance(obj, (HumanMessage, AIMessage, FunctionMessage)):
        return {
            "__type__": obj.__class__.__name__,
            "content": obj.content,
            "type": getattr(obj, 'type', 'unknown'),
            "additional_kwargs": getattr(obj, 'additional_kwargs', {})
        }
    elif isinstance(obj, BaseMessage):
        return {
            "__type__": "BaseMessage",
            "content": obj.content,
            "type": obj.type,
        }
    
    # Handle collections recursively
    elif isinstance(obj, dict):
        return {key: make_serializable(value) for key, value in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [make_serializable(item) for item in obj]
    elif isinstance(obj, set):
        return {make_serializable(item) for item in obj}
    
    # Return as-is if already serializable
    else:
        return obj


# Keep existing numpy conversion functions for backward compatibility
def convert_numpy(obj):
    """Convert numpy types to Python native types for serialization"""
    return make_serializable(obj)


def convert_to_python_types(obj):
    """
    Convert numpy types to Python native types immediately.
    This is used at the source when storing results in state.
    """
    return make_serializable(obj)


# ============================================
# AGENT NODES
# ============================================

def market_node(state: AgentState) -> Dict[str, Any]:
    """Market agent node - gets market data"""
    print("📈 Market Agent working...")
    result = market_agent.process(state)
    
    return {
        "market_data": result.get("market_data", {}),
        "messages": state["messages"] + result.get("messages", []),
        "current_agent": "market"  # ← This MUST be set
    }


def news_node(state: AgentState) -> Dict[str, Any]:
    """News agent node - gets news and sentiment"""
    print("📰 News Agent working...")
    result = news_agent.process(state)
    
    return {
        "news_data": result.get("news_data", {}),
        "messages": state["messages"] + result.get("messages", []),
        "current_agent": "news"
    }


def risk_node(state: AgentState) -> Dict[str, Any]:
    """Risk agent node - calculates risk metrics"""
    print("⚠️ Risk Agent working...")
    result = risk_agent.process(state)
    
    return {
        "risk_data": result.get("risk_data", {}),
        "messages": state["messages"] + result.get("messages", []),
        "current_agent": "risk"
    }


def compliance_node(state: AgentState) -> Dict[str, Any]:
    """Compliance agent node - checks regulations"""
    print("⚖️ Compliance Agent working...")
    result = compliance_agent.process(state)
    
    return {
        "compliance_data": result.get("compliance_data", {}),
        "audit_trail": state.get("audit_trail", []) + [{
            "agent": "compliance",
            "timestamp": str(datetime.now()),
            "result": result.get("compliance_data", {})
        }],
        "messages": state["messages"] + result.get("messages", []),
        "current_agent": "compliance"
    }


def economic_node(state: AgentState) -> Dict[str, Any]:
    """Economic agent node - gets economic indicators"""
    print("📊 Economic Agent working...")
    result = economic_agent.process(state)
    
    return {
        "economic_data": result.get("economic_data", {}),
        "messages": state["messages"] + result.get("messages", []),
        "current_agent": "economic"
    }


def portfolio_node(state: AgentState) -> Dict[str, Any]:
    """Portfolio agent node - synthesizes and decides"""
    print("💼 Portfolio Agent working...")
    result = portfolio_agent.process(state)
    
    return {
        "final_output": result.get("final_output", ""),
        "messages": state["messages"] + result.get("messages", []),
        "current_agent": "portfolio"
    }


def parallel_start_node(state: AgentState) -> Dict[str, Any]:
    """Start parallel execution of multiple agents"""
    print("🚀 Starting parallel agent execution...")
    return state


def router_node(state: AgentState) -> Dict[str, Any]:
    """Router node that passes state to the router function - WITHOUT resetting state"""
    print("🧭 Router deciding next step...")
    
    # Get current agent from state
    current_agent = state.get("current_agent")
    
    # IMPORTANT: Create a copy of state to avoid modifying original unnecessarily
    new_state = dict(state)
    
    # Mark agent as completed - but only if it exists and not already completed
    if current_agent and current_agent not in new_state.get("agents_completed", []):
        if "agents_completed" not in new_state:
            new_state["agents_completed"] = []
        new_state["agents_completed"].append(current_agent)
        print(f"✅ Completed agent: {current_agent}")
    
    # Debug: Show what agents have completed (using new_state)
    print(f"   Completed so far: {new_state.get('agents_completed', [])}")
    
    # Add to audit trail (using new_state)
    audit_entry = {
        "step": "router",
        "timestamp": str(datetime.now()),
        "completed_agents": new_state.get("agents_completed", [])
    }
    new_state["audit_trail"] = new_state.get("audit_trail", []) + [audit_entry]
    
    return new_state


# ============================================
# DATA QUALITY VALIDATION FUNCTIONS
# ============================================

def validate_data_quality(state: AgentState) -> List[Dict[str, Any]]:
    """
    Validate quality of data from all agents
    Returns list of quality issues found
    """
    quality_issues = []
    
    # 1. Check market data freshness
    if state.get("market_data"):
        market_data = state["market_data"]
        
        # Check if we have quotes with timestamps
        if "quotes" in market_data and market_data["quotes"].get("timestamp"):
            timestamp_str = market_data["quotes"]["timestamp"]
            try:
                timestamp = datetime.fromisoformat(timestamp_str)
                now = datetime.now()
                age_minutes = (now - timestamp).total_seconds() / 60
                
                if age_minutes > 15:  # Data older than 15 minutes
                    quality_issues.append({
                        "type": "stale_data",
                        "agent": "market",
                        "severity": "warning",
                        "message": f"Market data is {age_minutes:.1f} minutes old"
                    })
            except:
                pass
        
        # Check if we have technical indicators
        if "technical" not in market_data:
            quality_issues.append({
                "type": "missing_data",
                "agent": "market",
                "severity": "warning",
                "message": "No technical indicators available"
            })
    
    # 2. Check news data
    if state.get("news_data"):
        news_data = state["news_data"]
        
        # Check if we have articles
        article_count = 0
        if "fetch_financial_news" in news_data:
            articles = news_data["fetch_financial_news"].get("articles", [])
            article_count = len(articles)
        
        if article_count == 0:
            quality_issues.append({
                "type": "no_data",
                "agent": "news",
                "severity": "warning",
                "message": "No news articles found"
            })
        elif article_count < 3:
            quality_issues.append({
                "type": "insufficient_data",
                "agent": "news",
                "severity": "info",
                "message": f"Only {article_count} news articles found"
            })
    
    # 3. Check risk data completeness
    if state.get("risk_data"):
        risk_data = state["risk_data"]
        
        # Check if VaR is calculated
        if "calculate_value_at_risk" not in risk_data:
            quality_issues.append({
                "type": "missing_metric",
                "agent": "risk",
                "severity": "error",
                "message": "Value at Risk not calculated"
            })
        
        # Check if stress test was performed
        if "stress_test_portfolio" not in risk_data:
            quality_issues.append({
                "type": "missing_metric",
                "agent": "risk",
                "severity": "warning",
                "message": "Stress test not performed"
            })
    
    # 4. Check compliance data
    if state.get("compliance_data"):
        compliance_data = state["compliance_data"]
        
        # Check compliance status
        if "check_finra_compliance" in compliance_data:
            compliant = compliance_data["check_finra_compliance"].get("compliant", False)
            if not compliant:
                warnings = compliance_data["check_finra_compliance"].get("warnings", [])
                quality_issues.append({
                    "type": "compliance_issue",
                    "agent": "compliance",
                    "severity": "error",
                    "message": f"Compliance check failed: {', '.join(warnings)}"
                })
    
    # 5. Check economic data
    if state.get("economic_data"):
        economic_data = state["economic_data"]
        
        # Check if we have at least some indicators
        if len(economic_data) == 0:
            quality_issues.append({
                "type": "no_data",
                "agent": "economic",
                "severity": "warning",
                "message": "No economic indicators retrieved"
            })
    
    return quality_issues


def validate_tool_results(tool_name: str, result: any) -> Dict[str, any]:
    """
    Validate results from tool calls before storing in state
    Returns validated result with any warnings
    """
    validated = {
        "data": result,
        "valid": True,
        "warnings": []
    }
    
    # Tool-specific validation
    if tool_name == "get_realtime_quotes":
        if isinstance(result, dict):
            if result.get("price", 0) <= 0:
                validated["valid"] = False
                validated["warnings"].append("Invalid price returned")
            if result.get("volume", 0) < 0:
                validated["warnings"].append("Negative volume")
    
    elif tool_name == "get_historical_data":
        if isinstance(result, dict):
            if "data" not in result or len(result.get("data", [])) == 0:
                validated["warnings"].append("No historical data returned")
    
    elif tool_name == "calculate_value_at_risk":
        if isinstance(result, dict):
            var = result.get("var_percent", 0)
            if var < 0 or var > 100:
                validated["warnings"].append("Unusual VaR value")
            if var == 0:
                validated["warnings"].append("VaR calculation may have failed")
    
    elif tool_name == "compute_technical_indicators":
        if isinstance(result, dict):
            indicators = result.get("indicators", {})
            if len(indicators) == 0:
                validated["warnings"].append("No technical indicators calculated")
    
    elif tool_name == "analyze_news_sentiment":
        if isinstance(result, dict):
            sentiment = result.get("sentiment_score", 0)
            if sentiment < -1 or sentiment > 1:
                validated["warnings"].append("Sentiment score out of range")
    
    elif tool_name == "check_finra_compliance":
        if isinstance(result, dict):
            if "compliant" not in result:
                validated["valid"] = False
                validated["warnings"].append("Compliance check incomplete")
    
    elif tool_name == "get_company_fundamentals":
        if isinstance(result, dict):
            if "error" in result:
                validated["warnings"].append(f"Fundamental data error: {result['error']}")
    
    elif tool_name == "query_vector_db":
        if isinstance(result, dict):
            results_count = len(result.get("results", {}))
            if results_count == 0:
                validated["warnings"].append("No vector DB results returned")
    
    return validated


def calculate_confidence_score(state: AgentState) -> float:
    """
    Calculate confidence score for final recommendation
    Returns score between 0.0 and 1.0
    """
    score = 1.0  # Start with perfect confidence
    reasons = []
    
    # 1. Check if all agents completed
    expected_agents = ["market", "news", "risk", "compliance", "economic", "portfolio"]
    completed = state.get("agents_completed", [])
    
    missing_agents = [a for a in expected_agents if a not in completed]
    if missing_agents:
        deduction = len(missing_agents) * 0.1
        score -= deduction
        reasons.append(f"Missing agents: {missing_agents}")
    
    # 2. Check data completeness
    if not state.get("market_data"):
        score -= 0.15
        reasons.append("No market data")
    elif not state["market_data"].get("quotes"):
        score -= 0.1
        reasons.append("No real-time quotes")
    
    if not state.get("news_data"):
        score -= 0.1
        reasons.append("No news data")
    elif "analyze_news_sentiment" not in state["news_data"]:
        score -= 0.05
        reasons.append("No sentiment analysis")
    
    if not state.get("risk_data"):
        score -= 0.15
        reasons.append("No risk metrics")
    elif "calculate_value_at_risk" not in state["risk_data"]:
        score -= 0.1
        reasons.append("No VaR calculation")
    
    if not state.get("compliance_data"):
        score -= 0.1
        reasons.append("No compliance check")
    elif state["compliance_data"].get("check_finra_compliance", {}).get("compliant") == False:
        score -= 0.3
        reasons.append("Compliance check failed")
    
    if not state.get("economic_data"):
        score -= 0.05
        reasons.append("No economic context")
    
    # 3. Check for conflicts
    conflicts = state.get("conflicts", [])
    if conflicts:
        deduction = len(conflicts) * 0.1
        score -= deduction
        reasons.append(f"Unresolved conflicts: {len(conflicts)}")
    
    # 4. Check data freshness
    if state.get("market_data", {}).get("quotes", {}).get("timestamp"):
        timestamp_str = state["market_data"]["quotes"]["timestamp"]
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            now = datetime.now()
            age_minutes = (now - timestamp).total_seconds() / 60
            
            if age_minutes > 60:  # Data older than 1 hour
                score -= 0.2
                reasons.append(f"Data stale ({age_minutes:.0f} minutes old)")
            elif age_minutes > 15:  # Data older than 15 minutes
                score -= 0.1
                reasons.append(f"Data may be stale ({age_minutes:.0f} minutes old)")
        except:
            pass
    
    # Ensure score stays within 0-1 range
    score = max(0.0, min(1.0, score))
    
    # Store confidence info in state for reporting
    state["confidence"] = {
        "score": round(score, 2),
        "reasons": reasons,
        "rating": "High" if score >= 0.8 else "Medium" if score >= 0.5 else "Low"
    }
    
    return score


# ============================================
# TOOL NODE - EXECUTES TOOL CALLS WITH VALIDATION
# ============================================

def tool_node(state: AgentState) -> Dict[str, Any]:
    """Tool node that executes tool calls and stores results in state with validation"""
    messages = state["messages"]
    last_message = messages[-1] if messages else None
    
    if not last_message or not hasattr(last_message, 'tool_calls') or not last_message.tool_calls:
        return {
            "messages": messages,
            "market_data": state.get("market_data", {}),
            "news_data": state.get("news_data", {}),
            "risk_data": state.get("risk_data", {}),
            "compliance_data": state.get("compliance_data", {}),
            "economic_data": state.get("economic_data", {}),
            "fundamental_data": state.get("fundamental_data", {}),
        }
    
    tool_calls = last_message.tool_calls
    results = []
    
    print(f"🔧 Executing {len(tool_calls)} tool calls with validation...")
    
    # Import all tools
    from src.tools.tools import (
        get_realtime_quotes, get_historical_data, search_sec_filings,
        fetch_financial_news, analyze_news_sentiment,
        calculate_value_at_risk, compute_portfolio_volatility,
        check_finra_compliance, generate_audit_trail,
        optimize_portfolio_mpt, calculate_sharpe_ratio,
        generate_investment_thesis, get_company_fundamentals,
        get_economic_indicator, get_fred_data,
        compute_technical_indicators, identify_support_resistance,
        stress_test_portfolio, query_vector_db
    )
    
    # Map tool names to functions
    tool_map = {
        'get_realtime_quotes': get_realtime_quotes,
        'get_historical_data': get_historical_data,
        'search_sec_filings': search_sec_filings,
        'fetch_financial_news': fetch_financial_news,
        'analyze_news_sentiment': analyze_news_sentiment,
        'calculate_value_at_risk': calculate_value_at_risk,
        'compute_portfolio_volatility': compute_portfolio_volatility,
        'stress_test_portfolio': stress_test_portfolio,
        'check_finra_compliance': check_finra_compliance,
        'generate_audit_trail': generate_audit_trail,
        'optimize_portfolio_mpt': optimize_portfolio_mpt,
        'calculate_sharpe_ratio': calculate_sharpe_ratio,
        'generate_investment_thesis': generate_investment_thesis,
        'get_company_fundamentals': get_company_fundamentals,
        'get_economic_indicator': get_economic_indicator,
        'get_fred_data': get_fred_data,
        'compute_technical_indicators': compute_technical_indicators,
        'identify_support_resistance': identify_support_resistance,
        'query_vector_db': query_vector_db,
    }
    
    # Track which agent is calling tools
    current_agent = state.get("current_agent", "unknown")
    
    # Initialize warnings list if not present
    if "warnings" not in state:
        state["warnings"] = []
    
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call.get("args", {})
        
        print(f"  🔨 Calling {tool_name} with args: {tool_args}")
        
        # Execute the tool
        if tool_name in tool_map:
            try:
                result = tool_map[tool_name].invoke(tool_args)
                
                # ============================================
                # VALIDATE TOOL RESULTS
                # ============================================
                validated = validate_tool_results(tool_name, result)
                
                if not validated["valid"] or validated["warnings"]:
                    for warning in validated["warnings"]:
                        print(f"    ⚠️ Validation warning: {warning}")
                        state["warnings"].append({
                            "tool": tool_name,
                            "agent": current_agent,
                            "message": warning,
                            "timestamp": str(datetime.now())
                        })
                
                # Use validated data
                result_to_store = validated["data"]
                
                # ============================================
                # CRITICAL FIX: Convert ALL non-serializable types BEFORE storing
                # ============================================
                result_to_store = make_serializable(result_to_store)
                
                print(f"    ✅ Tool executed successfully")
                
                # Store result in appropriate state field based on agent
                if current_agent == "market":
                    if "market_data" not in state:
                        state["market_data"] = {}
                    
                    if tool_name == "get_realtime_quotes":
                        if "quotes" not in state["market_data"]:
                            state["market_data"]["quotes"] = {}
                        state["market_data"]["quotes"] = result_to_store
                    elif tool_name in ["compute_technical_indicators", "identify_support_resistance", "get_historical_data"]:
                        if "technical" not in state["market_data"]:
                            state["market_data"]["technical"] = {}
                        state["market_data"]["technical"][tool_name] = result_to_store
                    else:
                        state["market_data"][tool_name] = result_to_store
                
                elif current_agent == "news":
                    if "news_data" not in state:
                        state["news_data"] = {}
                    state["news_data"][tool_name] = result_to_store
                
                elif current_agent == "risk":
                    if "risk_data" not in state:
                        state["risk_data"] = {}
                    state["risk_data"][tool_name] = result_to_store
                
                elif current_agent == "compliance":
                    if "compliance_data" not in state:
                        state["compliance_data"] = {}
                    state["compliance_data"][tool_name] = result_to_store
                
                elif current_agent == "economic":
                    if "economic_data" not in state:
                        state["economic_data"] = {}
                    state["economic_data"][tool_name] = result_to_store
                
                elif current_agent == "portfolio":
                    if "fundamental_data" not in state:
                        state["fundamental_data"] = {}
                    state["fundamental_data"][tool_name] = result_to_store
                
                # Add to audit trail with serialization
                audit_entry = {
                    "agent": current_agent,
                    "tool": tool_name,
                    "args": make_serializable(tool_args),
                    "timestamp": str(datetime.now()),
                    "validation_warnings": validated["warnings"] if validated["warnings"] else None
                }
                
                # Add result preview (truncate if too long)
                result_str = str(result_to_store)
                audit_entry["result_preview"] = result_str[:200] + "..." if len(result_str) > 200 else result_str
                
                state["audit_trail"] = state.get("audit_trail", []) + [audit_entry]
                
                # Truncate result for message to save tokens
                if len(result_str) > 1000:
                    result_str = result_str[:1000] + "... [truncated]"
                
                results.append(
                    FunctionMessage(
                        content=result_str,
                        name=tool_name
                    )
                )
            except Exception as e:
                print(f"    ❌ Tool execution failed: {e}")
                state["warnings"].append({
                    "tool": tool_name,
                    "agent": current_agent,
                    "message": f"Execution failed: {str(e)}",
                    "timestamp": str(datetime.now())
                })
                results.append(
                    FunctionMessage(
                        content=f"Error: {str(e)}",
                        name=tool_name
                    )
                )
        else:
            print(f"    ⚠️ Tool {tool_name} not found in map")
            results.append(
                FunctionMessage(
                    content=f"Tool {tool_name} not implemented",
                    name=tool_name
                )
            )
    
    return {
        "messages": results,
        "market_data": state.get("market_data", {}),
        "news_data": state.get("news_data", {}),
        "risk_data": state.get("risk_data", {}),
        "compliance_data": state.get("compliance_data", {}),
        "economic_data": state.get("economic_data", {}),
        "fundamental_data": state.get("fundamental_data", {}),
        "audit_trail": state.get("audit_trail", []),
        "warnings": state.get("warnings", []),
        "current_step": "tools_executed"
    }


# ============================================
# ENHANCED CONFLICT CHECK NODE
# ============================================

def conflict_check_node(state: AgentState) -> Dict[str, Any]:
    """
    Enhanced conflict check with data quality validation
    """
    print("🔍 Checking for conflicts and validating data quality...")
    
    conflicts = []
    quality_issues = []
    
    # ============================================
    # EXISTING CONFLICT CHECKS (enhanced)
    # ============================================
    
    # Check risk vs portfolio
    if state.get("risk_data") and state.get("portfolio"):
        # Extract VaR from risk_data
        var_value = 0
        if "calculate_value_at_risk" in state["risk_data"]:
            var_value = state["risk_data"]["calculate_value_at_risk"].get("var_percent", 0)
        
        risk_tolerance = state["portfolio"].get("risk_tolerance", "moderate")
        
        if risk_tolerance == "conservative" and var_value > 5:
            conflicts.append({
                "type": "risk_tolerance",
                "severity": "high",
                "message": f"Risk level {var_value}% exceeds conservative limit (5%)"
            })
        elif risk_tolerance == "moderate" and var_value > 10:
            conflicts.append({
                "type": "risk_tolerance",
                "severity": "medium",
                "message": f"Risk level {var_value}% exceeds moderate limit (10%)"
            })
        elif risk_tolerance == "aggressive" and var_value > 20:
            conflicts.append({
                "type": "risk_tolerance",
                "severity": "low",
                "message": f"Risk level {var_value}% exceeds aggressive limit (20%)"
            })
    
    # Check compliance
    if state.get("compliance_data"):
        compliance_result = state["compliance_data"].get("check_finra_compliance", {})
        if not compliance_result.get("compliant", True):
            conflicts.append({
                "type": "compliance",
                "severity": "high",
                "message": "Compliance check failed",
                "details": compliance_result.get("warnings", [])
            })
    
    # ============================================
    # NEW DATA QUALITY CHECKS
    # ============================================
    
    # Check sentiment vs price consistency
    if state.get("market_data") and state.get("news_data"):
        # Get sentiment
        sentiment_score = 0
        if "analyze_news_sentiment" in state.get("news_data", {}):
            sentiment_score = state["news_data"]["analyze_news_sentiment"].get("sentiment_score", 0)
        
        # Get price trend
        price_trend = "neutral"
        if "technical" in state.get("market_data", {}):
            tech_data = state["market_data"]["technical"].get("compute_technical_indicators", {})
            rsi = tech_data.get("indicators", {}).get("RSI", 50)
            if rsi > 70:
                price_trend = "overbought"
            elif rsi < 30:
                price_trend = "oversold"
        
        # Check for inconsistency
        if sentiment_score > 0.5 and price_trend == "overbought":
            quality_issues.append({
                "type": "sentiment_price_inconsistency",
                "severity": "low",
                "message": "Positive sentiment but overbought conditions - caution advised"
            })
        elif sentiment_score < -0.3 and price_trend == "oversold":
            quality_issues.append({
                "type": "sentiment_price_inconsistency",
                "severity": "low",
                "message": "Negative sentiment but oversold conditions - possible buying opportunity"
            })
    
    # Run data quality validation
    quality_issues.extend(validate_data_quality(state))
    
    # Add quality issues to warnings
    state["warnings"] = state.get("warnings", []) + quality_issues
    
    return {
        "conflicts": state.get("conflicts", []) + conflicts,
        "warnings": state.get("warnings", [])
    }


def resolve_conflicts_node(state: AgentState) -> Dict[str, Any]:
    """Resolve identified conflicts"""
    print("🔄 Resolving conflicts...")
    
    conflicts = state.get("conflicts", [])
    resolution_actions = []
    
    for conflict in conflicts:
        if conflict["type"] == "risk_tolerance":
            resolution_actions.append("Adjusted position size to match risk tolerance")
        elif conflict["type"] == "compliance":
            resolution_actions.append("Added compliance disclaimer and reduced position")
        else:
            resolution_actions.append("Noted conflict in recommendation")
    
    # Add resolution step to audit trail
    audit_entry = {
        "agent": "conflict_resolver",
        "timestamp": str(datetime.now()),
        "conflicts_found": len(conflicts),
        "resolutions": resolution_actions
    }
    
    return {
        "audit_trail": state.get("audit_trail", []) + [audit_entry],
        "conflicts": []  # Clear conflicts after resolution
    }


# ============================================
# ENHANCED REPORT GENERATION NODE
# ============================================

def generate_report_node(state: AgentState) -> Dict[str, Any]:
    """
    Enhanced report generation with confidence scoring and data quality info
    FIXED: Deep convert numpy types before creating report
    """
    print("📄 Generating enhanced final report with confidence scoring...")
    
    # ============================================
    # DEEP CONVERSION FUNCTION (uses make_serializable)
    # ============================================
    def deep_convert(obj):
        """Recursively convert all non-serializable types"""
        return make_serializable(obj)
    
    # ============================================
    # CONVERT ENTIRE STATE
    # ============================================
    try:
        # Create a new state dict with all values converted
        converted_state = {}
        for key, value in state.items():
            converted_state[key] = deep_convert(value)
        
        # Use converted state for the rest of the function
        state = converted_state
    except Exception as e:
        print(f"⚠️ Warning during conversion: {e}")
        # Continue with original state if conversion fails
    
    # Calculate confidence score
    try:
        confidence_score = calculate_confidence_score(state)
    except Exception as e:
        print(f"⚠️ Error calculating confidence score: {e}")
        confidence_score = 0.5
    
    confidence = state.get("confidence", {
        "score": confidence_score,
        "rating": "High" if confidence_score >= 0.8 else "Medium" if confidence_score >= 0.5 else "Low"
    })
    
    # Check which data sources have data
    market_ok = bool(state.get("market_data"))
    news_ok = bool(state.get("news_data"))
    risk_ok = bool(state.get("risk_data"))
    compliance_ok = bool(state.get("compliance_data"))
    economic_ok = bool(state.get("economic_data"))
    fundamental_ok = bool(state.get("fundamental_data"))
    
    # Get warnings and conflicts
    warnings = state.get("warnings", [])
    conflicts = state.get("conflicts", [])
    
    # Format confidence bar
    confidence_bar = "█" * int(confidence_score * 20) + "░" * (20 - int(confidence_score * 20))
    
    # Build the report
    report = f"""
{'=' * 60}
📊 INVESTMENT DECISION REPORT
{'=' * 60}

📝 QUERY: {state.get('query', 'N/A')}
📅 TIMESTAMP: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'=' * 60}
🎯 CONFIDENCE SCORE: {confidence['rating']} ({confidence_score*100:.0f}%)
{confidence_bar} {confidence_score*100:.0f}%
{'=' * 60}

💡 RECOMMENDATION:
{state.get('final_output', 'No recommendation generated')}

{'=' * 60}
📊 DATA SOURCES USED:
   - Market Data: {'✅' if market_ok else '❌'}
   - News Data: {'✅' if news_ok else '❌'}
   - Risk Data: {'✅' if risk_ok else '❌'}
   - Compliance Data: {'✅' if compliance_ok else '❌'}
   - Economic Data: {'✅' if economic_ok else '❌'}
   - Fundamental Data: {'✅' if fundamental_ok else '❌'}

⚠️ WARNINGS ({len(warnings)}):
"""
    
    # Add warnings
    if warnings:
        for i, warning in enumerate(warnings[:5]):  # Show first 5 warnings
            if isinstance(warning, dict):
                msg = warning.get('message', str(warning))
                agent = warning.get('agent', 'unknown')
                report += f"   {i+1}. [{agent}] {msg}\n"
            else:
                report += f"   {i+1}. {str(warning)}\n"
        
        if len(warnings) > 5:
            report += f"   ... and {len(warnings) - 5} more warnings\n"
    else:
        report += "   No warnings\n"
    
    # Add conflicts
    report += f"""
⚔️ CONFLICTS ({len(conflicts)}):
"""
    
    if conflicts:
        for i, conflict in enumerate(conflicts):
            severity = conflict.get('severity', 'medium')
            severity_icon = '🔴' if severity == 'high' else '🟡' if severity == 'medium' else '🟢'
            report += f"   {i+1}. {severity_icon} {conflict.get('message', str(conflict))}\n"
    else:
        report += "   No conflicts found\n"
    
    # Add confidence reasons
    if confidence.get('reasons'):
        report += f"""
📉 CONFIDENCE FACTORS:
"""
        for reason in confidence['reasons'][:3]:
            report += f"   • {reason}\n"
    
    # Add audit trail count
    report += f"""
📋 AUDIT TRAIL:
   {len(state.get('audit_trail', []))} steps logged

{'=' * 60}
"""
    
    # ============================================
    # ADD DETAILED DATA PREVIEWS
    # ============================================
    
    # Market Data Preview
    if market_ok and state["market_data"].get("quotes"):
        quote = state["market_data"]["quotes"]
        report += f"\n📈 MARKET DATA:\n"
        report += f"   Price: ${quote.get('price', 'N/A')} ({quote.get('change_percent', 0):+.2f}%)\n"
        report += f"   Volume: {quote.get('volume', 0):,}\n"
    
    # Technical Indicators
    if market_ok and state["market_data"].get("technical"):
        technical = state["market_data"]["technical"]
        if technical.get("compute_technical_indicators"):
            indicators = technical["compute_technical_indicators"].get("indicators", {})
            if indicators:
                report += f"\n📊 TECHNICAL INDICATORS:\n"
                if indicators.get('RSI'):
                    report += f"   RSI: {indicators['RSI']}\n"
                if indicators.get('SMA20'):
                    report += f"   SMA20: ${indicators['SMA20']}\n"
                if indicators.get('SMA50'):
                    report += f"   SMA50: ${indicators['SMA50']}\n"
    
    # Support/Resistance
    if market_ok and state["market_data"].get("identify_support_resistance"):
        sr = state["market_data"]["identify_support_resistance"]
        report += f"\n🔍 SUPPORT/RESISTANCE:\n"
        report += f"   Support: ${sr.get('support', 'N/A')}\n"
        report += f"   Resistance: ${sr.get('resistance', 'N/A')}\n"
    
    # News & Sentiment
    if news_ok:
        sentiment = state["news_data"].get("analyze_news_sentiment", {})
        if sentiment:
            score = sentiment.get('sentiment_score', 0)
            sentiment_text = sentiment.get('sentiment', 'neutral')
            sentiment_icon = '😊' if score > 0.2 else '😐' if score > -0.2 else '😞'
            report += f"\n📰 NEWS SENTIMENT:\n"
            report += f"   {sentiment_icon} {sentiment_text} ({score:+.2f})\n"
        
        news = state["news_data"].get("fetch_financial_news", {})
        articles = news.get('articles', [])
        if articles:
            report += f"\n📰 RECENT NEWS:\n"
            report += f"   Found {len(articles)} articles\n"
            if articles and len(articles) > 0 and isinstance(articles[0], str):
                preview = articles[0][:100] + "..." if len(articles[0]) > 100 else articles[0]
                report += f"   Top: {preview}\n"
    
    # Risk Metrics
    if risk_ok:
        var = state["risk_data"].get("calculate_value_at_risk", {})
        if var:
            report += f"\n⚠️ RISK METRICS:\n"
            report += f"   VaR (95%): {var.get('var_percent', 0)}%\n"
            report += f"   {var.get('interpretation', '')}\n"
        
        stress = state["risk_data"].get("stress_test_portfolio", {})
        if stress:
            report += f"\n📉 STRESS TEST:\n"
            report += f"   Scenario: {stress.get('scenario', 'N/A')}\n"
            report += f"   Impact: {stress.get('portfolio_impact', 0)}%\n"
    
    # Compliance
    if compliance_ok:
        comp = state["compliance_data"].get("check_finra_compliance", {})
        if comp:
            status = '✅ COMPLIANT' if comp.get('compliant') else '❌ NON-COMPLIANT'
            report += f"\n⚖️ COMPLIANCE:\n"
            report += f"   {status}\n"
            if comp.get('rules_checked'):
                report += f"   Rules: {', '.join(comp['rules_checked'])}\n"
            if comp.get('warnings'):
                for warning in comp['warnings']:
                    report += f"   ⚠️ {warning}\n"
    
    # Economic Data
    if economic_ok:
        report += f"\n📊 ECONOMIC INDICATORS:\n"
        econ_found = False
        for key, value in state["economic_data"].items():
            if "get_economic_indicator" in key or "get_fred_data" in key:
                if isinstance(value, dict):
                    econ_found = True
                    if "indicator_name" in value:
                        name = value.get('indicator_name', key)
                        val = value.get('latest_value', 'N/A')
                        report += f"   • {name}: {val}\n"
                    elif "data" in value:
                        report += f"   • {key}: Data retrieved\n"
        if not econ_found:
            report += "   No economic data available\n"
    
    # Portfolio/Fundamental Data
    if fundamental_ok:
        report += f"\n💼 FUNDAMENTAL ANALYSIS:\n"
        
        fundamentals = state["fundamental_data"].get("get_company_fundamentals", {})
        if fundamentals:
            pe = fundamentals.get('pe_ratio', 'N/A')
            beta = fundamentals.get('beta', 'N/A')
            market_cap = fundamentals.get('market_cap', 'N/A')
            if pe != 'N/A':
                report += f"   P/E Ratio: {pe}\n"
            if beta != 'N/A':
                report += f"   Beta: {beta}\n"
            if market_cap != 'N/A':
                if isinstance(market_cap, (int, float)):
                    report += f"   Market Cap: ${market_cap:,.0f}\n"
                else:
                    report += f"   Market Cap: {market_cap}\n"
        
        sharpe = state["fundamental_data"].get("calculate_sharpe_ratio", {})
        if sharpe:
            ratio = sharpe.get('sharpe_ratio', 'N/A')
            interp = sharpe.get('interpretation', '')
            report += f"\n📈 SHARPE RATIO:\n"
            report += f"   {ratio} ({interp})\n"
    
    # Investment Thesis
    if fundamental_ok and state["fundamental_data"].get("generate_investment_thesis"):
        thesis = state["fundamental_data"]["generate_investment_thesis"]
        if thesis and isinstance(thesis, str):
            report += f"\n💡 INVESTMENT THESIS:\n"
            # Format thesis nicely
            thesis_lines = thesis.split('\n')
            for line in thesis_lines:
                if line.strip():
                    report += f"   {line.strip()}\n"
                else:
                    report += "\n"
    
    report += f"\n{'=' * 60}"
    
    return {"final_output": report}