# 🔄 Health Monitoring Migration Guide

**Version**: 1.0.0  
**Target**: Phase 8 - Advanced Platform Health Monitoring  
**Date**: 2025-08-08

---

## 🎯 Migration Overview

This guide helps teams migrate from basic platform adapters to the advanced health monitoring system implemented in Phase 8. The migration provides comprehensive platform health visibility, automated recovery, and proactive monitoring capabilities.

---

## 📋 Pre-Migration Checklist

### System Requirements
- [ ] **Docker**: Version 20.0+ with docker-compose
- [ ] **Python**: 3.11+ for health monitoring components
- [ ] **Redis**: 7.x for monitoring data storage
- [ ] **Environment Variables**: Monitoring configuration
- [ ] **API Access**: Platform API keys and credentials

### Current System Assessment
- [ ] **Platform Adapters**: Identify all active adapters
- [ ] **Health Endpoints**: Review existing `/health` endpoints
- [ ] **Monitoring**: Document current monitoring approach
- [ ] **Alerting**: Inventory existing alert mechanisms
- [ ] **Performance**: Baseline current performance metrics

---

## 🚀 Migration Steps

### Step 1: Environment Preparation

#### 1.1 Update Environment Variables
Add health monitoring configuration to your `.env` file:

```bash
# Health Monitoring Configuration
ENABLE_HEALTH_MONITORING=true
RATE_LIMIT_MONITORING=true
SESSION_MONITORING=true
PERFORMANCE_MONITORING=true
AUTOMATED_RECOVERY=true

# Monitoring Intervals
HEALTH_CHECK_INTERVAL=60
RATE_LIMIT_CHECK_INTERVAL=30
SESSION_CHECK_INTERVAL=300
PERFORMANCE_CHECK_INTERVAL=60

# Alert Thresholds
RATE_LIMIT_ALERT_THRESHOLD=90
SESSION_EXPIRY_WARNING_HOURS=2
PERFORMANCE_ALERT_THRESHOLD=2000
RECOVERY_MAX_ATTEMPTS=3

# Optional: Docker Environment Detection
DOCKER_ENV=true
```

#### 1.2 Update Docker Compose Configuration
Add health monitoring services to your `docker-compose.yml`:

```yaml
services:
  orchestrator:
    environment:
      - ENABLE_HEALTH_MONITORING=true
      - RATE_LIMIT_MONITORING=true
      - SESSION_MONITORING=true
      - PERFORMANCE_MONITORING=true
      - AUTOMATED_RECOVERY=true
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/platforms/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s

  # Add health monitoring volumes
  volumes:
    - monitoring_data:/app/monitoring
```

### Step 2: Platform Adapter Updates

#### 2.1 Enhanced Health Endpoint Migration

**Before (Basic Health Check)**:
```python
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "platform-adapter"}
```

**After (Enhanced Health Check)**:
```python
from platform_health_models import EnhancedHealthResponse, HealthStatus, ConnectionStatus

@app.get("/health", response_model=EnhancedHealthResponse)
async def health_check():
    # Test platform connection
    connection_status = await _check_platform_connection()
    
    # Get rate limit information
    rate_limit_info = await _check_rate_limits()
    
    # Validate session (for browser-based platforms)
    session_status = await _check_session_health()
    
    # Collect performance metrics
    metrics = await _collect_performance_metrics()
    
    return EnhancedHealthResponse(
        status=HealthStatus.HEALTHY,
        service=f"{PLATFORM_NAME}-adapter",
        platform=PLATFORM_NAME,
        connection=connection_status,
        rate_limits=rate_limit_info,
        session=session_status,
        capabilities=PlatformCapabilities(
            can_publish=True,
            can_schedule=True,
            can_upload_media=True,
            can_delete=False
        ),
        metrics=metrics
    )
```

#### 2.2 Rate Limit Integration

Add rate limit tracking to your platform adapters:

