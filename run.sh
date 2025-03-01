#!/bin/bash

# Install dependencies if needed
poetry install

# Run the application
poetry run uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
