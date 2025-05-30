from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class CalendarDTO(BaseModel):
    """DTO for calendar data"""
    id: str = Field(..., description="Unique identifier for the calendar")
    provider: str = Field(..., description="Calendar provider (e.g., GOOGLE, OUTLOOK)")
    name: str = Field(..., description="Name of the calendar")

class CalendarCreateDTO(BaseModel):
    provider: str = Field(..., description="Calendar provider (e.g., GOOGLE, OUTLOOK)")
    name: str = Field(..., description="Name of the calendar")

class ChatMessageDTO(BaseModel):
    """DTO for chat messages"""
    id: str = Field(..., description="Unique identifier for the message")
    conversation_id: str = Field(..., description="ID of the conversation this message belongs to")
    content: str = Field(..., description="Content of the message")
    role: str = Field(..., description="Role of the message sender (user/assistant)")

class ConversationDTO(BaseModel):
    """DTO for conversations"""
    id: str = Field(..., description="Unique identifier for the conversation")
    user_id: str = Field(..., description="ID of the user who owns the conversation")
    title: Optional[str] = Field(None, description="Title of the conversation")
    messages: List[ChatMessageDTO] = Field(default_factory=list, description="List of messages in the conversation")

