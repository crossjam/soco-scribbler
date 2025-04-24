# Build stage
FROM python:3.12-slim AS builder

# Copy uv from its official image
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv

# Set the working directory
WORKDIR /app

# Enable bytecode compilation for better performance
ENV UV_COMPILE_BYTECODE=1
ENV UV_SYSTEM_PYTHON=1

# Copy only requirements file first to leverage caching
COPY requirements.txt .

# Install dependencies with uv
RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install --system -r requirements.txt

# Final stage
FROM python:3.12-slim

# Set the working directory
WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

# Create data directory
RUN mkdir -p /app/data

# Copy application files
COPY . .

# Define volume for the data directory
VOLUME ["/app/data"]

# Run the application
CMD ["python", "./sonos_lastfm.py"] 