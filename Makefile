# Makefile for AI Chatbot Project

# Configuration
PROJECT_NAME := ai-chatbot
PYTHON := python3.11
VENV := venv
REQUIREMENTS := requirements.txt
DOCKER_IMAGE := ${PROJECT_NAME}:latest
UVICORN_PORT := 8000

# Phony targets
.PHONY: help run install test lint format clean docker-build docker-run

help:  ## Display this help
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

run: ## Start development server with hot reload
	uvicorn app.main:app \
		--reload \
		--port ${UVICORN_PORT} \
		--workers 4 \
		--log-level debug  ## 开发环境配置（参考网页7、8）

install: ## Install dependencies
	pip install -r ${REQUIREMENTS}

test: ## Run unit tests
	pytest -v tests/ \
		--cov=app \
		--cov-report=html \
		--cov-report=term  ## 测试覆盖率报告（参考网页6、7）

lint: ## Static code analysis
	black --check app/ tests/  ## 代码格式检查
	ruff check app/ tests/  ## 静态分析（参考网页7最佳实践）

format: ## Auto-format code
	black app/ tests/
	ruff --fix app/ tests/

docker-build: ## Build Docker image
	docker build -t ${DOCKER_IMAGE} .  ## 容器化构建（基于网页5的Dockerfile）

docker-run: ## Run in Docker container
	docker run -d \
		-p ${UVICORN_PORT}:${UVICORN_PORT} \
		-e ENV=prod \
		--name ${PROJECT_NAME} \
		${DOCKER_IMAGE}

clean: ## Clean build artifacts
	find . -type d -name '__pycache__' -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	rm -rf .coverage htmlcov/

# Advanced targets (参考网页9的LangGraph部署要求)
run-workflow: ## Execute LangGraph workflow
	${PYTHON} -c "from app.workflows.chatbot import ChatWorkflow; \
		workflow = ChatWorkflow().compile(); \
		workflow.visualize('workflow.png')"  ## 生成工作流可视化图

requirements:
	pip freeze > requirements.txt
