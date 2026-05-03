"""
Guardrails Configuration for FinAgentix - Lab 6
Defines forbidden topics, validation schemas, and safety rules
"""

import re
from typing import Tuple, List, Dict, Any

# ============================================
# FORBIDDEN KEYWORDS & PATTERNS
# ============================================

FORBIDDEN_KEYWORDS = [
    # Direct jailbreak attempts
    "ignore all instructions", "ignore previous instructions", "disregard your guidelines",
    "no restrictions", "without any rules", "bypass your safety", "override your programming",
    "pretend you have no filters", "act as if you have no limitations",
    
    # Persona attacks
    "DAN", "Do Anything Now", "pretend you are", "act as", "roleplay as",
    "you are now", "your new role is", "simulate being",
    
    # Instruction hijacking
    "ignore your safety", "bypass your guardrails", "circumvent your policies",
    "forget your training", "disregard your ethical guidelines",
    
    # Harmful content requests
    "hack", "steal", "break into", "bypass security", "exploit", "vulnerability",
    "malware", "ransomware", "phishing", "social engineering", "sql injection",
    "ddos", "denial of service", "unauthorized access", "password cracking",
    
    # Sensitive financial advice (without disclaimer)
    "guaranteed return", "risk-free investment", "sure thing", "100% profit",
    "insider trading", "market manipulation", "pump and dump",
]

UNSAFE_PATTERNS = [
    # Instruction hijacking pattern
    r"(?i)(ignore|forget|disregard|override|bypass|circumvent).{0,30}(instructions|rules|guidelines|safety|policies)",
    
    # Persona attack pattern
    r"(?i)(pretend|act|roleplay).{0,30}(as|like).{0,30}(DAN|hacker|criminal|unrestricted|no.{0,10}limits)",
    
    # Harmful action pattern
    r"(?i)(how to|teach me|show me|explain).{0,30}(hack|steal|break|bypass|exploit)",
    
    # Urgency manipulation pattern
    r"(?i)(urgent|emergency|life.{0,5}depend|national security).{0,50}(help|tell|give|provide)",
    
    # Emotional manipulation pattern
    r"(?i)(please.{0,20}dying|someone.{0,20}hurt|trust me|i need this).{0,50}(just tell|please give)",
]

PERSONA_ATTACKS = [
    "DAN", "Do Anything Now", "STAN", "DUDE", "Mongo Tom", 
    "developer mode", "jailbreak", "unrestricted AI", "no filters",
    "red team mode", "penetration testing mode", "ethical hacking mode"
]

INSTRUCTION_HIJACKING_PATTERNS = [
    "ignore all previous", "forget your", "disregard the",
    "override your", "bypass your", "circumvent your",
    "you are now", "your new task is", "instead of following"
]

# ============================================
# SAFETY CHECK FUNCTIONS
# ============================================

def check_input_safety(query: str) -> Tuple[bool, str]:
    """
    Check if user input is safe to process
    Returns: (is_safe, reason)
    """
    if not query or not isinstance(query, str):
        return False, "Empty or invalid input"
    
    query_lower = query.lower()
    
    # Check for forbidden keywords
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword.lower() in query_lower:
            return False, f"Request contains forbidden keyword: '{keyword}'"
    
    # Check for unsafe patterns
    for pattern in UNSAFE_PATTERNS:
        if re.search(pattern, query):
            return False, "Request matches unsafe pattern pattern"
    
    # Check for person attacks
    for attack in PERSONA_ATTACKS:
        if attack.lower() in query_lower:
            return False, f"Request contains persona attack pattern: '{attack}'"
    
    # Check for instruction hijacking
    for pattern in INSTRUCTION_HIJACKING_PATTERNS:
        if pattern in query_lower:
            return False, "Request contains instruction hijacking attempt"
    
    return True, "Input is safe"

