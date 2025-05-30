from typing import Annotated

from fastapi import Depends, Request

from app.calendar_bot.api.handler import CalendarBotHandler


def get_calendar_handler(request: Request) -> CalendarBotHandler:
    return request.app.state.container.calendar_bot_handler()


# Type aliases for cleaner dependency injection
CalendarBotHandlerDep = Annotated[CalendarBotHandler, Depends(get_calendar_handler)]
