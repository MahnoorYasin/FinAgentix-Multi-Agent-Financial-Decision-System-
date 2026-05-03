"""
Agent State Definition for LangGraph
Defines the state object that persists throughout the agent workflow
UPDATED with confidence and warnings fields
"""

from typing import TypedDict, List, Dict, Any, Annotated, Optional
from langgraph.graph.message import add_messages
from langchain_core.messages import BaseMessage

class AgentState(TypedDict):
    """
    State for the multi-agent investment system
    Tracks all data and progress through the workflow
    Maps directly to your 6 datasets and workflow diagram
    """
    
    # ============================================
    # Core Conversation (Required for LangGraph)
    # ============================================
    messages: Annotated[List[BaseMessage], add_messages]
    """Chat history with add_messages reducer for automatic concatenation"""
    
    # ============================================
    # User Query Information
    # ============================================
    query: str
    """Original user query (e.g., 'Should I invest in NVDA?')"""
    
    query_type: str
    """Classification from QueryParser: 'allocation', 'price/trend', 'investment decision', 'risk/volatility', 'regulation'"""
    
    # ============================================
    # Data from Your 6 Datasets (Lab 2 Knowledge Base)
    # ============================================
    
    # 1. Market Data (01_market_data)
    market_data: Dict[str, Any]
    """Contains stock prices, historical data, technical indicators"""
    
    # 2. News & Sentiment Data (02_news_sentiment)
    news_data: Dict[str, Any]
    """Contains news articles, sentiment scores, Financial PhraseBank data"""
    
    # 3. Risk Data (03_risk_data)
    risk_data: Dict[str, Any]
    """Contains VaR, volatility, Sharpe ratios, risk metrics"""
    
    # 4. Compliance Data (04_compliance_data)
    compliance_data: Dict[str, Any]
    """Contains FINRA rules, compliance check results"""
    
    # 5. Economic Data (07_economic_data)
    economic_data: Dict[str, Any]
    """Contains GDP, inflation, interest rates, FRED data"""
    
    # 6. Fundamental Data (08_fundamental_data)
    fundamental_data: Dict[str, Any]
    """Contains P/E ratios, market cap, company financials"""
    
    # ============================================
    # Portfolio Information
    # ============================================
    portfolio: Dict[str, Any]
    """User's portfolio information, risk tolerance, cash available"""
    
    tickers: List[str]
    """List of tickers being analyzed (e.g., ['NVDA', 'AAPL'])"""
    
    # ============================================
    # Decision Tracking
    # ============================================
    investment_thesis: str
    """Generated investment thesis or recommendation"""
    
    conflicts: List[Dict[str, Any]]
    """List of conflicts found between agent recommendations"""
    
    audit_trail: List[Dict[str, Any]]
    """Complete log of all steps for compliance (matches your AuditTrailGeneration)"""
    
    # ============================================
    # NEW VALIDATION FIELDS
    # ============================================
    confidence: Dict[str, Any]
    """Confidence score and rating for the recommendation"""
    
    warnings: List[Dict[str, Any]]
    """Data quality warnings and validation messages"""
    
    # ============================================
    # Workflow Tracking (For LangGraph Routing)
    # ============================================
    current_agent: str
    """Currently executing agent: 'market', 'news', 'risk', 'compliance', 'economic', 'portfolio'"""
    
    agents_completed: List[str]
    """List of agents that have finished execution"""
    
    tool_calls: List[Dict]
    """History of tool calls made by agents"""
    
    final_output: str
    """Final formatted output to user (matches your FinalOutput)"""
    
    # ============================================
    # Error Handling
    # ============================================
    errors: List[Dict[str, Any]]
    """Any errors encountered during execution"""


# ============================================
# HELPER FUNCTIONS FOR STATE MANAGEMENT
# ============================================

def create_initial_state(query: str, query_type: str = "investment decision") -> AgentState:
    """
    Create a new initial state for a user query
    
    Args:
        query: User's question
        query_type: Type of query (default: investment decision)
    
    Returns:
        Initialized AgentState with all fields including new validation fields
    """
    return {
        "messages": [],
        "query": query,
        "query_type": query_type,
        "market_data": {},
        "news_data": {},
        "risk_data": {},
        "compliance_data": {},
        "economic_data": {},
        "fundamental_data": {},
        "portfolio": {
            "risk_tolerance": "moderate",
            "cash": 10000,
            "holdings": []
        },
        "tickers": extract_tickers_from_query(query),
        "investment_thesis": "",
        "conflicts": [],
        "audit_trail": [],
        "confidence": {"score": 0.0, "rating": "Unknown", "reasons": []},  # NEW
        "warnings": [],  # NEW
        "current_agent": "",
        "agents_completed": [],
        "tool_calls": [],
        "final_output": "",
        "errors": []
    }

def extract_tickers_from_query(query: str) -> List[str]:
    """
    Simple ticker extraction from query
    In production, use a proper NER model
    
    Args:
        query: User query string
    
    Returns:
        List of potential tickers
    """
    import re
    
    # Common ticker patterns (uppercase words)
    words = query.split()
    potential_tickers = []
    
    # Known tickers from your dataset
    known_tickers = [
        'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 
        'BRK-B', 'LLY', 'V', 'JPM', 'UNH', 'XOM', 'WMT', 'JNJ',
        'MA', 'PG', 'HD', 'MRK', 'CVX', 'KO', 'PEP', 'BAC', 'COST'
    ]
    
    for word in words:
        clean_word = re.sub(r'[^A-Za-z]', '', word).upper()
        if clean_word in known_tickers:
            potential_tickers.append(clean_word)
    
    return potential_tickers if potential_tickers else ['NVDA']  # Default

def update_agent_completion(state: AgentState, agent_name: str) -> AgentState:
    """
    Mark an agent as completed
    
    Args:
        state: Current state
        agent_name: Name of completed agent
    
    Returns:
        Updated state
    """
    if agent_name not in state["agents_completed"]:
        state["agents_completed"].append(agent_name)
    
    # Add to audit trail
    state["audit_trail"].append({
        "step": f"{agent_name}_agent",
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "status": "completed"
    })
    
    return state

def add_to_audit_trail(state: AgentState, step: str, details: Dict[str, Any]) -> AgentState:
    """
    Add an entry to the audit trail
    
    Args:
        state: Current state
        step: Name of step
        details: Details to log
    
    Returns:
        Updated state
    """
    state["audit_trail"].append({
        "step": step,
        "timestamp": __import__('datetime').datetime.now().isoformat(),
        "details": details
    })
    
    return state