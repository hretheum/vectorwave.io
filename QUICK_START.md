# Quick Start

## Prerequisites
- Docker
- Python 3.11+

## 1. Setup
```bash
# Clone and enter repo
# git clone <repo-url>
cd vectorwave.io
```

## 2. Run (Docker)
```bash
docker compose up --build -d
```

## 3. Run (Direct)
```bash
pip install -r requirements-test.txt
python editorial-service/main.py
```

## 4. Verify
```bash
curl http://localhost:8040/health
open http://localhost:8040/docs
```

## 5. Basic Flow
- `curl -s -X POST http://localhost:8041/topics/novelty-check -H 'Content-Type: application/json' -d '{"title":"Test","summary":"Short"}'`

## 6. Troubleshooting
- `docker compose logs <service>` to inspect failing containers.

## 7. Next Steps
- See [README.md](README.md) for full architecture and service details.
