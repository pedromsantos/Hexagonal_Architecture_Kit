# Makefile for katacombs-api development

.PHONY: help install dev lint format type-check test check-all clean run

# Default target
help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

install: ## Install production dependencies
	uv sync

dev: ## Install development dependencies
	uv sync --extra dev

lint: ## Run linting with ruff
	uv run ruff check .

format: ## Format code with ruff
	uv run ruff format .

type-check: ## Run type checking with pyright
	uv run pyright

test: ## Run tests with pytest
	uv run pytest

check-all: ## Run all checks (lint, format check, type-check, test)
	uv run ruff check . && \
	uv run ruff format --check . && \
	uv run pyright && \
	uv run pytest

ci: ## Run all CI checks (comprehensive quality checks for CI/CD)
	@echo "Running CI checks..."
	@echo "1. Installing dependencies..."
	uv sync --extra dev
	@echo "2. Running linter..."
	uv run ruff check .
	@echo "3. Checking code formatting..."
	uv run ruff format --check .
	@echo "4. Running type checker..."
	uv run pyright
	@echo "5. Running tests..."
	uv run pytest --verbose
	@echo "✅ All CI checks passed!"

clean: ## Clean up cache files
	find . -type d -name "__pycache__" -delete
	find . -type f -name "*.pyc" -delete
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".ruff_cache" -exec rm -rf {} +

run: ## Run the FastAPI development server
	uv run uvicorn katacombs_api.main:app --reload --host 0.0.0.0 --port 8000