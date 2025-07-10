# app/routers/projects.py
"""The module defines the API routes for managing projects.
It includes endpoints for both 'Owner' and 'Customer' roles.
"""

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..crud import create_project, get_all_projects, get_projects_by_owner
from ..database import get_db
from ..security import (  # Import both owner and customer dependencies
    get_current_customer,
    get_current_owner,
)

router = APIRouter(
    prefix="/projects",
    tags=["Projects"],
)

# --- Owner Endpoints ---


@router.post(
    "/",
    response_model=schemas.ProjectOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project (Owner only)",
    description="Allows an authenticated owner to create a new project.",
)
async def create_project_for_owner(
    project: schemas.ProjectCreate,
    current_owner: models.User = Depends(
        get_current_owner
    ),  # Ensures only owners can create
    db: Session = Depends(get_db),
):
    """Creates a new project.

    The project will be automatically associated with the authenticated owner.

    Args:
        project (schemas.ProjectCreate): The project data provided in the request body.
        current_owner (models.User): The authenticated owner user object.
        db (Session): The database session dependency.

    Returns:
        schemas.ProjectOut: The newly created project's data.

    """
    db_project = create_project(db=db, project=project, owner_id=current_owner.id)
    return db_project


@router.get(
    "/owner",  # Changed path to /owner to distinguish from customer's /projects/
    response_model=list[schemas.ProjectOut],
    summary="Get all projects for the current owner (Owner only)",
    description="Retrieves a list of all projects owned by the authenticated owner.",
)
async def read_projects_for_owner(
    current_owner: models.User = Depends(
        get_current_owner
    ),  # Ensures only owners can view their projects
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Retrieves a list of projects owned by the authenticated owner.

    Args:
        current_owner (models.User): The authenticated owner user object.
        db (Session): The database session dependency.
        skip (int): Number of items to skip (for pagination).
        limit (int): Maximum number of items to return (for pagination).

    Returns:
        List[schemas.ProjectOut]: A list of project data.

    """
    projects = get_projects_by_owner(
        db, owner_id=current_owner.id, skip=skip, limit=limit
    )
    return projects


# --- Customer Endpoints ---


@router.get(
    "/",  # This is the general /projects/ endpoint for customers
    response_model=list[schemas.ProjectOut],
    summary="Get all projects (Customer or Owner)",
    description="Retrieves a list of all projects available in the system. "
    "Accessible by both customers and owners.",
)
async def read_all_projects(
    current_user: models.User = Depends(
        get_current_customer
    ),  # Ensures authentication as customer (or owner via get_current_user)
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Retrieves a list of all projects in the system.

    Args:
        current_user (models.User): The authenticated user object (customer or owner).
        db (Session): The database session dependency.
        skip (int): Number of items to skip (for pagination).
        limit (int): Maximum number of items to return (for pagination).

    Returns:
        List[schemas.ProjectOut]: A list of all project data.

    """
    # For simplicity, customers can view all projects.
    # In a more complex app, you'd filter based on customer's association with projects.
    projects = get_all_projects(db, skip=skip, limit=limit)
    return projects
