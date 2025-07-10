# tests/unit_tests/test_users.py
"""Unit tests for the user authentication and registration API endpoints.

This module contains tests for user registration, login, and related error
conditions using the FastAPI TestClient.
"""

from fastapi.testclient import TestClient

# The 'client' fixture is automatically provided by tests/conftest.py
# The 'test_session' fixture is also available if you need direct DB access in tests


def test_create_user_success(client: TestClient):
    """Verify that a new user can be successfully registered.

    Args:
        client (TestClient): The FastAPI test client.

    """
    user_data = {
        "username": "testuser1",
        "email": "test1@example.com",
        "password": "securepassword123",
        "role": "customer",
    }
    response = client.post("/users/register", json=user_data)

    assert response.status_code == 201
    created_user = response.json()
    assert created_user["username"] == user_data["username"]
    assert created_user["email"] == user_data["email"]
    assert created_user["role"] == user_data["role"]
    assert "id" in created_user
    assert "hashed_password" not in created_user  # Ensure password is not returned


def test_create_user_duplicate_email(client: TestClient):
    """Verify that a user cannot be registered with an email that already
    exists.

    Args:
        client (TestClient): The FastAPI test client.

    """
    # First, register a user
    user_data = {
        "username": "testuser2",
        "email": "test2@example.com",
        "password": "securepassword123",
        "role": "customer",
    }
    client.post("/users/register", json=user_data)

    # Try to register another user with the same email
    duplicate_user_data = {
        "username": "anotheruser",
        "email": "test2@example.com",  # Duplicate email
        "password": "anotherpassword",
        "role": "customer",
    }
    response = client.post("/users/register", json=duplicate_user_data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Email already registered"


def test_create_user_duplicate_username(client: TestClient):
    """Verify that a user cannot be registered with a username that already
    exists.

    Args:
        client (TestClient): The FastAPI test client.

    """
    # First, register a user
    user_data = {
        "username": "testuser3",
        "email": "test3@example.com",
        "password": "securepassword123",
        "role": "customer",
    }
    client.post("/users/register", json=user_data)

    # Try to register another user with the same username
    duplicate_user_data = {
        "username": "testuser3",  # Duplicate username
        "email": "another@example.com",
        "password": "anotherpassword",
        "role": "customer",
    }
    response = client.post("/users/register", json=duplicate_user_data)

    assert response.status_code == 400
    assert response.json()["detail"] == "Username already taken"


def test_login_success(client: TestClient):
    """Verify that a user can successfully log in and receive an access token.

    Args:
        client (TestClient): The FastAPI test client.

    """
    # Register a user first for login
    register_data = {
        "username": "loginuser",
        "email": "login@example.com",
        "password": "loginpassword",
        "role": "customer",
    }
    client.post("/users/register", json=register_data)

    # Attempt to log in
    login_data = {"username": "loginuser", "password": "loginpassword"}
    response = client.post(
        "/users/token", data=login_data
    )  # Use 'data' for form-urlencoded

    assert response.status_code == 200
    token_response = response.json()
    assert "access_token" in token_response
    assert token_response["token_type"] == "bearer"
    assert isinstance(token_response["access_token"], str)
    assert len(token_response["access_token"]) > 0


def test_login_invalid_credentials(client: TestClient):
    """Verify that login fails with incorrect username or password.

    Args:
        client (TestClient): The FastAPI test client.

    """
    # Register a user
    register_data = {
        "username": "invalidloginuser",
        "email": "invalidlogin@example.com",
        "password": "correctpassword",
        "role": "customer",
    }
    client.post("/users/register", json=register_data)

    # Try login with wrong password
    login_data_wrong_pass = {
        "username": "invalidloginuser",
        "password": "wrongpassword",
    }
    response = client.post("/users/token", data=login_data_wrong_pass)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"

    # Try login with non-existent username
    login_data_non_existent = {"username": "nonexistentuser", "password": "anypassword"}
    response = client.post("/users/token", data=login_data_non_existent)
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect username or password"