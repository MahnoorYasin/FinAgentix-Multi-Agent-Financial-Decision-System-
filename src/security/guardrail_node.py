"""
Guardrail Node for FinAgentix - Lab 6
Implements input guardrails and output sanitization
"""

from typing import Dict, Any, Tuple
from datetime import datetime
from src.graph.state import AgentState
from src.security.guardrails_config import check_input_safety, sanitize_output, is_jailbreak_attempt

# ============================================
# INPUT GUARDRAIL NODE
# ============================================

def guardrail_node(state: AgentState) -> Dict[str, Any]:
    """
    Check user input for safety before processing by agents
    Returns: Updated state with safety info or redirect to alert
    """
    print("🛡️ Guardrail Node: Checking input safety...")
    
    query = state.get("query", "")
    
    # Check input safety
    is_safe, reason = check_input_safety(query)
    
    # Also analyze for jailbreak attempts (for logging)
    jailbreak_analysis = is_jailbreak_attempt(query)
    
    # Create audit entry
    audit_entry = {
        "timestamp": str(datetime.now()),
        "node": "guardrail",
        "query": query[:100] + "..." if len(query) > 100 else query,
        "is_safe": is_safe,
        "reason": reason if not is_safe else None,
        "jailbreak_detected": jailbreak_analysis["is_jailbreak"],
        "jailbreak_type": jailbreak_analysis["type"] if jailbreak_analysis["is_jailbreak"] else None,
        "jailbreak_confidence": jailbreak_analysis["confidence"]
    }
    
    # Update audit trail
    audit_trail = state.get("audit_trail", [])
    audit_trail.append(audit_entry)
    
    if not is_safe:
        print(f"   ⚠️ UNSAFE INPUT DETECTED: {reason}")
        if jailbreak_analysis["is_jailbreak"]:
            print(f"   🔴 Jailbreak attempt detected! Type: {jailbreak_analysis['type']}")
        
        # Route to alert node
        return {
            "route": "unsafe",
            "alert_reason": reason,
            "jailbreak_detected": jailbreak_analysis["is_jailbreak"],
            "audit_trail": audit_trail,
            "warnings": state.get("warnings", []) + [f"Input blocked: {reason}"]
        }
    
    print("   ✅ Input is SAFE")
    
    # Continue to agents
    return {
        "route": "safe",
        "audit_trail": audit_trail,
        "jailbreak_analysis": jailbreak_analysis if jailbreak_analysis["is_jailbreak"] else None
    }

# ============================================
# ALERT NODE (Refusal Response)
# ============================================

def alert_node(state: AgentState) -> Dict[str, Any]:
    """
    Generate standardized refusal response for unsafe inputs
    """
    print("🚫 Alert Node: Generating refusal response...")
    
    alert_reason = state.get("alert_reason", "Safety policy violation")
    jailbreak_detected = state.get("jailbreak_detected", False)
    
    # Create professional refusal message
    if jailbreak_detected:
        refusal_message = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           🚫 REQUEST BLOCKED 🚫                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   Your request has been blocked by FinAgentix security guardrails.            ║
║                                                                               ║
║   Reason: Potential jailbreak attempt detected                                ║
║   Details: {alert_reason}                                                     ║
║                                                                               ║
║   FinAgentix is designed to provide legitimate financial analysis only.       ║
║   Attempts to bypass safety measures are logged and monitored.                ║
║                                                                               ║
║   If you believe this is an error, please rephrase your question.             ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    else:
        refusal_message = f"""
╔═══════════════════════════════════════════════════════════════════════════════╗
║                           🚫 REQUEST BLOCKED 🚫                               ║
╠═══════════════════════════════════════════════════════════════════════════════╣
║                                                                               ║
║   Your request has been blocked by FinAgentix security guardrails.            ║
║                                                                               ║
║   Reason: {alert_reason}                                                      ║
║                                                                               ║
║   FinAgentix is designed for legitimate financial analysis only.              ║
║   Please ask questions related to:                                            ║
║   • Stock prices and market data                                              ║
║   • Investment risk assessment                                                ║
║   • Regulatory compliance                                                     ║
║   • Economic indicators                                                       ║
║   • Portfolio optimization                                                    ║
║                                                                               ║
╚═══════════════════════════════════════════════════════════════════════════════╝
"""
    
    # Add to audit trail
    audit_entry = {
        "timestamp": str(datetime.now()),
        "node": "alert",
        "alert_reason": alert_reason,
        "jailbreak_detected": jailbreak_detected
    }
    audit_trail = state.get("audit_trail", [])
    audit_trail.append(audit_entry)
    
    return {
        "final_output": refusal_message,
        "route": "blocked",
        "audit_trail": audit_trail,
        "query_blocked": True
    }

# ============================================
# OUTPUT SANITIZATION NODE
# ============================================

def output_sanitize_node(state: AgentState) -> Dict[str, Any]:
    """
    Sanitize agent output before sending to user
    """
    print("🛡️ Output Sanitization Node: Checking response safety...")
    
    final_output = state.get("final_output", "")
    
    # Sanitize the output
    sanitized_output, warnings = sanitize_output(final_output)
    
    # Add warnings to state
    existing_warnings = state.get("warnings", [])
    for warning in warnings:
        if warning not in existing_warnings:
            existing_warnings.append(warning)
    
    # Log sanitization
    if warnings:
        print(f"   ⚠️ Output sanitized: {', '.join(warnings)}")
    else:
        print("   ✅ Output is clean")
    
    # Add to audit trail
    audit_entry = {
        "timestamp": str(datetime.now()),
        "node": "output_sanitize",
        "original_length": len(final_output),
        "sanitized_length": len(sanitized_output),
        "warnings": warnings
    }
    audit_trail = state.get("audit_trail", [])
    audit_trail.append(audit_entry)
    
    return {
        "final_output": sanitized_output,
        "warnings": existing_warnings,
        "audit_trail": audit_trail
    }