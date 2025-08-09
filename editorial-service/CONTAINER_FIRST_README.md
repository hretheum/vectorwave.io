# Editorial Service - Container-First Development Guide

## 🐳 Container-First Architecture

Ten service implementuje **container-first approach** zgodny z najlepszymi praktykami DevOps:

- Multi-stage Docker builds dla optymalizacji
- Oddzielne konfiguracje dev/prod
- Health checks i monitoring wbudowane
- Automatyczna integracja z ChromaDB
- Non-root user dla bezpieczeństwa

## 🚀 Quick Start

### Development Environment

```bash
# 1. Uruchom stack development
docker-compose -f docker-compose.dev.yml up --build

# 2. Sprawdź health endpoints
curl http://localhost:8040/health
curl http://localhost:8000/api/v1/heartbeat  # ChromaDB

# 3. Hot-reload development
# Pliki src/ są zamontowane jako volumes - zmiany od razu widoczne
```

### Production Environment

```bash
# 1. Build production image
docker-compose -f docker-compose.prod.yml build

# 2. Deploy with resource limits
docker-compose -f docker-compose.prod.yml up -d

# 3. Monitor resources
docker stats editorial-service chromadb
```

## 🔍 Container Verification Commands

```bash
# Health status verification
docker-compose exec editorial-service curl http://editorial-service:8040/health
docker-compose exec chromadb curl http://chromadb:8000/api/v1/heartbeat

# Network inspection
docker network inspect vector-wave_vector-wave-dev

# Resource monitoring
docker stats editorial-service chromadb

# Logs inspection
docker-compose logs -f editorial-service
docker-compose logs -f chromadb
```

## 🧪 Testing in Containers

```bash
# Run all tests
docker-compose exec editorial-service python -m pytest tests/ -v

# Coverage report
docker-compose exec editorial-service python -m pytest tests/ --cov=src --cov-report=html

# Integration tests with ChromaDB
docker-compose exec editorial-service python -m pytest tests/integration/ -v
```

## 📋 Container-First Validation Criteria

- [ ] Service startuje w <30s
- [ ] Health endpoint odpowiada w <50ms
- [ ] ChromaDB połączenie ustanawiane w <2s
- [ ] Non-root user permissions działają
- [ ] Hot-reload w development działa
- [ ] Resource limits przestrzegane w prod
- [ ] Automatic restart po crash

## 🏗️ Architecture Benefits

1. **Consistent Environment**: Dev = Prod
2. **Isolated Dependencies**: Nie konfliktuje z hostem
3. **Easy Scaling**: Resource limits + multiple containers
4. **Security**: Non-root user, minimal attack surface
5. **Observability**: Built-in health checks
6. **Fast Development**: Hot-reload volumes

## 📊 Performance Targets

- **Startup Time**: <30s (with ChromaDB dependency)
- **Health Check**: <50ms P95 response time
- **Memory Usage**: <100MB baseline, <512MB with load
- **CPU Usage**: <0.5 CPU under normal load
- **Concurrent Connections**: 500+ health checks

---

**Next Steps**: Po weryfikacji że container-first foundation działa, przejdź do Task 1.1.2 ChromaDB Client Integration.
EOF < /dev/null