from app.auth.service.auth_service import IAuthRepository
from app.auth.entities.entity import User, UserAuth
from app.auth.repository.schema.user import UserModel, UserAuthModel #
from pkg.log.logger import Logger
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker # Import async_sessionmaker
from sqlalchemy import select #
import uuid #

class AuthRepository(IAuthRepository):
    def __init__(self, session_factory: async_sessionmaker[AsyncSession], logger: Logger): # Changed signature
        self._session_factory = session_factory # Store the factory
        self.logger = logger

    async def get_user_by_email(self, email: str) -> User | None:
        """Retrieve user by email"""
        async with self._session_factory() as session: # Create a session for this operation
            query = select(UserModel).where(UserModel.email == email) #
            result = await session.execute(query)
            user_model = result.scalar_one_or_none() #

            if not user_model: #
                return None

            return User( #
                id=user_model.id, #
                email=user_model.email, #
                name=user_model.name #
            )

    async def create_user(self, email: str, password_hash: str, name: str) -> User:
        """Create a new user"""
        async with self._session_factory() as session: # Create a session
            async with session.begin(): # Start a transaction
                user_id = str(uuid.uuid4()) #

                user_model = UserModel( #
                    id=user_id, #
                    email=email, #
                    name=name #
                )
                user_auth_model = UserAuthModel( #
                    user_id=user_id, #
                    hashed_password=password_hash #
                )
                session.add(user_model)
                session.add(user_auth_model)

                return User( #
                    id=user_model.id, #
                    email=user_model.email, #
                    name=user_model.name #
                )

    async def get_user_by_id(self, user_id: str) -> User | None:
        """Retrieve user by ID"""
        async with self._session_factory() as session: # Create a session
            query = select(UserModel).where(UserModel.id == user_id) #
            result = await session.execute(query)
            user_model = result.scalar_one_or_none() #

            if not user_model: #
                return None

            return User( #
                id=user_model.id, #
                email=user_model.email, #
                name=user_model.name #
            )

    async def get_user_auth(self, user_email: str) -> UserAuth | None:
        """Retrieve user authentication details by email"""
        async with self._session_factory() as session: # Create a session
            query = select(UserAuthModel).join(UserModel).where(UserModel.email == user_email)
            result = await session.execute(query)
            user_auth_model = result.scalar_one_or_none()
            if not user_auth_model:
                return None
            return UserAuth(
                user_id=user_auth_model.user_id,
                hashed_password=user_auth_model.hashed_password
            )


