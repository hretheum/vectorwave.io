# Quick Start Template

Follow this template to provide a minimal, reliable start guide for any service.

## Prerequisites
- Runtime and version
- Docker (optional)
- Required external services (URLs)

## 1. Setup
```bash
# Clone and enter repo
# Configure environment
cp .env.template .env
# Fill required variables
```

## 2. Run (Docker)
```bash
docker compose up -d <service-name>
```

## 3. Run (Direct)
```bash
pip install -r requirements.txt
python src/main.py
```

## 4. Verify
```bash
curl http://localhost:<port>/health
open http://localhost:<port>/docs
```

## 5. Basic Flow
- One or two example requests (curl) to prove the happy path

## 6. Troubleshooting
- Most common startup issues and fixes

## 7. Next Steps
- Link to full README and advanced guides
