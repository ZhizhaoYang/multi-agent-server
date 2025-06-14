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

requirements:
	pip freeze > requirements.txt
