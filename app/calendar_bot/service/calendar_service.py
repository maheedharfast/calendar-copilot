from abc import abstractmethod, ABC
from app.calendar_bot.entities.entity import CalendarProvider, Calendar

class ICalendarRepository(ABC):
    @abstractmethod
    async def get_calendar_by_id(self, user_id: str, calendar_id: str) -> Calendar | None:
        """Get calendar by ID"""
        pass

    @abstractmethod
    async def create_calendar_credentials(self, user_id: str, provider: CalendarProvider, calendar_data: dict) -> Calendar:
        """Create a new calendar"""
        pass

    @abstractmethod
    async def update_calendar_credentials(self, user_id: str, calendar_id: str, calendar_data: dict) -> Calendar:
        """Update an existing calendar"""
        pass

    @abstractmethod
    async def list_calendars(self, user_id: str) -> list[Calendar]:
        """List all calendars for a user"""
        pass

    @abstractmethod
    async def delete_calendar(self, user_id: str, calendar_id: str) -> None:
        """Delete a calendar by ID"""
        pass

class CalendarService:
    def __init__(self, calendar_repository: ICalendarRepository):
        self.calendar_repository = calendar_repository

    async def get_calendar(self, user_id: str, calendar_id: str) -> Calendar | None:
        """Get a calendar by ID"""
        return await self.calendar_repository.get_calendar_by_id(user_id, calendar_id)

    async def create_calendar(self, user_id: str, provider: CalendarProvider, calendar_data: dict) -> Calendar:
        """Create a new calendar"""
        return await self.calendar_repository.create_calendar_credentials(user_id, provider, calendar_data)

    async def update_calendar(self, user_id: str, calendar_id: str, calendar_data: dict) -> Calendar:
        """Update an existing calendar"""
        return await self.calendar_repository.update_calendar_credentials(user_id, calendar_id, calendar_data)

    async def list_calendars(self, user_id: str) -> list[Calendar]:
        """List all calendars for a user"""
        return await self.calendar_repository.list_calendars(user_id)

    async def delete_calendar(self, user_id: str, calendar_id: str) -> None:
        """Delete a calendar by ID"""
        await self.calendar_repository.delete_calendar(user_id, calendar_id)

