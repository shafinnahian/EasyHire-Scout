FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy the application source code
COPY . .

# Install the package and its dependencies
RUN pip install --no-cache-dir .

# Environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "easyhire_scout.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
