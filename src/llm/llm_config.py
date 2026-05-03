"""
LLM Configuration for FinAgentix
Using Groq Llama 3.3 70B - Clean prints
UPDATED for Lab 7: Added LangSmith tracing (via environment variables only)
"""

import os
from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()

# ============================================
# LANGSMITH SETUP (Lab 7) - Environment Variables Only
# ============================================

def setup_langsmith():
    """Initialize LangSmith via environment variables (no imports needed)"""
    langsmith_api_key = os.getenv("LANGSMITH_API_KEY")
    langsmith_project = os.getenv("LANGSMITH_PROJECT", "FinAgentix")
    
    if langsmith_api_key:
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
        os.environ["LANGCHAIN_PROJECT"] = langsmith_project
        os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
        print(f"🔍 LangSmith tracing enabled for project: {langsmith_project}")
        return True
    else:
        print("⚠️ LangSmith not configured - tracing disabled")
        print("   Get API key from: https://smith.langchain.com")
        return False

# Initialize LangSmith
LANGSMITH_ENABLED = setup_langsmith()

def get_llm(provider="groq", model_name=None, temperature=0.1):
    if not model_name:
        model_name = "llama3-8b-8192"
    
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY not found in .env file")
    
    print(f"🚀 Using {model_name}")
    
    llm = ChatGroq(
        model_name=model_name,
        temperature=temperature,
        groq_api_key=api_key,
    )
    
    return llm

def get_llm_for_agent(agent_type):
    smart_model = "llama-3.3-70b-versatile"
    
    configs = {
        "market": {"temp": 0.1},
        "news": {"temp": 0.3},
        "risk": {"temp": 0.0},
        "compliance": {"temp": 0.0},
        "economic": {"temp": 0.1},
        "portfolio": {"temp": 0.2},
    }
    
    cfg = configs.get(agent_type, {"temp": 0.1})
    return get_llm(model_name=smart_model, temperature=cfg["temp"])