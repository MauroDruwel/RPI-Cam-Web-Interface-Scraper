# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies including ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Create non-root user for security
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/

# Create data directory and set permissions
RUN mkdir -p /data/videos && \
    chown -R appuser:appuser /app /data

# Switch to non-root user
USER appuser

# Set Python path to include src directory
ENV PYTHONPATH=/app/src

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python src/main.py --help > /dev/null 2>&1 || exit 1

# Default command - run scheduler
CMD ["python", "src/main.py"]
