# tests/unit_tests/test_owner_access.py
"""Unit tests for owner-specific API access.

This module contains tests for project and requirement management
functionalities accessible to users with the 'Owner' role.
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


# --- Helper functions ---
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


# --- End Helper functions ---


# --- Project Management Tests (Owner) ---


def test_owner_can_create_project(client: TestClient, test_session: Session):
    """Verify that an owner can successfully create a project.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner1",
        "owner1@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")

    project_data = {"name": "New Project", "description": "A project created by owner."}
    response = client.post(
        "/projects/",
        json=project_data,
        headers={"Authorization": f"Bearer {owner_token}"},
    )

    assert response.status_code == 201
    created_project = response.json()
    assert created_project["name"] == project_data["name"]
    assert created_project["description"] == project_data["description"]
    assert created_project["owner_id"] == owner_user.id
    assert "id" in created_project


def test_customer_cannot_create_project(client: TestClient, test_session: Session):
    """Verify that a customer cannot create a project.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    customer_user = create_test_user(
        test_session,
        "customer1",
        "customer1@example.com",
        "securepass",
        models.UserRole.CUSTOMER,
    )
    customer_token = get_auth_token(client, customer_user.email, "securepass")

    project_data = {"name": "Customer Project Attempt", "description": "Should fail"}
    response = client.post(
        "/projects/",
        json=project_data,
        headers={"Authorization": f"Bearer {customer_token}"},
    )
    assert response.status_code == 403  # Forbidden


def test_owner_can_read_their_projects(client: TestClient, test_session: Session):
    """Verify that an owner can retrieve only their own projects.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner2",
        "owner2@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")
    project1 = create_test_project(
        test_session, "Owner2 Project A", "Desc A", owner_user.id
    )
    project2 = create_test_project(
        test_session, "Owner2 Project B", "Desc B", owner_user.id
    )

    # Create another owner and their project, which should not be returned
    other_owner = create_test_user(
        test_session,
        "other_owner",
        "other@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    create_test_project(
        test_session, "Other Owner Project", "Desc Other", other_owner.id
    )

    response = client.get(
        "/projects/owner",  # Specific endpoint for owner's projects
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 200
    projects_data = response.json()
    assert len(projects_data) == 2
    assert any(p["id"] == project1.id for p in projects_data)
    assert any(p["id"] == project2.id for p in projects_data)
    assert all(p["owner_id"] == owner_user.id for p in projects_data)


# --- Requirement Management Tests (Owner) ---


def test_owner_can_create_requirement_for_their_project(
    client: TestClient, test_session: Session
):
    """Verify that an owner can create a requirement for a project they own.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner3",
        "owner3@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")
    project = create_test_project(
        test_session, "Project for Requirements", "Desc", owner_user.id
    )

    req_data = {"description": "Must have login feature", "type": "must_have"}
    response = client.post(
        f"/projects/{project.id}/requirements/",
        json=req_data,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 201
    created_req = response.json()
    assert created_req["description"] == req_data["description"]
    assert created_req["type"] == req_data["type"]
    assert created_req["project_id"] == project.id
    assert created_req["status"] == "pending"  # Default status


def test_owner_cannot_create_requirement_for_other_owners_project(
    client: TestClient, test_session: Session
):
    """Verify that an owner cannot create a requirement for a project they
    don't own.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner4",
        "owner4@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")

    other_owner = create_test_user(
        test_session,
        "other_owner4",
        "other4@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    other_project = create_test_project(
        test_session, "Other's Project", "Desc", other_owner.id
    )

    req_data = {
        "description": "Attempt to add to other's project",
        "type": "nice_to_have",
    }
    response = client.post(
        f"/projects/{other_project.id}/requirements/",
        json=req_data,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 403  # Forbidden


def test_owner_can_update_requirement(client: TestClient, test_session: Session):
    """Verify that an owner can update a requirement they own.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner5",
        "owner5@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")
    project = create_test_project(
        test_session, "Project for Update", "Desc", owner_user.id
    )
    req = create_test_requirement(
        test_session,
        project.id,
        "Original Desc",
        models.RequirementType.MUST_HAVE,
        models.RequirementStatus.PENDING,
    )

    update_data = {"description": "Updated description", "type": "nice_to_have"}
    response = client.put(
        f"/requirements/{req.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 200
    updated_req = response.json()
    assert updated_req["description"] == update_data["description"]
    assert updated_req["type"] == update_data["type"]


def test_owner_can_update_requirement_status(client: TestClient, test_session: Session):
    """Verify that an owner can update the status of a requirement they own.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner6",
        "owner6@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")
    project = create_test_project(
        test_session, "Project for Status Update", "Desc", owner_user.id
    )
    req = create_test_requirement(
        test_session,
        project.id,
        "Req for Status",
        models.RequirementType.MUST_HAVE,
        models.RequirementStatus.PENDING,
    )

    status_data = {"status": "in_progress"}
    response = client.patch(
        f"/requirements/{req.id}/status",
        json=status_data,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 200
    updated_req = response.json()
    assert updated_req["status"] == status_data["status"]


def test_owner_can_delete_requirement(client: TestClient, test_session: Session):
    """Verify that an owner can delete a requirement they own.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner7",
        "owner7@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")
    project = create_test_project(
        test_session, "Project for Delete", "Desc", owner_user.id
    )
    req = create_test_requirement(
        test_session,
        project.id,
        "Req to Delete",
        models.RequirementType.MUST_HAVE,
        models.RequirementStatus.PENDING,
    )

    response = client.delete(
        f"/requirements/{req.id}", headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert response.status_code == 204  # No Content

    # Verify it's actually deleted
    response_get = client.get(
        f"/projects/{project.id}/requirements/",
        headers={"Authorization": f"Bearer {owner_token}"}
    )
    assert response_get.status_code == 200
    assert len(response_get.json()) == 0


def test_owner_cannot_update_other_owners_requirement(
    client: TestClient, test_session: Session
):
    """Verify that an owner cannot update a requirement owned by another owner.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner8",
        "owner8@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")

    other_owner = create_test_user(
        test_session,
        "other_owner8",
        "other8@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    other_project = create_test_project(
        test_session, "Other's Project for Req Update", "Desc", other_owner.id
    )
    other_req = create_test_requirement(
        test_session,
        other_project.id,
        "Other's Req",
        models.RequirementType.MUST_HAVE,
        models.RequirementStatus.PENDING,
    )

    update_data = {"description": "Attempt to update other's req"}
    response = client.put(
        f"/requirements/{other_req.id}",
        json=update_data,
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 403  # Forbidden


def test_owner_cannot_delete_other_owners_requirement(
    client: TestClient, test_session: Session
):
    """Verify that an owner cannot delete a requirement owned by another owner.

    Args:
        client (TestClient): The FastAPI test client.
        test_session (Session): The database session for testing.

    """
    owner_user = create_test_user(
        test_session,
        "owner9",
        "owner9@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    owner_token = get_auth_token(client, owner_user.email, "securepass")

    other_owner = create_test_user(
        test_session,
        "other_owner9",
        "other9@example.com",
        "securepass",
        models.UserRole.OWNER,
    )
    other_project = create_test_project(
        test_session, "Other's Project for Req Delete", "Desc", other_owner.id
    )
    other_req = create_test_requirement(
        test_session,
        other_project.id,
        "Other's Req",
        models.RequirementType.MUST_HAVE,
        models.RequirementStatus.PENDING,
    )

    response = client.delete(
        f"/requirements/{other_req.id}",
        headers={"Authorization": f"Bearer {owner_token}"},
    )
    assert response.status_code == 403  # Forbidden