import asyncio
import pytz
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build, Resource
from googleapiclient.errors import HttpError

from integration_clients.g_suite.constants import TOKEN_URI
from integration_clients.g_suite.types import GoogleOAuthToken, TimeSlot, Appointment
from integration_clients.g_suite.exceptions import CalendarAPIError
from pkg.log.logger import Logger
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta, date






class GSuiteClient:
    def __init__(self, client_id: str, client_secret: str, logger: Logger):
        self.client_id = client_id
        self.client_secret = client_secret
        self.logger = logger

    async def make_user_credentials(
            self, google_oauth_tokens: GoogleOAuthToken) -> Credentials:
        try:
            credentials = Credentials(
                token=google_oauth_tokens.access_token,
                refresh_token=google_oauth_tokens.refresh_token,
                token_uri=TOKEN_URI,
                client_id=self.client_id,
                client_secret=self.client_secret,
                scopes=google_oauth_tokens.scopes,
            )
            return credentials

        except Exception as e:
            self.logger.error(f"Error making Google credentials: {e!s}")
            raise e


    async def get_user_calender_service(self, credentials: Credentials) -> Resource:
        try:
            service = build("calendar", "v3", credentials=credentials)
            return service
        except Exception as e:
            self.logger.error(f"Error getting user calender service: {str(e)}")
            raise e

    async def get_calendar_list(self, credentials: Credentials) -> List[Dict[str, Any]]:
        """Get list of user's calendars"""
        try:
            service = await self.get_user_calender_service( credentials=credentials)
            calendar_list = service.calendarList().list().execute()
            return calendar_list.get('items', [])
        except HttpError as e:
            self.logger.error(f"Error fetching calendar list: {e}")
            raise CalendarAPIError(f"Failed to fetch calendars: {str(e)}")


    async def fetch_calendar_events(self, credentials: Credentials, calendar_id: str = 'primary', time_min: Optional[datetime] = None, time_max: Optional[datetime] = None,
    max_results: int = 100, availability_check_days: int = 7) -> list[dict]:
        try:
            service = await self.get_user_calender_service(credentials)

            if not time_min:
                time_min = datetime.utcnow()
            if not time_max:
                time_max = time_min + timedelta(days= availability_check_days)
                
            # Convert to RFC3339 format
            time_min_str = time_min.isoformat() + 'Z'
            time_max_str = time_max.isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId=calendar_id,
                timeMin=time_min_str,
                timeMax=time_max_str,
                maxResults=max_results,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            return events_result.get('items', [])
        except HttpError as e:
            self.logger.error(f"Error fetching events: {e}")
            raise CalendarAPIError(f"Failed to fetch events: {str(e)}")

    async def create_event(self, credentials: Credentials, appointment: Appointment, calendar_id: str = 'primary', send_notifications: bool = True) -> Dict[str, Any]:
        """Create a new calendar event"""
        try:
            service = await self.get_user_calender_service(credentials)
            event = {
                'summary': appointment.title,
                'description': appointment.description,
                'start': {
                    'dateTime': appointment.start_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'end': {
                    'dateTime': appointment.end_time.isoformat(),
                    'timeZone': 'UTC',
                },
                'attendees': [{'email': email} for email in appointment.attendees],
                'reminders': {
                    'useDefault': True,
                },
            }
            
            if appointment.location:
                event['location'] = appointment.location
                
            created_event = service.events().insert(
                calendarId=calendar_id,
                body=event,
                sendNotifications=send_notifications
            ).execute()
            
            return created_event
        except HttpError as e:
            self.logger.error(f"Error creating event: {e}")
            raise e
    
    async def update_event(self, credentials: Credentials, event_id: str, updates: Dict[str, Any],
     calendar_id: str = 'primary', send_notifications: bool = True) -> Dict[str, Any]:
        """Update an existing calendar event"""
        try:
            service = await self.get_user_calender_service(credentials)
            # Get existing event    
            event = service.events().get(
                calendarId=calendar_id,
                eventId=event_id
            ).execute()
            
            # Apply updates
            if 'title' in updates:
                event['summary'] = updates['title']
            if 'description' in updates:
                event['description'] = updates['description']
            if 'start_time' in updates:
                event['start']['dateTime'] = updates['start_time'].isoformat()
            if 'end_time' in updates:
                event['end']['dateTime'] = updates['end_time'].isoformat()
            if 'location' in updates:
                event['location'] = updates['location']
            if 'attendees' in updates:
                event['attendees'] = [{'email': email} for email in updates['attendees']]
                
            updated_event = service.events().update(       
                calendarId=calendar_id,
                eventId=event_id,
                body=event,
                sendNotifications=send_notifications
            ).execute()
            
            return updated_event
        except HttpError as e:
            self.logger.error(f"Error updating event: {e}")
            raise CalendarAPIError(f"Failed to update event: {str(e)}")
    
    async def delete_event(self, credentials: Credentials, event_id: str, calendar_id: str = 'primary', send_notifications: bool = True) -> None:
        """Delete a calendar event"""
        try:
            service = await self.get_user_calender_service(credentials)
            service.events().delete(       
                calendarId=calendar_id,
                eventId=event_id,
                sendNotifications=send_notifications
            ).execute()
        except HttpError as e:
            self.logger.error(f"Error deleting event: {e}")
            raise e
    
    async def get_available_slots(self, credentials: Credentials,
                                  start_date: date, end_date: date,
                                  duration_minutes: int = 30,
                                  calendar_id: str = 'primary', timezone: str = 'UTC',
                                  business_hour_start:int =9,
    business_hour_end: int = 18) -> List[TimeSlot]:
        """Get available time slots within date range"""
        tz = pytz.timezone(timezone)
        
        # Convert dates to datetime with timezone
        start_datetime = tz.localize(datetime.combine(start_date, datetime.min.time()))
        end_datetime = tz.localize(datetime.combine(end_date, datetime.max.time()))
        
        # Get existing events
        events = await self.fetch_calendar_events(
            credentials=credentials,
            calendar_id=calendar_id,
            time_min=start_datetime.astimezone(pytz.UTC),
            time_max=end_datetime.astimezone(pytz.UTC)
        )
        
        # Convert events to busy periods
        busy_periods: List[Tuple[datetime, datetime]] = []
        for event in events:
            start = event.get('start', {})
            end = event.get('end', {})
            
            if 'dateTime' in start and 'dateTime' in end:
                event_start = datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00'))
                event_end = datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00'))
                busy_periods.append((event_start, event_end))
        
        # Generate available slots
        available_slots: List[TimeSlot] = []
        current_date = start_date
        
        while current_date <= end_date:
            # Set business hours for the day
            day_start = tz.localize(datetime.combine(
                current_date,
                datetime.min.time().replace(hour=business_hour_start)
            ))
            day_end = tz.localize(datetime.combine(
                current_date,
                datetime.min.time().replace(hour=business_hour_end)
            ))
            
            # Generate slots for the day
            slot_start = day_start
            while slot_start + timedelta(minutes=duration_minutes) <= day_end:
                slot_end = slot_start + timedelta(minutes=duration_minutes)
                
                # Check if slot overlaps with any busy period
                is_available = True
                for busy_start, busy_end in busy_periods:
                    if not (slot_end <= busy_start or slot_start >= busy_end):
                        is_available = False
                        break
                
                if is_available:
                    available_slots.append(TimeSlot(
                        start_time=slot_start.astimezone(pytz.UTC),
                        end_time=slot_end.astimezone(pytz.UTC),
                        available=True
                    ))
                
                slot_start = slot_end
            
            current_date += timedelta(days=1)
        
        return available_slots 




