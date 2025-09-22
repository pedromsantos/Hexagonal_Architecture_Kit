# Katacombs API Makefile
# DDD + Hexagonal Architecture + London School TDD Project

.PHONY: help install test test-unit test-integration test-contract test-acceptance test-e2e test-watch run dev clean lint format check lint-fix format-check type-check pylance quality quality-fix

help: ## Show this help message
	@echo "Katacombs API - DDD + Hexagonal Architecture"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development Setup
install: ## Install dependencies using uv
	uv sync

# Testing Commands (Following Pedro's Algorithm)
test: ## Run all tests (complete test suite)
	uv run pytest -v

test-unit: ## Run unit tests only (domain behavior)
	uv run pytest tests/unit/ -v

test-integration: ## Run integration tests only (driven adapters)
	uv run pytest tests/integration/ -v

test-contract: ## Run contract tests only (driving adapters)
	uv run pytest tests/contract/ -v

test-acceptance: ## Run acceptance tests only (complete business flows)
	uv run pytest tests/acceptance/ -v

test-e2e: ## Run end-to-end tests only (full system)
	uv run pytest tests/e2e/ -v

test-watch: ## Run tests in watch mode (for TDD)
	uv run pytest --looponfail tests/

test-coverage: ## Run tests with coverage report
	uv run pytest --cov=src --cov-report=html --cov-report=term-missing

# Application Commands
run: ## Run the application
	uv run python main.py

dev: ## Run the application in development mode
	uv run uvicorn src.katacombs.infrastructure.adapters.fastapi_app:create_app --factory --reload --host 0.0.0.0 --port 8000

# Code Quality
lint: ## Run ruff linter (strictest possible settings)
	uv run ruff check .

lint-fix: ## Run ruff linter and fix auto-fixable issues
	uv run ruff check . --fix

format: ## Format code with ruff formatter
	uv run ruff format .

format-check: ## Check if code is properly formatted
	uv run ruff format . --check

type-check: ## Run pyright type checker (strictest possible settings)
	uv run pyright

pylance: ## Run pyright/pylance with verbose output for debugging
	uv run pyright --verbose .

quality: ## Run all quality checks (lint + type check + format check)
	@echo "🔍 Running code quality checks..."
	uv run ruff check .
	uv run ruff format . --check
	uv run pyright
	@echo "✅ All code quality checks passed!"

quality-fix: ## Fix all auto-fixable quality issues
	@echo "🔧 Fixing auto-fixable issues..."
	uv run ruff check . --fix
	uv run ruff format .
	@echo "✅ Auto-fixes applied!"

check: ## Run all checks (quality + tests)
	make quality
	make test
	@echo "✅ All checks passed - ready to commit!"

# Cleanup
clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/
