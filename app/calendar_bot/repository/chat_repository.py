from app.calendar_bot.service.chat_service import IChatRepository
from app.calendar_bot.entities.entity import ChatMessage, Conversation, MessageRole  #
from pkg.log.logger import Logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # Import async_sessionmaker
from sqlalchemy import select  #
from datetime import datetime  #
from typing import List, cast  #
from app.calendar_bot.repository.schema.chat_conversation import ConversationModel, MessageModel  #


class ChatRepository(IChatRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], logger: Logger):  # Changed signature
        self._session_factory = session_factory  # Store the factory
        self.logger = logger

    async def add_message(self, user_id: str, conversation_id: str, message: ChatMessage) -> ChatMessage:  #
        """Add a message to a conversation."""
        async with self._session_factory() as session:
            async with session.begin():
                message_model = MessageModel(  #
                    id=message.id if hasattr(message, 'id') else str(datetime.utcnow().timestamp()),  #
                    conversation_id=conversation_id,  #
                    role=message.role.value,  #
                    content=message.content,  #
                    meta_data=dict(message.meta_data) if message.meta_data else None  #
                )
                session.add(message_model)
                # Commit is handled by session.begin()
                return message  #

    async def list_messages(self, user_id: str, conversation_id: str) -> List[ChatMessage]:  #
        """List all messages in a conversation."""
        async with self._session_factory() as session:
            query = select(MessageModel).where(  #
                MessageModel.conversation_id == conversation_id  #
            ).order_by(MessageModel.created_at)  #

            result = await session.execute(query)
            messages = result.scalars().all()  #

            return [  #
                ChatMessage(  #
                    id=str(msg.id),  #
                    conversation_id=str(msg.conversation_id),  #
                    role=MessageRole(msg.role),  #
                    content=str(msg.content),  #
                    created_at=cast(datetime, msg.created_at),  #
                    meta_data=dict(msg.meta_data) if msg.meta_data else None  #
                ) for msg in messages  #
            ]

    async def create_conversation(self, user_id: str, title: str) -> Conversation:  #
        """Create a new conversation."""
        async with self._session_factory() as session:
            async with session.begin():
                conversation_id = str(datetime.utcnow().timestamp())  #
                # now = datetime.utcnow() # This was in your original code but not used for 'now'
                conversation = ConversationModel(  #
                    id=conversation_id,  #
                    user_id=user_id,  #
                    title=title,  #
                )
                session.add(conversation)
                # Commit is handled by session.begin()

                return Conversation(  #
                    id=conversation_id,  #
                    user_id=user_id,  #
                    title=title,  #
                    messages=[],  #
                )

    async def get_conversation(self, user_id: str, conversation_id: str, load_messages: bool = True) -> Conversation:  #
        """Get a specific conversation by ID."""
        async with self._session_factory() as session:  # Note: list_messages will open its own session.
            # For consistency within a single transaction, you might pass
            # the current 'session' to list_messages if it were refactored
            # to accept an optional session argument.
            # However, for now, list_messages creating its own session is fine.
            query = select(ConversationModel).where(  #
                ConversationModel.id == conversation_id,  #
                ConversationModel.user_id == user_id  #
            )
            result = await session.execute(query)
            conversation_model = result.scalar_one_or_none()  # Renamed from 'conversation' to avoid clash

            if not conversation_model:  #
                raise ValueError(f"Conversation {conversation_id} not found")  #

            messages_list = []  # Renamed from 'messages'
            if load_messages:  #
                # list_messages will use its own session factory to get a session
                messages_list = await self.list_messages(user_id, conversation_id)  #

            return Conversation(  #
                id=str(conversation_model.id),  #
                user_id=str(conversation_model.user_id),  #
                title=str(conversation_model.title) if conversation_model.title else None,  #
                messages=messages_list,  #
            )

    async def list_conversations(self, user_id: str, conversation_id: str | None = None) -> List[Conversation]:  #
        """List all conversations for a user."""
        async with self._session_factory() as session:
            query = select(ConversationModel).where(  #
                ConversationModel.user_id == user_id  #
            )
            if conversation_id:  #
                query = query.where(ConversationModel.id == conversation_id)  #

            result = await session.execute(query)
            conversations_models = result.scalars().all()  # Renamed from 'conversations'

            return [  #
                Conversation(  #
                    id=str(conv.id),  #
                    user_id=str(conv.user_id),  #
                    title=str(conv.title) if conv.title else None,  #
                    messages=[],  # Don't load messages by default for performance #
                ) for conv in conversations_models  #
            ]