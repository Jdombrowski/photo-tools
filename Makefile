# Python settings
PYTHON := python3
VENV := .venv
VENV_BIN := $(VENV)/bin

# # Important files and directories
REQUIREMENTS := requirements.txt
SRC_DIR := src
BUILD_DIR := build
DIST_DIR := dist
CACHE_DIR := __pycache__

REQUIREMENTS := requirements.txt

# ANSI color codes for prettier output
YELLOW := "\033[33m"
RESET := "\033[0m"

# Default target
.DEFAULT_GOAL := help

# Automatically generate help text from comments
help:
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf $(YELLOW)"%-20s"$(RESET)" %s\n", $$1, $$2}'

venv: ## Virtual environment creation
	@echo "Creating virtual environment..."
	@$(PYTHON) -m venv $(VENV)
	@echo "Virtual environment created at $(VENV)"

deps: ## Install dependencies
	@echo "Installing dependencies..."
	@uv sync
	@echo "Dependencies installed successfully"

clean: ## Clean up build artifacts
	@echo "Cleaning up build artifacts..."
	@rm -rf $(VENV) $(BUILD_DIR) $(DIST_DIR) $(CACHE_DIR)
	@echo "Cleaned up build artifacts"

# Prevent these targets from being matched as files
.PHONY:  venv deps update-deps clean test help

# Add this at the bottom of your Makefile to handle arbitrary targets The %: rule at the bottom is necessary to prevent make from throwing errors about non-existent targets when it sees the filename argument.
%:
    @: