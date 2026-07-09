# Engineering foundation Makefile.
# Backend tools run from ./backend (config in backend/pyproject.toml + backend/pytest.ini).
# Frontend tools run via npm scripts in ./frontend.

VENV    := $(CURDIR)/.venv
PY      := $(VENV)/bin/python
PIP     := $(VENV)/bin/pip
COMPOSE := docker compose -f docker/docker-compose.dev.yml

.PHONY: help install install-backend install-frontend lint lint-backend lint-frontend \
        typecheck typecheck-backend typecheck-frontend test fmt build-frontend \
        up down migrate clean

help:
	@echo "install     - create backend venv, install backend + frontend deps"
	@echo "lint        - ruff (backend) + eslint (frontend)"
	@echo "typecheck   - mypy (backend) + tsc (frontend)"
	@echo "test        - pytest (backend)"
	@echo "fmt         - ruff format (backend)"
	@echo "up / down   - docker compose dev stack"
	@echo "migrate     - alembic upgrade head"

install: install-backend install-frontend

install-backend:
	python3.12 -m venv $(VENV)
	$(PIP) install --upgrade pip
	$(PIP) install -r backend/requirements.txt -r backend/requirements-dev.txt

install-frontend:
	cd frontend && npm install

lint: lint-backend lint-frontend
lint-backend:
	cd backend && $(VENV)/bin/ruff check .
lint-frontend:
	cd frontend && npm run lint

typecheck: typecheck-backend typecheck-frontend
typecheck-backend:
	cd backend && $(VENV)/bin/mypy app
typecheck-frontend:
	cd frontend && npm run typecheck

test:
	cd backend && $(VENV)/bin/pytest

fmt:
	cd backend && $(VENV)/bin/ruff format .

build-frontend:
	cd frontend && npm run build

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

migrate:
	cd backend && $(VENV)/bin/alembic upgrade head

clean:
	rm -rf $(VENV) frontend/node_modules frontend/dist
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
