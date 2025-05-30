from typing import Any

from fastapi import HTTPException

from app.auth.api.dto import (
    LoginDTO,
    UserRegisterDTO,UserDTO,
TokenResponse
)
from app.auth.service.auth_service import AuthService
from pkg.log.logger import Logger


class AuthHandler:
    def __init__(self, auth_service: AuthService, logger: Logger):
        self.auth_service = auth_service
        self.logger = logger

    async def register_user(self, user_data: UserRegisterDTO) -> TokenResponse:
        tokens = await self.auth_service.register_with_email(
            user_data.email,
            user_data.password,
            user_data.name,
        )
        return TokenResponse(access_token=tokens["access_token"],
                             refresh_token=tokens["refresh_token"], token_type= "bearer")

    async def login(self, login_data: LoginDTO) -> TokenResponse:
        tokens = await self.auth_service.login_with_email(
            login_data.email, login_data.password
        )
        return TokenResponse(access_token=tokens["access_token"],
                             refresh_token=tokens["refresh_token"], token_type= "bearer")



    async def refresh_token(self, refresh_token: str) -> TokenResponse:
        tokens = await self.auth_service.refresh_token(refresh_token)
        return TokenResponse(access_token=tokens["access_token"],
                             refresh_token=tokens["refresh_token"], token_type= "bearer")

    async def logout(self) -> dict[str, str]:
        return {"message": "Logged out successfully"}

    async def get_user_profile(self, user_id: str) -> dict[str, Any]:
        user_profile = await self.auth_service.get_user_by_id(user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        return {
            "id": user_profile.id,
            "email": user_profile.email,
            "name": user_profile.name,
        }
