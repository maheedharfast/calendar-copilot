from pydantic import  BaseModel, Field, constr


class TokenResponse(BaseModel):
    """Token response schema"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    refresh_token: str = Field(..., description="JWT refresh token")

class UserDTO(BaseModel):
    """DTO for user data"""
    id: str = Field(..., description="Unique identifier for the user")
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    password: constr(min_length=8, max_length=100)  # type: ignore

class UserRegisterDTO(BaseModel):
    """DTO for user registration"""
    name: str = Field(..., description="User's full name")
    email: str = Field(..., description="User's email address")
    password: constr(min_length=8, max_length=100)  # type: ignore



class LoginDTO(BaseModel):
    """DTO for user login"""

    email: str
    password: str

class RefreshTokenDTO(BaseModel):
    refresh_token: str
