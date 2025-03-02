# Makefile for OpenChains

# Define variables for directories and commands
PYTHON = poetry run
FRONTEND_DIR = frontend
BACKEND_DIR = backend

.PHONY: help test test-unit test-bdd test-integration test-all setup-test clean

help:
	@echo "Available targets:"
	@echo "  help              - Show this help message"
	@echo "  test-unit         - Run Python unit tests"
	@echo "  test-bdd          - Run BDD tests with Behave"
	@echo "  test-integration  - Run integration tests between frontend and backend"
	@echo "  test-all          - Run all tests (unit, BDD, and integration)"
	@echo "  setup-test        - Set up the test environment"
	@echo "  clean             - Clean up temporary files"

# Target to run Python unit tests
test-unit:
	@echo "Running unit tests..."
	$(PYTHON) pytest $(BACKEND_DIR)/tests/unit/ -v

# Target to run BDD tests with Behave
test-bdd:
	@echo "Running BDD tests..."
	$(PYTHON) behave $(BACKEND_DIR)/tests/bdd/ -v

# Target to set up the test environment
setup-test:
	@echo "Setting up test environment..."
	$(PYTHON) python -m $(BACKEND_DIR).scripts.create_admin admin adminpassword

# Target to run integration tests between frontend and backend
test-integration:
	@echo "Running integration tests..."
	# First check if servers are running
	curl -s http://localhost:8000/docs > /dev/null || (echo "Backend server is not running"; exit 1)
	curl -s http://localhost:5173 > /dev/null || (echo "Frontend server is not running"; exit 1)
	# Run integration tests
	$(PYTHON) pytest $(BACKEND_DIR)/tests/integration/ -v

# Target to run all tests
test-all: test-unit test-bdd test-integration
	@echo "All tests completed!"

# Target to clean up temporary files
clean:
	@echo "Cleaning up..."
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type f -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".venv" -exec rm -rf {} +
	find . -type d -name "node_modules" -exec rm -rf {} +
	rm -rf $(FRONTEND_DIR)/dist

# Default target
.DEFAULT_GOAL := help
