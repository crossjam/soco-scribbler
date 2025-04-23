.PHONY: setup install clean run

# Python version to use
PYTHON_VERSION := 3.11.2

# Default target
all: setup

# Setup Python environment
setup:
	@echo "Setting up Python environment..."
	uv venv
	@echo "Python environment setup complete. Run 'make install' to install dependencies."

# Install dependencies
install:
	@echo "Installing dependencies..."
	. .venv/bin/activate && uv pip install -r requirements.txt
	@echo "Dependencies installed successfully."

# Clean up
clean:
	@echo "Cleaning up..."
	rm -rf .venv
	rm -rf __pycache__
	rm -rf *.pyc
	@echo "Cleanup complete."

# Run the scrobbler
run:
	@echo "Running Sonos Last.fm scrobbler..."
	. .venv/bin/activate && uv run sonos_lastfm.py

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
	@echo "  make setup    - Set up Python environment with uv"
	@echo "  make install  - Install project dependencies"
	@echo "  make clean    - Clean up generated files"
	@echo "  make run      - Run the scrobbler"
	@echo "  make versions - Show available Python versions"
	@echo "  make version  - Show current Python version"
	@echo "  make help     - Show this help message" 