```python
from rate_limit_monitor import RateLimitMonitor

# Initialize rate limit monitor
rate_limit_monitor = RateLimitMonitor()

@app.post("/publish")
async def publish_content(request: PublishRequest):
    # Track rate limit usage before API call
    await rate_limit_monitor.track_publication(
        platform=PLATFORM_NAME,
        post_type="post",
        count=1
    )
    
    # Check if we should throttle
    should_throttle, wait_time = rate_limit_monitor.should_throttle(PLATFORM_NAME)
    if should_throttle:
        raise HTTPException(
            status_code=429, 
            detail=f"Rate limit threshold reached. Wait {wait_time} seconds."
        )
    
    # Proceed with publication
    result = await _publish_to_platform(request)
    
    # Track successful API request
    await rate_limit_monitor.track_request(PLATFORM_NAME, "api", 1)
    
    return result
```

#### 2.3 Session Health Integration (Browser-Based Platforms)

For platforms using browser automation:

```python
from session_health_monitor import SessionHealthMonitor

session_monitor = SessionHealthMonitor()

@app.post("/session/validate")
async def validate_session(account: str = "default"):
    result = await session_monitor.validate_session(PLATFORM_NAME, account)
    return result

@app.post("/session/monitor/start")
async def start_session_monitoring(account: str = "default"):
    success = await session_monitor.start_monitoring(PLATFORM_NAME, account)
    return {"success": success, "monitoring_started": success}
```

### Step 3: Orchestrator Integration

#### 3.1 Add Health Monitoring Components

Copy the health monitoring components to your orchestrator:

```bash
# Copy health monitoring files
cp src/orchestrator/platform_health_models.py /path/to/your/orchestrator/
cp src/orchestrator/rate_limit_monitor.py /path/to/your/orchestrator/
cp src/orchestrator/session_health_monitor.py /path/to/your/orchestrator/
cp src/orchestrator/performance_metrics_collector.py /path/to/your/orchestrator/
cp src/orchestrator/automated_recovery_system.py /path/to/your/orchestrator/
```

#### 3.2 Initialize Health Monitoring in Main Application

```python
from fastapi import FastAPI
from rate_limit_monitor import RateLimitMonitor
from session_health_monitor import SessionHealthMonitor
from performance_metrics_collector import PerformanceMetricsCollector
from automated_recovery_system import AutomatedRecoverySystem

app = FastAPI()

# Initialize monitoring components
rate_limit_monitor = RateLimitMonitor()
session_monitor = SessionHealthMonitor()
performance_collector = PerformanceMetricsCollector()
recovery_system = AutomatedRecoverySystem()

# Add health monitoring endpoints
@app.get("/platforms/health")
async def platforms_health():
    # Implementation from orchestrator/main.py
    pass

@app.get("/rate-limits/status")
async def rate_limits_status():
    # Implementation from orchestrator/main.py
    pass
```

### Step 4: Database Migration (Optional)

If you're using persistent storage for health data:

#### 4.1 Create Health Monitoring Tables

```sql
-- Performance metrics storage
CREATE TABLE IF NOT EXISTS performance_metrics (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    operation_type VARCHAR(50) NOT NULL,
    response_time_ms INTEGER NOT NULL,
    success BOOLEAN NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Rate limit tracking
CREATE TABLE IF NOT EXISTS rate_limit_usage (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    request_type VARCHAR(50) NOT NULL,
    count INTEGER NOT NULL DEFAULT 1,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Session health history
CREATE TABLE IF NOT EXISTS session_health (
    id SERIAL PRIMARY KEY,
    platform VARCHAR(50) NOT NULL,
    account VARCHAR(100) NOT NULL DEFAULT 'default',
    health_score DECIMAL(5,2) NOT NULL,
    is_valid BOOLEAN NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Recovery incidents
CREATE TABLE IF NOT EXISTS recovery_incidents (
    id SERIAL PRIMARY KEY,
    incident_id VARCHAR(100) UNIQUE NOT NULL,
    platform VARCHAR(50) NOT NULL,
    failure_type VARCHAR(100) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'active',
    recovery_action VARCHAR(100),
    attempts INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

#### 4.2 Migrate Existing Data (if applicable)

```python
# Example migration script for existing monitoring data
async def migrate_existing_data():
    # Migrate existing health check logs
    existing_health_logs = await get_existing_health_logs()
    
    for log in existing_health_logs:
        await performance_collector.record_performance(
            platform=log.platform,
            operation_type="health_check",
            response_time_ms=log.response_time,
            success=log.status == "healthy",
            timestamp=log.timestamp
        )
    
    print(f"Migrated {len(existing_health_logs)} health check records")
