# ReqWise API

A FastAPI application for customer requirement gathering and management.

This API provides functionalities for user authentication (registration, login),
project management by owners, and requirement tracking for both owners and
customers.

## Getting Started

Follow these steps to set up and run the ReqWise API locally.

### Prerequisites

* Python 3.12+ installed.
* `uv` (or `pip`) for dependency management. If you don't have `uv`, install it:
    ```bash
    pip install uv
    ```

### Installation

1.  **Clone the repository:**
    ```bash
    git clone [https://github.com/your-username/reqwise-api.git](https://github.com/your-username/reqwise-api.git)
    cd reqwise-api
    ```
2.  **Create a virtual environment and install dependencies using `uv`:**
    ```bash
    uv sync
    ```

### Environment Variables

Create a `.env` file in the project root directory based on `.env.example`.
This file will store sensitive information and configuration.

**`.env.example` content:**

**Important:** Replace `<GENERATE_A_LONG_RANDOM_STRING_HERE>` with a strong,
random string for `SECRET_KEY` in your actual `.env` file.

### Running the Application

1.  **Start the FastAPI development server:**
    This will also create the SQLite database file (`reqwise.db`) and
    initialize tables on first run.
    ```bash
    uv run uvicorn app.main:app --reload
    ```
    The API will be accessible at `http://127.0.0.1:8000`.

2.  **Access API Documentation:**
    * **Interactive Swagger UI:** `http://127.0.0.1:8000/docs`
    * **Redoc UI:** `http://127.0.0.1:8000/redoc`

## API Documentation & Schema Generation

### Generate OpenAPI YAML

You can generate the OpenAPI specification in YAML format for your API.
Ensure the FastAPI application is running before executing this command.

```bash
uv run python generate_openapi_yaml.py
```
This will create an `openapi.yaml` file in your project root.
You can inspect this file to understand all API endpoints, request/response
schemas, and authentication methods.

For a direct view of the generated schema, click here: [openapi.yaml](./openapi.yaml)
## Code Quality & Linting

This project uses `Ruff` for linting and formatting.

* **Run Ruff lint check:**
    ```bash
    uv run ruff check .
    ```
* **Run Ruff lint check and automatically fix issues:**
    ```bash
    uv run ruff check . --fix
    ```
* **Run Ruff formatter:**
    ```bash
    uv run ruff format .
    ```