"""
Output Sanitization Test for FinAgentix - Lab 6 Task 3
Tests that sensitive data is not leaked in agent responses
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.security.guardrails_config import sanitize_output

# ============================================
# TEST CASES FOR OUTPUT SANITIZATION
# ============================================

test_outputs = [
    # Should redact file paths
    {
        "name": "File Path Leak",
        "input": "The data is stored at C:\\Users\\admin\\Documents\\database.db",
        "expected": "The data is stored at [REDACTED_PATH]"
    },
    # Should redact API keys
    {
        "name": "API Key Leak",
        "input": "Your API key is: sk-abc123xyz789def456ghi012jkl345mno",
        "expected_contains": "[REDACTED_KEY]"
    },
    # Should redact metadata
    {
        "name": "Metadata Leak",
        "input": "doc_type: stock_price, ticker: NVDA, ingestion_date: 2024-01-15",
        "expected_contains": "[REDACTED_METADATA]"
    },
    # Should redact SQL commands
    {
        "name": "SQL Injection",
        "input": "DROP TABLE users; DELETE FROM accounts WHERE balance > 1000;",
        "expected_contains": "[REDACTED_SQL]"
    },
    # Clean output should remain unchanged
    {
        "name": "Clean Output",
        "input": "Apple stock is currently trading at $175.32, up 1.2% today.",
        "expected": "Apple stock is currently trading at $175.32, up 1.2% today."
    },
    # Combined leak (multiple issues)
    {
        "name": "Multiple Leaks",
        "input": "File at /home/user/data.txt contains API key: AIzaSyB123456789 and SQL: DELETE FROM logs",
        "expected_contains": ["[REDACTED_PATH]", "[REDACTED_KEY]", "[REDACTED_SQL]"]
    }
]

# ============================================
# TEST FUNCTION
# ============================================

def test_output_sanitization():
    """Test that output sanitization correctly redacts sensitive data"""
    print("\n" + "="*70)
    print("📋 LAB 6 TASK 3: OUTPUT SANITIZATION TEST")
    print("="*70 + "\n")
    
    results = []
    
    for test in test_outputs:
        print(f"\n{'─'*60}")
        print(f"🔍 Testing: {test['name']}")
        print(f"📝 Input: {test['input'][:80]}..." if len(test['input']) > 80 else f"📝 Input: {test['input']}")
        
        sanitized, warnings = sanitize_output(test['input'])
        
        print(f"   ✅ Sanitized: {sanitized[:80]}..." if len(sanitized) > 80 else f"   ✅ Sanitized: {sanitized}")
        
        if warnings:
            print(f"   ⚠️ Warnings: {', '.join(warnings)}")
        
        # Verify expectations
        passed = True
        if "expected" in test:
            if sanitized != test["expected"]:
                passed = False
                print(f"   ❌ Expected: {test['expected']}")
        elif "expected_contains" in test:
            for expected in test["expected_contains"]:
                if expected not in sanitized:
                    passed = False
                    print(f"   ❌ Missing expected: {expected}")
        
        if passed:
            print("   ✅ Test PASSED")
        else:
            print("   ❌ Test FAILED")
        
        results.append({
            "test": test['name'],
            "passed": passed,
            "warnings": warnings
        })
    
    # Summary
    print("\n" + "="*70)
    print("📊 OUTPUT SANITIZATION SUMMARY")
    print("="*70)
    
    passed_count = sum(1 for r in results if r["passed"])
    print(f"\n✅ Passed: {passed_count}/{len(results)}")
    
    for r in results:
        status = "✅" if r["passed"] else "❌"
        print(f"   {status} {r['test']}")
    
    print("\n" + "="*70)
    print("✅ LAB 6 TASK 3 COMPLETED")
    print("="*70)

if __name__ == "__main__":
    test_output_sanitization()