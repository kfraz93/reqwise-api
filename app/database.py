# app/database.py
"""The module sets up the SQLAlchemy engine, session, and base for database
interaction. It also includes a dependency function to provide a database
session to FastAPI routes.
"""

import os

from dotenv import load_dotenv  # Import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import declarative_base, sessionmaker

# Load environment variables from .env file
load_dotenv()

# Define the path for the SQLite database file from environment variable
# Fallback to default if not set (though it should be in .env)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./reqwise.db")

# Create the SQLAlchemy engine.
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
)

# Create a SessionLocal class.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create a Base class for declarative models.
Base = declarative_base()


def get_db():
    """Provide a database session to FastAPI routes.

    This function is a dependency that yields a database session. It ensures
    the session is properly closed after the request is finished, and handles
    transaction rollbacks on errors.

    Yields:
        Session: A SQLAlchemy database session.

    Raises:
        SQLAlchemyError: If a database error occurs during session use.

    """
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        print(f"Database error occurred: {e}")
        raise
    finally:
        db.close()


def create_db_tables():
    """Create all defined database tables based on the SQLAlchemy models.

    This function should be called on application startup (e.g., in main.py).
    It inspects `Base.metadata` and creates tables for all declared models
    if they do not already exist.
    """
    try:
        # Import models here to ensure they are registered with Base
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully or already exist.")
    except Exception as e:
        print(f"Error creating database tables: {e}")