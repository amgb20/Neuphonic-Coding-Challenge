.PHONY: all build run dev test clean logs restart help

# Default target
all: build run

# Build all services
build: build-backend build-frontend

# Run all services
run: docker-compose up -d

# Development mode (with logs)
dev: docker-compose up

# Build individual services
build-backend:
	docker-compose build backend

build-frontend:
	docker-compose build frontend

# Development targets
dev-backend:
	docker-compose up backend

dev-frontend:
	docker-compose up frontend

# Testing
test: test-backend test-frontend

test-backend:
	docker-compose run --rm backend pytest

test-frontend:
	docker-compose run --rm frontend npm test

# Audio processing
process-audio:
	docker-compose run --rm backend python -m src.process_audio

# Database operations
init-db:
	docker-compose run --rm backend python -m src.init_database

# Utility targets
logs:
	docker-compose logs -f

logs-backend:
	docker-compose logs -f backend

logs-frontend:
	docker-compose logs -f frontend

restart:
	docker-compose restart

stop:
	docker-compose down

clean:
	docker-compose down -v
	docker system prune -f

# Shell access
shell-backend:
	docker-compose exec backend bash

shell-frontend:
	docker-compose exec frontend sh

# Health checks
health:
	docker-compose ps
	@echo "Backend health:"
	@curl -f http://localhost:8000/health || echo "Backend not responding"
	@echo "Frontend health:"
	@curl -f http://localhost:3000 || echo "Frontend not responding"

# Help
help:
	@echo "Available commands:"
	@echo "  all          - Build and run all services"
	@echo "  build        - Build all services"
	@echo "  run          - Start all services in background"
	@echo "  dev          - Start all services with logs"
	@echo "  test         - Run all tests"
	@echo "  process-audio - Process audio files"
	@echo "  logs         - View all logs"
	@echo "  restart      - Restart all services"
	@echo "  stop         - Stop all services"
	@echo "  clean        - Stop and clean up"
	@echo "  shell-backend - Access backend shell"
	@echo "  shell-frontend - Access frontend shell"
	@echo "  health       - Check service health" 