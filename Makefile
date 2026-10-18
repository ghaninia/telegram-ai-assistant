# Telegram AI Bot — common development tasks. Run `make` to list them.

APP_NAME := TelegramAIBot
PYTHON   ?= python3
VENV     := .venv
BIN      := $(VENV)/bin
DATA_DIR := $(HOME)/Library/Application Support/$(APP_NAME)

.DEFAULT_GOAL := help
.PHONY: help install run test test-gui test-all lint fix check build open dmg-open logs data clean distclean

help: ## Show this help
	@awk 'BEGIN {FS = ":.*## "; printf "Usage: make <target>\n\n"} \
		/^[a-zA-Z_-]+:.*## / {printf "  \033[36m%-10s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# --- Setup ---

$(BIN)/python:
	$(PYTHON) -m venv $(VENV)

$(VENV)/.installed: $(BIN)/python pyproject.toml
	$(BIN)/pip install -q --upgrade pip
	$(BIN)/pip install -q -e ".[dev]"
	@touch $@

install: $(VENV)/.installed ## Create the virtualenv and install the app with dev tools

# --- Development ---

run: install ## Run the app from source
	$(BIN)/python -m telegram_ai_bot

test: install ## Run unit tests (headless)
	$(BIN)/python -m pytest -q

test-gui: install ## Run Qt WebEngine integration tests (needs a display)
	RUN_GUI_TESTS=1 $(BIN)/python -m pytest -q -m gui

test-all: test test-gui ## Run unit and GUI tests

lint: install ## Lint with ruff
	$(BIN)/ruff check src tests

fix: install ## Auto-fix lint issues where possible
	$(BIN)/ruff check --fix src tests

check: lint test ## Lint and run unit tests (use before committing)

# --- Build ---

build: check ## Build the .app and .dmg into dist/ (runs checks first)
	./scripts/build_macos.sh

open: ## Launch the built app
	open "dist/$(APP_NAME).app"

dmg-open: ## Open the built DMG in Finder
	open "dist/$(APP_NAME).dmg"

# --- App data ---

logs: ## Show the last lines of the app log
	@tail -n 50 "$(DATA_DIR)/logs/app.log" 2>/dev/null || echo "No log yet: $(DATA_DIR)/logs/app.log"

data: ## Open the app data folder (database, Telegram session, logs)
	open "$(DATA_DIR)"

# --- Cleanup ---

clean: ## Remove build output and caches
	rm -rf build dist .pytest_cache .ruff_cache
	find . -path ./$(VENV) -prune -o -name __pycache__ -type d -exec rm -rf {} +
	find . -path ./$(VENV) -prune -o -name "*.egg-info" -type d -exec rm -rf {} +

distclean: clean ## Also remove the virtualenv (user data is never touched)
	rm -rf $(VENV)
