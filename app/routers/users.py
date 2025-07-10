# app/routers/users.py
"""The module defines the API routes related to user management,
including registration and login.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Import schemas for request/response validation
from .. import schemas

# Import CRUD functions (will be defined in app/crud.py)
from ..crud import create_user, get_user_by_email, get_user_by_username

# Import database session dependency
from ..database import get_db

# Import security functions for password hashing and JWT handling
from ..security import (
    OAuth2PasswordRequestForm,
    authenticate_user,
    create_access_token,
    get_password_hash,
)

router = APIRouter(
    prefix="/users",  # All routes in this router will start with /users
    tags=["Users"],  # Tags for grouping endpoints in Swagger UI
)


@router.post(
    "/register",
    response_model=schemas.UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new user with a specified username, email, password, role."
    "The password will be hashed before storage. Default role is 'customer'.",
)
async def register_user(
    user_create: schemas.UserCreate,
    db: Session = Depends(get_db),
):
    """Registers a new user in the database.

    Args:
        user_create (schemas.UserCreate): User registration data in the request body.
        db (Session): The database session dependency.

    Returns:
        schemas.UserOut: The newly created user's data (excluding the hashed password).

    Raises:
        HTTPException: If a user with the provided email or username already exists.

    """
    db_user_email = get_user_by_email(db, email=user_create.email)
    if db_user_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered"
        )

    db_user_username = get_user_by_username(db, username=user_create.username)
    if db_user_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken"
        )

    hashed_password = get_password_hash(user_create.password)
    db_user = create_user(
        db=db, user_create=user_create, hashed_password=hashed_password
    )

    return db_user


@router.post(
    "/token",
    response_model=schemas.Token,
    summary="User Login",
    description="Authenticates a user and returns an OAuth2 access token.",
)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    """Authenticates a user with username and password, then issues a JWT access token.

    Args:
        form_data (OAuth2PasswordRequestForm): Form data containing username, password.
        db (Session): The database session dependency.

    Returns:
        schemas.Token: An object containing the access token and token type.

    Raises:
        HTTPException: If authentication fails (incorrect username or password).

    """
    # Authenticate the user using the function from app/security.py
    user = authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Create an access token for the authenticated user
    access_token = create_access_token(data={"sub": user.email})

    return {"access_token": access_token, "token_type": "bearer"}
