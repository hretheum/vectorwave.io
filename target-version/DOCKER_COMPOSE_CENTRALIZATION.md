# Centralized Docker Compose (Vector Wave)

This repository now uses a single root-level `docker-compose.yml` to orchestrate core services and optional profiles.

## Core services
- ChromaDB (port 8000)
- Redis (port 6379)
- Editorial Service (port 8040)
- CrewAI Orchestrator (port 8042)

Start core:

```bash
docker compose up -d --build
```

## Optional profiles
- publishing: Publishing Orchestrator, LinkedIn PPT Generator
- analytics: Analytics Service

Start with profiles:

```bash
docker compose --profile publishing up -d
# and/or
docker compose --profile analytics up -d
```

## Health checks
We use container health checks to ensure dependencies are ready:

- ChromaDB v2 heartbeat:
```yaml
healthcheck:
  test: ["CMD", "wget", "-q", "-O", "-", "http://localhost:8000/api/v2/heartbeat"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 20s
```

- CrewAI Orchestrator health:
```yaml
healthcheck:
  test: ["CMD", "wget", "-q", "-O", "-", "http://localhost:8042/health"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 20s
```

Quick manual checks:
```bash
curl -s http://localhost:8000/api/v2/heartbeat
curl -s http://localhost:8040/health
curl -s http://localhost:8042/health
```

## Logs & restart
```bash
docker compose logs -f editorial-service
docker compose logs -f crewai-orchestrator

docker compose up -d --build editorial-service crewai-orchestrator
```

## Cleanup of legacy containers
If you have older, module-scoped containers (e.g. `chromadb-1`, `editorial-service-1`, `crewai-orchestrator-dev`, `linkedin`, `publisher`, etc.) stop and remove them before starting the centralized stack to avoid port conflicts:

```bash
# Remove non-centralized containers that bind 8000/8040/8042 or legacy names
for name in $(docker ps --format '{{.Names}} {{.Ports}}' \
  | awk '{n=$1;p=$2; if (n !~ /^vector-wave-/ && (p ~ /8000->8000/ || p ~ /8040->8040/ || p ~ /8042->8042/)) print n}'); do
  docker rm -f "$name" || true
done

# Also remove legacy named services if present
for name in crewai-orchestrator-dev chromadb-1 editorial-service editorial-service-1 redis-1 linkedin linkedin_ppt_generator publisher; do
  docker rm -f "$name" 2>/dev/null || true
done

# Start centralized stack
docker compose up -d --build
```

## Service addressing inside the network
- Orchestrator -> Editorial Service: `http://editorial-service:8040`
- Editorial Service -> ChromaDB: `chromadb:8000`
- Editorial Service -> Redis: `redis://redis:6379`

## Notes
- The `version` field in Compose v2 is deprecated and omitted.
- Module-level compose files were removed in favor of the root compose.
