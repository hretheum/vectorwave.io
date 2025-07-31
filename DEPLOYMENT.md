# DEPLOYMENT PIPELINE - AI Kolegium Redakcyjne

## 🚀 Container-First Deployment Strategy

### Główne Założenia
1. **Zero lokalnego budowania** - wszystko na GitHub Actions
2. **GitHub Container Registry** (ghcr.io) jako image registry
3. **Watchtower auto-deploy** na Digital Ocean droplet
4. **Blue-Green deployment** dla zero-downtime updates
5. **Automated rollback** w przypadku problemów

## 🏗️ Architecture Overview

```mermaid
graph TB
    subgraph "Development"
        DEV[Developer Push]
        PR[Pull Request]
    end
    
    subgraph "GitHub Actions"
        BUILD[Build & Test]
        SCAN[Security Scan]
        IMAGE[Build Images]
        PUSH[Push to ghcr.io]
    end
    
    subgraph "Digital Ocean Droplet"
        WATCH[Watchtower]
        COMP[Docker Compose]
        APP[Application Stack]
        MON[Monitoring]
    end
    
    subgraph "External Services"
        GHCR[GitHub Container Registry]
        ALERTS[Alerting]
    end

    DEV --> PR
    PR --> BUILD
    BUILD --> SCAN
    SCAN --> IMAGE
    IMAGE --> PUSH
    PUSH --> GHCR
    
    GHCR --> WATCH
    WATCH --> COMP
    COMP --> APP
    APP --> MON
    MON --> ALERTS
```

## 📦 Container Architecture

### Microservices Containers

```yaml
services:
  # Load Balancer
  nginx:
    image: ghcr.io/username/kolegium-nginx:latest
    ports: ["80:80", "443:443"]
    depends_on: [api-gateway]
    
  # API Gateway  
  api-gateway:
    image: ghcr.io/username/kolegium-gateway:latest
    ports: ["8000:8000"]
    depends_on: [postgres, redis]
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - JWT_SECRET=${JWT_SECRET}
    
  # Domain Services
  content-scout:
    image: ghcr.io/username/kolegium-content-scout:latest
    depends_on: [postgres, redis]
    environment:
      - AG_UI_BROKER_URL=${REDIS_URL}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      
  trend-analyst:
    image: ghcr.io/username/kolegium-trend-analyst:latest
    depends_on: [postgres, redis]
    environment:
      - GOOGLE_TRENDS_API_KEY=${GOOGLE_TRENDS_API_KEY}
      
  editorial-strategist:
    image: ghcr.io/username/kolegium-editorial:latest
    depends_on: [postgres, redis]
    
  quality-assessor:
    image: ghcr.io/username/kolegium-quality:latest
    depends_on: [postgres, redis]
    environment:
      - FACT_CHECK_API_KEY=${FACT_CHECK_API_KEY}
      
  decision-coordinator:
    image: ghcr.io/username/kolegium-coordinator:latest
    depends_on: [postgres, redis]
    
  # Frontend
  frontend:
    image: ghcr.io/username/kolegium-frontend:latest
    ports: ["3000:3000"]
    environment:
      - REACT_APP_API_URL=http://api-gateway:8000
      - REACT_APP_WS_URL=ws://api-gateway:8000/ws
    
  # Infrastructure
  postgres:
    image: postgres:15-alpine
    volumes: ["postgres_data:/var/lib/postgresql/data"]
    environment:
      - POSTGRES_DB=kolegium
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      
  redis:
    image: redis:7-alpine
    volumes: ["redis_data:/data"]
    command: redis-server --appendonly yes
    
  # Monitoring
  prometheus:
    image: prom/prometheus:latest
    volumes: ["./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml"]
    ports: ["9090:9090"]
    
  grafana:
    image: grafana/grafana:latest
    volumes: ["grafana_data:/var/lib/grafana"]
    ports: ["3001:3000"]
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}
      
  jaeger:
    image: jaegertracing/all-in-one:latest
    ports: ["16686:16686"]
    
  # Auto-deployment
  watchtower:
    image: containrrr/watchtower:latest
    volumes: ["/var/run/docker.sock:/var/run/docker.sock"]
    environment:
      - WATCHTOWER_POLL_INTERVAL=60
      - WATCHTOWER_CLEANUP=true
      - WATCHTOWER_LABEL_ENABLE=true
    command: --interval 60 --cleanup
```

## 🔄 CI/CD Pipeline

### GitHub Actions Workflow

