# auth-service/app/routers/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

router = APIRouter()

class UserLogin(BaseModel):
    username: str
    password: str

class UserRegister(BaseModel):
    username: str
    email: str
    password: str

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_user(user: UserRegister):
    # Dummy logic for registration
    # In a real app: hash password, save to DB
    return {"message": f"User {user.username} registered successfully (dummy)"}

@router.post("/token", status_code=status.HTTP_200_OK)
async def login_for_access_token(form_data: UserLogin): # Typically uses OAuth2PasswordRequestForm
    # Dummy logic for login
    # In a real app: verify password, generate JWT
    if form_data.username == "test" and form_data.password == "password":
        return {"access_token": "dummy_jwt_token", "token_type": "bearer"}
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Incorrect username or password",
        headers={"WWW-Authenticate": "Bearer"},
    )

@router.get("/me", status_code=status.HTTP_200_OK)
async def read_users_me():
    # Dummy endpoint to get current user info (requires authentication)
    return {"username": "current_user", "email": "user@example.com"}