# AI Calendar Scheduling Chatbot

An AI-powered chatbot backend API that assists users in scheduling appointments through Google Calendar integration. The chatbot provides a conversational interface for scheduling appointments while handling the backend integration with Google Calendar's scheduling system.

## Features

- **Natural Language Processing**: Understands user intents for scheduling, checking availability, and managing appointments
- **Google Calendar Integration**: Direct integration with Google Calendar API for real-time scheduling
- **OAuth2 Authentication**: Secure authentication with Google accounts
- **RESTful API**: Well-structured API endpoints for all calendar operations
- **Chat Sessions**: Maintains conversation context across multiple interactions
- **Error Handling**: Robust error handling and recovery mechanisms
- **Type Safety**: Full Python type annotations throughout the codebase

## Tech Stack

- **Framework**: FastAPI (Python)
- **NLP**: Gemini LLM 2.5 Flash 
- **Calendar Integration**: Google Calendar API
- **Authentication**: OAuth2 with JWT tokens
- **Type Checking**: Pydantic for data validation
## Project Structure

```
calendar-copilot/
├── app/
│   ├── api/
│   │   └── v1/
│   │       ├── auth.py          # Authentication endpoints
│   │       ├── calendar.py      # Calendar management endpoints
│   │       └── chatbot.py       # Chatbot interaction endpoints
│   ├── core/
│   │   ├── exceptions.py        # Custom exception classes
│   │   └── logging.py           # Logging configuration
│   ├── models/
│   │   ├── user.py             # User data models
│   │   └── appointment.py      # Appointment data models
│   ├── schemas/
│   │   ├── auth.py             # Authentication schemas
│   │   ├── calendar.py         # Calendar operation schemas
│   │   └── chat.py             # Chat interaction schemas
│   ├── services/
│   │   ├── google_calendar.py  # Google Calendar service
│   │   └── chat_service.py     # NLP and chat processing
│   └── main.py                 # FastAPI application entry point
├── config/
│   └── settings.py             # Application configuration
├── tests/                      # Test suite
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/token` - Get access token
- `GET /api/v1/auth/profile` - Get current user info
- `POST /api/v1/auth/logout` - Logout user

### Calendar Operations
- `POST /api/v1/calendar/availability` - Check calendar availability
- `POST /api/v1/calendar/appointments` - Create new appointment
- `GET /api/v1/calendar/appointments` - List appointments
- `GET /api/v1/calendar/appointments/{id}` - Get specific appointment
- `PUT /api/v1/calendar/appointments/{id}` - Update appointment
- `DELETE /api/v1/calendar/appointments/{id}` - Delete appointment

### Chatbot
- `POST /api/v1/chat/message` - Send message to chatbot
- `GET /api/v1/chat/sessions/{id}` - Get chat session history
- `POST /api/v1/chat/sessions` - Create new chat session
- `DELETE /api/v1/chat/sessions/{id}` - Delete chat session
- `GET /api/v1/chat/intents` - Get supported intents

## Setup Instructions

### Prerequisites
- Python 3.8+
- Google Cloud Project with Calendar API enabled
- OpenAI API key
- Redis (optional, for caching)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/calendar-copilot.git
cd calendar-copilot
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
```

Edit `.env` file with your credentials:
```env
# Google OAuth2
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Application
SECRET_KEY=your-secret-key-here
```

5. Run the application:
```bash
uvicorn app.main_server:app --reload
```

The API will be available at `http://localhost:8000`

## Testing

Run the test suite:
```bash
pytest
```

With coverage:
```bash
pytest --cov=app tests/
```

## Usage Examples

### 1. Authenticate with Google
```bash
# Get login URL
curl http://localhost:8000/api/v1/auth/google/login
```

### 2. Send a chat message
```bash
curl -X POST http://localhost:8000/api/v1/chat/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to schedule a meeting tomorrow at 2pm"
  }'
```

### 3. Check availability
```bash
curl -X POST http://localhost:8000/api/v1/calendar/availability \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "start_date": "2024-01-15",
    "end_date": "2024-01-17",
    "duration_minutes": 30
  }'
```

## Architecture Overview

### Authentication Flow
1. User initiates Google OAuth2 login
2. User authorizes calendar access
3. Backend exchanges code for tokens
4. JWT token issued for API access

### Chat Processing Flow
1. User sends natural language message
2. Intent detection using OpenAI
3. Context extraction from conversation
4. Calendar operations if needed
5. Natural language response generation

### Calendar Integration
- Direct API calls to Google Calendar
- Real-time availability checking
- Conflict detection
- Automatic timezone handling

## Design Decisions

1. **FastAPI Framework**: Chosen for its modern async support, automatic API documentation, and type safety
2. **OpenAI for NLP**: Provides superior natural language understanding compared to rule-based systems
3. **JWT Authentication**: Stateless authentication suitable for API-first architecture
4. **Pydantic Models**: Ensures data validation and provides clear API contracts
5. **Service Layer Pattern**: Separates business logic from API endpoints for better testability

## Known Limitations

1. **Session Storage**: Currently stores chat sessions in memory (not persistent)
2. **User Management**: Simplified user management without full database integration
3. **Calendar Providers**: Only supports Google Calendar (extensible to others)
4. **Rate Limiting**: No built-in rate limiting (should be added for production)
5. **Webhook Support**: No real-time calendar updates via webhooks

## Future Enhancements

1. **Database Integration**: Add PostgreSQL for persistent storage
2. **Multi-Calendar Support**: Integrate with Outlook, Apple Calendar
3. **Advanced NLP**: Fine-tune models for better scheduling understanding
4. **Webhooks**: Real-time calendar updates
5. **Voice Integration**: Support for voice commands
6. **Meeting Suggestions**: AI-powered optimal meeting time suggestions

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

