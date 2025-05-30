# AI Calendar Scheduling Chatbot

An AI-powered chatbot backend API that assists users in scheduling appointments through Google Calendar integration. The chatbot provides a conversational interface for scheduling appointments while handling the backend integration with Google Calendar's scheduling system.

## Features

- **Natural Language Processing**: Understands user intents for scheduling, checking availability, and managing appointments using Pydantic AI with OpenAI
- **Google Calendar Integration**: Direct integration with Google Calendar API for real-time scheduling
- **OAuth2 Authentication**: Secure authentication with Google accounts
- **RESTful API**: Well-structured API endpoints for all calendar operations
- **Chat Sessions**: Maintains conversation context across multiple interactions
- **Error Handling**: Robust error handling and recovery mechanisms
- **Type Safety**: Full Python type annotations throughout the codebase
- **Dependency Injection**: Clean architecture with dependency injection container
- **Configuration Management**: YAML-based configuration with OmegaConf

## Tech Stack

- **Framework**: FastAPI (Python)
- **NLP**: Pydantic AI with OpenAI GPT models
- **Calendar Integration**: Google Calendar API
- **Authentication**: OAuth2 with JWT tokens
- **Type Checking**: Pydantic for data validation
- **Database**: SQLite with async support
- **Dependency Management**: UV package manager
- **Configuration**: OmegaConf for YAML configuration
- **Dependency Injection**: dependency-injector
- **Logging**: Loguru for structured logging

## Project Structure

```
calendar-copilot/
├── main_server/
│   ├── main.py                 # FastAPI application entry point
│   └── container.py            # Dependency injection container
├── app/
│   ├── auth/
│   │   ├── api/               # Authentication API endpoints
│   │   ├── service/           # Authentication business logic
│   │   ├── repository/        # Auth data access layer
│   │   └── entities/          # Auth domain models
│   ├── calendar_bot/
│   │   ├── api/               # Calendar bot API endpoints
│   │   ├── service/           # Calendar bot business logic
│   │   ├── repository/        # Calendar data access layer
│   │   └── entities/          # Calendar domain models
│   ├── api/
│   │   └── v1/               # API version 1 routes
│   └── middleware/
│       └── auth.py           # Authentication middleware
├── pkg/
│   ├── auth_token_client/    # JWT token utilities
│   ├── db_util/             # Database utilities and connections
│   ├── llm/                 # LLM integration utilities
│   └── log/                 # Logging utilities
├── integration_clients/
│   └── g_suite/             # Google Workspace integrations
├── conf/
│   ├── config.yaml          # Application configuration
│   └── config.py            # Configuration models
├── data/                    # Database and data files
├── pyproject.toml           # UV project configuration
├── uv.lock                  # UV lock file
├── Makefile                 # Build and run commands
└── README.md                # This file
```

## API Endpoints

### Authentication (`/auth`)
- `POST /auth/register` - Register a new user with email and password
- `POST /auth/login` - Login with email and password
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user
- `GET /auth/profile` - Get user profile information

### Calendar Bot & Chat (`/chat`)
**Conversation Management:**
- `POST /chat/conversation` - Create a new conversation for the calendar bot
- `POST /chat/conversation/{conversation_id}/message` - Add a message to a conversation
- `GET /chat/conversations/{conversation_id}` - Get a conversation by ID
- `GET /chat/conversations` - List all conversations for the user

**Calendar Management:**
- `POST /chat/calendar` - Create a new calendar
- `GET /chat/calendars` - List all calendars for the user
- `GET /chat/calendar/{calendar_id}` - Get a specific calendar by ID

## Setup Instructions

### Prerequisites
- Python 3.11+
- UV package manager
- Google Cloud Project with Calendar API enabled
- OpenAI API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/calendar-copilot.git
cd calendar-copilot
```

2. Install UV (if not already installed):
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

3. Install dependencies using UV:
```bash
uv sync
```

Or using the Makefile:
```bash
make install
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
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./data/calendar_copilot.db
```

5. Run the application:
```bash
# Using UV
uv run --env-file .env python3 -m main_server.main

# Or using Makefile
make run
```

The API will be available at `http://localhost:8000`

## Development Commands

### Using UV
```bash
# Install dependencies
uv sync

# Run the application
uv run --env-file .env python3 -m main_server.main

# Run with development reload
uv run --env-file .env uvicorn main_server.main:app --reload

# Add a new dependency
uv add package-name

# Add a development dependency
uv add --dev package-name
```

