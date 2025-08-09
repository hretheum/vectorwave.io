# Multi-stage Dockerfile for optimal container performance
FROM python:3.11-slim as builder

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python dependencies
COPY requirements.txt ./
COPY requirements-test.txt ./
RUN pip install --no-cache-dir --user -r requirements.txt
RUN pip install --no-cache-dir --user -r requirements-test.txt

# Production stage
FROM python:3.11-slim as production

# Install curl for health checks
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r editorial && useradd -r -g editorial editorial

# Copy installed packages from builder
COPY --from=builder /root/.local /home/editorial/.local

# Set PATH to include user packages and make src importable
ENV PATH="/home/editorial/.local/bin:$PATH" \
    PYTHONPATH="/app/src"

WORKDIR /app

# Copy application code
COPY --chown=editorial:editorial src/ ./src/
COPY --chown=editorial:editorial config/ ./config/

# Switch to non-root user
USER editorial

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import urllib.request; urllib.request.urlopen('http://localhost:8040/health', timeout=5)"

EXPOSE 8040

# Use uvicorn for production (workers configurable via WORKERS env)
ENV WORKERS=2
CMD ["/bin/sh", "-lc", "/home/editorial/.local/bin/uvicorn src.main:app --host 0.0.0.0 --port 8040 --workers ${WORKERS}"]