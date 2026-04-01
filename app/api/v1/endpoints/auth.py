"""
DocuSense - Authentication Endpoints
"""
from datetime import timedelta
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel

from app.core.config import get_settings
from app.core.security import (
    User,
    create_access_token,
    get_current_active_user,
    get_password_hash,
    verify_password,
)

router = APIRouter()
settings = get_settings()


class Token(BaseModel):
    """Token response model."""

    access_token: str
    token_type: str


class TokenResponse(Token):
    """Extended token response with user info."""

    username: str
    role: str
    expires_in: int


# Demo users database (replace with real database in production)
# Passwords: admin123, user123
# Note: Passwords are hashed lazily to avoid module load issues
_DEMO_USERS_DB: dict[str, dict] | None = None


def _get_demo_users_db() -> dict[str, dict]:
    """Get demo users database, initializing on first access."""
    global _DEMO_USERS_DB
    if _DEMO_USERS_DB is None:
        _DEMO_USERS_DB = {
            "admin": {
                "username": "admin",
                "hashed_password": get_password_hash("admin123"),
                "role": "admin",
                "disabled": False,
            },
            "user": {
                "username": "user",
                "hashed_password": get_password_hash("user123"),
                "role": "user",
                "disabled": False,
            },
        }
    return _DEMO_USERS_DB


def authenticate_user(username: str, password: str) -> User | None:
    """
    Authenticate a user by username and password.

    Args:
        username: User's username
        password: User's plain text password

    Returns:
        User object if authentication successful, None otherwise
    """
    users_db = _get_demo_users_db()
    user_dict = users_db.get(username)
    if not user_dict:
        return None
    if not verify_password(password, user_dict["hashed_password"]):
        return None
    return User(
        username=user_dict["username"],
        role=user_dict["role"],
        disabled=user_dict["disabled"],
    )


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Login for access token",
    description="""
    OAuth2 compatible token login endpoint.
    
    ## Demo Credentials for Testing
    
    | Username | Password | Role |
    |----------|----------|------|
    | `admin` | `admin123` | admin |
    | `user` | `user123` | user |
    
    ## Usage in Swagger UI
    
    1. Click the **Authorize** button (🔓) at the top of the page
    2. Enter username and password
    3. Click **Authorize**
    4. All protected endpoints will now include the JWT token
    """,
)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> TokenResponse:
    """
    Authenticate user and return JWT access token.

    - **username**: User's username
    - **password**: User's password

    Returns a JWT token that can be used to authenticate subsequent requests.
    """
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    access_token_expires = timedelta(minutes=settings.jwt_access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username, "role": user.role},
        expires_delta=access_token_expires,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        username=user.username,
        role=user.role,
        expires_in=settings.jwt_access_token_expire_minutes * 60,
    )


@router.get(
    "/me",
    response_model=User,
    summary="Get current user",
    description="Returns the currently authenticated user's information.",
)
async def read_users_me(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> User:
    """
    Get current authenticated user information.

    Requires a valid JWT token in the Authorization header.
    """
    return current_user


@router.get(
    "/verify",
    summary="Verify token",
    description="Verify that the current token is valid.",
)
async def verify_token(
    current_user: Annotated[User, Depends(get_current_active_user)],
) -> dict:
    """
    Verify the current JWT token is valid.

    Returns user info if token is valid.
    """
    return {
        "valid": True,
        "username": current_user.username,
        "role": current_user.role,
    }
