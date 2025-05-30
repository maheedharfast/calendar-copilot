from pkg.log.logger import Logger
from abc import ABC, abstractmethod
from app.calendar_bot.entities.entity import ChatMessage, Conversation, MessageRole
from integration_clients.g_suite.client import GSuiteClient
from app.calendar_bot.service.calendar_service import CalendarService
from app.calendar_bot.service.calendar_agent import CalendarAgent, Deps
from integration_clients.g_suite.types import GoogleOAuthToken
from typing import List, Optional
from datetime import datetime


class IChatRepository(ABC):  # Interface definition (already provided)
    @abstractmethod
    async def add_message(self, user_id: str, conversation_id: str, message: ChatMessage) -> ChatMessage:
        pass

    @abstractmethod
    async def list_messages(self, user_id: str, conversation_id: str) -> List[ChatMessage]:
        pass

    @abstractmethod
    async def create_conversation(self, user_id: str, title: str) -> Conversation:
        pass

    @abstractmethod
    async def get_conversation(self, user_id: str, conversation_id: str, load_messages: bool = True) -> Conversation:
        pass

    @abstractmethod
    async def list_conversations(self, user_id: str, conversation_id: Optional[str] = None) -> List[Conversation]:
        pass


class ChatService:
    def __init__(self, calendar_agent: CalendarAgent, logger: Logger,
                 chat_repository: IChatRepository, g_suite_client: GSuiteClient, calendar_service: CalendarService):
        self.logger = logger
        self.chat_repository = chat_repository
        self.g_suite_client = g_suite_client
        self.calendar_service = calendar_service
        self.calendar_agent = calendar_agent

    async def create_conversation(self, user_id: str) -> Conversation:
        try:
            conversation = await self.chat_repository.create_conversation(user_id, "New Conversation")
            return conversation
        except Exception as e:
            self.logger.error(f"Error creating conversation: {e!s}", exc_info=True)
            raise

    async def get_conversation(self, user_id: str, conversation_id: str) -> Conversation:
        try:
            conversation = await self.chat_repository.get_conversation(user_id, conversation_id)
            return conversation
        except Exception as e:
            self.logger.error(f"Error retrieving conversation: {e!s}", exc_info=True)
            raise

    async def list_conversations(self, user_id: str) -> List[Conversation]:
        try:
            conversations = await self.chat_repository.list_conversations(user_id, None)
            return conversations
        except Exception as e:
            self.logger.error(f"Error listing conversations: {e!s}", exc_info=True)
            raise

    async def process_message(self, user_id: str, conversation_id: str, message_content: str) -> ChatMessage:
        """Process a chat message using the LLM client."""
        try:
            # It's crucial that `get_conversation` loads messages if history is to be used.
            conversation = await self.chat_repository.get_conversation(user_id, conversation_id, load_messages=True)
            if not conversation:
                # Consider creating a conversation if one doesn't exist, or raise a more specific error.
                self.logger.error(f"Conversation not found: user_id={user_id}, conversation_id={conversation_id}")
                raise ValueError("Conversation not found")

            # Create user message object
            user_message = ChatMessage(
                # Ensure ID generation is robust, e.g., using uuid
                id=str(datetime.utcnow().timestamp()) + "_" + user_id,  # Example ID
                conversation_id=conversation_id,
                role=MessageRole.USER,
                content=message_content,
                created_at=datetime.utcnow()
            )

            # Add user message to conversation history IN THE REPOSITORY
            await self.chat_repository.add_message(user_id, conversation_id, user_message)


            history_for_agent = []

            messages_for_history = conversation.messages


            for conv_msg in messages_for_history:
                if hasattr(conv_msg, 'role') and hasattr(conv_msg.role, 'value') and hasattr(conv_msg, 'content'):
                    history_for_agent.append({"role": conv_msg.role.value, "content": conv_msg.content})
                else:
                    self.logger.warning(f"Skipping message in history due to unexpected structure: {conv_msg!r}")

            # Retrieve calendar credentials
            # Consider how to handle multiple calendars or if user has no calendar linked
            user_calendars = await self.calendar_service.list_calendars(user_id)
            if not user_calendars or not user_calendars[0].credentials:
                # TODO: Handle this case - perhaps the agent should respond about linking calendar
                # For now, raising an error as per original logic.
                self.logger.error(f"No calendar credentials found for user_id: {user_id}")
                raise ValueError("No calendar credentials found for user. Please link your Google Calendar.")

            calendar_creds = user_calendars[0].credentials

            g_oauth_token = GoogleOAuthToken(
                access_token=calendar_creds.get("access_token"),
                refresh_token=calendar_creds.get("refresh_token"),
                scope=calendar_creds.get("scope"),  # Ensure scope is a string
                token_type="Bearer"  # As per GoogleOAuthToken model
            )
            g_credentials = await self.g_suite_client.make_user_credentials(g_oauth_token)

            deps = Deps(
                g_credentials=g_credentials,
                g_suite_client=self.g_suite_client
            )

            # Get response from CalendarAgent
            response_text = await self.calendar_agent.run(
                prompt_text=message_content,  # Current user input
                history=history_for_agent,  # Formatted previous messages
                deps=deps
            )

            # Create assistant message object
            assistant_message = ChatMessage(
                id=str(datetime.utcnow().timestamp()) + "_assistant",  # Example ID
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content=response_text,
                created_at=datetime.utcnow()
            )
            # Add assistant message to conversation history in the repository
            await self.chat_repository.add_message(user_id, conversation_id, assistant_message)

            # Add assistant message to conversation history
            return assistant_message

        except ValueError as ve:  # Catch specific, known errors
            self.logger.warning(f"Validation error in process_message: {ve!s}")
            # Return a ChatMessage indicating the error to the user
            error_response_message = ChatMessage(
                id=str(datetime.utcnow().timestamp()) + "_error",
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,  # Or a SYSTEM role if appropriate
                content=str(ve),  # Send the validation error message back
                created_at=datetime.utcnow()
            )
            # Optionally, add this error message to the repository if it should be part of history
            # await self.chat_repository.add_message(user_id, conversation_id, error_response_message)
            return error_response_message  # Or raise a custom HTTPException for an API
        except Exception as e:
            self.logger.error(f"Error processing message: {e!s}", exc_info=True)
            # Depending on desired behavior, raise e or return an error message
            # For a chatbot, returning an error message might be better UX
            fallback_error_message = ChatMessage(
                id=str(datetime.utcnow().timestamp()) + "_fallback_error",
                conversation_id=conversation_id,
                role=MessageRole.ASSISTANT,
                content="I'm sorry, I encountered an unexpected problem while processing your request. Please try again later.",
                created_at=datetime.utcnow()
            )
            # await self.chat_repository.add_message(user_id, conversation_id, fallback_error_message)
            return fallback_error_message  # Or re-raise a wrapped exception