from typing import Dict, Any, Optional,Annotated
from fastapi import  HTTPException, Depends

from fastapi import APIRouter

from app.calendar_bot.api.dependencies import CalendarBotHandlerDep
from app.middleware import get_token_detail
from app.calendar_bot.api.dto import CalendarCreateDTO, ChatMessageDTO, ConversationDTO, CalendarDTO, MessageDTO

calendar_bot_router = APIRouter(prefix="/chat", tags=["calendar_bot"])

@calendar_bot_router.post("/conversation")
async def create_conversation(  token_detail: Annotated[str, Depends(get_token_detail)],
                                handler: CalendarBotHandlerDep) -> ConversationDTO:
    """Create a new conversation for the calendar bot"""
    return await handler.create_conversation(token_detail.user_id)

@calendar_bot_router.post("/conversation/{conversation_id}/message")
async def add_message_to_conversation(
    conversation_id: str,
    message: MessageDTO,
    token_detail: Annotated[str, Depends(get_token_detail)],
    handler: CalendarBotHandlerDep
) -> ChatMessageDTO:
    """Add a message to a conversation"""

    return await handler.process_message(
        user_id=token_detail.user_id,
        conversation_id=conversation_id,
        message=message
    )

@calendar_bot_router.get("/conversations/{conversation_id}")
async def get_conversation(conversation_id: str, token_detail: Annotated[str, Depends(get_token_detail)],
    handler: CalendarBotHandlerDep) -> ConversationDTO:
    """Get a conversation by ID"""
    conversation = await handler.get_conversation(
        user_id=token_detail.user_id,
        conversation_id=conversation_id
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return conversation

@calendar_bot_router.get("/conversations")
async def list_conversations(
    token_detail: Annotated[str, Depends(get_token_detail)],
    handler: CalendarBotHandlerDep
) -> Dict[str, Any]:
    """List all conversations for the user"""
    return await handler.list_conversations(token_detail.user_id)
@calendar_bot_router.post("/calendar")
async def create_calendar(
    calendar_data: CalendarCreateDTO,
    token_detail: Annotated[str, Depends(get_token_detail)],
    handler: CalendarBotHandlerDep
) -> CalendarDTO:
    """Create a new calendar"""
    return await handler.create_calendar(
        user_id=token_detail.user_id,
        provider=calendar_data.provider,
        calendar_data=calendar_data.credentials
    )
@calendar_bot_router.get("/calendars")
async def list_calendars(
    token_detail: Annotated[str, Depends(get_token_detail)],
    handler: CalendarBotHandlerDep
) -> Dict[str, Any]:
    """List all calendars for the user"""
    return await handler.list_calendars(token_detail.user_id)
@calendar_bot_router.get("/calendar/{calendar_id}")
async def get_calendar(
    calendar_id: str,
    token_detail: Annotated[str, Depends(get_token_detail)],
    handler: CalendarBotHandlerDep
) -> CalendarDTO:
    """Get a specific calendar by ID"""
    calendar = await handler.get_calendar(
        user_id=token_detail.user_id,
        calendar_id=calendar_id
    )

    if not calendar:
        raise HTTPException(status_code=404, detail="Calendar not found")

    return calendar




