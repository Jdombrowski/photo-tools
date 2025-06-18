lint: dev-deps ## Lint code with flake8
	@echo $(YELLOW)"🔍 Linting code with flake8..."$(RESET)
	@$(UV) run flake8 $(SRC_DIR) tests/ --
# Python settings - use uv for everything
PYTHON := python3
UV := uv
PROJECT_NAME := exif-analyzer

# Virtual environment detection (uv creates .venv automatically)
VENV := .venv
VENV_PYTHON := $(VENV)/bin/python
VENV_PIP := $(VENV)/bin/pip

# Important files and directories
REQUIREMENTS := requirements.txt
SRC_DIR := src
BUILD_DIR := build
DIST_DIR := dist
CACHE_DIR := __pycache__
LOGS_DIR := logs

# ANSI color codes for prettier output
YELLOW := "\033[33m"
GREEN := "\033[32m"
BLUE := "\033[34m"
RED := "\033[31m"
RESET := "\033[0m"

# Default target
.DEFAULT_GOAL := help

# Automatically generate help text from comments
help: ## Show this help message
	@echo $(BLUE)"📸 Photography Portfolio Analytics - Build System"$(RESET)
	@echo ""
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf $(YELLOW)"  %-20s"$(RESET)" %s\n", $$1, $$2}'
	@echo ""
	@echo $(BLUE)"Environment Info:"$(RESET)
	@echo "  UV Version: $(shell $(UV) --version 2>/dev/null || echo 'Not installed')"
	@echo "  Python: $(shell $(PYTHON) --version 2>/dev/null || echo 'Not found')"
	@echo "  Virtual Env: $(shell [ -d $(VENV) ] && echo 'Active (.venv)' || echo 'Not created')"

# Check if uv is installed
check-uv: ## Check if uv is installed and install if missing
	@echo $(YELLOW)"🔍 Checking for uv..."$(RESET)
	@if ! command -v $(UV) &> /dev/null; then \
		echo $(RED)"❌ uv not found. Installing uv..."$(RESET); \
		curl -LsSf https://astral.sh/uv/install.sh | sh; \
		echo $(GREEN)"✅ uv installed successfully"$(RESET); \
	else \
		echo $(GREEN)"✅ uv is already installed"$(RESET); \
	fi

# Virtual environment setup using uv
venv: check-uv ## Create virtual environment using uv
	@echo $(YELLOW)"🐍 Setting up virtual environment with uv..."$(RESET)
	@if [ ! -d $(VENV) ]; then \
		$(UV) venv; \
		echo $(GREEN)"✅ Virtual environment created at $(VENV)"$(RESET); \
	else \
		echo $(GREEN)"✅ Virtual environment already exists"$(RESET); \
	fi

# Install dependencies using uv
deps: venv ## Install all dependencies using uv
	@echo $(YELLOW)"📦 Installing dependencies with uv..."$(RESET)
	@$(UV) sync
	@echo $(GREEN)"✅ Dependencies installed successfully"$(RESET)
	@echo $(BLUE)"📋 Installed packages:"$(RESET)
	@$(UV) pip list

# Install development dependencies
dev-deps: deps ## Install development dependencies
	@echo $(YELLOW)"🛠️  Installing development dependencies..."$(RESET)
	@$(UV) add --dev pytest black flake8 mypy
	@echo $(GREEN)"✅ Development dependencies installed"$(RESET)

# Update dependencies
update-deps: venv ## Update all dependencies to latest versions
	@echo $(YELLOW)"🔄 Updating dependencies..."$(RESET)
	@$(UV) sync --upgrade
	@echo $(GREEN)"✅ Dependencies updated successfully"$(RESET)

# Lock dependencies (regenerate uv.lock)
lock: venv ## Lock current dependency versions
	@echo $(YELLOW)"🔒 Locking dependency versions..."$(RESET)
	@$(UV) lock
	@echo $(GREEN)"✅ Dependencies locked in uv.lock"$(RESET)

# Run the Streamlit dashboard
run: deps ## Run the Streamlit dashboard
	@echo $(YELLOW)"🚀 Starting Streamlit dashboard..."$(RESET)
	@$(UV) run streamlit run streamlit_dashboard.py

# Run the CLI analyzer
cli: deps ## Run the CLI photo analyzer
	@echo $(YELLOW)"⚙️  Running CLI analyzer..."$(RESET)
	@if [ -z "$(DIR)" ]; then \
		echo $(RED)"❌ Please provide a directory: make cli DIR=/path/to/photos"$(RESET); \
	else \
		$(UV) run python cli.py "$(DIR)" $(ARGS); \
	fi

# Test the photo analyzer
test: deps ## Run basic tests
	@echo $(YELLOW)"🧪 Running tests..."$(RESET)
	@$(UV) run python -m pytest tests/ -v 2>/dev/null || \
	$(UV) run python photo_analyzer/photo_metadata_analyzer.py

# Code formatting and linting
format: dev-deps ## Format code with black
	@echo $(YELLOW)"🎨 Formatting code with black..."$(RESET)
	@$(UV) run black . --line-length 100
	@echo $(GREEN)"✅ Code formatted"$(RESET)

lint: dev-deps ## Lint code with flake8
	@echo $(YELLOW)"🔍 Linting code with flake8..."$(RESET)
	@$(UV) run flake8 . --max-line-length=100 --exclude=.venv,build,dist
	@echo $(GREEN)"✅ Linting complete"$(RESET)

