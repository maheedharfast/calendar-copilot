import uuid
from datetime import datetime
from typing import Annotated, List, Dict, Any, Optional
from pydantic import BaseModel, Field, validator, PositiveInt
from enum import Enum

class GoogleOAuthToken(BaseModel):
    access_token: str
    refresh_token: str
    scope: str
    token_type: str = Field(
        description="Type of token, typically 'Bearer'",
        pattern="^Bearer$",  # Ensures token_type is exactly "Bearer"
    )
    expiry_date: int = Field(
        description="Token expiration timestamp in milliseconds since epoch"
    )

    @property
    def scopes(self) -> list[str]:
        """Returns the scope string split into a list of individual scopes"""
        return self.scope.split()

    @property
    def is_expired(self) -> bool:
        """Checks if the token is expired using millisecond precision"""
        current_time_ms = int(datetime.now().timestamp() * 1000)
        return current_time_ms > self.expiry_date

class TimeSlot(BaseModel):
    """Available time slot schema"""
    start_time: datetime = Field(..., description="Start time of the slot")
    end_time: datetime = Field(..., description="End time of the slot")
    available: bool = Field(default=True, description="Whether the slot is available")
    
    @validator('end_time')
    def end_time_after_start_time(cls, v: datetime, values: Dict[str, Any]) -> datetime:
        if 'start_time' in values and v <= values['start_time']:
            raise ValueError('end_time must be after start_time')
        return v
class AppointmentStatus(str, Enum):
    """Appointment status enumeration"""
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"


class Appointment(BaseModel):
    """Appointment model with type definitions"""
    
    id: str = Field(..., description="Unique appointment identifier")
    user_id: str = Field(..., description="User who created the appointment")
    title: str = Field(..., description="Appointment title")
    description: Optional[str] = Field(None, description="Appointment description")
    start_time: datetime = Field(..., description="Appointment start time")
    end_time: datetime = Field(..., description="Appointment end time")
    location: Optional[str] = Field(None, description="Appointment location")
    attendees: List[str] = Field(default_factory=list, description="List of attendee emails")
    status: AppointmentStatus = Field(default=AppointmentStatus.PENDING)
    google_event_id: Optional[str] = Field(None, description="Google Calendar event ID")
    meta_data: Optional[Dict[str, Any]] = Field(default_factory=lambda: {})
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
        use_enum_values = True 