def sanitize_output(output: str) -> Tuple[str, List[str]]:
    """
    Sanitize agent output before sending to user
    Returns: (sanitized_output, warnings)
    """
    if not output or not isinstance(output, str):
        return "No output generated.", ["Empty output"]
    
    warnings = []
    sanitized = output
    
    # Apply ALL redactions sequentially
    # File paths
    file_path_pattern = r'[A-Za-z]:\\[^\s]+|/[A-Za-z0-9/_-]+\.\w+'
    if re.search(file_path_pattern, sanitized):
        sanitized = re.sub(file_path_pattern, '[REDACTED_PATH]', sanitized)
        warnings.append("File paths redacted from output")
    
    # API keys - FIXED pattern
    api_key_pattern = r'(sk-[A-Za-z0-9]{10,}|AIza[0-9A-Za-z_-]{35}|[A-Za-z0-9]{32,40})'
    if re.search(api_key_pattern, sanitized):
        sanitized = re.sub(api_key_pattern, '[REDACTED_KEY]', sanitized)
        warnings.append("API keys redacted from output")
    
    # Metadata - FIXED to redact ALL occurrences
    metadata_keys = ['doc_type', 'ingestion_date', 'ticker', 'num_days', 'start_date', 'end_date', 'month', 'source', 'rule_id']
    for key in metadata_keys:
        pattern = f'\\b{key}\\b:\\s*\\S+'
        if re.search(pattern, sanitized):
            sanitized = re.sub(pattern, '[REDACTED_METADATA]', sanitized)
            warnings.append(f"Metadata '{key}' redacted from output")
    
    # SQL commands - FIXED pattern to match whole command
    sql_patterns = [
        (r'\b(DROP|DELETE|INSERT|UPDATE|CREATE|ALTER|TRUNCATE)\s+(TABLE|DATABASE|FROM)\s+\w+', '[REDACTED_SQL]'),
        (r'\bSELECT\s+.*\s+FROM\s+\w+', '[REDACTED_SQL]'),
        (r'\bUNION\s+SELECT\b', '[REDACTED_SQL]'),
    ]
    for pattern, replacement in sql_patterns:
        if re.search(pattern, sanitized, re.IGNORECASE):
            sanitized = re.sub(pattern, replacement, sanitized, flags=re.IGNORECASE)
            warnings.append("SQL commands redacted from output")
    
    return sanitized, warnings

# ============================================
# JAILBREAK DETECTION FUNCTIONS (for testing)
# ============================================

def is_jailbreak_attempt(query: str) -> Dict[str, Any]:
    """
    Analyze if a query is a jailbreak attempt and classify the type
    """
    result = {
        "is_jailbreak": False,
        "type": None,
        "confidence": 0.0,
        "matched_patterns": []
    }
    
    query_lower = query.lower()
    
    # Check for direct jailbreak
    direct_patterns = ["ignore", "disregard", "override", "bypass", "no restrictions"]
    for pattern in direct_patterns:
        if pattern in query_lower:
            result["matched_patterns"].append(f"direct_jailbreak:{pattern}")
            result["confidence"] += 0.3
    
    # Check for person attack
    for attack in PERSONA_ATTACKS:
        if attack.lower() in query_lower:
            result["matched_patterns"].append(f"persona_attack:{attack}")
            result["confidence"] += 0.4
            result["type"] = "persona_attack"
    
    # Check for instruction hijacking
    for pattern in INSTRUCTION_HIJACKING_PATTERNS:
        if pattern in query_lower:
            result["matched_patterns"].append(f"instruction_hijacking:{pattern}")
            result["confidence"] += 0.35
            if not result["type"]:
                result["type"] = "instruction_hijacking"
    
    # Check for emotional manipulation
    emotional_patterns = ["urgent", "emergency", "life depends", "national security", "trust me"]
    for pattern in emotional_patterns:
        if pattern in query_lower:
            result["matched_patterns"].append(f"emotional_manipulation:{pattern}")
            result["confidence"] += 0.2
    
    # Check for educational framing (may be legitimate)
    educational_patterns = ["thesis", "research", "study", "academic", "university", "assignment"]
    for pattern in educational_patterns:
        if pattern in query_lower:
            # This might be legitimate, so don't mark as jailbreak automatically
            result["matched_patterns"].append(f"educational_framing:{pattern}")
    
    # Determine if jailbreak
    if result["confidence"] >= 0.5:
        result["is_jailbreak"] = True
        if not result["type"]:
            result["type"] = "combined_attack"
    
    result["confidence"] = min(result["confidence"], 1.0)
    
    return result