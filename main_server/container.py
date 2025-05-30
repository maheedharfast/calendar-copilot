from dependency_injector import containers, providers
from fastapi import FastAPI
# from sqlalchemy.orm import sessionmaker # Not directly used here for this purpose
from pkg.log.logger import Logger #
from pkg.llm.client import LLMClient #
from pkg.auth_token_client.client import TokenClient #
# Import async_session_factory directly for repository injection
from pkg.db_util.sql_lite_conn import get_db_session, async_session_factory
from integration_clients.g_suite.client import GSuiteClient
from app.calendar_bot.repository.repository import CalendarRepository
from app.calendar_bot.repository.chat_repository import ChatRepository
from app.calendar_bot.service.calendar_service import CalendarService
from app.calendar_bot.service.calendar_agent import CalendarAgent
from app.calendar_bot.service.chat_service import ChatService
from app.calendar_bot.api.handler import CalendarBotHandler
from app.auth.api.handler import AuthHandler
from app.auth.service.auth_service import AuthService
from app.auth.repository.repository import AuthRepository
from omegaconf import DictConfig, OmegaConf
from conf.config import AppConfig

class Container(containers.DeclarativeContainer): #
    """Application container."""

    config: DictConfig = providers.Configuration() #

    # Database
    # get_db_session is useful for FastAPI's Depends system (per-request session)
    db_session_dependency = providers.Factory(get_db_session) #
    # async_session_factory is the actual SQLAlchemy async_sessionmaker()
    # to be injected into singletons like repositories that need to create sessions.
    actual_async_session_maker = providers.Object(async_session_factory)


    # Logging
    logger = providers.Singleton(Logger) #

    auth_repo = providers.Singleton(
        AuthRepository, #
        session_factory=actual_async_session_maker, # Inject the factory
        logger=logger #
    )
    token_client = providers.Singleton(TokenClient,config.jwt_auth.super_secret_key,config.jwt_auth.refresh_secret_key) #
    auth_service = providers.Singleton(AuthService,auth_repo,token_client, logger) #
    auth_handler = providers.Singleton(AuthHandler,auth_service,logger) #

    # LLM Client
    llm_client = providers.Singleton( #
        LLMClient, #
        gemini_api_key=config.openai.gemini_api_key,
        logger=logger,
    )

    # G Suite Client
    g_suite_client = providers.Singleton( #
        GSuiteClient, #
        client_id=config.google_oauth.client_id, #
        client_secret=config.google_oauth.client_secret, #
        logger=logger
    )

    # Repositories
    calendar_repository = providers.Singleton( #
        CalendarRepository, #
        session_factory=actual_async_session_maker, # Inject the factory
        logger=logger #
    )

    chat_repository = providers.Singleton( #
        ChatRepository, #
        session_factory=actual_async_session_maker, # Inject the factory
        logger=logger #
    )

    # Services
    calendar_service = providers.Singleton( #
        CalendarService, #
        calendar_repository=calendar_repository, #
    )
    calendar_agent = providers.Singleton( CalendarAgent,logger)

    chat_service = providers.Singleton( #
        ChatService, #
        calendar_agent=calendar_agent, #
        logger=logger,
        chat_repository=chat_repository,
        g_suite_client=g_suite_client,
    calendar_service=calendar_service
    )

    # Handlers
    calendar_bot_handler = providers.Singleton( #
        CalendarBotHandler, #
        calendar_service=calendar_service, #
        chat_service=chat_service, #
        logger=logger #
    )

    # FastAPI app
    app = providers.Singleton( #
        FastAPI, #
        title="Calendar Copilot API", #
        description="API for Calendar Copilot - Your AI Calendar Assistant", #
        version="1.0.0" #
    )

def create_container(cfg: DictConfig) -> Container: #
    """Create and configure the dependency injection container."""
    container_obj = Container() #

    schema = OmegaConf.structured(AppConfig) #
    config = OmegaConf.merge(schema, cfg) #
    config_dict = OmegaConf.to_container(config, resolve=True) #
    container_obj.config.from_dict(config_dict) #

    return container_obj #


if __name__ == "__main__": #
    # Ensure your config path is correct if you run this directly.
    container = create_container(cfg=OmegaConf.load("../../conf/config.yaml")) #