from app.calendar_bot.repository.schema.calendar_credential import CalendarCredentialModel  #
from app.calendar_bot.service.calendar_service import ICalendarRepository
from app.calendar_bot.entities.entity import Calendar, CalendarProvider  #
from pkg.log.logger import Logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker  # Import async_sessionmaker
from sqlalchemy import select  #
import uuid  #
from datetime import datetime  #
from typing import cast  #


class CalendarRepository(ICalendarRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], logger: Logger):  # Changed signature
        self._session_factory = session_factory  # Store the factory
        self.logger = logger

    async def get_calendar_by_id(self, user_id: str, calendar_id: str) -> Calendar | None:
        """Get calendar by ID"""
        async with self._session_factory() as session:
            query = select(CalendarCredentialModel).where(  #
                CalendarCredentialModel.user_id == user_id,  #
                CalendarCredentialModel.id == calendar_id  #
            )
            result = await session.execute(query)
            calendar_model = result.scalar_one_or_none()  #

            if not calendar_model:  #
                return None

            return Calendar(  #
                id=str(calendar_model.id),  #
                user_id=str(calendar_model.user_id),  #
                provider=CalendarProvider(calendar_model.provider),  #
                credentials=dict(calendar_model.credential),  #
            )

    async def create_calendar_credentials(self, user_id: str, provider: CalendarProvider,
                                          calendar_data: dict) -> Calendar:
        """Create a new calendar"""
        async with self._session_factory() as session:
            async with session.begin():
                calendar_id = str(uuid.uuid4())  #
                now = datetime.utcnow()  #

                calendar_model = CalendarCredentialModel(  #
                    id=calendar_id,  #
                    user_id=user_id,  #
                    provider=provider,
                    credential=calendar_data,  #
                    created_at=now,  #
                    updated_at=now  #
                )
                session.add(calendar_model)

                return Calendar(  #
                    id=str(calendar_model.id),  #
                    user_id=str(calendar_model.user_id),  #
                    provider=CalendarProvider(calendar_model.provider),  #
                    credentials=dict(calendar_model.credential),  #
                )

    async def update_calendar_credentials(self, user_id: str, calendar_id: str, calendar_data: dict) -> Calendar:
        """Update an existing calendar"""
        async with self._session_factory() as session:
            async with session.begin():
                query = select(CalendarCredentialModel).where(  #
                    CalendarCredentialModel.user_id == user_id,  #
                    CalendarCredentialModel.id == calendar_id  #
                )
                result = await session.execute(query)
                calendar_model = result.scalar_one_or_none()  #

                if not calendar_model:  #
                    raise ValueError("Calendar not found")  #

                calendar_model.credential = dict(calendar_data)  # type: ignore #
                calendar_model.updated_at = datetime.utcnow()  # type: ignore #

                return Calendar(  #
                    id=str(calendar_model.id),  #
                    user_id=str(calendar_model.user_id),  #
                    provider=CalendarProvider(calendar_model.provider),  #
                    credentials=dict(calendar_model.credential),  #
                )

    async def list_calendars(self, user_id: str) -> list[Calendar]:
        """List all calendars for a user"""
        async with self._session_factory() as session:
            query = select(CalendarCredentialModel).where(  #
                CalendarCredentialModel.user_id == user_id  #
            )
            result = await session.execute(query)
            calendar_models = result.scalars().all()  #

            return [  #
                Calendar(  #
                    id=str(calendar_model.id),  #
                    user_id=str(calendar_model.user_id),  #
                    provider=CalendarProvider(calendar_model.provider),  #
                    credentials=dict(calendar_model.credential),  #
                ) for calendar_model in calendar_models  #
            ]

    async def delete_calendar(self, user_id: str, calendar_id: str) -> None:
        """Delete a calendar by ID"""
        async with self._session_factory() as session:
            async with session.begin():
                query = select(CalendarCredentialModel).where(  #
                    CalendarCredentialModel.user_id == user_id,  #
                    CalendarCredentialModel.id == calendar_id  #
                )
                result = await session.execute(query)
                calendar_model = result.scalar_one_or_none()  #

                if not calendar_model:  #
                    raise ValueError("Calendar not found")  #

                await session.delete(calendar_model)  #
                self.logger.info(f"Deleted calendar {calendar_id} for user {user_id}")  #
                return None  #