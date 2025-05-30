
class CredentialsExpiredException(Exception):
    """
    Exception raised when the credentials are expired
    """
    pass

class CalendarBotException:
    """
    Base exception for Calendar Bot errors
    """

    def __init__(self, status_code: int, detail: str, error_code: str) -> None:
        self.status_code = status_code
        self.detail = detail
        self.error_code = error_code

    def __str__(self) -> str:
        return f"{self.error_code}: {self.detail} (Status Code: {self.status_code})"

class CalendarAPIError(CalendarBotException):
    """Raised when Google Calendar API operations fail"""
    
    def __init__(self, detail: str = "Calendar API error") -> None:
        super().__init__(
            status_code=503,
            detail=detail,
            error_code="CALENDAR_API_ERROR"
        )
