# auth-service/app/schemas/token.py
from pydantic import BaseModel

class Token(BaseModel):
    """Schema for JWT access token response."""
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    """Schema for data contained in a JWT."""
    username: str | None = None