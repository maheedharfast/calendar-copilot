# pkg/config/config.py

from dataclasses import dataclass


@dataclass
class GoogleOAuthConfig:
    client_id: str
    client_secret: str


@dataclass
class JWTAuthConfig:
    super_secret_key: str
    refresh_secret_key: str



@dataclass
class OpenAIConfig:
    gemini_api_key: str




@dataclass
class AppConfig:
    google_oauth: GoogleOAuthConfig
    jwt_auth: JWTAuthConfig
    openai: OpenAIConfig


