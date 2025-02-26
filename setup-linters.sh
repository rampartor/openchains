#!/bin/bash

# Update Python dependencies with Poetry
echo "Installing Python dependencies..."
poetry update
poetry install

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
poetry run pre-commit install

# Update JavaScript dependencies
echo "Installing JavaScript dependencies..."
cd frontend && yarn install

echo "Setup complete! Linters and code-style checkers have been installed as git pre-commit hooks."
echo "You can run them manually with:"
echo "  - For Python: poetry run black backend/ && poetry run isort backend/ && poetry run flake8 backend/"
echo "  - For JavaScript/Svelte: cd frontend && yarn lint && yarn format"
