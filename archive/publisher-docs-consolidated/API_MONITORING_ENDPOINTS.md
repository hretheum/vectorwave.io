# 📡 Platform Health Monitoring API Documentation

**Version**: 1.0.0  
**Last Updated**: 2025-08-08  
**Phase**: Phase 8 - Advanced Platform Health Monitoring

---

## 🎯 Overview

This document provides comprehensive API documentation for the advanced platform health monitoring system implemented in Phase 8. All endpoints are production-ready and integrated with the existing Multi-Channel Publisher API.

## 🔌 Base URLs

- **Orchestrator**: `http://localhost:8085`
- **Twitter Adapter**: `http://localhost:8083`
- **Ghost Adapter**: `http://localhost:8086`
- **Beehiiv Adapter**: `http://localhost:8087`
- **LinkedIn Adapter**: Integrated with session monitoring

---

## 🏥 Enhanced Health Check Endpoints

### GET /platforms/health

**Description**: Global health overview for all platform adapters

**Response**:
```json
{
  "overall_status": "healthy",
  "platforms": {
    "twitter": {
      "status": "healthy",
      "response_time_ms": 120,
      "last_check": "2025-08-08T14:25:30Z"
    },
    "ghost": {
      "status": "healthy", 
      "response_time_ms": 85,
      "last_check": "2025-08-08T14:25:28Z"
    }
  },
  "summary": {
    "healthy_count": 2,
    "total_count": 4,
    "average_response_time_ms": 102.5
  }
}
```

### GET /adapters/{platform}/health

**Description**: Enhanced health check for specific platform adapter

**Parameters**:
- `platform` (path): Platform name (`twitter`, `ghost`, `beehiiv`, `linkedin`)

**Response**:
```json
{
  "status": "healthy",
  "service": "twitter-adapter",
  "platform": "twitter",
  "connection": {
    "status": "connected",
    "last_test": "2025-08-08T14:25:30Z",
    "test_duration_ms": 120
  },
  "rate_limits": {
    "current_usage": 45,
    "limit": 100,
    "percentage_used": 45.0,
    "reset_time": "2025-08-08T15:30:00Z",
    "time_until_reset_minutes": 65
  },
  "session": {
    "status": "active",
    "account": "default",
    "expires_at": "2025-08-08T18:00:00Z",
    "time_until_expiry_hours": 3.6
  },
  "capabilities": {
    "can_publish": true,
    "can_schedule": true,
    "can_upload_media": true,
    "can_delete": false
  },
  "metrics": {
    "last_successful_operation": "2025-08-08T14:20:15Z",
    "operations_count_24h": 23,
    "average_response_time_ms": 145,
    "success_rate_percentage": 98.5
  }
}
```

**Status Codes**:
- `200`: Health check successful
- `503`: Platform unhealthy
- `404`: Platform adapter not found

---

## 📈 Rate Limit Monitoring Endpoints

### GET /rate-limits/status

**Description**: Rate limit status across all platforms

**Response**:
```json
{
  "timestamp": "2025-08-08T14:25:30Z",
  "platforms": {
    "twitter": {
      "hour_usage": 12,
      "hour_limit": 100,
      "day_usage": 234,
      "day_limit": 2000,
      "month_usage": 5670,
      "month_limit": 50000,
      "should_throttle": false,
      "throttle_until": null
    },
    "ghost": {
      "hour_usage": 8,
      "hour_limit": 50,
      "day_usage": 89,
      "day_limit": 500,
      "month_usage": 1234,
      "month_limit": 10000,
      "should_throttle": false,
      "throttle_until": null
    }
  },
  "alerts": [
    {
      "platform": "twitter",
      "threshold": 90,
      "current": 78.5,
      "status": "ok"
    }
  ]
}
```

### GET /rate-limits/{platform}

**Description**: Detailed rate limit information for specific platform

**Parameters**:
- `platform` (path): Platform name
- `period` (query, optional): Time period (`hour`, `day`, `month`)

**Response**:
```json
{
  "platform": "twitter",
  "current_period": "hour",
  "usage": 12,
  "limit": 100,
  "percentage_used": 12.0,
  "remaining": 88,
  "reset_time": "2025-08-08T15:00:00Z",
  "time_until_reset_minutes": 35,
  "should_throttle": false,
  "throttle_recommendation": null,
  "historical_usage": {
    "last_hour": 12,
    "last_day": 234,
    "last_month": 5670
  }
}
```

