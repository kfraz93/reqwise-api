"""The module contains the Create, Read, Update, Delete (CRUD) operations
for the SQLAlchemy models (User, Project, Requirement).
"""

from sqlalchemy.orm import Session

from . import models, schemas

# --- User CRUD Operations ---


def get_user_by_email(db: Session, email: str) -> models.User | None:
    """Retrieve a user by their email address.

    Args:
        db (Session): The database session.
        email (str): The email address of the user to retrieve.

    Returns:
        models.User | None: The user object if found, otherwise None.

    """
    return db.query(models.User).filter(models.User.email == email).first()


def get_user_by_username(db: Session, username: str) -> models.User | None:
    """Retrieve a user by their username.

    Args:
        db (Session): The database session.
        username (str): The username of the user to retrieve.

    Returns:
        models.User | None: The user object if found, otherwise None.

    """
    return db.query(models.User).filter(models.User.username == username).first()


def create_user(
    db: Session, user_create: schemas.UserCreate, hashed_password: str
) -> models.User:
    """Create a new user in the database.

    Args:
        db (Session): The database session.
        user_create (schemas.UserCreate): Pydantic schema with user data.
        hashed_password (str): The hashed password for the user.

    Returns:
        models.User: The newly created user object.

    """
    db_user = models.User(
        username=user_create.username,
        email=user_create.email,
        hashed_password=hashed_password,
        role=user_create.role,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


# --- Project CRUD Operations ---


def create_project(
    db: Session, project: schemas.ProjectCreate, owner_id: int
) -> models.Project:
    """Create a new project associated with an owner.

    Args:
        db (Session): The database session.
        project (schemas.ProjectCreate): Pydantic schema with project data.
        owner_id (int): The ID of the user who will own this project.

    Returns:
        models.Project: The newly created project object.

    """
    db_project = models.Project(
        name=project.name, description=project.description, owner_id=owner_id
    )
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


def get_project(db: Session, project_id: int) -> models.Project | None:
    """Retrieve a project by its ID.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project to retrieve.

    Returns:
        models.Project | None: The project object if found, otherwise None.

    """
    return db.query(models.Project).filter(models.Project.id == project_id).first()


def get_projects_by_owner(
    db: Session, owner_id: int, skip: int = 0, limit: int = 100
) -> list[models.Project]:
    """Retrieve projects owned by a specific user.

    Args:
        db (Session): The database session.
        owner_id (int): The ID of the owner.
        skip (int): The number of records to skip for pagination. Defaults to 0.
        limit (int): The maximum number of records to return. Defaults to 100.

    Returns:
        list[models.Project]: A list of project objects.

    """
    return (
        db.query(models.Project)
        .filter(models.Project.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_all_projects(
    db: Session, skip: int = 0, limit: int = 100
) -> list[models.Project]:
    """Retrieve all projects in the database.

    Args:
        db (Session): The database session.
        skip (int): The number of records to skip for pagination. Defaults to 0.
        limit (int): The maximum number of records to return. Defaults to 100.

    Returns:
        list[models.Project]: A list of all project objects.

    """
    return db.query(models.Project).offset(skip).limit(limit).all()


# --- Requirement CRUD Operations ---


def create_project_requirement(
    db: Session, requirement: schemas.RequirementCreate, project_id: int
) -> models.Requirement:
    """Create a new requirement for a specific project.

    Args:
        db (Session): The database session.
        requirement (schemas.RequirementCreate): Pydantic schema with
            requirement data.
        project_id (int): The ID of the project to associate the requirement
            with.

    Returns:
        models.Requirement: The newly created requirement object.

    """
    db_requirement = models.Requirement(
        description=requirement.description,
        type=requirement.type,
        project_id=project_id,
    )
    db.add(db_requirement)
    db.commit()
    db.refresh(db_requirement)
    return db_requirement


def get_requirement(db: Session, requirement_id: int) -> models.Requirement | None:
    """Retrieve a requirement by its ID.

    Args:
        db (Session): The database session.
        requirement_id (int): The ID of the requirement to retrieve.

    Returns:
        models.Requirement | None: The requirement object if found, otherwise
            None.

    """
    return (
        db.query(models.Requirement)
        .filter(models.Requirement.id == requirement_id)
        .first()
    )


def update_requirement(
    db: Session,
    db_requirement: models.Requirement,
    requirement_update: schemas.RequirementUpdate,
) -> models.Requirement:
    """Update an existing requirement's details.

    Args:
        db (Session): The database session.
        db_requirement (models.Requirement): The SQLAlchemy requirement object
            to update.
        requirement_update (schemas.RequirementUpdate): Pydantic schema with
            updated requirement data.

    Returns:
        models.Requirement: The updated requirement object.

    """
    if requirement_update.description is not None:
        db_requirement.description = requirement_update.description
    if requirement_update.type is not None:
        db_requirement.type = requirement_update.type
    db.commit()
    db.refresh(db_requirement)
    return db_requirement


def update_requirement_status(
    db: Session,
    db_requirement: models.Requirement,
    new_status: schemas.RequirementStatusUpdate,
) -> models.Requirement:
    """Update an existing requirement's status.

    Args:
        db (Session): The database session.
        db_requirement (models.Requirement): The SQLAlchemy requirement object
            to update.
        new_status (schemas.RequirementStatusUpdate): Pydantic schema with the
            new status value.

    Returns:
        models.Requirement: The updated requirement object.

    """
    db_requirement.status = new_status.status
    db.commit()
    db.refresh(db_requirement)
    return db_requirement


def delete_requirement(db: Session, requirement_id: int) -> bool:
    """Delete a requirement by its ID.

    Args:
        db (Session): The database session.
        requirement_id (int): The ID of the requirement to delete.

    Returns:
        bool: True if the requirement was deleted, False otherwise.

    """
    db_requirement = (
        db.query(models.Requirement)
        .filter(models.Requirement.id == requirement_id)
        .first()
    )
    if db_requirement:
        db.delete(db_requirement)
        db.commit()
        return True
    return False


def get_requirements_by_project(
    db: Session, project_id: int, skip: int = 0, limit: int = 100
) -> list[models.Requirement]:
    """Retrieve all requirements for a specific project.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project whose requirements to retrieve.
        skip (int): The number of records to skip for pagination. Defaults to 0.
        limit (int): The maximum number of records to return. Defaults to 100.

    Returns:
        list[models.Requirement]: A list of requirement objects.

    """
    return (
        db.query(models.Requirement)
        .filter(models.Requirement.project_id == project_id)
        .offset(skip)
        .limit(limit)
        .all()
    )