```yaml
# .github/workflows/ci-cd.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        service: [content-scout, trend-analyst, editorial, quality, coordinator, frontend]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
        
    - name: Setup Node.js (for frontend)
      if: matrix.service == 'frontend'
      uses: actions/setup-node@v4
      with:
        node-version: '18'
        
    - name: Install dependencies
      run: |
        if [ "${{ matrix.service }}" = "frontend" ]; then
          cd frontend && npm ci
        else
          cd services/${{ matrix.service }} && pip install -r requirements.txt
        fi
        
    - name: Run tests
      run: |
        if [ "${{ matrix.service }}" = "frontend" ]; then
          cd frontend && npm test -- --coverage --watchAll=false
        else
          cd services/${{ matrix.service }} && python -m pytest --cov=src --cov-report=xml
        fi
        
    - name: Upload coverage
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
        flags: ${{ matrix.service }}
        
  security-scan:
    runs-on: ubuntu-latest
    needs: test
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Run Trivy vulnerability scanner
      uses: aquasecurity/trivy-action@master
      with:
        scan-type: 'fs'
        scan-ref: '.'
        format: 'sarif'
        output: 'trivy-results.sarif'
        
    - name: Upload Trivy scan results
      uses: github/codeql-action/upload-sarif@v2
      with:
        sarif_file: 'trivy-results.sarif'
        
  build-and-push:
    runs-on: ubuntu-latest
    needs: [test, security-scan]
    if: github.ref == 'refs/heads/main'
    
    strategy:
      matrix:
        service: [
          nginx, api-gateway, content-scout, trend-analyst, 
          editorial, quality, coordinator, frontend
        ]
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Log in to Container Registry
      uses: docker/login-action@v2
      with:
        registry: ${{ env.REGISTRY }}
        username: ${{ github.actor }}
        password: ${{ secrets.GITHUB_TOKEN }}
        
    - name: Extract metadata
      id: meta
      uses: docker/metadata-action@v4
      with:
        images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}-${{ matrix.service }}
        tags: |
          type=ref,event=branch
          type=ref,event=pr
          type=sha,prefix={{branch}}-
          type=raw,value=latest,enable={{is_default_branch}}
          
    - name: Build and push Docker image
      uses: docker/build-push-action@v4
      with:
        context: ./services/${{ matrix.service }}
        push: true
        tags: ${{ steps.meta.outputs.tags }}
        labels: ${{ steps.meta.outputs.labels }}
        cache-from: type=gha
        cache-to: type=gha,mode=max
        
  deploy:
    runs-on: ubuntu-latest
    needs: build-and-push
    if: github.ref == 'refs/heads/main'
    
    steps:
    - name: Deploy to Digital Ocean
      uses: appleboy/ssh-action@v0.1.5
      with:
        host: 46.101.156.14
        username: editorial
        key: ${{ secrets.DO_SSH_KEY }}
        script: |
          cd /home/editorial/kolegium
          git pull origin main
          docker-compose -f docker-compose.prod.yml down
          docker-compose -f docker-compose.prod.yml pull
          docker-compose -f docker-compose.prod.yml up -d
          
          # Health check
          sleep 30
          curl -f http://localhost:8000/health || exit 1
          
    - name: Notify deployment
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        channel: '#deployments'
        webhook_url: ${{ secrets.SLACK_WEBHOOK }}
```

## 🔧 Service-Specific Dockerfiles

### API Gateway Dockerfile
```dockerfile
# services/api-gateway/Dockerfile
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ python3-dev libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -u 1000 app && chown -R app:app /app
USER app

# Install Python dependencies
COPY --chown=app:app requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Add local bin to PATH
ENV PATH="/home/app/.local/bin:${PATH}"

# Copy source code
COPY --chown=app:app . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Content Scout Dockerfile
```dockerfile
# services/content-scout/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# System dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ python3-dev libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

# Create user
RUN useradd -m -u 1000 scout && chown -R scout:scout /app
USER scout

# Python dependencies
COPY --chown=scout:scout requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

ENV PATH="/home/scout/.local/bin:${PATH}"

# Application code
COPY --chown=scout:scout . .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import sys; sys.exit(0)" || exit 1

CMD ["python", "-m", "src.main"]
```

### Frontend Dockerfile
```dockerfile
# services/frontend/Dockerfile
FROM node:18-alpine as build

WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm ci --only=production

# Build application
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine

# Copy built application
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost || exit 1

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

## 🔍 Monitoring & Observability

### Prometheus Configuration
```yaml
# monitoring/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'kolegium-api-gateway'
    static_configs:
      - targets: ['api-gateway:8000']
    metrics_path: '/metrics'
    
  - job_name: 'kolegium-content-scout'
    static_configs:
      - targets: ['content-scout:8001']
      
  - job_name: 'kolegium-trend-analyst'
    static_configs:
      - targets: ['trend-analyst:8002']
      
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
      
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
```

