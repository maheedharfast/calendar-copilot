from abc import ABC, abstractmethod
import bcrypt
from fastapi import HTTPException
from app.auth.entities.entity import User, UserAuth
from pkg.auth_token_client.client import TokenClient, TokenPayload
from pkg.log.logger import Logger

class IAuthRepository(ABC):
    @abstractmethod
    async def get_user_by_email(self, email: str) -> User | None:
        pass

    @abstractmethod
    async def create_user(self, email: str, password_hash: str, name: str) -> User:
        pass

    @abstractmethod
    async def get_user_by_id(self, user_id: str) -> User | None:
        pass

    @abstractmethod
    async def get_user_auth(self, user_email: str) -> UserAuth | None:
        pass


class AuthService:
    def __init__(self, auth_repo: IAuthRepository, token_client: TokenClient, logger: Logger):
        self.token_client: TokenClient = token_client

        self.repo: IAuthRepository = auth_repo
        self.logger = logger


    def _hash_password(self, password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode(), salt).decode()

    def _verify_password(self, password: str, hashed: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode(), hashed.encode())

    def _create_tokens(self, user_id: str, email: str | None = None ) -> dict[str, str]:
        payload = TokenPayload(user_id=user_id,
                               email=email)
        return self.token_client.create_tokens(payload)

    async def register_with_email(self, email: str, password: str, name: str) -> dict[str, str]:
        """Register a new user with email and password"""
        # Check if user exists
        existing_user = await self.repo.get_user_by_email(email)
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")


        # Create user with hashed password
        hashed_password = self._hash_password(password)
        try:
            user = await self.repo.create_user(email, hashed_password, name)
        except Exception as e:
            raise HTTPException(status_code=500, detail="Error in creating user")

        return self._create_tokens(user.id, email=email)



    async def login_with_email(self, email: str, password: str) -> dict[str, str]:
        """Login with email and password"""
        user: UserAuth | None = await self.repo.get_user_auth(email)

        if (
            not user
            or not self._verify_password(password, user.hashed_password)
        ):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        return self._create_tokens(user.id, email=email)

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Get user by ID"""
        user: User | None = await self.repo.get_user_by_id(user_id)
        if not user :
            raise HTTPException(status_code=404, detail="User not found")
        return user



    async def refresh_token(self, refresh_token: str) -> dict[str, str]:
        """Generate new access token using refresh token"""
        try:
            payload = self.token_client.decode_token(refresh_token, is_refresh=True)

            user: User | None = await self.repo.get_user_by_id(payload["user_id"])
            if not user :
                raise HTTPException(status_code=401, detail="User not found")
            return self._create_tokens(user.id,  email=user.email)

        except Exception as e:
            self.logger.error(f"Error refreshing token: {e}")

            raise HTTPException(status_code=401, detail=e)


