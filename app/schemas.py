# app/schemas.py
"""The module defines the Pydantic schemas for the ReqWise API.

These schemas are used for data validation, serialization, and deserialization
of API request bodies and responses. They mirror the structure of the
SQLAlchemy models but are tailored for API interaction.
"""

from pydantic import BaseModel, EmailStr, Field

# Import enums from models for consistent type definitions
from .models import RequirementStatus, RequirementType, UserRole

# --- User Schemas ---


class UserBase(BaseModel):
    """Base schema for common user properties.

    Attributes:
        username (str): Unique username for the user. Minimum 3, maximum 50
            characters.
        email (EmailStr): Unique email address for the user.
        full_name (str | None): Optional full name of the user. Maximum 100
            characters.

    """

    username: str = Field(
        ..., min_length=3, max_length=50, description="Unique username for the user."
    )
    email: EmailStr = Field(..., description="Unique email address for the user.")
    full_name: str | None = Field(
        None, max_length=100, description="Optional full name of the user."
    )


class UserCreate(UserBase):
    """Schema for user creation request body.

    Extends `UserBase` by adding the password and allowing role specification
    during registration.

    Attributes:
        password (str): User's password. Must be at least 8 characters long.
        role (UserRole): Role of the user (customer or owner). Defaults to
            `UserRole.CUSTOMER`.

    """

    password: str = Field(
        ...,
        min_length=8,
        description="User's password. Must be at least 8 characters long.",
    )
    role: UserRole = Field(
        UserRole.CUSTOMER, description="Role of the user (customer or owner)."
    )


class UserOut(UserBase):
    """Schema for user output response body.

    Extends `UserBase` by including the unique ID and the assigned role,
    suitable for sending user data to clients without sensitive information.

    Attributes:
        id (int): Unique identifier of the user.
        role (UserRole): Role of the user.

    """

    id: int = Field(..., description="Unique identifier of the user.")
    role: UserRole = Field(..., description="Role of the user.")

    class Config:
        """Pydantic configuration for ORM mode.

        Enables Pydantic to read data directly from SQLAlchemy ORM model
        attributes, facilitating seamless conversion from database objects
        to API response schemas.
        """

        from_attributes = True


# --- Token Schemas (for Authentication) ---


class Token(BaseModel):
    """Schema for the OAuth2 token response.

    Represents the structure of the access token returned upon successful login.

    Attributes:
        access_token (str): The JWT access token.
        token_type (str): The type of the token, typically "bearer".

    """

    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field("bearer", description="Type of the token (e.g., 'bearer').")


class TokenData(BaseModel):
    """Schema for data contained within a JWT token.

    Defines the payload structure expected when decoding a JWT.

    Attributes:
        username (str | None): The username encoded in the JWT, used to identify
            the user.

    """

    username: str | None = Field(None, description="Username encoded in the JWT.")


# --- Project Schemas ---


class ProjectBase(BaseModel):
    """Base schema for common project properties.

    Attributes:
        name (str): Name of the project. Minimum 3, maximum 100 characters.
        description (str | None): Detailed description of the project. Optional.

    """

    name: str = Field(
        ..., min_length=3, max_length=100, description="Name of the project."
    )
    description: str | None = Field(
        None, description="Detailed description of the project."
    )


class ProjectCreate(ProjectBase):
    """Schema for project creation request body.

    Extends `ProjectBase` without additional fields, as the owner ID is
    derived from the authenticated user.
    """

    pass


class ProjectOut(ProjectBase):
    """Schema for project output response body.

    Extends `ProjectBase` by including the unique ID and the ID of the
    project's owner.

    Attributes:
        id (int): Unique identifier of the project.
        owner_id (int): ID of the user who owns this project.

    """

    id: int = Field(..., description="Unique identifier of the project.")
    owner_id: int = Field(..., description="ID of the user who owns this project.")

    class Config:
        """Pydantic configuration for ORM mode.

        Enables Pydantic to read data directly from SQLAlchemy ORM model
        attributes, facilitating seamless conversion from database objects
        to API response schemas.
        """

        from_attributes = True


# --- Requirement Schemas ---


class RequirementBase(BaseModel):
    """Base schema for common requirement properties.

    Attributes:
        description (str): Detailed description of the requirement. Minimum 5
            characters.
        type (RequirementType): Type of the requirement, e.g., 'must_have' or
            'nice_to_have'. Defaults to `RequirementType.MUST_HAVE`.

    """

    description: str = Field(
        ..., min_length=5, description="Detailed description of the requirement."
    )
    type: RequirementType = Field(
        RequirementType.MUST_HAVE,
        description="Type of the requirement (must_have or nice_to_have).",
    )


class RequirementCreate(RequirementBase):
    """Schema for requirement creation request body.

    Extends `RequirementBase` without additional fields, as the project ID is
    derived from the URL path.
    """

    pass


class RequirementUpdate(RequirementBase):
    """Schema for updating requirement details request body.

    Extends `RequirementBase` with all fields being optional, allowing for
    partial updates of a requirement's description or type.

    Attributes:
        description (str | None): Updated description of the requirement. Optional.
        type (RequirementType | None): Updated type of the requirement. Optional.

    """

    description: str | None = Field(
        None, min_length=5, description="Updated description of the requirement."
    )
    type: RequirementType | None = Field(
        None, description="Updated type of the requirement."
    )


class RequirementStatusUpdate(BaseModel):
    """Schema for updating only the status of a requirement request body.

    Used specifically for changing the progress status of a requirement.

    Attributes:
        status (RequirementStatus): New status of the requirement, e.g.,
            'pending', 'in_progress', or 'done'.

    """

    status: RequirementStatus = Field(
        ...,
        description="New status of the requirement (pending, in_progress, or done).",
    )


class RequirementOut(RequirementBase):
    """Schema for requirement output response body.

    Extends `RequirementBase` by adding fields that are typically generated or
    managed by the backend, such as the unique ID, the current status, and
    the project ID it belongs to.

    Attributes:
        id (int): Unique identifier of the requirement.
        status (RequirementStatus): Current status of the requirement.
        project_id (int): ID of the project this requirement belongs to.

    """

    id: int = Field(..., description="Unique identifier of the requirement.")
    status: RequirementStatus = Field(
        ..., description="Current status of the requirement."
    )
    project_id: int = Field(
        ..., description="ID of the project this requirement belongs to."
    )

    class Config:
        """Pydantic configuration for ORM mode.

        Enables Pydantic to read data directly from SQLAlchemy ORM model
        attributes, facilitating seamless conversion from database objects
        to API response schemas.
        """

        from_attributes = True