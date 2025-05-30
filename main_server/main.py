from fastapi import FastAPI
import uvicorn
from fastapi.middleware.cors import CORSMiddleware # Not in your provided main.py, but often used
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from main_server.container import Container, create_container #
import app.auth.api.router as auth_routes #
import app.calendar_bot.api.router as calendar_bot_routes #
from omegaconf import OmegaConf #
from app.middleware.auth import AuthMiddleware #

# Assuming sql_lite_conn.py is in pkg.db_util
# Adjust the import path if your project structure is different
from pkg.db_util.sql_lite_conn import init_db, close_db, DB_PATH #

def create_app() -> FastAPI:
    app: FastAPI = FastAPI()
    # Create container
    container: Container = create_container(cfg=OmegaConf.load("conf/config.yaml")) #
    app.state.container = container #

    @app.on_event("startup")
    async def on_startup():
        """Event handler for application startup."""
        # Assuming logger is accessible via container, or use a direct logger instance
        app.state.container.logger().info(f"Attempting to initialize database at: {DB_PATH}") #
        await init_db() #
        app.state.container.logger().info("Database initialized successfully.")

    @app.on_event("shutdown")
    async def on_shutdown():
        """Event handler for application shutdown."""
        await close_db() #
        app.state.container.logger().info("Database connection closed.")

    app.add_middleware(AuthMiddleware) #

    # Add exception handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request, exc): #
        return JSONResponse( #
            status_code=422, #
            content={"detail": str(exc)}, #
        )

    # Include routers
    app.include_router(auth_routes.auth_router) #
    app.include_router(calendar_bot_routes.calendar_bot_router) #
    container.wire( #
        modules=[ #
            auth_routes, #
            calendar_bot_routes, #
        ]
    )
    return app


app = create_app() #

if __name__ == "__main__":
    uvicorn.run(app, #
        port=8000, #
        timeout_keep_alive=120, timeout_graceful_shutdown=300 #
    )