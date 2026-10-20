.PHONY: install lint format type-check test migrate makemigrations run docker-build docker-up docker-down clean all help

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
MANAGE := $(PYTHON) src/markdown_notes/manage.py

install: ## Create venv and install dependencies
	python3 -m venv $(VENV)
	$(PIP) install --upgrade pip setuptools wheel
	$(PIP) install -e ".[dev]"

lint: ## Run linter
	$(PYTHON) -m ruff check src/ tests/
	$(PYTHON) -m ruff format --check src/ tests/

format: ## Auto-format code
	$(PYTHON) -m ruff format src/ tests/
	$(PYTHON) -m ruff check --fix src/ tests/

type-check: ## Run type checker
	$(PYTHON) -m mypy src/

test: ## Run tests with coverage
	$(PYTHON) -m pytest

migrate: ## Apply database migrations
	$(MANAGE) migrate

makemigrations: ## Create new database migrations
	$(MANAGE) makemigrations

run: ## Run Django development server
	$(MANAGE) runserver 0.0.0.0:8000

docker-build: ## Build Docker image
	docker build -t markdown-notes .

docker-up: ## Start all services
	docker compose up -d

docker-down: ## Stop all services
	docker compose down

clean: ## Remove caches and venv
	rm -rf $(VENV) .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

all: lint type-check test ## Run all checks

help: ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'
