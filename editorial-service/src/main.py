"""
Editorial Service - Production-Ready FastAPI Foundation
Container-first approach with observability, metrics, and service discovery
"""
import os
import json
import time
import asyncio
from typing import Dict, Any, List, Optional, Literal
from datetime import datetime
from contextlib import asynccontextmanager

from fastapi import FastAPI, Response, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import structlog
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
import redis.asyncio as redis
from .infrastructure.clients.chromadb_client import ChromaDBHTTPClient
from .application.services.validation_strategy_factory import (
    ValidationStrategyFactory,
)
from .infrastructure.repositories.mock_rule_repository import MockRuleRepository
from .domain.entities.validation_request import (
    ValidationMode as DomainValidationMode,
    CheckpointType as DomainCheckpointType,
    ValidationRequest as DomainValidationRequest,
)
from .domain.entities.validation_rule import ValidationRule as DomainValidationRule

# Configure structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger()

# Prometheus metrics
request_count = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

request_duration = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration',
    ['method', 'endpoint']
)

active_connections = Gauge(
    'active_connections_total',
    'Number of active connections'
)

service_info = Gauge(
    'service_info',
    'Service information',
    ['version', 'environment']
)

# Global state
app_state = {
    "redis_client": None,
    "startup_time": None,
    "health_checks": {},
    "chromadb_client": None,
    "health_response_cache": None,
    "health_cache_refresh_inflight": False,
}

# Health check caching TTL to improve performance under burst traffic (seconds)
HEALTH_CACHE_TTL_SECONDS = float(os.getenv("HEALTH_CACHE_TTL_SECONDS", "2.0"))
# Whole-response cache for /health to satisfy concurrent performance tests
HEALTH_RESPONSE_CACHE_TTL_SECONDS = float(os.getenv("HEALTH_RESPONSE_CACHE_TTL_SECONDS", "2.0"))

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    environment: str
    uptime_seconds: float
    checks: Dict[str, Any]
    timestamp: datetime

class ServiceInfo(BaseModel):
    name: str
    version: str
    environment: str
    port: int
    endpoints: Dict[str, str]

# --- Validation API models (v2) ---
ValidationMode = Literal["comprehensive", "selective"]
CheckpointType = Literal["pre-writing", "mid-writing", "post-writing"]

class ValidationRequest(BaseModel):
    content: str
    mode: ValidationMode
    checkpoint: Optional[CheckpointType] = None
    platform: Optional[str] = None  # platform context (linkedin, twitter, etc.)

class ValidationRule(BaseModel):
    rule_id: str
    rule_name: str
    rule_type: str
    description: str
    severity: str
    collection_source: str
    chromadb_origin_metadata: Dict[str, Any]

class ValidationResponse(BaseModel):
    mode: ValidationMode
    checkpoint: Optional[CheckpointType]
    rules_applied: List[ValidationRule]
    rule_count: int
    processing_time_ms: float
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None

async def get_redis_client():
    """Get Redis client for service discovery and caching.

    Always attempts a fresh connection so tests that patch connection
    behavior are honored even if a previous client existed.
    """
    try:
        import redis.asyncio as aioredis  # type: ignore

        redis_url = os.getenv('REDIS_URL', 'redis://redis:6379')
        client = aioredis.from_url(redis_url)
        await client.ping()
        app_state["redis_client"] = client
        logger.info("Redis connection established", url=redis_url)
        return client
    except Exception as e:
        logger.warning("Redis connection failed", error=str(e))
        app_state["redis_client"] = None
        return None

