# Makefile for AI Chatbot Project

# Configuration
PROJECT_NAME := ai-chatbot
PYTHON := python3.11
VENV := venv
REQUIREMENTS := requirements.txt
DOCKER_IMAGE := ${PROJECT_NAME}:latest
UVICORN_PORT := 8000

# Phony targets
.PHONY: help run install test lint format clean docker-build docker-run deploy

dev:
	langgraph dev

run: ## Start development server with hot reload
	uvicorn app.main:app \
		--reload \
		--port ${UVICORN_PORT} \
		--workers 4 \
		--log-level debug

install: ## Install dependencies
	uv pip install -e .

requirements: ## Update requirements lock file
	source .venv/bin/activate && uv pip freeze > requirements-lock.txt

env-create: ## Create virtual environment
	uv venv --python 3.11

env-update: ## Update environment with locked dependencies
	source .venv/bin/activate && uv pip sync requirements-lock.txt

clean-env: ## Remove virtual environment
	rm -rf .venv

# ===== DEPLOYMENT COMMANDS =====

deploy-setup: ## Setup for deployment (login and validate)
	@echo "🔧 Setting up deployment environment..."
	langgraph login
	langgraph config validate

deploy: ## Deploy to LangGraph Cloud
	@echo "🚀 Deploying to LangGraph Cloud..."
	./deploy.sh

deploy-test: ## Test deployment locally before deploying
	@echo "🧪 Testing deployment locally..."
	./deploy.sh --test

deploy-status: ## Check deployment status
	langgraph status

deploy-logs: ## View deployment logs
	langgraph logs --tail 50

deploy-list: ## List all deployments
	langgraph list

# ===== DOCKER COMMANDS =====

docker-build: ## Build Docker image
	docker build -t ${DOCKER_IMAGE} .

docker-run: ## Run Docker container locally
	docker run -p ${UVICORN_PORT}:8000 --env-file .env.production ${DOCKER_IMAGE}

docker-test: ## Test Docker container
	docker run --rm -p ${UVICORN_PORT}:8000 --env-file .env.production ${DOCKER_IMAGE}

# ===== MONITORING COMMANDS =====

monitor: ## Open LangSmith monitoring dashboard
	@echo "📊 Opening LangSmith dashboard..."
	@echo "Visit: https://smith.langchain.com"

health-check: ## Check if local server is healthy
	curl -f http://localhost:${UVICORN_PORT}/health || echo "❌ Health check failed"

# ===== UTILITY COMMANDS =====

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	rm -rf build/ dist/ *.egg-info/

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*?## "}; {printf "  %-20s %s\n", $$1, $$2}'