### POST /rate-limits/{platform}/track

**Description**: Manually track rate limit usage (for testing)

**Parameters**:
- `platform` (path): Platform name

**Request Body**:
```json
{
  "request_type": "api",
  "count": 1
}
```

**Response**:
```json
{
  "success": true,
  "new_usage": 13,
  "percentage_used": 13.0,
  "should_throttle": false
}
```

---

## 🔐 Session Health Tracking Endpoints

### GET /session/health

**Description**: Overall session health for browser-based platforms

**Response**:
```json
{
  "timestamp": "2025-08-08T14:25:30Z",
  "platforms": {
    "linkedin": {
      "account": "default",
      "status": "active",
      "health_score": 95.0,
      "expires_at": "2025-08-08T18:00:00Z",
      "time_until_expiry_hours": 3.6,
      "needs_refresh": false
    }
  },
  "alerts": [
    {
      "platform": "linkedin",
      "account": "default", 
      "alert_type": "expiry_warning",
      "severity": "low",
      "time_until_expiry_hours": 3.6
    }
  ]
}
```

### POST /session/validate

**Description**: Validate session for specific platform and account

**Request Body**:
```json
{
  "platform": "linkedin",
  "account": "default"
}
```

**Response**:
```json
{
  "platform": "linkedin",
  "account": "default",
  "is_valid": true,
  "health_score": 95.0,
  "logged_in": true,
  "session_active": true,
  "expires_at": "2025-08-08T18:00:00Z",
  "capabilities": ["publish", "schedule"],
  "last_activity": "2025-08-08T14:20:00Z",
  "validation_timestamp": "2025-08-08T14:25:30Z"
}
```

### POST /session/monitor/start

**Description**: Start session monitoring for platform/account

**Request Body**:
```json
{
  "platform": "linkedin",
  "account": "default",
  "check_interval_minutes": 30
}
```

**Response**:
```json
{
  "success": true,
  "monitoring_started": true,
  "platform": "linkedin",
  "account": "default",
  "check_interval_minutes": 30,
  "next_check": "2025-08-08T14:55:30Z"
}
```

### POST /session/monitor/stop

**Description**: Stop session monitoring

**Request Body**:
```json
{
  "platform": "linkedin", 
  "account": "default"
}
```

### GET /session/history/{platform}/{account}

**Description**: Session validation history

**Response**:
```json
{
  "platform": "linkedin",
  "account": "default",
  "history": [
    {
      "timestamp": "2025-08-08T14:25:30Z",
      "health_score": 95.0,
      "is_valid": true,
      "response_time_ms": 120
    }
  ],
  "statistics": {
    "average_health_score": 95.0,
    "uptime_percentage": 99.8,
    "total_checks": 48
  }
}
```

---

## ⚡ Performance Metrics Endpoints

### GET /performance/metrics

**Description**: Comprehensive performance metrics for all platforms

**Parameters**:
- `hours` (query, optional): Time window in hours (default: 24)
- `include_history` (query, optional): Include historical trends (default: false)

**Response**:
```json
{
  "timestamp": "2025-08-08T14:25:30Z",
  "time_window_hours": 24,
  "platforms": {
    "twitter": {
      "total_requests": 234,
      "successful_requests": 230,
      "failed_requests": 4,
      "success_rate_percentage": 98.3,
      "response_times": {
        "p50_ms": 120,
        "p95_ms": 280,
        "p99_ms": 450,
        "average_ms": 145,
        "min_ms": 85,
        "max_ms": 520
      },
      "uptime_percentage": 99.8,
      "performance_level": "excellent",
      "throughput_per_hour": 9.75
    }
  },
  "overall": {
    "total_requests": 567,
    "average_success_rate": 97.8,
    "average_response_time_ms": 132,
    "best_performing_platform": "ghost",
    "needs_attention": []
  }
}
```

### GET /performance/{platform}

**Description**: Detailed performance metrics for specific platform

**Parameters**:
- `platform` (path): Platform name
- `hours` (query, optional): Time window in hours

