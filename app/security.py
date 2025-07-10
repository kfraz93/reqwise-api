# app/security.py
"""The module handles security-related functionalities, including:
- Password hashing and verification using passlib.
- OAuth2 scheme definition.
- JWT token creation and decoding.
- FastAPI dependencies for user authentication and authorization.
"""

import os
from datetime import UTC, datetime, timedelta
from typing import Optional

from dotenv import load_dotenv
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

# Import Pydantic schemas for token data
# Import SQLAlchemy models for user role checking
from . import models, schemas

# Import CRUD functions
from .crud import get_user_by_email

# Import database session dependency
from .database import get_db

# Load environment variables from .env file
load_dotenv()

# --- Load Configuration from Environment Variables ---
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 30))

# Validate that SECRET_KEY is set
if not SECRET_KEY:
    raise ValueError("SECRET_KEY environment variable not set. "
                     "Please set it in your .env file.")

# --- Password Hashing ---

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a plain-text password using bcrypt.

    Args:
        password (str): The plain-text password to hash.

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain-text password against a hashed password.

    Args:
        plain_password (str): The plain-text password provided by the user.
        hashed_password (str): The hashed password stored in the database.

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


# --- User Authentication ---


def authenticate_user(db: Session, username: str, password: str) -> (
    models.User | None
):
    """Authenticate a user by verifying their username and password
    against the database.

    Args:
        db (Session): The database session.
        username (str): The username (email) provided by the user.
        password (str): The plain-text password provided by the user.

    Returns:
        models.User | None: The user object if authentication is successful,
            otherwise None.
    """
    user = get_user_by_email(db, email=username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user


# --- JWT Token Configuration ---

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/token")


# --- JWT Token Creation and Decoding ---


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """Create a JWT access token.

    Args:
        data (dict): The payload to encode into the token
            (e.g., {"sub": user_email}).
        expires_delta (timedelta | None): Optional timedelta for token
            expiration. If None, `ACCESS_TOKEN_EXPIRE_MINUTES` is used.

    Returns:
        str: The encoded JWT access token.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(UTC) + expires_delta
    else:
        expire = datetime.now(UTC) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> schemas.TokenData | None:
    """Decode a JWT access token and return the payload.

    Args:
        token (str): The JWT access token to decode.

    Returns:
        schemas.TokenData | None: The decoded token data if valid,
            otherwise None.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
        token_data = schemas.TokenData(username=username)
    except JWTError:
        return None
    return token_data


# --- FastAPI Dependencies for Authentication and Authorization ---


async def get_current_user(token: str = Depends(oauth2_scheme),
                           db: Session = Depends(get_db)) -> models.User:
    """Get the current authenticated user from the JWT token.

    Args:
        token (str): The JWT token from the Authorization header.
        db (Session): The database session dependency.

    Returns:
        models.User: The authenticated user object from the database.

    Raises:
        HTTPException: If the token is invalid, expired, or the user is
            not found.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    token_data = decode_access_token(token)
    if token_data is None:
        raise credentials_exception

    user = get_user_by_email(db, email=token_data.username)
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(current_user: models.User =
                                  Depends(get_current_user)) -> models.User:
    """Get the current active authenticated user.

    Args:
        current_user (models.User): The user object from `get_current_user`.

    Returns:
        models.User: The active authenticated user object.
    """
    # In a real app, you might check user.is_active or similar
    return current_user


async def get_current_owner(current_user: models.User =
                            Depends(get_current_active_user)) -> models.User:
    """Get the current authenticated user if they have the 'OWNER' role.

    Args:
        current_user (models.User): The user object from
            `get_current_active_user`.

    Returns:
        models.User: The authenticated owner user object.

    Raises:
        HTTPException: If the user does not have the 'OWNER' role.
    """
    if current_user.role != models.UserRole.OWNER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Owner role required."
        )
    return current_user


async def get_current_customer(current_user: models.User =
                               Depends(get_current_active_user)) -> models.User:
    """Get the current authenticated user if they have the 'CUSTOMER' role.

    Args:
        current_user (models.User): The user object from
            `get_current_active_user`.

    Returns:
        models.User: The authenticated customer user object.

    Raises:
        HTTPException: If the user does not have the 'CUSTOMER' role.
    """
    if current_user.role != models.UserRole.CUSTOMER:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to perform this action. Customer role required."
        )
    return current_user