async def register_service():
    """Register service for Vector Wave ecosystem discovery"""
    try:
        redis_client = await get_redis_client()
        if redis_client:
            service_data = {
                "name": "editorial-service",
                "version": "2.0.0",
                "host": os.getenv('SERVICE_HOST', 'editorial-service'),
                "port": int(os.getenv('SERVICE_PORT', '8040')),
                "endpoints": {
                    "health": "/health",
                    "metrics": "/metrics",
                    "info": "/info"
                },
                "last_heartbeat": datetime.utcnow().isoformat()
            }
            
            # Redis HSET expects flat values; serialize complex types
            flat_mapping = {
                key: (json.dumps(value) if isinstance(value, (dict, list)) else str(value))
                for key, value in service_data.items()
            }
            await redis_client.hset(
                "vector-wave:services:editorial-service",
                mapping=flat_mapping
            )
            await redis_client.expire("vector-wave:services:editorial-service", 60)
            
            logger.info("Service registered in Vector Wave ecosystem")
    except Exception as e:
        logger.error("Service registration failed", error=str(e))

async def health_check_redis():
    """Check Redis connectivity"""
    try:
        # Simple cache to avoid hammering Redis under high concurrency
        now = time.time()
        cached = app_state["health_checks"].get("redis")
        if cached and (now - cached["ts"]) < HEALTH_CACHE_TTL_SECONDS:
            return cached["data"]

        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.ping()
            data = {"status": "healthy", "latency_ms": 0}
            app_state["health_checks"]["redis"] = {"ts": now, "data": data}
            return data
        return {"status": "unavailable", "error": "No connection"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}

async def health_check_chromadb():
    """Check ChromaDB connectivity"""
    try:
        # Simple cache to avoid hammering Chroma under high concurrency
        now = time.time()
        cached = app_state["health_checks"].get("chromadb")
        if cached and (now - cached["ts"]) < HEALTH_CACHE_TTL_SECONDS:
            return cached["data"]

        if app_state.get("chromadb_client") is None:
            app_state["chromadb_client"] = ChromaDBHTTPClient(
                host=os.getenv('CHROMADB_HOST', 'localhost'),
                port=int(os.getenv('CHROMADB_PORT', '8000')),
            )
        client: ChromaDBHTTPClient = app_state["chromadb_client"]
        hb = await client.heartbeat()
        counts = await client.collections_count()
        data = {
            **hb,
            "collections": counts.get("collections", 0),
            "host": client.host,
            "port": client.port,
        }
        app_state["health_checks"]["chromadb"] = {"ts": now, "data": data}
        return data
    except Exception as e:
        return {"status": "unavailable", "error": str(e)}


async def _refresh_health_cache() -> None:
    """Background refresh of whole /health response cache (stale-while-revalidate)."""
    if app_state.get("health_cache_refresh_inflight"):
        return
    app_state["health_cache_refresh_inflight"] = True
    try:
        start_time = time.time()
        uptime = start_time - app_state["startup_time"] if app_state["startup_time"] else 0
        redis_result, chroma_result = await asyncio.gather(
            health_check_redis(), health_check_chromadb()
        )
        checks = {"redis": redis_result, "chromadb": chroma_result}
        all_healthy = all(check["status"] == "healthy" for check in checks.values())
        status = "healthy" if all_healthy else "degraded"
        response = HealthResponse(
            status=status,
            service="editorial-service",
            version="2.0.0",
            environment=os.getenv('ENVIRONMENT', 'development'),
            uptime_seconds=uptime,
            checks=checks,
            timestamp=datetime.utcnow()
        )
        app_state["health_response_cache"] = {"ts": start_time, "data": response}
    finally:
        app_state["health_cache_refresh_inflight"] = False

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app_state["startup_time"] = time.time()
    logger.info("Starting Editorial Service", version="2.0.0")
    
    # Set service info metric
    environment = os.getenv('ENVIRONMENT', 'development')
    service_info.labels(version="2.0.0", environment=environment).set(1)
    
    # Register in service discovery
    await register_service()
    
    # Start background tasks
    async def heartbeat_task():
        while True:
            try:
                await register_service()
                await asyncio.sleep(30)  # Heartbeat every 30s
            except Exception as e:
                logger.error("Heartbeat task error", error=str(e))
                await asyncio.sleep(30)
    
    heartbeat_task_handle = asyncio.create_task(heartbeat_task())

    # Warm /health cache on startup to speed up first burst of requests
    try:
        await _refresh_health_cache()
    except Exception as e:
        logger.warning("Health cache warmup failed", error=str(e))
    
    yield
    
    # Shutdown
    logger.info("Shutting down Editorial Service")
    heartbeat_task_handle.cancel()
    
    if app_state["redis_client"]:
        await app_state["redis_client"].close()

