# -----------------------------
# Configuration
# -----------------------------

PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin
UVICORN := $(VENV_BIN)/uvicorn
PIP := $(VENV_BIN)/pip
APP := main:app
PORT := 8000

# -----------------------------
# Targets
# -----------------------------

.PHONY: help create install run dev freeze lint clean db-reset

help:
	@echo "Available targets:"
	@echo "  make create      Create Python virtual environment"
	@echo "  make install     Install dependencies into venv"
	@echo "  make run         Run FastAPI server"
	@echo "  make dev         Run FastAPI with auto-reload"
	@echo "  make freeze      Freeze requirements.txt"
	@echo "  make lint        Run basic Python lint checks"
	@echo "  make clean       Remove __pycache__ and .pyc files"
	@echo "  make db-reset    ⚠️ Drop and recreate DB tables (local only)"

# -----------------------------
# Virtual Environment
# -----------------------------

create:
	$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created in $(VENV)"
	@echo "Activate with: source $(VENV)/bin/activate"

install: create
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

freeze:
	$(PIP) freeze > requirements.txt

# -----------------------------
# Application
# -----------------------------

run:
	$(UVICORN) $(APP) --host 0.0.0.0 --port $(PORT)

dev:
	$(UVICORN) $(APP) --reload --host 0.0.0.0 --port $(PORT)

# -----------------------------
# Utilities
# -----------------------------

lint:
	$(VENV_BIN)/python -m py_compile \
		banking_store.py \
		banking_system.py \
		banking_system_impl.py \
		main.py

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# -----------------------------
# Database (LOCAL ONLY)
# -----------------------------

db-reset:
	psql "postgresql://bank_user:bank_pass@127.0.0.1:5432/banking_db" -f schema.sql