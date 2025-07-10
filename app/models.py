# app/models.py
"""The module defines the SQLAlchemy ORM models for the ReqWise API.

It includes models for Users, Projects, and Requirements, along with their
relationships and associated enums.
"""

import enum

from sqlalchemy import Column, Enum, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from .database import Base

# --- Enums for Model Fields ---


class UserRole(str, enum.Enum):
    """Define the possible roles for a user in the system.

    Attributes:
        CUSTOMER (str): Represents a customer user.
        OWNER (str): Represents a project owner user.

    """

    CUSTOMER = "customer"
    OWNER = "owner"


class RequirementType(str, enum.Enum):
    """Define the type of a requirement.

    Attributes:
        MUST_HAVE (str): Indicates a mandatory requirement.
        NICE_TO_HAVE (str): Indicates an optional or desirable requirement.

    """

    MUST_HAVE = "must_have"
    NICE_TO_HAVE = "nice_to_have"


class RequirementStatus(str, enum.Enum):
    """Define the current status of a requirement.

    Attributes:
        PENDING (str): The requirement is awaiting work.
        IN_PROGRESS (str): The requirement is currently being worked on.
        DONE (str): The requirement has been completed.

    """

    PENDING = "pending"
    IN_PROGRESS = "in_PROGRESS"
    DONE = "done"


# --- SQLAlchemy Models ---


class User(Base):
    """SQLAlchemy model for a User.

    Represents a user in the system, who can be either a Customer or an Owner.

    Attributes:
        id (int): Primary key, unique identifier for the user.
        username (str): Unique username for the user.
        email (str): Unique email address for the user.
        hashed_password (str): Hashed password for security.
        role (UserRole): The role of the user (Customer or Owner).
        projects (list[Project]): Relationship to projects owned by this user.

    """

    __tablename__ = "users"

    id: int = Column(Integer, primary_key=True, index=True)
    username: str = Column(String, unique=True, index=True, nullable=False)
    email: str = Column(String, unique=True, index=True, nullable=False)
    hashed_password: str = Column(String, nullable=False)
    role: UserRole = Column(Enum(UserRole), default=UserRole.CUSTOMER, nullable=False)

    projects = relationship("Project", back_populates="owner")

    def __repr__(self) -> str:
        """Provide a string representation for debugging.

        Returns:
            str: A string representation of the User object.

        """
        return (f"<User(id={self.id}, username='{self.username}', "
                f"role='{self.role.value}')>")


class Project(Base):
    """SQLAlchemy model for a Project.

    Each project is associated with an Owner (User).

    Attributes:
        id (int): Primary key, unique identifier for the project.
        name (str): Name of the project.
        description (str | None): Optional detailed description of the project.
        owner_id (int): Foreign key linking to the `User` table, representing
            the owner of the project.
        owner (User): Relationship to the `User` object that owns this project.
        requirements (list[Requirement]): Relationship to requirements
            belonging to this project.

    """

    __tablename__ = "projects"

    id: int = Column(Integer, primary_key=True, index=True)
    name: str = Column(String, index=True, nullable=False)
    description: str = Column(String, nullable=True)

    owner_id: int = Column(Integer, ForeignKey("users.id"), nullable=False)

    owner = relationship("User", back_populates="projects")
    requirements = relationship(
        "Requirement", back_populates="project", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        """Provide a string representation for debugging.

        Returns:
            str: A string representation of the Project object.

        """
        return f"<Project(id={self.id}, name='{self.name}', owner_id={self.owner_id})>"


class Requirement(Base):
    """SQLAlchemy model for a Requirement.

    Each requirement belongs to a specific Project.

    Attributes:
        id (int): Primary key, unique identifier for the requirement.
        description (str): Detailed description of the requirement.
        type (RequirementType): The type of the requirement (e.g., must-have,
            nice-to-have).
        status (RequirementStatus): The current status of the requirement
            (e.g., pending, in-progress, done).
        project_id (int): Foreign key linking to the `Project` table.
        project (Project): Relationship to the `Project` object this
            requirement belongs to.

    """

    __tablename__ = "requirements"

    id: int = Column(Integer, primary_key=True, index=True)
    description: str = Column(String, nullable=False)
    type: RequirementType = Column(
        Enum(RequirementType), default=RequirementType.MUST_HAVE, nullable=False
    )
    status: RequirementStatus = Column(
        Enum(RequirementStatus), default=RequirementStatus.PENDING, nullable=False
    )

    project_id: int = Column(Integer, ForeignKey("projects.id"), nullable=False)

    project = relationship("Project", back_populates="requirements")

    def __repr__(self) -> str:
        """Provide a string representation for debugging.

        Returns:
            str: A string representation of the Requirement object.

        """
        return (f"<Requirement(id={self.id}, project_id={self.project_id}, "
                f"status='{self.status.value}')>")