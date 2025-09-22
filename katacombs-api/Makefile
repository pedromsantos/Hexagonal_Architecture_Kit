# Katacombs API Makefile
# DDD + Hexagonal Architecture + London School TDD Project

.PHONY: help install test test-unit test-integration test-contract test-acceptance test-e2e test-watch run dev clean lint format check lint-fix format-check type-check quality quality-fix

# Default target
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

# London School TDD Workflow
tdd-red: ## Start TDD cycle - write failing test
	@echo "🔴 RED: Write a failing test"
	@echo "Run: make test-unit (or test-acceptance for new feature)"

tdd-green: ## Make tests pass - implement minimum code
	@echo "🟢 GREEN: Make the test pass"
	uv run pytest -v
	@echo "✅ All tests should be GREEN before refactoring"

tdd-refactor: ## Clean up code while keeping tests green
	@echo "🔄 REFACTOR: Improve code structure"
	@echo "Keep running: make test to ensure tests stay GREEN"

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

# Pedro's Algorithm Workflow
acceptance-first: ## Start new feature with acceptance test (Pedro's Algorithm Step 1)
	@echo "🎯 PEDRO'S ALGORITHM - Step 1: Write failing acceptance test"
	@echo "1. Define complete business flow in tests/acceptance/"
	@echo "2. Test should be RED (failing)"
	@echo "3. Use: make test-acceptance"

unit-cycle: ## Work on domain objects with unit tests (Pedro's Algorithm Step 2)
	@echo "🔄 PEDRO'S ALGORITHM - Step 2: Unit test cycle"
	@echo "While acceptance test is RED:"
	@echo "  - Write failing unit test (tests/unit/)"
	@echo "  - Implement domain behavior"
	@echo "  - Use: make test-unit"
	@echo "  - Commit when GREEN"

integration-driven: ## Test driven adapters (Pedro's Algorithm Step 3)
	@echo "🔌 PEDRO'S ALGORITHM - Step 3: Integration tests"
	@echo "Test repositories and external system adapters"
	@echo "Use: make test-integration"

contract-driving: ## Test driving adapters (Pedro's Algorithm Step 4)
	@echo "📡 PEDRO'S ALGORITHM - Step 4: Contract tests"
	@echo "Test HTTP controllers and API contracts"
	@echo "Use: make test-contract"

e2e-optional: ## End-to-end validation (Pedro's Algorithm Step 5)
	@echo "🚀 PEDRO'S ALGORITHM - Step 5: E2E tests (optional)"
	@echo "Test complete system workflows"
	@echo "Use: make test-e2e"

# Workflow Helpers
pedro-algorithm: ## Show Pedro's Algorithm workflow
	@echo "🎯 PEDRO'S ALGORITHM (London School TDD)"
	@echo ""
	@echo "1️⃣  make acceptance-first  - Write failing acceptance test (complete business flow)"
	@echo "2️⃣  make unit-cycle        - Unit test cycle (domain behavior)"
	@echo "3️⃣  make integration-driven - Test driven adapters (repositories, external)"
	@echo "4️⃣  make contract-driving   - Test driving adapters (HTTP controllers)"
	@echo "5️⃣  make e2e-optional      - End-to-end tests (full system)"
	@echo ""
	@echo "🔄 TDD Cycle: make tdd-red → make tdd-green → make tdd-refactor"

# Architecture Validation
arch-check: ## Validate hexagonal architecture principles
	@echo "🏗️  ARCHITECTURE VALIDATION"
	@echo "✅ Domain layer has no external dependencies"
	@echo "✅ Use cases orchestrate without business logic"
	@echo "✅ Adapters implement ports from domain/application"
	@echo "✅ Tests follow London School TDD principles"
	@echo "Run: make test to verify all layers work correctly"

# Cleanup
clean: ## Clean up generated files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf .pytest_cache/

# Documentation
docs: ## Show project documentation
	@echo "📚 DOCUMENTATION"
	@echo "- README.md: DDD + Hexagonal Architecture rules"
	@echo "- CLAUDE.md: Development methodology and TDD guidance"
	@echo "- main.py: Application entry point"
	@echo ""
	@echo "🏗️  ARCHITECTURE"
	@echo "- src/katacombs/domain/: Entities, Value Objects, Repository interfaces"
	@echo "- src/katacombs/application/: Use Cases, DTOs"
	@echo "- src/katacombs/infrastructure/: Adapters (HTTP, Repositories)"
	@echo ""
	@echo "🧪 TESTS"
	@echo "- tests/unit/: Domain behavior testing"
	@echo "- tests/integration/: Driven adapter testing"
	@echo "- tests/contract/: Driving adapter testing"
	@echo "- tests/acceptance/: Complete business flow testing"
	@echo "- tests/e2e/: End-to-end system testing"