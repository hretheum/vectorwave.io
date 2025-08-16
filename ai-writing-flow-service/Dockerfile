FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_ROOT_USER_ACTION=ignore \
    HOST=0.0.0.0 \
    PORT=8044

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl ca-certificates && \
    rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY src ./src

RUN python -m pip install --upgrade pip setuptools wheel && \
    python -m pip install fastapi uvicorn && \
    python -m pip install .

EXPOSE 8044

CMD ["uvicorn", "ai_writing_flow.main:create_enhanced_app", "--factory", "--host", "0.0.0.0", "--port", "8044"]


