from sqlalchemy import Column, String, JSON, ForeignKey
from sqlalchemy.orm import relationship
from pkg.db_util.declarative_base import Base

class ConversationModel(Base):
    """SQLAlchemy model for Conversation"""
    __tablename__ = "conversations"

    id = Column(String, primary_key=True)
    user_id = Column(String, nullable=False)
    title = Column(String, nullable=False)
    
    # Relationship to messages
    messages = relationship("MessageModel", back_populates="conversation")

class MessageModel(Base):
    """SQLAlchemy model for ChatMessage"""
    __tablename__ = "messages"

    id = Column(String, primary_key=True)
    conversation_id = Column(String, ForeignKey("conversations.id"), nullable=False)
    role = Column(String, nullable=False)  # Use appropriate type for MessageRole
    content = Column(String, nullable=False)
    created_at = Column(String, nullable=False)  # Use appropriate type for timestamp
    meta_data = Column(JSON, nullable=True)  # Additional meta_data if needed
    
    # Relationship to conversation
    conversation = relationship("ConversationModel", back_populates="messages")