# ============================================
# FinAgentix Dockerfile - Lab 9
# Base: python:3.11-slim (minimal, secure, 150MB)
# ============================================

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Prevent Python from writing .pyc files and buffering output
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies for ChromaDB
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements FIRST (layer caching optimization)
COPY requirements-docker.txt .
RUN pip install --no-cache-dir -r requirements-docker.txt

# Copy application code SECOND (only rebuilds when code changes)
COPY . .

# Expose the API port
EXPOSE 8000

# Run the FastAPI server
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]