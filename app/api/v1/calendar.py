from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from datetime import datetime, date
import logging
from google.oauth2.credentials import Credentials

from app.schemas.calendar import (
    AvailabilityRequest, AvailabilityResponse,
    CreateAppointmentRequest, UpdateAppointmentRequest,
    AppointmentResponse, TimeSlot
)
from app.models.appointment import Appointment, AppointmentStatus
from app.services.google_calendar import GoogleCalendarService
from app.core.exceptions import CalendarAPIError, NotFoundError, ValidationError
from config.settings import settings


router = APIRouter()


def get_user_credentials(user: Dict[str, Any]) -> Credentials:
    """Get Google credentials for user"""
    # In production, retrieve stored tokens from database
    google_tokens = user.get("google_tokens", {})
    
    if not google_tokens:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Google Calendar not connected. Please authenticate with Google."
        )
    
    credentials = Credentials(
        token=google_tokens.get("access_token"),
        refresh_token=google_tokens.get("refresh_token"),
        token_uri=google_tokens.get("token_uri"),
        client_id=google_tokens.get("client_id"),
        client_secret=google_tokens.get("client_secret"),
        scopes=google_tokens.get("scopes")
    )
    
    return credentials


@router.post("/availability", response_model=AvailabilityResponse)
async def check_availability(
    request: AvailabilityRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AvailabilityResponse:
    """Check calendar availability for given date range"""
    try:
        # Get user's Google credentials
        credentials = get_user_credentials(current_user)
        
        # Initialize calendar service
        calendar_service = GoogleCalendarService(credentials)
        
        # Get available slots
        available_slots = calendar_service.get_available_slots(
            start_date=request.start_date,
            end_date=request.end_date,
            duration_minutes=request.duration_minutes,
            timezone=request.timezone
        )
        
        return AvailabilityResponse(
            slots=available_slots,
            timezone=request.timezone
        )
        
    except CalendarAPIError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error checking availability: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to check availability"
        )


