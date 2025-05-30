from pkg.llm.client import LLMClient, LLMModel, gemini_model_map
from pkg.log.logger import Logger
from pkg.llm.prompts import get_calendar_bot_system_prompt
from abc import ABC, abstractmethod
from app.calendar_bot.entities.entity import ChatMessage, Conversation, MessageRole
from integration_clients.g_suite.client import GSuiteClient
from integration_clients.g_suite.types import GoogleOAuthToken, TimeSlot, AppointmentStatus, Appointment
from typing import Annotated, List, Dict, Any, Optional
from datetime import datetime
from pydantic_ai.models.gemini import GeminiModel

from pydantic_ai import Agent, Tool

class IChatRepository(ABC):
    @abstractmethod
    async def add_message(self, user_id: str, conversation_id: str, message: ChatMessage) -> ChatMessage:
        """Process a chat message and return a response."""
        pass

    @abstractmethod
    async def list_messages(self, user_id: str, conversation_id: str) -> List[ChatMessage]:
        """List all messages in a conversation."""
        pass

    @abstractmethod
    async def create_conversation(self, user_id: str, title: str) -> Conversation:
        """Create a new conversation."""
        pass

    @abstractmethod
    async def get_conversation(self, user_id: str, conversation_id: str, load_messages: bool = True) -> Conversation:
        """Get a specific conversation by ID."""
        pass

    @abstractmethod
    async def list_conversations(self, user_id: str, conversation_id: Optional[str] = None) -> List[Conversation]:
        """List all conversations for a user."""
        pass



class ChatService:
    def __init__(self, llm_client: LLMClient, logger: Logger,
                 chat_repository: IChatRepository, g_suite_client: GSuiteClient):
        self.llm_client = llm_client
        self.logger = logger
        self.chat_repository = chat_repository
        self.g_suite_client = g_suite_client
        model_value = GeminiModel(
            model_name=gemini_model_map[LLMModel.GEMINI_2_5_FLASH.value],
            provider="google-gla",
        )
        system_prompt = get_calendar_bot_system_prompt()
        self.calendar_agent = Agent(
            model=model_value,
            system_prompt=system_prompt,
        )

    async def create_conversation(self, user_id: str) -> Conversation:
        """Create a new conversation for the user."""
        try:
            conversation = await self.chat_repository.create_conversation(user_id, "New Conversation")
            return conversation
        except Exception as e:
            self.logger.error(f"Error creating conversation: {e}")
            raise

    async def get_conversation(self, user_id: str, conversation_id: str) -> Conversation:
        """Get a specific conversation by ID."""
        try:
            conversation = await self.chat_repository.get_conversation(user_id, conversation_id)
            return conversation
        except Exception as e:
            self.logger.error(f"Error retrieving conversation: {e}")
            raise

    async def list_conversations(self, user_id: str) -> List[Conversation]:
        """List all conversations for the user."""
        try:
            conversations = await self.chat_repository.list_conversations(user_id, None)
            return conversations
        except Exception as e:
            self.logger.error(f"Error listing conversations: {e}")
            raise

    async def process_message(self, user_id: str, conversation_id: str, message: str) -> ChatMessage:
        """Process a chat message using the LLM client."""
        try:
            conversation = await self.chat_repository.get_conversation(user_id, conversation_id, True)
            if not conversation:
                raise ValueError("Conversation not found")

            # Create user message
            user_message = ChatMessage(
                id=str(datetime.utcnow().timestamp()),
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=message,
                created_at=datetime.utcnow()
            )

            # Add user message to conversation
            await self.chat_repository.add_message(user_id, conversation_id, user_message)

            # Get response from LLM
            response_text = await self.llm_client.get_response(
                prompt=message,
                model=LLMModel.GEMINI_2_0_PRO_EXP,
                system_msg="You are a helpful calendar assistant."
            )
            
            # Create assistant message
            assistant_message = ChatMessage(
                id=str(datetime.utcnow().timestamp()),
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                created_at=datetime.utcnow()
            )

            # Add assistant message to conversation
            return await self.chat_repository.add_message(user_id, conversation_id, assistant_message)
        except Exception as e:
            self.logger.error(f"Error processing message: {e}")
            raise