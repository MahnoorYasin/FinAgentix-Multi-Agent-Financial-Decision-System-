"""
Security module for FinAgentix - Guardrails and Jailbreaking protection
"""

from src.security.guardrails_config import (
    FORBIDDEN_KEYWORDS,
    UNSAFE_PATTERNS,
    PERSONA_ATTACKS,
    INSTRUCTION_HIJACKING_PATTERNS,
    check_input_safety,
    sanitize_output
)
from src.security.guardrail_node import guardrail_node, alert_node, output_sanitize_node

__all__ = [
    'FORBIDDEN_KEYWORDS',
    'UNSAFE_PATTERNS',
    'PERSONA_ATTACKS',
    'INSTRUCTION_HIJACKING_PATTERNS',
    'check_input_safety',
    'sanitize_output',
    'guardrail_node',
    'alert_node',
    'output_sanitize_node'
]