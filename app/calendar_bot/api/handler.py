from typing import Optional
from app.calendar_bot.service.calendar_service import CalendarService
from app.calendar_bot.service.chat_service import ChatService
from app.calendar_bot.entities.entity import Calendar, ChatMessage, Conversation, CalendarProvider

from pkg.log.logger import Logger
from app.calendar_bot.api.dto import CalendarDTO, ConversationDTO, ChatMessageDTO

class CalendarBotHandler:
    def __init__(self, calendar_service: CalendarService, chat_service: ChatService, logger: Logger):
        self.calendar_service = calendar_service
        self.chat_service = chat_service
        self.logger = logger

    async def create_calendar(self, user_id: str, provider: CalendarProvider, calendar_data: dict) -> CalendarDTO:
        """Create a new calendar for the user."""
        try:
            calendar = await self.calendar_service.create_calendar(user_id, provider, calendar_data)
            return CalendarDTO(
                id=calendar.id,
                provider=calendar.provider.name,
                name=calendar.name,
            )
        except Exception as e:
            self.logger.error(f"Error creating calendar: {str(e)}")
            raise

    async def get_calendar(self, user_id: str, calendar_id: str) -> Optional[CalendarDTO]:
        """Get a specific calendar by ID."""
        try:
            calendar = await self.calendar_service.get_calendar(user_id, calendar_id)
            if not calendar:
                return None
            return CalendarDTO(
                id=calendar.id,

                provider=calendar.provider.name,
                name=calendar.name,
            )
        except Exception as e:
            self.logger.error(f"Error getting calendar: {str(e)}")
            raise

    async def create_conversation(self, user_id: str) -> ConversationDTO:
        """Create a new conversation for the user."""
        try:
            conversation = await self.chat_service.create_conversation(user_id)
            return ConversationDTO(
                id=conversation.id,
                user_id=conversation.user_id,
                title=conversation.title,
                messages=[],
            )
        except Exception as e:
            self.logger.error(f"Error creating conversation: {str(e)}")
            raise

    async def get_conversation(self, user_id: str, conversation_id: str) -> Optional[ConversationDTO]:
        """Get a specific conversation by ID."""
        try:
            conversation = await self.chat_service.get_conversation(user_id, conversation_id)
            if not conversation:
                return None
            return ConversationDTO(
                id=conversation.id,
                user_id=conversation.user_id,
                title=conversation.title,
                messages=[
                    ChatMessageDTO(
                        id=msg.id,
                        conversation_id=msg.conversation_id,
                        content=msg.content,
                        role=msg.role,
                    ) for msg in conversation.messages
                ],
            )
        except Exception as e:
            self.logger.error(f"Error getting conversation: {str(e)}")
            raise

    async def process_message(self, user_id: str, conversation_id: str, message: str) -> ChatMessageDTO:
        """Process a chat message and return a response."""
        try:
            response = await self.chat_service.process_message(user_id, conversation_id, message)
            return ChatMessageDTO(
                id=response.id,
                conversation_id=response.conversation_id,
                content=response.content,
                role=response.role,
            )
        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            raise