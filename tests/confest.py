# tests/conftest.py
"""Contains pytest fixtures for setting up the test environment.

It includes fixtures for a test database and a FastAPI test client.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker  # Import Session for type hinting

# Import Base and get_db from your app's database module
from app.database import Base, get_db

# Import your main FastAPI application
from app.main import app

# Define a URL for the test database.
# Using a temporary in-memory SQLite database for fast, isolated tests.
TEST_DATABASE_URL = "sqlite:///./test_reqwise.db"


@pytest.fixture(name="test_engine")
def test_engine_fixture():
    """Provide a SQLAlchemy engine for the test database.

    Returns:
        sqlalchemy.engine.Engine: The SQLAlchemy engine configured for the
            test database.

    """
    return create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})


@pytest.fixture(name="test_session")
def test_session_fixture(test_engine) -> Session:
    """Provide a SQLAlchemy session for the test database.

    It creates and drops tables for each test, ensuring a clean state.

    Args:
        test_engine (sqlalchemy.engine.Engine): The SQLAlchemy engine fixture.

    Yields:
        Session: A SQLAlchemy database session for testing.

    """
    # Create all tables before the tests run
    Base.metadata.create_all(bind=test_engine)
    TestingSessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=test_engine
    )
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        # Drop all tables after the tests are done to clean up
        db.close()
        Base.metadata.drop_all(bind=test_engine)


@pytest.fixture(name="client")
def client_fixture(test_session: Session) -> TestClient:
    """Provide a FastAPI TestClient configured to use the test database.

    This allows testing API endpoints without running a live server.

    Args:
        test_session (Session): The SQLAlchemy session fixture for testing.

    Yields:
        TestClient: A FastAPI test client instance.

    """

    def override_get_db():
        """Override the get_db dependency to use the test session.

        Yields:
            Session: The test database session.

        """
        try:
            yield test_session
        finally:
            test_session.close()

    # Override the get_db dependency in the main app
    app.dependency_overrides[get_db] = override_get_db

    # Create a TestClient instance for the FastAPI app
    with TestClient(app) as c:
        yield c

    # Clean up the override after tests
    app.dependency_overrides.clear()