```

---

## 🧪 Testing Your Migration

### Step 1: Basic Health Check Validation

```bash
# Test enhanced health endpoints
curl http://localhost:8085/platforms/health | jq
curl http://localhost:8085/adapters/twitter/health | jq
curl http://localhost:8085/adapters/ghost/health | jq
```

Expected response format:
```json
{
  "status": "healthy",
  "platform": "twitter",
  "connection": {"status": "connected"},
  "rate_limits": {"percentage_used": 15.0},
  "capabilities": {"can_publish": true}
}
```

### Step 2: Rate Limit Monitoring Test

```bash
# Check rate limit status
curl http://localhost:8085/rate-limits/status | jq

# Test rate limit tracking
curl -X POST http://localhost:8085/rate-limits/twitter/track \
  -H "Content-Type: application/json" \
  -d '{"request_type": "api", "count": 5}'
```

### Step 3: Session Health Test (Browser Platforms)

```bash
# Validate session
curl -X POST http://localhost:8085/session/validate \
  -H "Content-Type: application/json" \
  -d '{"platform": "linkedin", "account": "default"}'

# Start monitoring
curl -X POST http://localhost:8085/session/monitor/start \
  -H "Content-Type: application/json" \
  -d '{"platform": "linkedin", "account": "default"}'
```

### Step 4: Performance Metrics Test

```bash
# Check performance metrics
curl http://localhost:8085/performance/metrics | jq

# Record test performance data
curl -X POST http://localhost:8085/performance/record \
  -H "Content-Type: application/json" \
  -d '{"platform": "twitter", "operation_type": "test", "response_time_ms": 120, "success": true}'
```

### Step 5: Recovery System Test

```bash
# Check recovery system status
curl http://localhost:8085/recovery/status | jq

# Test recovery procedure
curl -X POST http://localhost:8085/recovery/trigger \
  -H "Content-Type: application/json" \
  -d '{"platform": "twitter", "failure_type": "connection_timeout", "error_message": "Test recovery"}'
```

---

## 🚨 Migration Troubleshooting

### Common Issues and Solutions

#### Issue 1: Import Errors
```
ImportError: No module named 'platform_health_models'
```

**Solution**: Ensure health monitoring files are copied to each adapter directory:
```bash
# Copy to each adapter
cp src/orchestrator/platform_health_models.py src/adapters/twitter/
cp src/orchestrator/platform_health_models.py src/adapters/ghost/
cp src/orchestrator/platform_health_models.py src/adapters/beehiiv/
```

#### Issue 2: Docker Container Health Check Failures
```
Health check failed: Connection refused
```

**Solution**: Update Docker health check commands:
```yaml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
  # Instead of /platforms/health which might not be available yet
```

#### Issue 3: Rate Limit Monitor Not Working
```
AttributeError: 'NoneType' object has no attribute 'track_request'
```

**Solution**: Initialize rate limit monitor in each service:
```python
# In each adapter's main.py
from rate_limit_monitor import RateLimitMonitor
rate_limit_monitor = RateLimitMonitor()
```

#### Issue 4: Session Validation Errors
```
'SessionValidationResult' object has no attribute 'logged_in_user'
```

**Solution**: Use safe attribute access:
```python
logged_in = getattr(result, 'logged_in', getattr(result, 'logged_in_user', False))
```

#### Issue 5: Performance Metrics Docker URLs
```
Connection refused to localhost:8083 from Docker container
```

**Solution**: Use Docker service names and add environment detection:
```python
if os.getenv("DOCKER_ENV"):
    base_url = "http://twitter-adapter:8080"
