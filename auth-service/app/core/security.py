# auth-service/app/core/security.py
import os
from datetime import datetime, timedelta
from typing import Union
import uuid # For jti claim

from passlib.context import CryptContext
from jose import JWTError, jwt, ExpiredSignatureError # JWSAlgorithmError # Import specific JWT errors
from dotenv import load_dotenv

# Add these imports for database interaction if not already present
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..models.user import User # Import your User model

load_dotenv()

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable is not set. Please set it for JWT security.")


# --- Existing functions (keep them as they are) ---
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict, expires_delta: Union[timedelta, None] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({
        "exp": expire,
        "jti": str(uuid.uuid4())
    })
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- NEW: Function to decode and verify JWT ---
def decode_access_token(token: str) -> dict:
    """
    Decodes and verifies a JWT access token.

    Raises:
        ExpiredSignatureError: If the token has expired.
        JWTError: If the token is invalid for any other reason (e.g., bad signature).
    Returns:
        dict: The decoded payload if valid.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except ExpiredSignatureError:
        # Re-raise with a more specific error for easier handling in dependencies
        raise ExpiredSignatureError("Token has expired")
    except JWTError:
        # Catch all other JWT related errors
        raise JWTError("Could not validate credentials")


# --- NEW: Function to get a user by username from DB ---
async def get_user_by_username(session: AsyncSession, username: str) -> Union[User, None]:
    """
    Retrieves a user from the database by username.
    """
    query = select(User).where(User.username == username)
    result = await session.execute(query)
    user = result.scalar_one_or_none()
    return user