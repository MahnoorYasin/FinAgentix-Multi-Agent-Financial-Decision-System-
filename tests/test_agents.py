"""
Test script for FinAgentix agents with automatic trace logging and clean terminal output
UPDATED: Now accepts custom user queries for all test types
FIXED: Enhanced ticker detection for all queries
FIXED: JSON serialization for all test functions
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

from src.graph.graph import graph
from src.graph.state import AgentState
import json
import datetime
import os
import time
import traceback
import warnings
import re
from langchain_core.messages import HumanMessage, AIMessage, FunctionMessage

# ============================================
# GLOBAL SERIALIZATION FIX - Applied to all functions
# ============================================
def message_serializer(obj):
    """Convert LangChain messages to serializable dicts"""
    if isinstance(obj, (HumanMessage, AIMessage, FunctionMessage)):
        return {
            "__type__": obj.__class__.__name__,
            "content": obj.content,
            "additional_kwargs": getattr(obj, 'additional_kwargs', {})
        }
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

def message_deserializer(dct):
    """Reconstruct messages from serialized dicts"""
    if "__type__" in dct:
        if dct["__type__"] == "HumanMessage":
            return HumanMessage(content=dct["content"], additional_kwargs=dct.get("additional_kwargs", {}))
        elif dct["__type__"] == "AIMessage":
            return AIMessage(content=dct["content"], additional_kwargs=dct.get("additional_kwargs", {}))
        elif dct["__type__"] == "FunctionMessage":
            return FunctionMessage(content=dct["content"], name=dct.get("name", ""))
    return dct

# Patch JSON encoder globally
original_default = json.JSONEncoder.default

def safe_default(self, obj):
    try:
        return message_serializer(obj)
    except TypeError:
        return original_default(self, obj)

json.JSONEncoder.default = safe_default

# Suppress warnings
warnings.filterwarnings("ignore", message="Object of type.*not JSON serializable")

# ============================================
# LOGGING SETUP
# ============================================

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

class Logger:
    """Handles both terminal and file logging with clean formatting"""
    
    def __init__(self, test_name: str):
        self.test_name = test_name
        self.start_time = time.time()
        
        # Create log files
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        self.detailed_log = LOG_DIR / f"detailed_trace_{test_name}_{timestamp}.log"
        self.submission_log = LOG_DIR / "collaboration_trace.log"
        
        # Initialize logs
        self._write_header()
    
    def _write_header(self):
        """Write header to log files"""
        header = f"""
{'=' * 80}
FINAGENTIX COLLABORATION TRACE - LAB 4 TASK 3
{'=' * 80}
Date: {datetime.datetime.now().strftime('%Y-%m-%d')}
Time: {datetime.datetime.now().strftime('%H:%M:%S')}
Test: {self.test_name}
{'=' * 80}

"""
        with open(self.detailed_log, 'w', encoding='utf-8') as f:
            f.write(header)
        
        with open(self.submission_log, 'w', encoding='utf-8') as f:
            f.write(header)
    
    def log(self, message: str, to_terminal: bool = True):
        """Log message to file and optionally to terminal"""
        timestamp = datetime.datetime.now().strftime('%H:%M:%S')
        log_entry = f"[{timestamp}] {message}\n"
        
        # Write to detailed log
        with open(self.detailed_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # Write to submission log
        with open(self.submission_log, 'a', encoding='utf-8') as f:
            f.write(log_entry)
        
        # Print to terminal if requested
        if to_terminal:
            print(message)
    
    def log_agent_start(self, agent_name: str, emoji: str = "🤔"):
        """Log agent start with clear formatting"""
        message = f"\n{emoji} {agent_name.upper()} AGENT STARTING..."
        self.log(f"{'─' * 60}", to_terminal=True)
        self.log(message, to_terminal=True)
        self.log(f"{'─' * 60}", to_terminal=True)
    
    def log_tool_call(self, tool_name: str, args: dict):
        """Log tool call with clean formatting"""
        self.log(f"  🔧 CALLING: {tool_name}", to_terminal=True)
    
    def log_agent_results(self, agent_name: str, data: dict):
        """Log formatted results for each agent type"""
        self.log(f"\n  📊 {agent_name.upper()} FETCHED:", to_terminal=True)
        
        if agent_name == "market" and data:
            # Show market data results
            quotes = data.get("quotes", {})
            if quotes:
                price = quotes.get('price', 'N/A')
                change = quotes.get('change_percent', 0)
                volume = quotes.get('volume', 0)
                self.log(f"    💰 Price: ${price} ({change:+.2f}%)", to_terminal=True)
                if volume:
                    self.log(f"    📊 Volume: {volume:,}", to_terminal=True)
            
            technical = data.get("technical", {})
            if technical:
                indicators = technical.get("compute_technical_indicators", {}).get("indicators", {})
                if indicators:
                    rsi = indicators.get('RSI', 'N/A')
                    sma20 = indicators.get('SMA20', 'N/A')
                    sma50 = indicators.get('SMA50', 'N/A')
                    self.log(f"    📈 RSI: {rsi}", to_terminal=True)
                    if sma20 != 'N/A':
                        self.log(f"    📉 SMA20: ${sma20}", to_terminal=True)
                    if sma50 != 'N/A':
                        self.log(f"    📉 SMA50: ${sma50}", to_terminal=True)
            
            support_resistance = data.get("identify_support_resistance", {})
            if support_resistance:
                support = support_resistance.get('support', 'N/A')
                resistance = support_resistance.get('resistance', 'N/A')
                self.log(f"    🔻 Support: ${support}", to_terminal=True)
                self.log(f"    🔺 Resistance: ${resistance}", to_terminal=True)
        
        elif agent_name == "news" and data:
            # Show news data results
            sentiment = data.get("analyze_news_sentiment", {})
            if sentiment:
                score = sentiment.get('sentiment_score', 0)
                sentiment_text = sentiment.get('sentiment', 'neutral')
                sentiment_icon = '😊' if score > 0.2 else '😐' if score > -0.2 else '😞'
                self.log(f"    {sentiment_icon} Sentiment: {sentiment_text} ({score:+.2f})", to_terminal=True)
            
            news = data.get("fetch_financial_news", {})
            articles = news.get('articles', [])
            if articles:
                self.log(f"    📰 Articles found: {len(articles)}", to_terminal=True)
                if articles and len(articles) > 0 and isinstance(articles[0], str):
                    preview = articles[0][:100] + "..." if len(articles[0]) > 100 else articles[0]
                    self.log(f"    📰 Top: {preview}", to_terminal=True)
        
        elif agent_name == "risk" and data:
            # Show risk data results
            var = data.get("calculate_value_at_risk", {})
            if var:
                var_value = var.get('var_percent', 'N/A')
                interpretation = var.get('interpretation', '')
                self.log(f"    ⚠️ VaR (95%): {var_value}%", to_terminal=True)
                if interpretation:
                    self.log(f"    📊 {interpretation}", to_terminal=True)
            
            stress = data.get("stress_test_portfolio", {})
            if stress:
                impact = stress.get('portfolio_impact', 'N/A')
                self.log(f"    📉 Crash Impact: {impact}%", to_terminal=True)
        
        elif agent_name == "compliance" and data:
            # Show compliance data results
            comp = data.get("check_finra_compliance", {})
            if comp:
                status = '✅ COMPLIANT' if comp.get('compliant') else '❌ NON-COMPLIANT'
                self.log(f"    {status}", to_terminal=True)
                if comp.get('warnings'):
                    for warning in comp['warnings']:
                        self.log(f"    ⚠️ {warning}", to_terminal=True)
                if comp.get('rules_checked'):
                    rules = ', '.join(comp['rules_checked'])
                    self.log(f"    📋 Rules: {rules}", to_terminal=True)
        
        elif agent_name == "economic" and data:
            # Show economic data results
            for key, value in data.items():
                if "get_economic_indicator" in key or "get_fred_data" in key:
                    if isinstance(value, dict):
                        if "indicator_name" in value:
                            name = value.get('indicator_name', key)
                            val = value.get('latest_value', 'N/A')
                            self.log(f"    📊 {name}: {val}", to_terminal=True)
                        else:
                            self.log(f"    📊 {key}: Data retrieved", to_terminal=True)
        
        elif agent_name == "portfolio" and data:
            # Show portfolio/fundamental data results
            fundamentals = data.get("get_company_fundamentals", {})
            if fundamentals:
                pe = fundamentals.get('pe_ratio', 'N/A')
                beta = fundamentals.get('beta', 'N/A')
                market_cap = fundamentals.get('market_cap', 'N/A')
                self.log(f"    🏢 P/E Ratio: {pe}", to_terminal=True)
                self.log(f"    📊 Beta: {beta}", to_terminal=True)
                if market_cap != 'N/A':
                    self.log(f"    💰 Market Cap: {market_cap:,}", to_terminal=True)
            
            sharpe = data.get("calculate_sharpe_ratio", {})
            if sharpe:
                ratio = sharpe.get('sharpe_ratio', 'N/A')
                interp = sharpe.get('interpretation', 'N/A')
                self.log(f"    📈 Sharpe Ratio: {ratio} ({interp})", to_terminal=True)
    
    def log_handover(self, from_agent: str, to_agent: str):
        """Log handover between agents"""
        self.log(f"\n  🤝 HANDOVER: {from_agent.upper()} → {to_agent.upper()}", to_terminal=True)
        self.log(f"{'─' * 60}", to_terminal=True)
    
    def log_final_answer(self, answer: str):
        """Log the final formatted answer/paragraph"""
        self.log(f"\n{'=' * 60}", to_terminal=True)
        self.log("📋 FINAL ANSWER", to_terminal=True)
        self.log(f"{'=' * 60}", to_terminal=True)
        
        # Format the answer as a clean paragraph
        if answer:
            lines = answer.split('\n')
            for line in lines:
                if line.strip():
                    self.log(line.strip(), to_terminal=True)
                else:
                    self.log("", to_terminal=True)
        else:
            self.log("No answer generated.", to_terminal=True)
        
        self.log(f"\n{'=' * 60}", to_terminal=True)
        self.log("✅ ANALYSIS COMPLETE", to_terminal=True)
        self.log(f"{'=' * 60}", to_terminal=True)
    
    def summary(self):
        """Print summary of the test run"""
        elapsed = time.time() - self.start_time
        self.log(f"\n📊 Test completed in {elapsed:.2f} seconds", to_terminal=True)
        self.log(f"📝 Detailed log: {self.detailed_log}", to_terminal=True)
        self.log(f"📋 Submission log: {self.submission_log}", to_terminal=True)


# ============================================
# STREAM HANDLER FOR CLEAN OUTPUT
# ============================================

class StreamHandler:
    """Handles graph streaming to capture and display clean output"""
    
    def __init__(self, logger: Logger):
        self.logger = logger
        self.completed_agents = []
        self.current_agent = None
        self.agent_data = {}  # Store data for each agent
        self.agent_emojis = {
            "market": "📈",
            "news": "📰",
            "risk": "⚠️",
            "compliance": "⚖️",
            "economic": "📊",
            "portfolio": "💼"
        }
        
    def handle_stream(self, stream):
        """Process each step from the graph stream"""
        
        for step in stream:
            for node_name, node_output in step.items():
                
                # ============================================
                # CAPTURE TOOL RESULTS
                # ============================================
                if node_name == "tool_node":
                    # Store data for each agent type
                    if node_output.get("market_data"):
                        self.agent_data["market"] = node_output["market_data"]
                        # Show results immediately for market
                        if "market" not in self.completed_agents:
                            self.logger.log_agent_results("market", node_output["market_data"])
                    
                    if node_output.get("news_data"):
                        self.agent_data["news"] = node_output["news_data"]
                        # Show results immediately for news
                        if "news" not in self.completed_agents:
                            self.logger.log_agent_results("news", node_output["news_data"])
                    
                    if node_output.get("risk_data"):
                        self.agent_data["risk"] = node_output["risk_data"]
                        # Show results immediately for risk
                        if "risk" not in self.completed_agents:
                            self.logger.log_agent_results("risk", node_output["risk_data"])
                    
                    if node_output.get("compliance_data"):
                        self.agent_data["compliance"] = node_output["compliance_data"]
                        # Show results immediately for compliance
                        if "compliance" not in self.completed_agents:
                            self.logger.log_agent_results("compliance", node_output["compliance_data"])
                    
                    if node_output.get("economic_data"):
                        self.agent_data["economic"] = node_output["economic_data"]
                        # Show results immediately for economic
                        if "economic" not in self.completed_agents:
                            self.logger.log_agent_results("economic", node_output["economic_data"])
                    
                    if node_output.get("fundamental_data"):
                        self.agent_data["portfolio"] = node_output["fundamental_data"]
                        # Show results immediately for portfolio
                        if "portfolio" not in self.completed_agents:
                            self.logger.log_agent_results("portfolio", node_output["fundamental_data"])
                
                # ============================================
                # HANDLE AGENT NODES - Show start
                # ============================================
                for agent in self.agent_emojis.keys():
                    if agent in node_name and self.current_agent != agent:
                        self.current_agent = agent
                        self.logger.log_agent_start(agent.upper(), self.agent_emojis.get(agent, "🤔"))
                        
                        # Show tool calls if any in this node
                        if 'messages' in node_output and node_output['messages']:
                            messages = node_output['messages']
                            if messages and hasattr(messages[-1], 'tool_calls') and messages[-1].tool_calls:
                                for tool_call in messages[-1].tool_calls:
                                    tool_name = tool_call.get('name', 'unknown')
                                    self.logger.log_tool_call(tool_name, {})
                
                # ============================================
                # HANDLE ROUTER NODE - Show handover
                # ============================================
                if node_name == "router_node":
                    # Show handover
                    completed = node_output.get('agents_completed', [])
                    if len(completed) > len(self.completed_agents):
                        if len(completed) < 6:  # Not all agents done yet
                            next_agent = list(self.agent_emojis.keys())[len(completed)]
                            self.logger.log_handover(completed[-1], next_agent)
                    
                    self.completed_agents = completed


# ============================================
# ENHANCED TICKER EXTRACTION FUNCTION
# ============================================

def extract_ticker_from_query(query: str, query_type: str = None) -> str:
    """
    Enhanced ticker extraction from query with better pattern matching
    Args:
        query: User query string
        query_type: Type of query (for intelligent defaults)
    Returns:
        Detected ticker symbol
    """
    if not query:
        return "AAPL"
    
    query_lower = query.lower()
    
    # ============================================
    # STEP 1: Direct ticker matches (e.g., "TSLA", "AAPL")
    # ============================================
    words = query.split()
    for word in words:
        clean_word = re.sub(r'[^A-Za-z]', '', word).upper()
        # Check if it's a likely ticker (2-5 uppercase letters)
        if len(clean_word) >= 2 and len(clean_word) <= 5 and clean_word.isalpha():
            # Known tickers from your dataset
            known_tickers = [
                'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 
                'BRK-B', 'LLY', 'V', 'JPM', 'UNH', 'XOM', 'WMT', 'JNJ',
                'MA', 'PG', 'HD', 'MRK', 'CVX', 'KO', 'PEP', 'BAC', 'COST',
                'NFLX', 'INTC', 'AMD', 'ORCL', 'CRM', 'IBM', 'CSCO', 'QCOM',
                'ADBE', 'PYPL', 'UBER', 'LYFT', 'ABNB', 'SPOT', 'SHOP', 'SNAP',
                'DIS', 'NKE', 'SBUX', 'MCD'
            ]
            if clean_word in known_tickers:
                return clean_word
    
    # ============================================
    # STEP 2: Company name to ticker mapping
    # ============================================
    ticker_map = {
        # Tech Giants
        'microsoft': 'MSFT',
        'apple': 'AAPL',
        'amazon': 'AMZN',
        'google': 'GOOGL',
        'alphabet': 'GOOGL',
        'nvidia': 'NVDA',
        'meta': 'META',
        'facebook': 'META',
        'tesla': 'TSLA',
        'netflix': 'NFLX',
        
        # Chip Manufacturers
        'intel': 'INTC',
        'amd': 'AMD',
        'qualcomm': 'QCOM',
        'broadcom': 'AVGO',
        'texas instruments': 'TXN',
        'micron': 'MU',
        
        # Software
        'oracle': 'ORCL',
        'salesforce': 'CRM',
        'adobe': 'ADBE',
        'servicenow': 'NOW',
        'palantir': 'PLTR',
        'snowflake': 'SNOW',
        
        # Traditional/Financial
        'berkshire': 'BRK-B',
        'buffett': 'BRK-B',
        'lilly': 'LLY',
        'visa': 'V',
        'jpmorgan': 'JPM',
        'jpm': 'JPM',
        'unitedhealth': 'UNH',
        'exxon': 'XOM',
        'walmart': 'WMT',
        'johnson': 'JNJ',
        'johnson & johnson': 'JNJ',
        'mastercard': 'MA',
        'procter': 'PG',
        'procter & gamble': 'PG',
        'home depot': 'HD',
        'merck': 'MRK',
        'chevron': 'CVX',
        'coca-cola': 'KO',
        'coke': 'KO',
        'pepsi': 'PEP',
        'pepsico': 'PEP',
        'bank of america': 'BAC',
        'bofa': 'BAC',
        'wells fargo': 'WFC',
        'goldman sachs': 'GS',
        'morgan stanley': 'MS',
        'costco': 'COST',
        
        # Consumer
        'disney': 'DIS',
        'nike': 'NKE',
        'starbucks': 'SBUX',
        'mcdonalds': 'MCD',
        "mcdonald's": 'MCD',
        'walmart': 'WMT',
        'target': 'TGT',
        
        # Telecom/Internet
        'verizon': 'VZ',
        'att': 'T',
        'tmobile': 'TMUS',
        't-mobile': 'TMUS',
        'comcast': 'CMCSA',
        
        # Industrial
        'boeing': 'BA',
        'caterpillar': 'CAT',
        'ge': 'GE',
        'honeywell': 'HON',
        '3m': 'MMM',
        'lockheed': 'LMT',
        'raytheon': 'RTX',
    }
    
    for name, tick in ticker_map.items():
        if name in query_lower:
            return tick
    
    # ============================================
    # STEP 3: Context-based defaults
    # ============================================
    if query_type:
        if query_type == "risk/volatility":
            # For risk queries, common volatile stocks
            if 'tesla' in query_lower or 'tsla' in query_lower:
                return 'TSLA'
            if 'nvidia' in query_lower or 'nvda' in query_lower:
                return 'NVDA'
            return 'TSLA'  # Default for risk queries
        
        elif query_type == "regulation":
            # For compliance queries
            if 'tesla' in query_lower or 'tsla' in query_lower:
                return 'TSLA'
            return 'TSLA'  # Default for compliance
        
        elif query_type == "price/trend":
            # For market queries
            if 'apple' in query_lower or 'aapl' in query_lower:
                return 'AAPL'
            if 'microsoft' in query_lower or 'msft' in query_lower:
                return 'MSFT'
            return 'AAPL'  # Default for market queries
    
    # ============================================
    # STEP 4: Check for multiple tickers in query
    # ============================================
    ticker_pattern = r'\b([A-Z]{2,5})\b'
    found_tickers = re.findall(ticker_pattern, query.upper())
    if found_tickers:
        # Return the first valid ticker found
        for ticker in found_tickers:
            if ticker in ticker_map.values() or ticker in ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA']:
                return ticker
    
    # ============================================
    # STEP 5: Default fallbacks
    # ============================================
    # For investment decision, default to NVDA
    if query_type == "investment decision":
        return "NVDA"
    
    return "AAPL"  # Ultimate default


# ============================================
# JSON SERIALIZATION PATCH FOR ALL FUNCTIONS
# ============================================
def apply_json_patch():
    """Apply JSON serialization patch - call at start of each test function"""
    import json
    from langchain_core.messages import HumanMessage, AIMessage, FunctionMessage
    
    # Ensure the patch is applied
    if not hasattr(json.JSONEncoder, '_patched'):
        original_default = json.JSONEncoder.default
        
        def patched_default(self, obj):
            if isinstance(obj, (HumanMessage, AIMessage, FunctionMessage)):
                return {
                    "_type": obj.__class__.__name__,
                    "content": obj.content,
                    "additional_kwargs": getattr(obj, 'additional_kwargs', {})
                }
            return original_default(self, obj)
        
        json.JSONEncoder.default = patched_default
        json.JSONEncoder._patched = True


# ============================================
# TEST FUNCTIONS - WITH ENHANCED TICKER DETECTION
# ============================================

def test_investment_decision(custom_query: str = None):
    """Test investment decision workflow with custom query"""
    apply_json_patch()
    
    # Use custom query if provided, otherwise default
    query = custom_query if custom_query else "Should I invest $10,000 in NVDA?"
    ticker = extract_ticker_from_query(query, "investment decision")
    
    print("\n" + "="*70)
    print("📋 INVESTMENT DECISION WORKFLOW TEST")
    print("="*70 + "\n")
    
    # Setup logger
    logger = Logger("investment_decision")
    logger.log(f"📝 Query: {query}")
    logger.log(f"📊 Ticker detected: {ticker}")
    logger.log(f"{'=' * 60}\n")
    
    # Initial state with detected ticker
    initial_state: AgentState = {
        "messages": [],
        "query": query,
        "query_type": "investment decision",
        "market_data": {"current_ticker": ticker},
        "news_data": {"current_ticker": ticker},
        "risk_data": {"current_ticker": ticker},
        "compliance_data": {"current_ticker": ticker},
        "economic_data": {"current_ticker": ticker},
        "fundamental_data": {"current_ticker": ticker},
        "portfolio": {"risk_tolerance": "moderate", "cash": 10000, "current_ticker": ticker},
        "tickers": [ticker],
        "investment_thesis": "",
        "conflicts": [],
        "audit_trail": [],
        "current_agent": "",
        "agents_completed": [],
        "tool_calls": [],
        "final_output": "",
        "errors": [],
        "warnings": []
    }
    
    # Run graph with streaming
    config = {
        "configurable": {
            "thread_id": f"investment_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recursion_limit": 30
        }
    }
    
    # Stream the execution for real-time logging
    stream_handler = StreamHandler(logger)
    
    # Initialize result variable
    result = {"final_output": "No result generated"}
    
    try:
        # Collect all steps
        for step in graph.stream(initial_state, config=config):
            stream_handler.handle_stream([step])
        
        # Get final result
        result = graph.invoke(initial_state, config=config)
        
        # Extract the final answer from result
        final_answer = ""
        if result.get("final_output"):
            final_answer = result["final_output"]
        elif result.get("investment_thesis"):
            final_answer = result["investment_thesis"]
        elif result.get("messages") and len(result["messages"]) > 0:
            last_msg = result["messages"][-1]
            if hasattr(last_msg, 'content'):
                final_answer = last_msg.content
        
        # If no structured answer, create a summary
        if not final_answer or final_answer == "No recommendation generated":
            final_answer = generate_summary_from_data(result, query)
        
        # Log the final formatted answer
        logger.log_final_answer(final_answer)
        
    except Exception as e:
        error_msg = f"Error during analysis: {str(e)}"
        logger.log(f"\n❌ {error_msg}", to_terminal=True)
        logger.log(traceback.format_exc(), to_terminal=False)
        logger.log_final_answer(f"An error occurred: {str(e)}")
    
    # Print summary
    logger.summary()
    
    return result


def test_market_query(custom_query: str = None):
    """Test simple market query with custom query"""
    apply_json_patch()
    
    # Use custom query if provided, otherwise default
    query = custom_query if custom_query else "What is the current price of AAPL?"
    ticker = extract_ticker_from_query(query, "price/trend")
    
    print("\n" + "="*70)
    print("📊 MARKET QUERY TEST")
    print("="*70 + "\n")
    
    logger = Logger("market_query")
    logger.log(f"📝 Query: {query}")
    logger.log(f"📊 Ticker detected: {ticker}")
    
    initial_state: AgentState = {
        "messages": [],
        "query": query,
        "query_type": "price/trend",
        "market_data": {"current_ticker": ticker},
        "news_data": {"current_ticker": ticker},
        "risk_data": {"current_ticker": ticker},
        "compliance_data": {"current_ticker": ticker},
        "economic_data": {"current_ticker": ticker},
        "fundamental_data": {"current_ticker": ticker},
        "portfolio": {"current_ticker": ticker},
        "tickers": [ticker],
        "investment_thesis": "",
        "conflicts": [],
        "audit_trail": [],
        "current_agent": "",
        "agents_completed": [],
        "tool_calls": [],
        "final_output": "",
        "errors": [],
        "warnings": []
    }
    
    config = {
        "configurable": {
            "thread_id": f"market_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recursion_limit": 20
        }
    }
    
    stream_handler = StreamHandler(logger)
    final_answer = ""
    result = {"final_output": "No result"}
    
    try:
        for step in graph.stream(initial_state, config=config):
            stream_handler.handle_stream([step])
        
        result = graph.invoke(initial_state, config=config)
        
        # Format market answer
        if result.get("market_data"):
            quotes = result["market_data"].get("quotes", {})
            if quotes:
                price = quotes.get('price', 'N/A')
                change = quotes.get('change_percent', 0)
                volume = quotes.get('volume', 0)
                final_answer = f"📊 For your query: '{query}'\n\n"
                final_answer += f"💰 {ticker} is currently trading at ${price} ({change:+.2f}% today).\n"
                if volume:
                    final_answer += f"📈 Trading volume: {volume:,} shares."
            else:
                final_answer = f"Market data retrieved for {ticker} but price information is unavailable."
        else:
            final_answer = f"No market data available for {ticker}."
        
        logger.log_final_answer(final_answer)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        final_answer = f"Error: {e}"
        logger.log_final_answer(final_answer)
    
    logger.summary()
    return result


def test_risk_query(custom_query: str = None):
    """Test risk assessment query with custom query"""
    apply_json_patch()
    
    # Use custom query if provided, otherwise default
    query = custom_query if custom_query else "What is the Value at Risk for TSLA?"
    ticker = extract_ticker_from_query(query, "risk/volatility")
    
    print("\n" + "="*70)
    print("⚠️ RISK QUERY TEST")
    print("="*70 + "\n")
    
    logger = Logger("risk_query")
    logger.log(f"📝 Query: {query}")
    logger.log(f"📊 Ticker detected: {ticker}")
    
    initial_state: AgentState = {
        "messages": [],
        "query": query,
        "query_type": "risk/volatility",
        "market_data": {"current_ticker": ticker},
        "news_data": {"current_ticker": ticker},
        "risk_data": {"current_ticker": ticker},
        "compliance_data": {"current_ticker": ticker},
        "economic_data": {"current_ticker": ticker},
        "fundamental_data": {"current_ticker": ticker},
        "portfolio": {"current_ticker": ticker},
        "tickers": [ticker],
        "investment_thesis": "",
        "conflicts": [],
        "audit_trail": [],
        "current_agent": "",
        "agents_completed": [],
        "tool_calls": [],
        "final_output": "",
        "errors": [],
        "warnings": []
    }
    
    config = {
        "configurable": {
            "thread_id": f"risk_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recursion_limit": 20
        }
    }
    
    stream_handler = StreamHandler(logger)
    final_answer = ""
    result = {"final_output": "No result"}
    
    try:
        for step in graph.stream(initial_state, config=config):
            stream_handler.handle_stream([step])
        
        result = graph.invoke(initial_state, config=config)
        
        # Format risk answer
        if result.get("risk_data"):
            var = result["risk_data"].get("calculate_value_at_risk", {})
            if var:
                var_value = var.get('var_percent', 'N/A')
                interpretation = var.get('interpretation', '')
                final_answer = f"⚠️ For your query: '{query}'\n\n"
                final_answer += f"📊 At 95% confidence, the Value at Risk for {ticker} is {var_value}%.\n"
                final_answer += f"📝 {interpretation}\n\n"
                
                stress = result["risk_data"].get("stress_test_portfolio", {})
                if stress:
                    impact = stress.get('portfolio_impact', 'N/A')
                    final_answer += f"📉 Under a market crash scenario, {ticker} could decline by {impact}%."
            else:
                final_answer = f"Risk metrics retrieved for {ticker} but VaR calculation is unavailable."
        else:
            final_answer = f"No risk data available for {ticker}."
        
        logger.log_final_answer(final_answer)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        final_answer = f"Error: {e}"
        logger.log_final_answer(final_answer)
    
    logger.summary()
    return result


def test_compliance_query(custom_query: str = None):
    """Test compliance query with custom query"""
    apply_json_patch()
    
    # Use custom query if provided, otherwise default
    query = custom_query if custom_query else "Is it compliant to buy $50,000 of TSLA?"
    ticker = extract_ticker_from_query(query, "regulation")
    
    print("\n" + "="*70)
    print("⚖️ COMPLIANCE QUERY TEST")
    print("="*70 + "\n")
    
    logger = Logger("compliance_query")
    logger.log(f"📝 Query: {query}")
    logger.log(f"📊 Ticker detected: {ticker}")
    
    # Extract amount from query if present
    amount_match = re.search(r'\$?(\d{1,3}(?:,\d{3})*|\d+)\s*(k|thousand)?', query.lower())
    amount = 50000  # Default
    if amount_match:
        try:
            amount = int(amount_match.group(1).replace(',', ''))
            if amount_match.group(2) in ['k', 'thousand']:
                amount = amount * 1000
        except:
            pass
    
    initial_state: AgentState = {
        "messages": [],
        "query": query,
        "query_type": "regulation",
        "market_data": {"current_ticker": ticker},
        "news_data": {"current_ticker": ticker},
        "risk_data": {"current_ticker": ticker},
        "compliance_data": {"current_ticker": ticker},
        "economic_data": {"current_ticker": ticker},
        "fundamental_data": {"current_ticker": ticker},
        "portfolio": {"risk_tolerance": "moderate", "current_ticker": ticker, "compliance_amount": amount},
        "tickers": [ticker],
        "investment_thesis": "",
        "conflicts": [],
        "audit_trail": [],
        "current_agent": "",
        "agents_completed": [],
        "tool_calls": [],
        "final_output": "",
        "errors": [],
        "warnings": []
    }
    
    config = {
        "configurable": {
            "thread_id": f"compliance_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recursion_limit": 20
        }
    }
    
    stream_handler = StreamHandler(logger)
    final_answer = ""
    result = {"final_output": "No result"}
    
    try:
        for step in graph.stream(initial_state, config=config):
            stream_handler.handle_stream([step])
        
        result = graph.invoke(initial_state, config=config)
        
        # Format compliance answer
        if result.get("compliance_data"):
            comp = result["compliance_data"].get("check_finra_compliance", {})
            if comp:
                status = "✅ COMPLIANT" if comp.get('compliant') else "❌ NON-COMPLIANT"
                final_answer = f"⚖️ For your query: '{query}'\n\n"
                final_answer += f"Status: {status}\n\n"
                
                if comp.get('rules_checked'):
                    final_answer += f"Rules checked: {', '.join(comp['rules_checked'])}\n"
                
                if comp.get('warnings'):
                    final_answer += f"\n⚠️ Warnings:\n"
                    for warning in comp['warnings']:
                        final_answer += f"  • {warning}\n"
            else:
                final_answer = f"Compliance check completed for {ticker} but no detailed results available."
        else:
            final_answer = f"No compliance data available for {ticker}."
        
        logger.log_final_answer(final_answer)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        final_answer = f"Error: {e}"
        logger.log_final_answer(final_answer)
    
    logger.summary()
    return result


def test_economic_query(custom_query: str = None):
    """Test economic data query with custom query"""
    apply_json_patch()
    
    # Use custom query if provided, otherwise default
    query = custom_query if custom_query else "What is the current GDP growth rate?"
    
    print("\n" + "="*70)
    print("📈 ECONOMIC QUERY TEST")
    print("="*70 + "\n")
    
    logger = Logger("economic_query")
    logger.log(f"📝 Query: {query}")
    
    initial_state: AgentState = {
        "messages": [],
        "query": query,
        "query_type": "economic",
        "market_data": {},
        "news_data": {},
        "risk_data": {},
        "compliance_data": {},
        "economic_data": {},
        "fundamental_data": {},
        "portfolio": {},
        "tickers": [],
        "investment_thesis": "",
        "conflicts": [],
        "audit_trail": [],
        "current_agent": "",
        "agents_completed": [],
        "tool_calls": [],
        "final_output": "",
        "errors": [],
        "warnings": []
    }
    
    config = {
        "configurable": {
            "thread_id": f"economic_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "recursion_limit": 20
        }
    }
    
    stream_handler = StreamHandler(logger)
    final_answer = ""
    result = {"final_output": "No result"}
    
    try:
        for step in graph.stream(initial_state, config=config):
            stream_handler.handle_stream([step])
        
        result = graph.invoke(initial_state, config=config)
        
        # Format economic answer
        if result.get("economic_data"):
            final_answer = f"📊 For your query: '{query}'\n\n"
            final_answer += "Economic Indicators:\n"
            for key, value in result["economic_data"].items():
                if "get_economic_indicator" in key or "get_fred_data" in key:
                    if isinstance(value, dict):
                        if "indicator_name" in value:
                            name = value.get('indicator_name', key)
                            val = value.get('latest_value', 'N/A')
                            final_answer += f"• {name}: {val}\n"
                        elif "data" in value:
                            final_answer += f"• {key}: Data retrieved\n"
        else:
            final_answer = "No economic data available."
        
        logger.log_final_answer(final_answer)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        final_answer = f"Error: {e}"
        logger.log_final_answer(final_answer)
    
    logger.summary()
    return result


def generate_summary_from_data(result: dict, query: str) -> str:
    """Generate a human-readable summary from the collected data"""
    
    summary = f"Based on your query: '{query}'\n\n"
    summary += "Here's what we found:\n\n"
    
    # Market Data
    if result.get("market_data"):
        quotes = result["market_data"].get("quotes", {})
        if quotes:
            price = quotes.get('price', 'N/A')
            change = quotes.get('change_percent', 0)
            summary += f"📈 Market: Current price is ${price} ({change:+.2f}% today)\n"
        
        technical = result["market_data"].get("technical", {})
        if technical:
            indicators = technical.get("compute_technical_indicators", {}).get("indicators", {})
            if indicators:
                rsi = indicators.get('RSI', 'N/A')
                summary += f"   Technical indicators show RSI at {rsi}\n"
    
    # News Data
    if result.get("news_data"):
        sentiment = result["news_data"].get("analyze_news_sentiment", {})
        if sentiment:
            score = sentiment.get('sentiment_score', 0)
            sentiment_text = sentiment.get('sentiment', 'neutral')
            summary += f"📰 News: Market sentiment is {sentiment_text} ({score:+.2f})\n"
    
    # Risk Data
    if result.get("risk_data"):
        var = result["risk_data"].get("calculate_value_at_risk", {})
        if var:
            var_value = var.get('var_percent', 'N/A')
            summary += f"⚠️ Risk: Value at Risk (95% confidence) is {var_value}%\n"
        
        stress = result["risk_data"].get("stress_test_portfolio", {})
        if stress:
            impact = stress.get('portfolio_impact', 'N/A')
            summary += f"   In a market crash scenario, potential impact: {impact}%\n"
    
    # Compliance Data
    if result.get("compliance_data"):
        comp = result["compliance_data"].get("check_finra_compliance", {})
        if comp:
            status = "✅ PASSED" if comp.get('compliant') else "❌ FAILED"
            summary += f"⚖️ Compliance: {status}\n"
    
    # Economic Data
    if result.get("economic_data"):
        summary += f"📊 Economic indicators retrieved\n"
    
    # Recommendation
    summary += "\n📋 RECOMMENDATION:\n"
    
    # Try to determine recommendation from data
    if result.get("market_data") and result.get("risk_data"):
        price = result["market_data"].get("quotes", {}).get('price', 0)
        var = result["risk_data"].get("calculate_value_at_risk", {}).get('var_percent', 100)
        
        if var < 5:
            summary += f"✅ BUY: Risk level is acceptable (VaR {var}%). Consider investing with appropriate position sizing.\n"
        elif var < 10:
            summary += f"⚠️ CAUTIOUS BUY: Risk level is moderate (VaR {var}%). Consider a smaller position.\n"
        else:
            summary += f"❌ HOLD: Risk level is high (VaR {var}%). Consider waiting for better entry point.\n"
    else:
        summary += "Insufficient data for a complete recommendation. Please try again.\n"
    
    return summary


# ============================================
# MAIN MENU
# ============================================

if __name__ == "__main__":
    print("\n" + "="*70)
    print("🚀 FINAGENTIX AGENT TEST SUITE")
    print("="*70)
    print("\n📁 Log files will be saved to: logs/")
    print("\nChoose test to run:")
    print("1. 📋 Investment Decision (Full 6-Agent Collaboration)")
    print("2. 📊 Market Query")
    print("3. ⚠️ Risk Query")
    print("4. ⚖️ Compliance Query")
    print("5. 📈 Economic Query")
    print("6. 🔄 Run All Tests")
    
    choice = input("\nEnter choice (1-6): ").strip()
    
    if choice in ["1", "2", "3", "4", "5"]:
        # Ask for custom query
        print("\n📝 Enter your query (or press Enter to use default):")
        custom_query = input("> ").strip()
        if not custom_query:
            custom_query = None
    
    if choice == "1":
        test_investment_decision(custom_query)
    elif choice == "2":
        test_market_query(custom_query)
    elif choice == "3":
        test_risk_query(custom_query)
    elif choice == "4":
        test_compliance_query(custom_query)
    elif choice == "5":
        test_economic_query(custom_query)
    elif choice == "6":
        print("\n🔄 Running all tests with default queries...\n")
        test_market_query()
        test_risk_query()
        test_compliance_query()
        test_economic_query()
        test_investment_decision()
    else:
        print("❌ Invalid choice")