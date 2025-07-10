# app/main.py
"""The main application file for the ReqWise API.
It initializes the FastAPI application, includes API routers,
and handles application-wide events like database table creation.
"""

from contextlib import asynccontextmanager

from fastapi import FastAPI

# Import the database functions
from .database import create_db_tables

# Import the routers
from .routers import projects, requirements, users


# Define an asynchronous context manager for application lifespan events.
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown events.

    On startup, it creates database tables.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        None

    """
    print("Application startup: Creating database tables...")
    create_db_tables()
    print("Database tables created or already exist.")
    yield
    print("Application shutdown.")


# Initialize the FastAPI application with the defined lifespan.
app = FastAPI(
    title="ReqWise API",
    description="API for managing customer project requirements.",
    version="0.1.0",
    lifespan=lifespan,
)

# Include the routers.
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(requirements.router)


# You can add a simple root endpoint for testing purposes
@app.get("/")
async def read_root():
    """Retrieve a welcome message from the root endpoint.

    Returns:
        dict[str, str]: A dictionary containing a welcome message.

    """
    return {"message": "Welcome to ReqWise API!"}