### Alert Rules
```yaml
# monitoring/alert_rules.yml
groups:
- name: kolegium_alerts
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "High error rate detected"
      
  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: "Service {{ $labels.instance }} is down"
      
  - alert: HighMemoryUsage
    expr: container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.9
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High memory usage on {{ $labels.container_label_com_docker_compose_service }}"
      
  - alert: AgentResponseSlow
    expr: ag_ui_agent_response_duration_seconds > 2
    for: 2m
    labels:
      severity: warning
    annotations:
      summary: "Agent {{ $labels.agent_id }} response time > 2s"
```

## 🔐 Security Configuration

### Environment Variables Template
```bash
# .env.production
# Database
DATABASE_URL=postgresql://kolegium:${DB_PASSWORD}@postgres:5432/kolegium
DB_USER=kolegium
DB_PASSWORD=${SECURE_DB_PASSWORD}

# Redis
REDIS_URL=redis://redis:6379

# Authentication
JWT_SECRET=${SECURE_JWT_SECRET}
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=1440

# External APIs
OPENAI_API_KEY=${OPENAI_API_KEY}
GOOGLE_TRENDS_API_KEY=${GOOGLE_TRENDS_API_KEY}
FACT_CHECK_API_KEY=${FACT_CHECK_API_KEY}

# Monitoring
GRAFANA_PASSWORD=${SECURE_GRAFANA_PASSWORD}
PROMETHEUS_AUTH_TOKEN=${PROMETHEUS_AUTH_TOKEN}

# Security
CORS_ORIGINS=https://your-domain.com
RATE_LIMIT_PER_MINUTE=60
MAX_REQUEST_SIZE=10MB

# AG-UI Configuration
AG_UI_WEBSOCKET_TIMEOUT=300
AG_UI_MAX_CONNECTIONS=1000
AG_UI_EVENT_RETENTION_DAYS=30
```

### Nginx Security Configuration
```nginx
# services/nginx/nginx.conf
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    
    # Security Headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Rate Limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/s;
    limit_req_zone $binary_remote_addr zone=login:10m rate=1r/s;
    
    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # API
    location /api/ {
        limit_req zone=api burst=20 nodelay;
        proxy_pass http://api-gateway:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # WebSocket
    location /ws {
        proxy_pass http://api-gateway:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 300s;
        proxy_send_timeout 300s;
    }
}
```

## 📋 Deployment Checklist

### Pre-Deployment
- [ ] All tests passing (>80% coverage)
- [ ] Security scan passed
- [ ] Docker images built successfully
- [ ] Environment variables configured
- [ ] SSL certificates ready
- [ ] Database migrations prepared

### Deployment Steps
1. **Build Phase**
   ```bash
   # Automated by GitHub Actions
   docker build -t ghcr.io/username/kolegium-service:latest .
   docker push ghcr.io/username/kolegium-service:latest
   ```

2. **Deploy Phase**
   ```bash
   # On Digital Ocean droplet
   cd /home/editorial/kolegium
   docker-compose -f docker-compose.prod.yml pull
   docker-compose -f docker-compose.prod.yml up -d
   ```

3. **Verification Phase**
   ```bash
   # Health checks
   curl -f https://your-domain.com/health
   curl -f https://your-domain.com/api/health
   
   # Service checks
   docker-compose ps
   docker-compose logs --tail=50
   ```

### Post-Deployment
- [ ] All services healthy
- [ ] Monitoring dashboards updated
- [ ] Load balancer routing correctly
- [ ] WebSocket connections working
- [ ] AG-UI events flowing
- [ ] Database connections stable

## 🚨 Emergency Procedures

### Rollback Process
```bash
# Quick rollback to previous version
cd /home/editorial/kolegium
docker-compose -f docker-compose.prod.yml down
git checkout HEAD~1
docker-compose -f docker-compose.prod.yml up -d

# Verify rollback
curl -f https://your-domain.com/health

# If successful, update monitoring
echo "Rollback completed at $(date)" >> /var/log/deployments.log
```

### Emergency Contacts
- **Technical Issues**: DevOps Lead
- **Security Incidents**: Security Officer  
- **Business Impact**: Product Owner
- **Infrastructure**: Digital Ocean Support

### Monitoring Alerts
- **Slack Channel**: #kolegium-alerts
- **Email**: ops-team@company.com
- **PagerDuty**: For critical issues
- **Phone**: Emergency on-call rotation

---

**Key Principles**:
1. **Automate Everything** - Zero manual steps
2. **Monitor Everything** - Full observability
3. **Secure by Default** - Security-first approach
4. **Fail Fast** - Quick detection and recovery
5. **Document Everything** - Clear procedures for all scenarios