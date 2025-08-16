FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src

ENV HOST=0.0.0.0
ENV SERVICE_PORT=8081

EXPOSE 8081

HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8081/health || exit 1

CMD ["python", "src/main.py"]


