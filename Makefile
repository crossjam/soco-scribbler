.PHONY: check-types check-all install-dev clean setup install run versions version help

# Python version to use
PYTHON_VERSION := 3.11.2

# Source files
PYTHON_FILES := sonos_lastfm.py utils.py

# Install development dependencies
install-dev:
	uv pip install mypy ruff types-setuptools

# Check types with mypy
check-types:
	mypy --strict --python-version=3.12 $(PYTHON_FILES)

# Run ruff type checking and linting
check-ruff:
	ruff check --select=ALL --target-version=py312 $(PYTHON_FILES)

# Run all checks
check-all: check-types check-ruff

# Clean up cache directories
clean:
	rm -rf .mypy_cache .ruff_cache __pycache__ */__pycache__ .venv

# Setup Python environment
setup:
	@echo "Setting up Python environment..."
	uv venv
	@echo "Python environment setup complete. Run 'make install' to install dependencies."

# Install dependencies
install:
	@echo "Installing dependencies..."
	uv pip install -r requirements.txt
	@echo "Dependencies installed successfully."

# Run the scrobbler
run:
	@echo "Running Sonos Last.fm scrobbler..."
	uv run sonos_lastfm.py

# Show available Python versions
versions:
	@echo "Available Python versions:"
	uv python list

# Show current Python version
version:
	@echo "Current Python version:"
	uv python --version

# Help
help:
	@echo "Available commands:"
	@echo "  make setup      - Set up Python environment with uv"
	@echo "  make install    - Install project dependencies"
	@echo "  make install-dev- Install development dependencies"
	@echo "  make check-types- Run mypy type checker"
	@echo "  make check-ruff - Run ruff linter"
	@echo "  make check-all  - Run all checks"
	@echo "  make clean      - Clean up generated files"
	@echo "  make run        - Run the scrobbler"
	@echo "  make versions   - Show available Python versions"
	@echo "  make version    - Show current Python version"
	@echo "  make help       - Show this help message" 