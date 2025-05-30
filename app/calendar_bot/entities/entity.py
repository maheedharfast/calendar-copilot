from enum import Enum
from pydantic import BaseModel, Field
from datetime import datetime, date
from typing import Optional, Dict, Any

class CalendarProvider(Enum):
    GOOGLE = "GOOGLE"
    MICROSOFT = "MICROSOFT"

class Calendar(BaseModel):
    """Calendar entity schema"""
    id: str = Field(..., description="Unique identifier for the calendar")
    user_id: str = Field(..., description="ID of the user who owns the calendar")
    provider: CalendarProvider = Field(..., description="Calendar provider (e.g., GOOGLE, OUTLOOK)")
    credentials: dict = Field(..., description="Calendar credentials")

class MessageRole(str, Enum):
    """Message role enumeration"""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ChatMessage(BaseModel):
    """Chat message schema"""
    id: str = Field(..., description="Unique identifier for the message")
    conversation_id: str = Field(..., description="ID of the conversation this message belongs to")
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Message content")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Message creation time")
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=lambda: {}, description="Additional meta_data")

class Conversation(BaseModel):
    """Conversation schema"""
    id: str = Field(..., description="Unique conversation identifier")
    user_id: str = Field(..., description="User ID associated with the conversation")
    title: Optional[str] = Field(None, description="Title of the conversation")
    messages: list[ChatMessage] = Field(default_factory=list, description="List of messages in the conversation")
