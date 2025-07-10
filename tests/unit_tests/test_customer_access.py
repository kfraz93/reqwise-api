# tests/unit_tests/test_customer_access.py
"""Unit tests for customer-specific API access, including viewing projects
and requirements.
"""

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app import (  # Import necessary modules for setup and assertions
    crud,
    models,
    schemas,
    security,
)

# The 'client' and 'test_session' fixtures are provided by tests/conftest.py


def create_test_user(
    db: Session, username: str, email: str, password: str, role: models.UserRole
) -> models.User:
    """Create a user for testing.

    Args:
        db (Session): The database session.
        username (str): The username of the user.
        email (str): The email of the user.
        password (str): The plain-text password of the user.
        role (models.UserRole): The role of the user (CUSTOMER or OWNER).

    Returns:
        models.User: The created user object.

    """
    hashed_password = security.get_password_hash(password)
    user_create = schemas.UserCreate(
        username=username, email=email, password=password, role=role
    )
    return crud.create_user(db, user_create, hashed_password)


def get_auth_token(client: TestClient, username: str, password: str) -> str:
    """Get an authentication token for a user.

    Args:
        client (TestClient): The FastAPI test client.
        username (str): The username of the user.
        password (str): The password of the user.

    Returns:
        str: The access token.

    """
    response = client.post(
        "/users/token", data={"username": username, "password": password}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def create_test_project(
    db: Session, name: str, description: str, owner_id: int
) -> models.Project:
    """Create a project for testing.

    Args:
        db (Session): The database session.
        name (str): The name of the project.
        description (str): The description of the project.
        owner_id (int): The ID of the owner user.

    Returns:
        models.Project: The created project object.

    """
    project_create = schemas.ProjectCreate(name=name, description=description)
    return crud.create_project(db, project_create, owner_id)


def create_test_requirement(
    db: Session,
    project_id: int,
    description: str,
    req_type: models.RequirementType,
    status: models.RequirementStatus,
) -> models.Requirement:
    """Create a requirement for testing.

    Args:
        db (Session): The database session.
        project_id (int): The ID of the project the requirement belongs to.
        description (str): The description of the requirement.
        req_type (models.RequirementType): The type of the requirement.
        status (models.RequirementStatus): The status of the requirement.

    Returns:
        models.Requirement: The created requirement object.

    """
    requirement_create = schemas.RequirementCreate(
        description=description, type=req_type
    )
    db_req = crud.create_project_requirement(db, requirement_create, project_id)
    # Manually update status if different from default
    if db_req.status != status:
        db_req.status = status
        db.commit()
        db.refresh(db_req)
    return db_req


def test_customer_can_read_all_projects(client: TestClient, test_session: Session):
    """Verify that an authenticated customer can retrieve a list of all projects.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    # Create an owner and a project
    owner_user = create_test_user(
        test_session,
        "owner_cust_test",
        "owner_cust@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    project1 = create_test_project(
        test_session, "Customer Project 1", "Description 1", owner_user.id
    )
    project2 = create_test_project(
        test_session, "Customer Project 2", "Description 2", owner_user.id
    )

    # Create a customer user
    customer_user = create_test_user(
        test_session,
        "customer_test",
        "customer@example.com",
        "securepass",
        models.UserRole.CUSTOMER,
    )
    customer_token = get_auth_token(client, customer_user.email, "securepass")

    # Customer tries to get all projects
    response = client.get(
        "/projects/", headers={"Authorization": f"Bearer {customer_token}"}
    )

    assert response.status_code == 200
    projects_data = response.json()
    assert len(projects_data) == 2
    assert any(p["name"] == project1.name for p in projects_data)
    assert any(p["name"] == project2.name for p in projects_data)


def test_customer_can_read_requirements_for_any_project(
    client: TestClient, test_session: Session
):
    """Verify that an authenticated customer can read requirements for an
    existing project.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    # Create an owner and a project
    owner_user = create_test_user(
        test_session,
        "owner_req_test",
        "owner_req@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    project = create_test_project(
        test_session, "Requirements Project", "Project for requirements", owner_user.id
    )
    req1 = create_test_requirement(
        test_session,
        project.id,
        "Req 1 Desc",
        models.RequirementType.MUST_HAVE,
        models.RequirementStatus.PENDING,
    )
    req2 = create_test_requirement(
        test_session,
        project.id,
        "Req 2 Desc",
        models.RequirementType.NICE_TO_HAVE,
        models.RequirementStatus.IN_PROGRESS,
    )

    # Create a customer user
    customer_user = create_test_user(
        test_session,
        "customer_req_test",
        "customer@example.com",
        "securepass",
        models.UserRole.CUSTOMER,
    )
    customer_token = get_auth_token(client, customer_user.email, "securepass")

    # Customer tries to get requirements for the project
    response = client.get(
        f"/projects/{project.id}/requirements/",
        headers={"Authorization": f"Bearer {customer_token}"},
    )

    assert response.status_code == 200
    requirements_data = response.json()
    assert len(requirements_data) == 2
    assert any(r["description"] == req1.description for r in requirements_data)
    assert any(r["description"] == req2.description for r in requirements_data)
    assert all(r["project_id"] == project.id for r in requirements_data)


def test_customer_cannot_read_requirements_for_non_existent_project(
    client: TestClient, test_session: Session
):
    """Verify that a customer gets a 404 for a non-existent project's
    requirements.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    Returns:
        None

    """
    # Create a customer user
    customer_user = create_test_user(
        test_session,
        "customer_non_exist",
        "customer_non@example.com",
        "securepass",
        models.UserRole.CUSTOMER,
    )
    customer_token = get_auth_token(client, customer_user.email, "securepass")

    # Customer tries to get requirements for a non-existent project ID
    non_existent_project_id = 999
    response = client.get(
        f"/projects/{non_existent_project_id}/requirements/",
        headers={"Authorization": f"Bearer {customer_token}"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Project not found"


def test_unauthenticated_user_cannot_access_customer_endpoints(
    client: TestClient, test_session: Session
):
    """Verify that an unauthenticated user cannot access customer-specific
    endpoints.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    Returns:
        None

    """
    # Create an owner and a project
    owner_user = create_test_user(
        test_session,
        "owner_unauth",
        "owner_unauth@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    project = create_test_project(test_session, "Unauth Project", "Desc", owner_user.id)
    create_test_requirement(
        test_session,
        project.id,
        "Unauth Req",
        models.RequirementType.MUST_HAVE,
        models.RequirementStatus.PENDING,
    )

    # Try to access /projects/ without token
    response_projects = client.get("/projects/")
    assert response_projects.status_code == 401
    assert response_projects.json()["detail"] == "Not authenticated"

    # Try to access /projects/{project_id}/requirements/ without token
    response_requirements = client.get(f"/projects/{project.id}/requirements/")
    assert response_requirements.status_code == 401
    assert response_requirements.json()["detail"] == "Not authenticated"