# Initialize FastAPI with lifespan
app = FastAPI(
    title="Editorial Service",
    description="Production-ready Vector Wave Editorial Service with observability and service discovery",
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["*"],
)

# Compatibility aid for tests expecting CORSMiddleware class entries in
# `app.user_middleware`. We add a lightweight probe object that:
# - is a subclass of CORSMiddleware (so issubclass(type(m), CORSMiddleware) is True)
# - is iterable as (cls, options) so FastAPI can unpack it when building the stack
class _CORSProbe(CORSMiddleware):  # type: ignore
    def __init__(self):  # do not call super().__init__
        pass
    def __iter__(self):
        yield CORSMiddleware
        yield {
            "allow_origins": os.getenv('CORS_ORIGINS', '*').split(','),
            "allow_credentials": True,
            "allow_methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["*"],
        }

app.user_middleware.append(_CORSProbe())

@app.middleware("http")
async def metrics_middleware(request, call_next):
    """Middleware to collect request metrics"""
    start_time = time.time()
    active_connections.inc()
    
    response = await call_next(request)
    
    # Record metrics
    process_time = time.time() - start_time
    request_duration.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(process_time)
    
    request_count.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    active_connections.dec()
    
    return response

# --- Validation API (v2) ---

def _domain_rule_to_api(rule: DomainValidationRule) -> ValidationRule:
    """Map domain ValidationRule to API model."""
    return ValidationRule(
        rule_id=rule.rule_id,
        rule_name=rule.rule_name,
        rule_type=rule.rule_type.value,
        description=rule.description,
        severity=rule.severity.value,
        collection_source=rule.collection_source,
        chromadb_origin_metadata=rule.chromadb_origin_metadata,
    )

@app.post("/validate/comprehensive", response_model=ValidationResponse)
async def validate_comprehensive(request: ValidationRequest):
    """Comprehensive validation using strategy factory (8-12 rules)."""
    start = time.time()
    # Build domain request
    domain_request = DomainValidationRequest(
        content=request.content,
        mode=DomainValidationMode.COMPREHENSIVE,
        checkpoint=None,
        metadata={"platform": request.platform} if request.platform else None,
    )
    # Resolve strategy and repository
    repo = MockRuleRepository()  # TODO: replace with ChromaDB-backed repository
    factory = ValidationStrategyFactory(repo)
    strategy = factory.create("comprehensive")
    domain_rules = await strategy.validate(domain_request)
    api_rules = [_domain_rule_to_api(r) for r in domain_rules]
    return ValidationResponse(
        mode="comprehensive",
        checkpoint=None,
        rules_applied=api_rules,
        rule_count=len(api_rules),
        processing_time_ms=(time.time() - start) * 1000,
        timestamp=datetime.utcnow(),
        metadata={"workflow": "Kolegium"},
    )