else:
    base_url = "http://localhost:8083"
```

---

## 📊 Post-Migration Validation

### Health Monitoring Dashboard
After migration, verify your monitoring dashboard shows:
- ✅ All platform adapters reporting enhanced health status
- ✅ Rate limit usage tracking across all platforms
- ✅ Session health monitoring for browser-based platforms
- ✅ Performance metrics collection and analysis
- ✅ Automated recovery system active and responsive

### Performance Benchmarks
Expected performance after migration:
- **Health Check Response**: <50ms average
- **Rate Limit Calculation**: <10ms per request
- **Session Validation**: <200ms (including browser checks)
- **Performance Analysis**: <100ms for statistical calculations
- **Recovery System**: <5s average recovery time

### Monitoring Metrics
Verify these metrics are being collected:
- Platform health status (healthy/degraded/unhealthy)
- Response time percentiles (P50, P95, P99)
- Success rates per platform
- Rate limit usage patterns
- Session health scores
- Recovery success rates

---

## 🔧 Rollback Plan

If issues arise during migration, you can rollback:

### Step 1: Disable Health Monitoring
```bash
# Set in .env
ENABLE_HEALTH_MONITORING=false
RATE_LIMIT_MONITORING=false
SESSION_MONITORING=false
PERFORMANCE_MONITORING=false
AUTOMATED_RECOVERY=false
```

### Step 2: Revert to Basic Health Endpoints
```python
@app.get("/health")
async def health():
    return {"status": "healthy", "service": "platform-adapter"}
```

### Step 3: Remove Health Monitoring Components
```bash
# Remove health monitoring files if needed
rm platform_health_models.py
rm rate_limit_monitor.py
rm session_health_monitor.py
# etc.
```

---

## 📈 Benefits After Migration

### Operational Benefits
- **Proactive Monitoring**: Issues detected before user impact
- **Automated Recovery**: Reduced manual intervention needs
- **Performance Visibility**: Data-driven optimization opportunities
- **Comprehensive Alerts**: Multi-channel alert integration

### Technical Benefits
- **Unified Health Model**: Consistent health reporting across platforms
- **Rate Limit Awareness**: Intelligent throttling and usage optimization
- **Session Management**: Automated session health tracking
- **Statistical Analysis**: P50/P95/P99 performance insights
- **Circuit Breakers**: Preventing cascading failures

### Business Benefits
- **Improved Uptime**: Faster issue detection and resolution
- **Better User Experience**: Reduced failed publications
- **Cost Optimization**: Efficient platform usage through rate limit management
- **Scalability**: Foundation for enterprise-grade operations

---

## 📞 Support and Next Steps

### Getting Help
- **Documentation**: Review `API_MONITORING_ENDPOINTS.md` for detailed API docs
- **Testing**: Use provided test scripts and examples
- **Troubleshooting**: Check common issues section above
- **Integration**: Follow Phase 6 integration guide for AI Writing Flow

### Next Steps After Migration
1. **Phase 6 Integration**: Connect with AI Writing Flow for intelligent content generation
2. **Custom Dashboards**: Build Grafana dashboards for monitoring visualization
3. **Alert Tuning**: Adjust alert thresholds based on your usage patterns
4. **Performance Optimization**: Use metrics data to optimize platform performance

---

**Migration Guide Version**: 1.0.0  
**Target System**: Phase 8 - Advanced Platform Health Monitoring  
**Support**: Check Phase 8 documentation for detailed technical information  
**Next Update**: Phase 9 integration capabilities