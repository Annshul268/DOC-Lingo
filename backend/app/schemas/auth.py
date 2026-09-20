from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

class User(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_guest: bool = False
    created_at: datetime = Field(default_factory=datetime.utcnow)

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    is_guest: bool = False

class AuthTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=2, max_length=50)
    password: str = Field(..., min_length=4)
    email: Optional[str] = None

class LoginRequest(BaseModel):
    username: str = Field(..., min_length=1)
    password: str = Field(..., min_length=1)

class SessionRequest(BaseModel):
    username: Optional[str] = None
