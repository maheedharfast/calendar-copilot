from typing import Dict, Any, Optional,Annotated
from fastapi import  HTTPException, Depends

from fastapi import APIRouter

from app.auth.api.dependencies import AuthHandlerDep
from app.auth.api.dto import (
    LoginDTO,
    TokenResponse,
    RefreshTokenDTO,
    UserRegisterDTO,
)
from app.middleware import get_token_detail

auth_router = APIRouter(prefix="/auth", tags=["Authentication"])


@auth_router.post("/register")
async def register(user_data: UserRegisterDTO, auth_handler: AuthHandlerDep) ->TokenResponse:
    """Register a new user with email and password"""
    return await auth_handler.register_user(user_data)



@auth_router.post("/login")
async def login(login_data: LoginDTO, auth_handler: AuthHandlerDep) ->TokenResponse:
    """Login with email and password"""

    return await auth_handler.login(login_data)



@auth_router.post("/refresh")
async def refresh_token( refresh_token_dto: RefreshTokenDTO, auth_handler: AuthHandlerDep) -> TokenResponse:
    """Refresh access token"""
    try:
        return await auth_handler.refresh_token(refresh_token_dto.refresh_token)
    except ValueError as e:
        if str(e) == "Token has expired":
            raise HTTPException(status_code=401, detail="Refresh token has expired")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        auth_handler.logger.error(f"Error refreshing token: {e!s}")
        raise HTTPException(status_code=500, detail="Internal server error")

@auth_router.post("/logout")
async def logout( auth_handler: AuthHandlerDep):
    return await auth_handler.logout()

@auth_router.get("/profile")
async def get_profile(token_detail: Annotated[str, Depends(get_token_detail)], auth_handler: AuthHandlerDep) -> Dict[str, Any]:
    """Get user profile information"""
    try:
        return await auth_handler.get_user_profile(token_detail.user_id)
    except Exception as e:
        auth_handler.logger.error(f"Error retrieving user profile: {e!s}")
        raise HTTPException(status_code=500, detail="Internal server error")

