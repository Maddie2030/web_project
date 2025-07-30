# auth-service/app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field

class UserCreate(BaseModel):
    """Schema for user registration input."""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr # Validates format like "test@example.com"
    password: str = Field(..., min_length=8) # Basic strength validation

class UserLogin(BaseModel):
    """Schema for user login input."""
    username: str
    password: str

class UserResponse(BaseModel):
    """Schema for user data returned in API responses."""
    id: int
    username: str
    email: EmailStr
    is_active: bool

    class Config:
        orm_mode = True # Enables ORM mode for Pydantic (compatible with SQLAlchemy models)