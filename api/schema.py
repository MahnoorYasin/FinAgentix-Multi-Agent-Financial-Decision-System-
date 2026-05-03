"""
Pydantic schemas for FinAgentix API
"""

from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4


class ChatRequest(BaseModel):
    """Request model for /chat and /stream endpoints"""
    message: str = Field(..., description="User's query/message", min_length=1)
    thread_id: str = Field(
        default_factory=lambda: str(uuid4()),
        description="Conversation thread ID for persistence"
    )


class ChatResponse(BaseModel):
    """Response model for /chat endpoint"""
    answer: str = Field(..., description="Agent's final response")
    status: str = Field(default="success", description="Status of the request")
    thread_id: str = Field(..., description="Conversation thread ID")
    tools_used: List[str] = Field(default_factory=list, description="Tools called by the agent")


class StreamEvent(BaseModel):
    """Event model for /stream SSE responses"""
    event: str = Field(..., description="Event type (node name or 'complete')")
    status: str = Field(default="processing", description="Current status")
    data: Optional[str] = Field(default=None, description="Event data")
    answer: Optional[str] = Field(default=None, description="Final answer (only on 'complete')")


class ErrorResponse(BaseModel):
    """Error response model"""
    status: str = Field(default="error")
    message: str = Field(..., description="Error description")
    thread_id: Optional[str] = Field(default=None)