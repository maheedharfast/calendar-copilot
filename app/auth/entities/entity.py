from pydantic import BaseModel

class User(BaseModel):
    """User entity schema"""
    id: str
    name: str
    email: str

class UserAuth(BaseModel):
    user_id: str
    hashed_password: str