@router.post("/appointments", response_model=AppointmentResponse)
async def create_appointment(
    request: CreateAppointmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AppointmentResponse:
    """Create a new appointment"""
    try:
        # Validate time range
        if request.end_time <= request.start_time:
            raise ValidationError("End time must be after start time")
        
        # Get user's Google credentials
        credentials = get_user_credentials(current_user)
        
        # Initialize calendar service
        calendar_service = GoogleCalendarService(credentials)
        
        # Create appointment object
        appointment = Appointment(
            id=f"apt_{datetime.utcnow().timestamp()}",
            user_id=current_user["id"],
            title=request.title,
            description=request.description,
            start_time=request.start_time,
            end_time=request.end_time,
            location=request.location,
            attendees=request.attendees,
            status=AppointmentStatus.PENDING
        )
        
        # Create event in Google Calendar
        google_event = calendar_service.create_event(
            appointment=appointment,
            send_notifications=request.send_notifications
        )
        
        # Update appointment with Google event ID
        appointment.google_event_id = google_event["id"]
        appointment.status = AppointmentStatus.CONFIRMED
        
        # In production, save to database
        
        return AppointmentResponse(
            id=appointment.id,
            title=appointment.title,
            description=appointment.description,
            start_time=appointment.start_time,
            end_time=appointment.end_time,
            location=appointment.location,
            attendees=appointment.attendees,
            status=appointment.status.value,
            google_event_id=appointment.google_event_id,
            created_at=appointment.created_at,
            updated_at=appointment.updated_at
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except CalendarAPIError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error creating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create appointment"
        )


@router.get("/appointments", response_model=List[AppointmentResponse])
async def list_appointments(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> List[AppointmentResponse]:
    """List user's appointments"""
    try:
        # Get user's Google credentials
        credentials = get_user_credentials(current_user)
        
        # Initialize calendar service
        calendar_service = GoogleCalendarService(credentials)
        
        # Convert dates to datetime if provided
        time_min = datetime.combine(start_date, datetime.min.time()) if start_date else None
        time_max = datetime.combine(end_date, datetime.max.time()) if end_date else None
        
        # Get events from Google Calendar
        events = calendar_service.get_events(
            time_min=time_min,
            time_max=time_max
        )
        
        # Convert to appointment responses
        appointments = []
        for event in events:
            # Parse event data
            start = event.get('start', {})
            end = event.get('end', {})
            
            if 'dateTime' in start and 'dateTime' in end:
                appointments.append(AppointmentResponse(
                    id=event['id'],
                    title=event.get('summary', 'No Title'),
                    description=event.get('description'),
                    start_time=datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00')),
                    end_time=datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00')),
                    location=event.get('location'),
                    attendees=[att['email'] for att in event.get('attendees', [])],
                    status=event.get('status', 'confirmed'),
                    google_event_id=event['id'],
                    created_at=datetime.fromisoformat(event['created'].replace('Z', '+00:00')),
                    updated_at=datetime.fromisoformat(event['updated'].replace('Z', '+00:00'))
                ))
        
        return appointments
        
    except CalendarAPIError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error listing appointments: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list appointments"
        )


@router.get("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def get_appointment(
    appointment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AppointmentResponse:
    """Get a specific appointment"""
    # In production, fetch from database
    # For now, fetch from Google Calendar
    appointments = await list_appointments(current_user=current_user)
    
    for appointment in appointments:
        if appointment.id == appointment_id:
            return appointment
    
    raise NotFoundError(f"Appointment {appointment_id} not found")


@router.put("/appointments/{appointment_id}", response_model=AppointmentResponse)
async def update_appointment(
    appointment_id: str,
    request: UpdateAppointmentRequest,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> AppointmentResponse:
    """Update an existing appointment"""
    try:
        # Get user's Google credentials
        credentials = get_user_credentials(current_user)
        
        # Initialize calendar service
        calendar_service = GoogleCalendarService(credentials)
        
        # Prepare updates
        updates = {}
        if request.title is not None:
            updates['title'] = request.title
        if request.description is not None:
            updates['description'] = request.description
        if request.start_time is not None:
            updates['start_time'] = request.start_time
        if request.end_time is not None:
            updates['end_time'] = request.end_time
        if request.location is not None:
            updates['location'] = request.location
        if request.attendees is not None:
            updates['attendees'] = request.attendees
        
        # Update event in Google Calendar
        updated_event = calendar_service.update_event(
            event_id=appointment_id,
            updates=updates
        )
        
        # Convert to response
        start = updated_event.get('start', {})
        end = updated_event.get('end', {})
        
        return AppointmentResponse(
            id=updated_event['id'],
            title=updated_event.get('summary', 'No Title'),
            description=updated_event.get('description'),
            start_time=datetime.fromisoformat(start['dateTime'].replace('Z', '+00:00')),
            end_time=datetime.fromisoformat(end['dateTime'].replace('Z', '+00:00')),
            location=updated_event.get('location'),
            attendees=[att['email'] for att in updated_event.get('attendees', [])],
            status=updated_event.get('status', 'confirmed'),
            google_event_id=updated_event['id'],
            created_at=datetime.fromisoformat(updated_event['created'].replace('Z', '+00:00')),
            updated_at=datetime.fromisoformat(updated_event['updated'].replace('Z', '+00:00'))
        )
        
    except CalendarAPIError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error updating appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update appointment"
        )


@router.delete("/appointments/{appointment_id}")
async def delete_appointment(
    appointment_id: str,
    current_user: Dict[str, Any] = Depends(get_current_user)
) -> Dict[str, str]:
    """Delete an appointment"""
    try:
        # Get user's Google credentials
        credentials = get_user_credentials(current_user)
        
        # Initialize calendar service
        calendar_service = GoogleCalendarService(credentials)
        
        # Delete event from Google Calendar
        calendar_service.delete_event(event_id=appointment_id)
        
        # In production, also delete from database
        
        return {"message": f"Appointment {appointment_id} deleted successfully"}
        
    except CalendarAPIError as e:
        logger.error(f"Calendar API error: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error deleting appointment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete appointment"
        ) 