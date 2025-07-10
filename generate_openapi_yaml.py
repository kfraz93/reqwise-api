# generate_openapi_yaml.py
"""
This script fetches the OpenAPI JSON schema from a running FastAPI application
and converts it into a YAML file (openapi.yaml).
"""

import httpx
import yaml
import json
import os

# Define the URL of your FastAPI application's OpenAPI JSON endpoint
# Make sure your FastAPI app is running on this address and port
FASTAPI_OPENAPI_URL = "http://127.0.0.1:8000/openapi.json"
OUTPUT_FILE_NAME = "openapi.yaml"

def generate_openapi_yaml():
    """
    Fetches the OpenAPI JSON from the FastAPI app and saves it as YAML.
    """
    print(f"Attempting to fetch OpenAPI schema from: {FASTAPI_OPENAPI_URL}")
    try:
        # Make an HTTP GET request to the OpenAPI JSON endpoint
        response = httpx.get(FASTAPI_OPENAPI_URL)
        response.raise_for_status()  # Raise an exception for HTTP errors (4xx or 5xx)

        # Parse the JSON response
        openapi_json_data = response.json()

        # Save the JSON data as a YAML file
        with open(OUTPUT_FILE_NAME, "w", encoding="utf-8") as f:
            # Use yaml.dump to write the Python dictionary to a YAML file
            # sort_keys=False preserves the order of keys as much as possible,
            # which is often preferred for OpenAPI schemas.
            yaml.dump(openapi_json_data, f, sort_keys=False)

        print(f"Successfully generated {OUTPUT_FILE_NAME} in the project root.")

    except httpx.RequestError as e:
        print(f"Error connecting to FastAPI app: {e}")
        print("Please ensure your FastAPI application is running at "
              f"{FASTAPI_OPENAPI_URL.replace('/openapi.json', '')}")
    except json.JSONDecodeError:
        print("Error: Could not decode JSON response from FastAPI app. "
              "Is the endpoint returning valid JSON?")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    generate_openapi_yaml()