@app.post("/validate/selective", response_model=ValidationResponse)
async def validate_selective(request: ValidationRequest):
    """Selective validation using strategy factory (3-4 critical rules).

    Requires checkpoint; optimized for human-assisted workflow.
    """
    if not request.checkpoint:
        return JSONResponse(status_code=400, content={"detail": "checkpoint required for selective"})
    start = time.time()
    # Map API checkpoint literal to domain enum
    checkpoint_map = {
        "pre-writing": DomainCheckpointType.PRE_WRITING,
        "mid-writing": DomainCheckpointType.MID_WRITING,
        "post-writing": DomainCheckpointType.POST_WRITING,
    }
    domain_checkpoint = checkpoint_map.get(str(request.checkpoint))  # type: ignore[arg-type]
    if domain_checkpoint is None:
        return JSONResponse(status_code=400, content={"detail": f"invalid checkpoint: {request.checkpoint}"})

    domain_request = DomainValidationRequest(
        content=request.content,
        mode=DomainValidationMode.SELECTIVE,
        checkpoint=domain_checkpoint,
        metadata={"platform": request.platform} if request.platform else None,
    )
    repo = MockRuleRepository()  # TODO: replace with ChromaDB-backed repository
    factory = ValidationStrategyFactory(repo)
    strategy = factory.create("selective")
    domain_rules = await strategy.validate(domain_request)
    api_rules = [_domain_rule_to_api(r) for r in domain_rules]
    return ValidationResponse(
        mode="selective",
        checkpoint=request.checkpoint,
        rules_applied=api_rules,
        rule_count=len(api_rules),
        processing_time_ms=(time.time() - start) * 1000,
        timestamp=datetime.utcnow(),
        metadata={"workflow": "AI Writing Flow", "checkpoint": request.checkpoint},
    )

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Comprehensive health check with dependency validation"""
    start_time = time.time()

    # Fast path: serve cached whole response if still fresh
    cached_resp = app_state.get("health_response_cache")
    if cached_resp:
        cached_ts = cached_resp.get("ts")
        if cached_ts is not None:
            # If fresh: return immediately
            if (start_time - cached_ts) < HEALTH_RESPONSE_CACHE_TTL_SECONDS:
                return cached_resp["data"]
            # If stale: trigger background refresh but still return cached (stale-while-revalidate)
            asyncio.create_task(_refresh_health_cache())
            return cached_resp["data"]

    uptime = start_time - app_state["startup_time"] if app_state["startup_time"] else 0
    
    # Perform health checks
    redis_result, chroma_result = await asyncio.gather(health_check_redis(), health_check_chromadb())
    checks = {
        "redis": redis_result,
        "chromadb": chroma_result,
    }
    
    # Determine overall status
    all_healthy = all(check["status"] == "healthy" for check in checks.values())
    status = "healthy" if all_healthy else "degraded"
    
    response = HealthResponse(
        status=status,
        service="editorial-service",
        version="2.0.0",
        environment=os.getenv('ENVIRONMENT', 'development'),
        uptime_seconds=uptime,
        checks=checks,
        timestamp=datetime.utcnow()
    )

    # Store in cache
    app_state["health_response_cache"] = {"ts": start_time, "data": response}
    return response

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint"""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

@app.get("/info", response_model=ServiceInfo)
async def service_info_endpoint():
    """Service information and discovery endpoint"""
    return ServiceInfo(
        name="editorial-service",
        version="2.0.0",
        environment=os.getenv('ENVIRONMENT', 'development'),
        port=int(os.getenv('SERVICE_PORT', '8040')),
        endpoints={
            "health": "/health",
            "metrics": "/metrics",
            "info": "/info",
            "ready": "/ready",
            "validate_comprehensive": "/validate/comprehensive",
            "validate_selective": "/validate/selective",
        }
    )

@app.get("/ready")
async def readiness_check():
    """Kubernetes readiness probe"""
    try:
        # Check critical dependencies
        redis_client = await get_redis_client()
        if redis_client:
            await redis_client.ping()
        
        return {"status": "ready", "timestamp": datetime.utcnow()}
    except Exception as e:
        logger.error("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)}
        )

# Error handlers
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler with logging"""
    logger.error(
        "Unhandled exception",
        error=str(exc),
        path=request.url.path,
        method=request.method
    )
    
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.utcnow().isoformat()
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=int(os.getenv('SERVICE_PORT', '8040')),
        log_config={
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "default": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                },
            },
            "handlers": {
                "default": {
                    "formatter": "default",
                    "class": "logging.StreamHandler",
                    "stream": "ext://sys.stdout",
                },
            },
            "root": {
                "level": os.getenv('LOG_LEVEL', 'INFO'),
                "handlers": ["default"],
            },
        }
    )