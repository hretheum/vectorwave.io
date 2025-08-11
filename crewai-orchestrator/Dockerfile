FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src/
COPY config/ ./config/
EXPOSE 8042

# Default Editorial Service URL for local Docker Desktop
ENV EDITORIAL_SERVICE_URL=http://host.docker.internal:8040

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8042/health || exit 1

CMD ["python", "src/main.py"]