**Response**:
```json
{
  "platform": "twitter",
  "time_window_hours": 24,
  "timestamp": "2025-08-08T14:25:30Z",
  "metrics": {
    "requests": {
      "total": 234,
      "successful": 230, 
      "failed": 4,
      "success_rate": 98.3
    },
    "response_times": {
      "percentiles": {
        "p50": 120,
        "p95": 280,
        "p99": 450
      },
      "statistics": {
        "average": 145,
        "min": 85,
        "max": 520,
        "std_dev": 67.2
      }
    },
    "availability": {
      "uptime_percentage": 99.8,
      "downtime_minutes": 2.88,
      "incident_count": 1
    },
    "performance_classification": {
      "level": "excellent",
      "score": 95.2,
      "factors": {
        "success_rate": "excellent",
        "response_time": "good", 
        "uptime": "excellent"
      }
    }
  },
  "trends": {
    "success_rate_trend": "stable",
    "response_time_trend": "improving",
    "availability_trend": "stable"
  }
}
```

### POST /performance/record

**Description**: Record performance data (for integration testing)

**Request Body**:
```json
{
  "platform": "twitter",
  "operation_type": "publish",
  "response_time_ms": 120,
  "success": true,
  "timestamp": "2025-08-08T14:25:30Z"
}
```

**Response**:
```json
{
  "success": true,
  "recorded": true,
  "platform": "twitter",
  "new_average_response_time_ms": 145
}
```

---

## 🔄 Automated Recovery System Endpoints

### GET /recovery/status

**Description**: Overall automated recovery system status

**Response**:
```json
{
  "system_status": "active",
  "timestamp": "2025-08-08T14:25:30Z",
  "active_incidents": 0,
  "total_incidents_24h": 3,
  "successful_recoveries_24h": 3,
  "recovery_success_rate": 100.0,
  "platforms": {
    "twitter": {
      "incidents_24h": 1,
      "successful_recoveries": 1,
      "last_incident": "2025-08-08T10:15:00Z",
      "circuit_breaker_status": "closed"
    },
    "ghost": {
      "incidents_24h": 2,
      "successful_recoveries": 2,
      "last_incident": "2025-08-08T12:30:00Z",
      "circuit_breaker_status": "closed"
    }
  }
}
```

### GET /recovery/incidents

**Description**: Active and recent failure incidents

**Parameters**:
- `status` (query, optional): Filter by status (`active`, `resolved`, `failed`)
- `platform` (query, optional): Filter by platform
- `hours` (query, optional): Time window (default: 24)

**Response**:
```json
{
  "incidents": [
    {
      "incident_id": "inc_2025080814251234",
      "platform": "twitter",
      "failure_type": "connection_timeout",
      "status": "resolved",
      "created_at": "2025-08-08T10:15:00Z",
      "resolved_at": "2025-08-08T10:16:30Z",
      "recovery_action": "retry_request",
      "attempts": 2,
      "success": true,
      "recovery_time_seconds": 90
    }
  ],
  "summary": {
    "total_incidents": 3,
    "active_incidents": 0,
    "resolved_incidents": 3,
    "failed_recoveries": 0,
    "average_recovery_time_seconds": 78
  }
}
```

### POST /recovery/trigger

**Description**: Manually trigger recovery procedure (for testing)

**Request Body**:
```json
{
  "platform": "twitter",
  "failure_type": "connection_timeout",
  "error_message": "Connection timeout after 30 seconds",
  "force_recovery": true
}
```

**Response**:
```json
{
  "incident_id": "inc_2025080814251234",
  "recovery_triggered": true,
  "platform": "twitter",
  "failure_type": "connection_timeout",
  "recovery_action": "retry_request",
  "estimated_recovery_time_seconds": 60
}
```

### GET /recovery/procedures

**Description**: Available recovery procedures for each failure type

**Response**:
```json
{
  "failure_types": {
    "connection_timeout": {
      "description": "Network connection timeout",
      "recovery_actions": ["retry_request", "check_network_connectivity"],
      "priority": "high",
      "max_attempts": 3
    },
    "authentication_failed": {
      "description": "Authentication or authorization failure", 
      "recovery_actions": ["refresh_token", "re_authenticate"],
      "priority": "critical",
      "max_attempts": 2
    }
  },
  "recovery_actions": {
    "retry_request": {
      "description": "Retry the failed request",
      "timeout_seconds": 30,
      "success_criteria": "HTTP 200 response"
    },
    "refresh_token": {
      "description": "Refresh authentication token",
      "timeout_seconds": 60,
      "success_criteria": "Valid token obtained"
    }
  }
}
```

