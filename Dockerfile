# ========================================
# DOCKERFILE FOR PAYROLL AI AGENT
# ========================================
# This Dockerfile builds a container image for the Python backend application.
# It uses a multi-stage build pattern for optimization.

# Start from Python 3.11 slim image
# - slim variant is smaller than the full image but includes essential libraries
FROM python:3.11-slim

# ========================================
# ENVIRONMENT VARIABLES
# ========================================
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files
# - Reduces container size and improves security
ENV PYTHONDONTWRITEBYTECODE=1

# PYTHONUNBUFFERED: Forces Python to print output immediately
# - Essential for Docker logging to work correctly
ENV PYTHONUNBUFFERED=1

# PIP_NO_CACHE_DIR: Prevents pip from caching downloaded packages
# - Reduces container size
ENV PIP_NO_CACHE_DIR=1

# ========================================
# WORKING DIRECTORY
# ========================================
# Set /app as the working directory for all subsequent commands
WORKDIR /app

# ========================================
# SYSTEM DEPENDENCIES
# ========================================
# Install system packages needed for Python packages
# --no-install-recommends: Only install essential packages
# rm -rf /var/lib/apt/lists/*: Clean up apt cache to reduce image size
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    ca-certificates \
    git && \
    rm -rf /var/lib/apt/lists/*

# ========================================
# PYTHON DEPENDENCIES
# ========================================
# Copy requirements.txt first (separate layer for caching)
# Docker will only rebuild this layer if requirements.txt changes
COPY requirements.txt /app/requirements.txt

# Install Python packages
# --upgrade pip: Ensure we have the latest pip version
RUN pip install --upgrade pip && pip install -r requirements.txt

# ========================================
# APPLICATION CODE
# ========================================
# Copy the entire application code into the container
# This happens after pip install so code changes don't invalidate the pip cache layer
COPY . /app

# ========================================
# EXPOSE PORT
# ========================================
# Document that the container listens on port 8080
# Note: This is documentation only, doesn't actually expose the port
# Port mapping is done in docker-compose.yml or docker run command
EXPOSE 8080

# ========================================
# STARTUP COMMAND
# ========================================
# Use shell form to allow environment variable expansion
# uvicorn: ASGI server
# app.api.main:app: Import path to FastAPI app instance
# --host 0.0.0.0: Listen on all network interfaces (required for Docker)
# --port 8080: Listen on port 8080
# --reload: Auto-reload on code changes (remove in production)
CMD ["sh", "-c", "uvicorn app.api.main:app --host 0.0.0.0 --port 8080"]

