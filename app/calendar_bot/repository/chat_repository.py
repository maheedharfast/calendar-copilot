from app.calendar_bot.service.chat_service import IChatRepository
from app.calendar_bot.entities.entity import ChatMessage, Conversation, MessageRole  #
from pkg.log.logger import Logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # Import async_sessionmaker
from sqlalchemy import select  #
from datetime import datetime  #
from typing import List, cast, Optional  #
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
                    created_at=message.created_at.isoformat() if hasattr(message, 'created_at') and message.created_at else datetime.utcnow().isoformat(),  #
                    meta_data=dict(message.meta_data) if message.meta_data else None  #
                )
                session.add(message_model)
                # Commit is handled by session.begin()
                return message  #

    async def _list_messages_with_session(self, session: AsyncSession, conversation_id: str) -> List[ChatMessage]:
        """Internal method to list messages using an existing session."""
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
                created_at=datetime.fromisoformat(msg.created_at) if msg.created_at else datetime.utcnow(),  #
                meta_data=dict(msg.meta_data) if msg.meta_data else None  #
            ) for msg in messages  #
        ]

    async def list_messages(self, user_id: str, conversation_id: str) -> List[ChatMessage]:  #
        """List all messages in a conversation."""
        async with self._session_factory() as session:
            return await self._list_messages_with_session(session, conversation_id)

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
        async with self._session_factory() as session:
            # Fetch conversation data
            query = select(ConversationModel).where(  #
                ConversationModel.id == conversation_id,  #
                ConversationModel.user_id == user_id  #
            )
            result = await session.execute(query)
            conversation_model = result.scalar_one_or_none()  # Renamed from 'conversation' to avoid clash
            
            if not conversation_model:  #
                self.logger.error(f"Conversation {conversation_id} not found for user {user_id}")
                raise ValueError(f"Conversation {conversation_id} not found")  #

            messages_list: List[ChatMessage] = []  # Renamed from 'messages'
            if load_messages:  #
                # Use the same session to fetch messages for consistency
                messages_list = await self._list_messages_with_session(session, conversation_id)  #

            return Conversation(  #
                id=conversation_model.id,  #
                user_id=conversation_model.user_id,  #
                title=conversation_model.title if conversation_model.title else None,  #
                messages=messages_list,  #
            )

    async def list_conversations(self, user_id: str, conversation_id: Optional[str] = None) -> List[Conversation]:  #
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