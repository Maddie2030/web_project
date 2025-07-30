# auth-service/app/routers/auth.py

import os # Required for os.getenv to access environment variables directly in this file
from datetime import timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select # Used for querying the database

# --- Import your project's custom modules ---
from ..database.config import get_session # Dependency for getting a database session
from ..models.user import User # Your SQLAlchemy ORM model for the User table
from ..schemas.user import UserCreate, UserLogin, UserResponse # Pydantic schemas for request/response bodies
from ..schemas.token import Token # Pydantic schema for the JWT token response
from ..core.security import hash_password, verify_password, create_access_token # Security utility functions

# --- Initialize the FastAPI Router ---
router = APIRouter()

# --- Endpoint: User Registration (/register) ---
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_in: UserCreate, # Pydantic model for validating the incoming request body for registration
    session: AsyncSession = Depends(get_session) # Dependency Injection: Provides an async database session
):
    """
    Registers a new user in the system.

    - Validates the input format (e.g., email format, password minimum length).
    - Checks if the provided username or email already exists in the database to prevent duplicates.
    - Hashes the user's plain-text password using bcrypt before storing it.
    - Stores the new user record (with hashed password) in the PostgreSQL database.
    - Returns the newly created user's public information.
    """
    # 1. Check for Duplicate Username
    # Construct a SQLAlchemy SELECT query to find a user by username
    query_username = select(User).where(User.username == user_in.username)
    # Execute the query asynchronously and get the first result, or None if not found
    existing_user_by_username = (await session.execute(query_username)).scalar_one_or_none()
    if existing_user_by_username:
        # If a user with this username exists, raise a 409 Conflict error
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered"
        )

    # 2. Check for Duplicate Email
    # Construct a SQLAlchemy SELECT query to find a user by email
    query_email = select(User).where(User.email == user_in.email)
    # Execute the query asynchronously and get the first result, or None if not found
    existing_user_by_email = (await session.execute(query_email)).scalar_one_or_none()
    if existing_user_by_email:
        # If a user with this email exists, raise a 409 Conflict error
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    # 3. Hash the User's Password
    # Use the hash_password utility function from app.core.security
    hashed_password = hash_password(user_in.password)

    # 4. Create a New User ORM Object
    # Instantiate your SQLAlchemy User model with data from the Pydantic input model
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        hashed_password=hashed_password # Store the hashed password in the database
    )

    # 5. Add User to Session and Commit to Database
    session.add(db_user) # Add the new user object to the current database session
    await session.commit() # Commit the transaction, saving the user to the database
    await session.refresh(db_user) # Refresh the object to get updated fields (like auto-generated ID, created_at)

    # 6. Return the Created User
    # FastAPI will automatically serialize this db_user object into the UserResponse Pydantic model
    return db_user

# --- Endpoint: User Login and Token Generation (/token) ---
@router.post("/token", response_model=Token)
async def login_for_access_token(
    user_in: UserLogin, # Pydantic model for validating the incoming request body for login
    session: AsyncSession = Depends(get_session) # Dependency Injection: Provides an async database session
):
    """
    Authenticates a user and generates a JWT access token upon successful login.

    - Retrieves the user from the database based on the provided username.
    - Verifies the plain-text password against the stored hashed password.
    - If credentials are valid, generates a JSON Web Token (JWT) access token.
    - Returns the access token and its type ('bearer').
    """
    # 1. Retrieve User from Database
    # Query the database to find the user by their username
    query = select(User).where(User.username == user_in.username)
    user = (await session.execute(query)).scalar_one_or_none()

    # 2. Check if User Exists
    if not user:
        # If no user is found with the given username, raise a 401 Unauthorized error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"}, # Standard header for failed authentication attempts
        )

    # 3. Verify Password
    # Use the verify_password utility function from app.core.security to compare passwords
    if not verify_password(user_in.password, user.hashed_password):
        # If the password does not match, raise a 401 Unauthorized error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 4. Get Access Token Expiration Time
    # Read ACCESS_TOKEN_EXPIRE_MINUTES from environment variables, defaulting to 30 minutes
    access_token_expire_minutes = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))
    access_token_expires = timedelta(minutes=access_token_expire_minutes)

    # 5. Create the JWT Access Token
    # Use the create_access_token utility function from app.core.security
    # 'sub' (subject) is a standard JWT claim, often used for a unique identifier (here, username)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    # 6. Return the Access Token
    # FastAPI will automatically serialize this dictionary into the Token Pydantic model
    return {"access_token": access_token, "token_type": "bearer"}

# --- Placeholder Endpoint: Get Current User Info (/me) ---
@router.get("/me", status_code=status.HTTP_200_OK)
async def read_users_me():
    """
    A placeholder endpoint to retrieve information about the currently authenticated user.
    The actual authentication and user retrieval logic for this endpoint
    will be implemented in a future task (e.g., using OAuth2 with JWTBearer).
    """
    return {"message": "Endpoint for getting current user info (requires authentication)"}