### Using Makefile
```bash
# Install dependencies
make install

# Run the application
make run
```

## Testing

Run the test suite:
```bash
uv run pytest
```

With coverage:
```bash
uv run pytest --cov=app tests/
```

## Configuration

The application uses YAML-based configuration managed by OmegaConf. Configuration files are located in the `conf/` directory:

- `config.yaml` - Main application configuration
- `config.py` - Configuration models and validation

Example configuration structure:
```yaml
server:
  host: "0.0.0.0"
  port: 8000
  
database:
  url: "sqlite:///./data/calendar_copilot.db"
  
auth:
  secret_key: "${SECRET_KEY}"
  algorithm: "HS256"
  expire_minutes: 30

google:
  client_id: "${GOOGLE_CLIENT_ID}"
  client_secret: "${GOOGLE_CLIENT_SECRET}"

openai:
  api_key: "${OPENAI_API_KEY}"
  model: "gpt-4"
```

## Usage Examples

### 1. Register and Login
```bash
# Register a new user
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'

# Login to get access token
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "your_password"
  }'
```

### 2. Create a conversation and send a message
```bash
# Create a new conversation
curl -X POST http://localhost:8000/chat/conversation \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json"

# Send a message to the conversation
curl -X POST http://localhost:8000/chat/conversation/{conversation_id}/message \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I want to schedule a meeting tomorrow at 2pm"
  }'
```

### 3. Manage calendars
```bash
# Create a new calendar
curl -X POST http://localhost:8000/chat/calendar \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "google",
    "credentials": {
      "access_token": "your_google_access_token"
    }
  }'

# List all calendars
curl -X GET http://localhost:8000/chat/calendars \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## Architecture Overview

### Clean Architecture
The project follows clean architecture principles with clear separation of concerns:
- **API Layer**: FastAPI endpoints for external communication
- **Service Layer**: Business logic and use cases
- **Repository Layer**: Data access and persistence
- **Entities**: Domain models and business rules

### Dependency Injection
Uses `dependency-injector` for managing dependencies and ensuring testability.

### Authentication Flow
1. User initiates Google OAuth2 login
2. User authorizes calendar access
3. Backend exchanges code for tokens
4. JWT token issued for API access

### Chat Processing Flow
1. User sends natural language message
2. Intent detection using Pydantic AI with OpenAI
3. Context extraction from conversation
4. Calendar operations if needed
5. Natural language response generation

### Calendar Integration
- Direct API calls to Google Calendar
- Real-time availability checking
- Conflict detection
- Automatic timezone handling

## Design Decisions

1. **FastAPI Framework**: Modern async support, automatic API documentation, and type safety
2. **UV Package Manager**: Fast, reliable Python package management
3. **Pydantic AI**: Type-safe AI integration with better development experience
4. **Clean Architecture**: Separation of concerns for maintainability and testability
5. **Dependency Injection**: Loose coupling and improved testability
6. **OmegaConf**: Flexible configuration management with environment variable support
7. **SQLite**: Lightweight database perfect for development and small deployments

## Known Limitations

1. **Database**: Currently uses SQLite (can be upgraded to PostgreSQL for production)
2. **User Management**: Simplified user management without full RBAC
3. **Calendar Providers**: Only supports Google Calendar (extensible architecture for others)
4. **Rate Limiting**: No built-in rate limiting (should be added for production)
5. **Caching**: No Redis caching layer (can be added via dependency injection)

## Future Enhancements

1. **Database Migration**: Add PostgreSQL support with Alembic migrations
2. **Multi-Calendar Support**: Integrate with Outlook, Apple Calendar
3. **Advanced NLP**: Fine-tune models for better scheduling understanding
4. **Webhooks**: Real-time calendar updates
5. **Voice Integration**: Support for voice commands
6. **Meeting Suggestions**: AI-powered optimal meeting time suggestions
7. **Notification System**: Email/SMS notifications for appointments
8. **Multi-tenancy**: Support for multiple organizations

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes with type annotations
4. Ensure tests pass: `uv run pytest`
5. Push to the branch
6. Create a Pull Request

### Development Guidelines
- Always use Python type definitions (as per project requirements)
- Follow clean architecture principles
- Write tests for new features
- Update documentation for API changes

## License

This project is licensed under the MIT License - see the LICENSE file for details.



