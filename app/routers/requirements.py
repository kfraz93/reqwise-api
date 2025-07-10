# app/routers/requirements.py
"""The module defines the API routes for managing requirements.
It includes endpoints for both 'Owner' and 'Customer' roles.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from .. import models, schemas
from ..crud import (
    create_project_requirement,
    delete_requirement,
    get_project,
    get_requirement,
    get_requirements_by_project,
    update_requirement,
    update_requirement_status,
)
from ..database import get_db
from ..security import (  # Import both owner and customer dependencies
    get_current_customer,
    get_current_owner,
)

router = APIRouter(
    tags=["Requirements"],
)

# --- Owner Endpoints ---


@router.post(
    "/projects/{project_id}/requirements/",
    response_model=schemas.RequirementOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new requirement for a project (Owner only)",
    description="Allows owner to create requirement for a project they own.",
)
async def create_requirement_for_project(
    project_id: int,
    requirement: schemas.RequirementCreate,
    current_owner: models.User = Depends(
        get_current_owner
    ),  # Ensures only owners can create
    db: Session = Depends(get_db),
):
    """Creates a new requirement for a specified project.

    Args:
        project_id (int): The ID of the project to add the requirement to.
        requirement (schemas.RequirementCreate): The requirement data.
        current_owner (models.User): The authenticated owner user object.
        db (Session): The database session dependency.

    Returns:
        schemas.RequirementOut: The newly created requirement's data.

    Raises:
        HTTPException: Misisng project or owner.

    """
    db_project = get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )
    if db_project.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to add requirements to this project",
        )

    db_requirement = create_project_requirement(
        db=db, requirement=requirement, project_id=project_id
    )
    return db_requirement


@router.put(
    "/requirements/{requirement_id}",
    response_model=schemas.RequirementOut,
    summary="Update a requirement (Owner only)",
    description="Allows the owner to update the requirement.",
)
async def update_single_requirement(
    requirement_id: int,
    requirement_update: schemas.RequirementUpdate,
    current_owner: models.User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Updates an existing requirement.

    Args:
        requirement_id (int): The ID of the requirement to update.
        requirement_update (schemas.RequirementUpdate): The updated requirement data.
        current_owner (models.User): The authenticated owner user object.
        db (Session): The database session dependency.

    Returns:
        schemas.RequirementOut: The updated requirement's data.

    Raises:
        HTTPException: Missing requirement or the owner.

    """
    db_requirement = get_requirement(db, requirement_id=requirement_id)
    if not db_requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found"
        )

    db_project = get_project(db, project_id=db_requirement.project_id)
    if not db_project or db_project.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this requirement",
        )

    updated_requirement = update_requirement(
        db=db, db_requirement=db_requirement, requirement_update=requirement_update
    )
    return updated_requirement


@router.patch(
    "/requirements/{requirement_id}/status",
    response_model=schemas.RequirementOut,
    summary="Update requirement status (Owner only)",
    description="Allows an authenticated owner to change the status of requirement.",
)
async def update_single_requirement_status(
    requirement_id: int,
    status_update: schemas.RequirementStatusUpdate,
    current_owner: models.User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Updates the status of an existing requirement.

    Args:
        requirement_id (int): The ID of the requirement to update.
        status_update (schemas.RequirementStatusUpdate): The new status data.
        current_owner (models.User): The authenticated owner user object.
        db (Session): The database session dependency.

    Returns:
        schemas.RequirementOut: The requirement's data with the updated status.

    Raises:
        HTTPException: Missing requirement or owner.

    """
    db_requirement = get_requirement(db, requirement_id=requirement_id)
    if not db_requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found"
        )

    db_project = get_project(db, project_id=db_requirement.project_id)
    if not db_project or db_project.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this requirement's status",
        )

    updated_requirement = update_requirement_status(
        db=db, db_requirement=db_requirement, new_status=status_update
    )
    return updated_requirement


@router.delete(
    "/requirements/{requirement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a requirement (Owner only)",
    description="Allows an authenticated owner to delete a specific requirement.",
)
async def delete_single_requirement(
    requirement_id: int,
    current_owner: models.User = Depends(get_current_owner),
    db: Session = Depends(get_db),
):
    """Deletes an existing requirement.

    Args:
        requirement_id (int): The ID of the requirement to delete.
        current_owner (models.User): The authenticated owner user object.
        db (Session): The database session dependency.

    Raises:
        HTTPException: Missing requirement or the owner.

    """
    db_requirement = get_requirement(db, requirement_id=requirement_id)
    if not db_requirement:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Requirement not found"
        )

    db_project = get_project(db, project_id=db_requirement.project_id)
    if not db_project or db_project.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to delete this requirement",
        )

    delete_requirement(db=db, requirement_id=requirement_id)
    return {"message": "Requirement deleted successfully"}


# --- Customer Endpoints ---


@router.get(
    "/projects/{project_id}/requirements/",
    response_model=list[schemas.RequirementOut],
    summary="Get requirements for a specific project (Customer or Owner)",
    description="Retrieves a list of requirements for a given project. "
    "Accessible by both customers and owners.",
)
async def read_requirements_for_project(
    project_id: int,
    current_user: models.User = Depends(
        get_current_customer
    ),  # Authenticates as customer (or owner)
    db: Session = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
):
    """Retrieves a list of requirements for a specific project.

    Args:
        project_id (int): The ID of the project to retrieve requirements for.
        current_user (models.User): The authenticated user object (customer or owner).
        db (Session): The database session dependency.
        skip (int): Number of items to skip (for pagination).
        limit (int): Maximum number of items to return (for pagination).

    Returns:
        List[schemas.RequirementOut]: A list of requirement data for the project.

    Raises:
        HTTPException: If the project is not found.

    """
    db_project = get_project(db, project_id=project_id)
    if not db_project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Project not found"
        )

    # For simplicity, customers can view requirements for any existing project.
    # In a more complex app, you'd filter based on customer's association with projects.
    requirements = get_requirements_by_project(
        db, project_id=project_id, skip=skip, limit=limit
    )
    return requirements
