.PHONY: help install dev-install test lint format type-check security clean docker-build docker-up docker-down

# Default target
help:
	@echo "Available commands:"
	@echo "  install      Install production dependencies"
	@echo "  dev-install  Install development dependencies"
	@echo "  test         Run all tests"
	@echo "  lint         Run linting checks"
	@echo "  format       Format code with black and isort"
	@echo "  type-check   Run type checking with mypy"
	@echo "  security     Run security checks"
	@echo "  clean        Clean up temporary files"
	@echo "  docker-build Build Docker image"
	@echo "  docker-up    Start Docker services"
	@echo "  docker-down  Stop Docker services"

# Installation
install:
	pip install -r requirements.txt

dev-install:
	pip install -r requirements.txt
	pip install -e .

# Testing
test:
	pytest tests/ -v

test-unit:
	pytest tests/unit/ -v

test-integration:
	pytest tests/integration/ -v

test-e2e:
	pytest tests/e2e/ -v

test-coverage:
	pytest tests/ --cov=src --cov-report=html --cov-report=term

# Code Quality
lint:
	flake8 src/ tests/
	black --check src/ tests/
	isort --check-only src/ tests/

format:
	black src/ tests/
	isort src/ tests/

type-check:
	mypy src/

# Security
security:
	safety check
	bandit -r src/

# Cleanup
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/
	rm -rf dist/
	rm -rf .coverage
	rm -rf htmlcov/
	rm -rf .pytest_cache/
	rm -rf .mypy_cache/

# Docker
docker-build:
	docker build -t ai-trading-bot .

docker-up:
	docker-compose up -d

docker-down:
	docker-compose down

docker-logs:
	docker-compose logs -f

# Development
dev: docker-up
	python src/main.py

# Database
db-migrate:
	alembic upgrade head

db-reset:
	docker-compose down -v
	docker-compose up -d postgres
	sleep 5
	alembic upgrade head

# Monitoring
monitor:
	@echo "Grafana: http://localhost:3000 (admin/admin)"
	@echo "Prometheus: http://localhost:9090"
	@echo "API: http://localhost:8000"
	@echo "API Docs: http://localhost:8000/docs"