typecheck: dev-deps ## Type check with mypy
	@echo $(YELLOW)"🔍 Type checking with mypy..."$(RESET)
	@$(UV) run mypy . --ignore-missing-imports
	@echo $(GREEN)"✅ Type checking complete"$(RESET)

# Quality checks
check: format lint typecheck ## Run all code quality checks
	@echo $(GREEN)"✅ All quality checks passed"$(RESET)

# Build package
build: deps ## Build the package
	@echo $(YELLOW)"📦 Building package..."$(RESET)
	@$(UV) build
	@echo $(GREEN)"✅ Package built successfully"$(RESET)
	@ls -la dist/

# Create example data
sample-data: deps ## Generate sample photo metadata for testing
	@echo $(YELLOW)"📊 Generating sample data..."$(RESET)
	@mkdir -p $(LOGS_DIR)
	@$(UV) run python -c "\
	import pandas as pd; \
	import numpy as np; \
	from datetime import datetime; \
	np.random.seed(42); \
	data = [{'filename': f'IMG_{i:04d}.jpg', 'camera': np.random.choice(['Canon EOS R5', 'Sony A7IV']), 'iso': np.random.choice([100, 400, 800, 1600])} for i in range(20)]; \
	df = pd.DataFrame(data); \
	df.to_csv('sample_metadata.csv', index=False); \
	print(f'Sample data saved to sample_metadata.csv ({len(df)} rows)')"
	@echo $(GREEN)"✅ Sample data generated"$(RESET)

# Clean up build artifacts and virtual environment
clean: ## Clean up build artifacts and virtual environment
	@echo $(YELLOW)"🧹 Cleaning up..."$(RESET)
	@rm -rf $(VENV) $(BUILD_DIR) $(DIST_DIR) $(CACHE_DIR)
	@find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -f sample_metadata.csv photo_metadata_*.csv photo_analysis_*.html *.log
	@echo $(GREEN)"✅ Cleanup complete"$(RESET)

# Clean only cache and temporary files (keep venv)
clean-cache: ## Clean only cache and temporary files
	@echo $(YELLOW)"🧹 Cleaning cache files..."$(RESET)
	@rm -rf $(CACHE_DIR)
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.pyc" -delete 2>/dev/null || true
	@rm -f *.log
	@echo $(GREEN)"✅ Cache cleaned"$(RESET)

# Show project information
info: ## Show project and environment information
	@echo $(BLUE)"📸 Photography Portfolio Analytics"$(RESET)
	@echo ""
	@echo "Project Information:"
	@echo "  Name: $(PROJECT_NAME)"
	@echo "  Python: $(shell $(PYTHON) --version 2>/dev/null || echo 'Not found')"
	@echo "  UV: $(shell $(UV) --version 2>/dev/null || echo 'Not installed')"
	@echo ""
	@echo "Environment:"
	@echo "  Virtual Env: $(shell [ -d $(VENV) ] && echo 'Active (.venv)' || echo 'Not created')"
	@echo "  Dependencies: $(shell [ -f uv.lock ] && echo 'Locked (uv.lock)' || echo 'Not locked')"
	@echo ""
	@echo "Files:"
	@echo "  Config: $(shell [ -f pyproject.toml ] && echo 'pyproject.toml ✓' || echo 'pyproject.toml ✗')"
	@echo "  Lock: $(shell [ -f uv.lock ] && echo 'uv.lock ✓' || echo 'uv.lock ✗')"
	@echo "  Dashboard: $(shell [ -f streamlit_dashboard.py ] && echo 'streamlit_dashboard.py ✓' || echo 'streamlit_dashboard.py ✗')"
	@echo "  CLI: $(shell [ -f cli.py ] && echo 'cli.py ✓' || echo 'cli.py ✗')"

# Install project in development mode
install-dev: deps ## Install project in development mode
	@echo $(YELLOW)"📦 Installing project in development mode..."$(RESET)
	@$(UV) pip install -e .
	@echo $(GREEN)"✅ Project installed in development mode"$(RESET)

# Create production build
production: clean deps build ## Create production-ready build
	@echo $(YELLOW)"🏭 Creating production build..."$(RESET)
	@$(UV) sync --frozen
	@$(UV) build
	@echo $(GREEN)"✅ Production build complete"$(RESET)

# Quick start for new users
setup: check-uv venv deps sample-data ## Complete setup for new users
	@echo $(GREEN)"🎉 Setup complete! You can now:"$(RESET)
	@echo "  • Run dashboard: $(YELLOW)make run$(RESET)"
	@echo "  • Analyze photos: $(YELLOW)make cli DIR=/path/to/photos$(RESET)"
	@echo "  • View help: $(YELLOW)make help$(RESET)"

# Export requirements.txt for compatibility
export-requirements: deps ## Export requirements.txt from uv.lock
	@echo $(YELLOW)"📋 Exporting requirements.txt..."$(RESET)
	@$(UV) pip compile pyproject.toml -o requirements.txt
	@echo $(GREEN)"✅ requirements.txt exported"$(RESET)

# Prevent these targets from being matched as files
.PHONY: help check-uv venv deps dev-deps update-deps lock run cli test format lint typecheck check build sample-data clean clean-cache info install-dev production setup export-requirements

# Handle arbitrary targets gracefully
%:
	@echo $(RED)"❌ Unknown target: $@"$(RESET)
	@echo "Run $(YELLOW)make help$(RESET) to see available targets"