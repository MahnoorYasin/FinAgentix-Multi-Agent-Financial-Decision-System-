"""
FinAgentix FastAPI Application - Lab 8
Exposes LangGraph agent via REST API with streaming support.
AVOIDS ChromaDB-dependent tools to prevent ONNX crashes.
"""

import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))

import json
import asyncio
from typing import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse

# Import our schemas
from api.schema import ChatRequest, ChatResponse, StreamEvent, ErrorResponse

# ============================================
# LIFESPAN: Initialize and cleanup resources
# ============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize checkpointer on startup, cleanup on shutdown"""
    global graph, checkpointer
    
    print("="*50)
    print("Starting FinAgentix API Server...")
    
    try:
        # Import graph and state
        from src.graph.graph import graph as agent_graph
        graph = agent_graph
        print("Agent graph loaded successfully")
    except Exception as e:
        print(f"ERROR loading graph: {e}")
        graph = None
    
    print("="*50)
    
    yield  # Server runs here
    
    print("Shutting down FinAgentix API Server...")
    # Cleanup if needed


# Initialize FastAPI
app = FastAPI(
    title="FinAgentix API",
    description="Financial AI Agent API - Lab 8",
    version="1.0.0",
    lifespan=lifespan
)

# Global graph reference
graph = None


# ============================================
# HELPER: Extract ticker from query
# ============================================

def extract_ticker(query: str) -> str:
    """Extract stock ticker from query"""
    tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'META', 'NFLX']
    for t in tickers:
        if t in query.upper():
            return t
    
    mapping = {
        'apple': 'AAPL', 'microsoft': 'MSFT', 'nvidia': 'NVDA',
        'tesla': 'TSLA', 'amazon': 'AMZN', 'google': 'GOOGL'
    }
    for name, ticker in mapping.items():
        if name in query.lower():
            return ticker
    
    return "NVDA"


# ============================================
# ENDPOINT 1: POST /chat
# ============================================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Standard chat endpoint.
    Sends message to agent and returns complete response.
    """
    if graph is None:
        raise HTTPException(status_code=500, detail="Agent graph not initialized")
    
    try:
        from src.graph.state import create_initial_state
        
        ticker = extract_ticker(request.message)
        print(f"[/chat] Query: {request.message[:50]}... | Ticker: {ticker} | Thread: {request.thread_id}")
        
        # Create initial state
        initial_state = create_initial_state(
            query=request.message,
            query_type="price/trend"
        )
        initial_state["ticker"] = ticker
        initial_state["tickers"] = [ticker]
        initial_state["portfolio"] = {"risk_tolerance": "moderate", "cash": 10000}
        
        # Graph config with thread_id for persistence
        config = {
            "configurable": {"thread_id": request.thread_id},
            "recursion_limit": 25
        }
        
        # Run the agent
        result = graph.invoke(initial_state, config=config)
        
        final_output = result.get("final_output", "")
        if isinstance(final_output, dict):
            final_output = json.dumps(final_output)
        
        audit_trail = result.get("audit_trail", [])
        tools_used = []
        for entry in audit_trail:
            if isinstance(entry, dict):
                tool = entry.get('tool') or entry.get('name')
                if tool:
                    tools_used.append(str(tool))
        
        return ChatResponse(
            answer=str(final_output)[:2000],
            status="success",
            thread_id=request.thread_id,
            tools_used=tools_used
        )
    
    except Exception as e:
        print(f"[/chat] Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# ENDPOINT 2: POST /stream
# ============================================

@app.post("/stream")
async def stream(request: ChatRequest):
    """
    Streaming endpoint using Server-Sent Events.
    Uses synchronous invoke with manual event yielding.
    """
    if graph is None:
        raise HTTPException(status_code=500, detail="Agent graph not initialized")
    
    async def event_generator() -> AsyncGenerator:
        """Generate SSE events as agent runs"""
        try:
            from src.graph.state import create_initial_state
            import time
            
            ticker = extract_ticker(request.message)
            print(f"[/stream] Query: {request.message[:50]}... | Ticker: {ticker} | Thread: {request.thread_id}")
            
            # Yield start event
            yield {
                "event": "start",
                "data": json.dumps({
                    "status": "Starting agent execution...",
                    "ticker": ticker,
                    "thread_id": request.thread_id
                })
            }
            
            # Create initial state
            initial_state = create_initial_state(
                query=request.message,
                query_type="price/trend"
            )
            initial_state["ticker"] = ticker
            initial_state["tickers"] = [ticker]
            initial_state["portfolio"] = {"risk_tolerance": "moderate", "cash": 10000}
            
            # Graph config
            config = {
                "configurable": {"thread_id": request.thread_id},
                "recursion_limit": 25
            }
            
            # Yield processing event
            yield {
                "event": "processing",
                "data": json.dumps({
                    "status": "Agent is processing your request...",
                    "ticker": ticker
                })
            }
            
            # Use synchronous invoke (works with SqliteSaver)
            result = graph.invoke(initial_state, config=config)
            
            final_output = result.get("final_output", "")
            if isinstance(final_output, dict):
                final_output = json.dumps(final_output)
            
            # Extract tools used
            audit_trail = result.get("audit_trail", [])
            tools_used = []
            for entry in audit_trail:
                if isinstance(entry, dict):
                    tool = entry.get('tool') or entry.get('name')
                    if tool:
                        tools_used.append(str(tool))
            
            # Yield complete event
            yield {
                "event": "complete",
                "data": json.dumps({
                    "answer": str(final_output)[:2000],
                    "status": "success",
                    "thread_id": request.thread_id,
                    "tools_used": tools_used
                })
            }
            
        except Exception as e:
            print(f"[/stream] Error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({
                    "status": "error",
                    "message": str(e),
                    "thread_id": request.thread_id
                })
            }
    
    return EventSourceResponse(event_generator())
# ============================================
# HEALTH CHECK ENDPOINT
# ============================================

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "agent": "FinAgentix",
        "graph_loaded": graph is not None,
        "model": "llama-3.3-70b-versatile"
    }


# ============================================
# ROOT ENDPOINT
# ============================================

@app.get("/")
async def root():
    """Root endpoint with API info"""
    return {
        "service": "FinAgentix API",
        "version": "1.0.0",
        "endpoints": {
            "chat": "POST /chat",
            "stream": "POST /stream",
            "health": "GET /health"
        },
        "docs": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)  # 0.0.0.0 for Docker