"""
Complete LangGraph for FinAgentix (Lab 3 Task 2 & 3)
UPDATED for Lab 5: Added SqliteSaver persistence and interrupt_before for HITL
UPDATED for Lab 6: Added security guardrail node and output sanitization
"""

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.constants import Send
import sqlite3
from typing import Any, Dict, List, Optional

from src.graph.state import AgentState
from src.graph.nodes import (
    market_node, news_node, risk_node, compliance_node,
    economic_node, portfolio_node, parallel_start_node,
    tool_node, router_node,
    conflict_check_node, resolve_conflicts_node, generate_report_node
)
from src.graph.router import router, conflict_router, tool_router
from src.security.guardrail_node import guardrail_node, alert_node, output_sanitize_node

# Initialize the graph
workflow = StateGraph(AgentState)

# ============================================
# ADD ALL NODES
# ============================================

# Security nodes (Lab 6)
workflow.add_node("guardrail_node", guardrail_node)
workflow.add_node("alert_node", alert_node)
workflow.add_node("output_sanitize_node", output_sanitize_node)

# Router node - decides next step
workflow.add_node("router_node", router_node)

# Agent nodes
workflow.add_node("market_node", market_node)
workflow.add_node("news_node", news_node)
workflow.add_node("risk_node", risk_node)
workflow.add_node("compliance_node", compliance_node)
workflow.add_node("economic_node", economic_node)
workflow.add_node("portfolio_node", portfolio_node)

# Tool node - executes tool calls
workflow.add_node("tool_node", tool_node)

# Parallel execution node - ONLY runs at start
workflow.add_node("parallel_start", parallel_start_node)

# Decision and conflict nodes
workflow.add_node("conflict_check", conflict_check_node)
workflow.add_node("resolve_conflicts", resolve_conflicts_node)
workflow.add_node("generate_report", generate_report_node)

# ============================================
# SET ENTRY POINT
# ============================================
workflow.set_entry_point("parallel_start")

# ============================================
# ADD EDGES
# ============================================

# From parallel start, go to guardrail first (Lab 6)
workflow.add_edge("parallel_start", "guardrail_node")

# Guardrail routes to either alert or router
workflow.add_conditional_edges(
    "guardrail_node",
    lambda state: state.get("route", "safe"),
    {
        "safe": "router_node",
        "unsafe": "alert_node"
    }
)

# Alert node ends the workflow
workflow.add_edge("alert_node", END)

# Router decides which agent to run next
workflow.add_conditional_edges(
    "router_node",
    router,
    {
        "market_node": "market_node",
        "news_node": "news_node",
        "risk_node": "risk_node",
        "compliance_node": "compliance_node",
        "economic_node": "economic_node",
        "portfolio_node": "portfolio_node",
        "tool_node": "tool_node",
        "conflict_check_node": "conflict_check",
        END: END
    }
)

# After each agent, check if tools were called
for node in ["market_node", "news_node", "risk_node", "compliance_node", "economic_node", "portfolio_node"]:
    workflow.add_conditional_edges(
        node,
        tool_router,
        {
            "tool_node": "tool_node",
            "next_agent": "router_node"
        }
    )

# After tool execution, go to router
workflow.add_edge("tool_node", "router_node")

# Conflict resolution
workflow.add_conditional_edges(
    "conflict_check",
    conflict_router,
    {
        "resolve_conflicts_node": "resolve_conflicts",
        "generate_report_node": "generate_report"
    }
)

# After resolving conflicts, go back to portfolio
workflow.add_edge("resolve_conflicts", "portfolio_node")

# Generate final report, then sanitize output (Lab 6)
workflow.add_edge("generate_report", "output_sanitize_node")

# Output sanitization node ends the workflow
workflow.add_edge("output_sanitize_node", END)

# ============================================
# CHECKPOINTER SETUP
# ============================================
conn = sqlite3.connect("checkpoint_db.sqlite", check_same_thread=False)
memory = SqliteSaver(conn)

# Compile with interrupt before portfolio_node
graph = workflow.compile(
    checkpointer=memory,
    #interrupt_before=["portfolio_node"]
)

# Export the compiled graph
__all__ = ["graph"]