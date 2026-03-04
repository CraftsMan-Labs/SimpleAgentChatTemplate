SHELL := /bin/bash

.PHONY: help install-frontend install-backend run-frontend run-backend run-postgres up down logs reload-workflows

help:
	@echo "Targets:"
	@echo "  install-frontend   Install frontend dependencies"
	@echo "  install-backend    Install backend dependencies into .venv"
	@echo "  run-frontend       Start Vue dev server"
	@echo "  run-backend        Start FastAPI dev server"
	@echo "  run-postgres       Start postgres via docker compose"
	@echo "  up                 Start full docker compose stack"
	@echo "  down               Stop docker compose stack"
	@echo "  logs               Tail docker compose logs"
	@echo "  reload-workflows   Refresh workflow model registry"

install-frontend:
	npm --prefix frontend install

install-backend:
	python3 -m venv backend/.venv
	backend/.venv/bin/pip install -r backend/requirements.txt

run-frontend:
	npm --prefix frontend run dev

run-backend:
	backend/.venv/bin/uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir backend

run-postgres:
	docker compose up -d postgres

up:
	docker compose up --build

down:
	docker compose down

logs:
	docker compose logs -f

reload-workflows:
	curl -s -X POST http://localhost:8000/internal/workflows/reload | python3 -m json.tool