---

## 📊 Monitoring & Alerting Integration

### GET /monitoring/alerts

**Description**: Current monitoring alerts from health system

**Response**:
```json
{
  "active_alerts": [
    {
      "alert_id": "alert_rate_limit_warning",
      "platform": "twitter",
      "type": "rate_limit_warning",
      "severity": "warning",
      "message": "Rate limit usage at 85% for twitter platform",
      "created_at": "2025-08-08T14:20:00Z",
      "threshold": 80,
      "current_value": 85
    }
  ],
  "alert_summary": {
    "total_alerts": 1,
    "critical_alerts": 0,
    "warning_alerts": 1,
    "info_alerts": 0
  }
}
```

### POST /monitoring/test-health-alert

**Description**: Test health monitoring alert system

**Request Body**:
```json
{
  "alert_type": "platform_health",
  "platform": "twitter",
  "severity": "warning",
  "message": "Test health monitoring alert"
}
```

---

## 🔧 Utility Endpoints

### GET /health/summary

**Description**: Quick health summary for all monitoring systems

**Response**:
```json
{
  "overall_health": "healthy",
  "systems": {
    "platform_health": "healthy",
    "rate_limits": "healthy",
    "sessions": "healthy", 
    "performance": "healthy",
    "recovery": "active"
  },
  "alerts_count": 0,
  "last_check": "2025-08-08T14:25:30Z"
}
```

### POST /health/refresh

**Description**: Force refresh of all health monitoring data

**Response**:
```json
{
  "refresh_triggered": true,
  "systems_refreshed": [
    "platform_health",
    "rate_limits", 
    "sessions",
    "performance"
  ],
  "refresh_timestamp": "2025-08-08T14:25:30Z"
}
```

---

## ❗ Error Responses

### Standard Error Format
```json
{
  "error": {
    "code": "HEALTH_CHECK_FAILED",
    "message": "Platform health check failed",
    "details": {
      "platform": "twitter",
      "reason": "Connection timeout",
      "retry_after_seconds": 30
    },
    "timestamp": "2025-08-08T14:25:30Z",
    "request_id": "req_1234567890"
  }
}
```

### Common Error Codes
- `PLATFORM_UNAVAILABLE`: Platform adapter not responding
- `RATE_LIMIT_EXCEEDED`: Rate limit threshold exceeded  
- `SESSION_INVALID`: Browser session validation failed
- `MONITORING_DISABLED`: Monitoring system disabled
- `RECOVERY_FAILED`: Automated recovery attempt failed

---

## 🚀 Usage Examples

### Complete Health Check Flow
```bash
# 1. Check overall platform health
curl http://localhost:8085/platforms/health | jq

# 2. Check specific platform details
curl http://localhost:8085/adapters/twitter/health | jq

# 3. Monitor rate limits
curl http://localhost:8085/rate-limits/status | jq

# 4. Check session health
curl http://localhost:8085/session/health | jq

# 5. Review performance metrics
curl http://localhost:8085/performance/metrics | jq

# 6. Check recovery system status
curl http://localhost:8085/recovery/status | jq
```

### Integration Testing
```bash
# Test rate limit tracking
curl -X POST http://localhost:8085/rate-limits/twitter/track \
  -H "Content-Type: application/json" \
  -d '{"request_type": "api", "count": 5}'

# Test session validation
curl -X POST http://localhost:8085/session/validate \
  -H "Content-Type: application/json" \
  -d '{"platform": "linkedin", "account": "default"}'

# Test recovery system
curl -X POST http://localhost:8085/recovery/trigger \
  -H "Content-Type: application/json" \
  -d '{"platform": "twitter", "failure_type": "connection_timeout"}'
```

---

**Document Version**: 1.0.0  
**API Version**: Phase 8 - Advanced Platform Health Monitoring  
**Last Updated**: 2025-08-08  
**Next Update**: Phase 9 integration documentation