# 🚀 Vector Wave Complete API Specifications
**Comprehensive API Documentation for ChromaDB-Centric Architecture**

## 📊 API Architecture Overview

### Service Ecosystem
```yaml
# Vector Wave Service Architecture
services:
  editorial-service:
    port: 8040
    purpose: "ChromaDB-centric content validation and rule management"
    type: "Core Intelligence"
    
  topic-manager:
    port: 8041
    purpose: "Topic database management with AI-powered suggestions"
    type: "Content Intelligence"
    
  crewai-orchestrator:
    port: 8042
    purpose: "CrewAI agent orchestration and flow execution"
    type: "AI Agent Coordination"
    
  publishing-orchestrator:
    port: 8080
    purpose: "Multi-platform publishing coordination"
    type: "Publishing Automation"
    
  chromadb-server:
    port: 8000
    purpose: "Vector database for all rules and content intelligence"
    type: "Data Layer"
    
  presentor-service:
    port: 8089
    purpose: "PPT/PDF generation for LinkedIn manual uploads"
    type: "Content Generation"
    
  analytics-blackbox:
    port: 8090
    purpose: "Performance tracking and user learning (placeholder)"
    type: "Business Intelligence"
```

### API Design Principles
✅ **ChromaDB-First**: All business logic sourced from vector database
✅ **REST + GraphQL**: RESTful APIs with GraphQL for complex queries
✅ **OpenAPI Compliant**: Complete Swagger/OpenAPI 3.0 documentation
✅ **Async by Default**: Non-blocking operations for better performance
✅ **Type Safety**: Pydantic models for request/response validation
✅ **Error Consistency**: Standardized error responses across all services
✅ **Rate Limiting**: Built-in protection against abuse
✅ **Security First**: JWT authentication and API key support

---

## 🎯 1. Editorial Service API (Port 8040)
**Core ChromaDB-centric validation and rule management service**

### 1.1 Authentication & Security

```yaml
# Authentication Configuration
authentication:
  methods: ["jwt_bearer", "api_key"]
  jwt_secret: "${JWT_SECRET_KEY}"
  token_expiry: "1h"
  api_key_prefix: "es_"
  
rate_limiting:
  authenticated_requests: "1000/hour"
  validation_requests: "500/hour"
  cache_requests: "100/minute"
  
security_headers:
  - "X-Content-Type-Options: nosniff"
  - "X-Frame-Options: DENY"
  - "Strict-Transport-Security: max-age=31536000"
```

### 1.2 Core Validation Endpoints

#### POST /validate/comprehensive
**Purpose**: Full validation for Kolegium AI-first workflow
```python
from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Dict, Optional
import uuid
from datetime import datetime

class ValidationRequest(BaseModel):
    content: str
    platform: str
    content_type: str
    context: Optional[Dict] = {}
    user_id: Optional[str] = None

class ValidationRule(BaseModel):
    rule_id: str
    content: str
    rule_type: str
    priority: str
    platform: str
    confidence: float
    chromadb_metadata: Dict

class ValidationViolation(BaseModel):
    rule_id: str
    violation_type: str
    description: str
    severity: str
    suggestion: str
    auto_fixable: bool

class ValidationResponse(BaseModel):
    validation_id: str
    mode: str = "comprehensive"
    content_analyzed: str
    platform: str
    content_type: str
    
    # Rule Application
    rules_applied: List[ValidationRule]
    rules_count: int
    
    # Validation Results
    violations: List[ValidationViolation]
    suggestions: List[Dict[str, str]]
    overall_score: float  # 0-1 quality score
    
    # Performance Metrics
    processing_time_ms: float
    chromadb_queries: int
    cache_hits: int
    
    # Metadata
    chromadb_sourced: bool = True
    timestamp: datetime
    expires_at: Optional[datetime]

@app.post("/validate/comprehensive", response_model=ValidationResponse)
async def validate_comprehensive(
    request: ValidationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Comprehensive content validation using 8-12 ChromaDB rules
    Designed for Kolegium full AI workflow
    """
    
    validation_id = f"comp_{uuid.uuid4().hex[:12]}"
    start_time = time.time()
    
    try:
        # Get comprehensive validation strategy
        strategy = validation_strategy_factory.create("comprehensive")
        
        # Execute validation with full rule set
        validation_result = await strategy.validate(
            content=request.content,
            platform=request.platform,
            context={
                **request.context,
                "content_type": request.content_type,
                "user_id": request.user_id,
                "validation_mode": "comprehensive"
            }
        )
        
        # Calculate processing metrics
        processing_time = (time.time() - start_time) * 1000
        
        # Build response
        response = ValidationResponse(
            validation_id=validation_id,
            content_analyzed=request.content[:100] + "..." if len(request.content) > 100 else request.content,
            platform=request.platform,
            content_type=request.content_type,
            rules_applied=validation_result.rules_applied,
            rules_count=len(validation_result.rules_applied),
            violations=validation_result.violations,
            suggestions=validation_result.suggestions,
            overall_score=validation_result.quality_score,
            processing_time_ms=processing_time,
            chromadb_queries=validation_result.chromadb_queries,
            cache_hits=validation_result.cache_hits,
            timestamp=datetime.now()
        )
        
        # Log validation for analytics
        await analytics_logger.log_validation(validation_id, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Comprehensive validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "validation_failed",
                "message": "Comprehensive validation encountered an error",
                "validation_id": validation_id,
                "chromadb_status": await check_chromadb_health()
            }
        )

# Example Request
POST /validate/comprehensive
{
    "content": "AI is revolutionizing marketing by leveraging machine learning to paradigm-shift customer engagement through synergistic approaches that disrupt traditional methodologies.",
    "platform": "linkedin",
    "content_type": "THOUGHT_LEADERSHIP",
    "context": {
        "target_audience": "marketing_professionals",
        "urgency": "normal"
    },
    "user_id": "user_123"
}

# Example Response
{
    "validation_id": "comp_a1b2c3d4e5f6",
    "mode": "comprehensive",
    "content_analyzed": "AI is revolutionizing marketing by leveraging machine learning to paradigm-shift customer...",
    "platform": "linkedin",
    "content_type": "THOUGHT_LEADERSHIP",
    "rules_applied": [
        {
            "rule_id": "style_001_buzzwords",
            "content": "Avoid overusing buzzwords like 'paradigm', 'leverage', 'synergy'",
            "rule_type": "style",
            "priority": "high",
            "platform": "universal",
            "confidence": 0.95,
            "chromadb_metadata": {
                "collection": "style_editorial_rules",
                "similarity_score": 0.89,
                "query_timestamp": "2025-01-30T10:30:15Z"
            }
        },
        {
            "rule_id": "editorial_002_linkedin_hooks",
            "content": "LinkedIn posts should have engaging hooks in the first 2 lines",
            "rule_type": "engagement",
            "priority": "critical",
            "platform": "linkedin",
            "confidence": 0.85,
            "chromadb_metadata": {
                "collection": "style_editorial_rules",
                "similarity_score": 0.76,
                "query_timestamp": "2025-01-30T10:30:15Z"
            }
        }
    ],
    "rules_count": 10,
    "violations": [
        {
            "rule_id": "style_001_buzzwords",
            "violation_type": "buzzword_overuse",
            "description": "Content contains 4 buzzwords: 'leveraging', 'paradigm-shift', 'synergistic', 'disrupt'",
            "severity": "high",
            "suggestion": "Replace buzzwords with specific, concrete language",
            "auto_fixable": true
        }
    ],
    "suggestions": [
        {
            "type": "style_improvement",
            "description": "Replace 'leveraging' with 'using' or 'applying'",
            "original": "leveraging machine learning",
            "suggested": "using machine learning"
        }
    ],
    "overall_score": 0.65,
    "processing_time_ms": 157.3,
    "chromadb_queries": 3,
    "cache_hits": 2,
    "chromadb_sourced": true,
    "timestamp": "2025-01-30T10:30:15.123Z"
}
```

#### POST /validate/selective
**Purpose**: Checkpoint validation for AI Writing Flow human-assisted workflow
```python
class SelectiveValidationRequest(ValidationRequest):
    checkpoint: str  # pre_writing, mid_writing, post_writing
    previous_validations: Optional[List[str]] = []  # Previous validation IDs

@app.post("/validate/selective", response_model=ValidationResponse)
async def validate_selective(
    request: SelectiveValidationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Selective content validation using 3-4 critical ChromaDB rules
    Designed for AI Writing Flow human-assisted workflow with checkpoints
    """
    
    validation_id = f"sel_{uuid.uuid4().hex[:12]}"
    start_time = time.time()
    
    try:
        # Get selective validation strategy
        strategy = validation_strategy_factory.create("selective")
        
        # Add checkpoint context
        context = {
            **request.context,
            "checkpoint": request.checkpoint,
            "validation_mode": "selective",
            "previous_validations": request.previous_validations
        }
        
        # Execute selective validation
        validation_result = await strategy.validate(
            content=request.content,
            platform=request.platform,
            context=context
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        response = ValidationResponse(
            validation_id=validation_id,
            mode="selective",
            content_analyzed=request.content[:100] + "..." if len(request.content) > 100 else request.content,
            platform=request.platform,
            content_type=request.content_type,
            rules_applied=validation_result.rules_applied,
            rules_count=len(validation_result.rules_applied),
            violations=validation_result.violations,
            suggestions=validation_result.suggestions,
            overall_score=validation_result.quality_score,
            processing_time_ms=processing_time,
            chromadb_queries=validation_result.chromadb_queries,
            cache_hits=validation_result.cache_hits,
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Selective validation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "validation_failed",
                "message": "Selective validation encountered an error",
                "validation_id": validation_id,
                "checkpoint": request.checkpoint
            }
        )

# Example Request - Pre-writing Checkpoint
POST /validate/selective
{
    "content": "Planning to write about AI marketing trends for Q1 2025",
    "platform": "linkedin",
    "content_type": "THOUGHT_LEADERSHIP", 
    "checkpoint": "pre_writing",
    "context": {
        "target_length": 1500,
        "include_statistics": true
    }
}

# Example Response - Pre-writing Checkpoint
{
    "validation_id": "sel_x1y2z3a4b5c6",
    "mode": "selective",
    "content_analyzed": "Planning to write about AI marketing trends for Q1 2025",
    "platform": "linkedin",
    "content_type": "THOUGHT_LEADERSHIP",
    "rules_applied": [
        {
            "rule_id": "structure_001_linkedin_planning",
            "content": "LinkedIn thought leadership should start with a clear value proposition",
            "rule_type": "structure",
            "priority": "critical",
            "platform": "linkedin",
            "confidence": 0.9
        },
        {
            "rule_id": "audience_002_professional_targeting",
            "content": "Content should target specific professional audience segments",
            "rule_type": "audience",
            "priority": "high",
            "platform": "universal",
            "confidence": 0.85
        }
    ],
    "rules_count": 3,
    "violations": [],
    "suggestions": [
        {
            "type": "structure_improvement",
            "description": "Consider starting with a specific problem or trend statistic",
            "suggestion": "Lead with '73% of marketers report AI has increased their ROI in 2024...'"
        }
    ],
    "overall_score": 0.85,
    "processing_time_ms": 89.2,
    "chromadb_queries": 2,
    "cache_hits": 1,
    "chromadb_sourced": true,
    "timestamp": "2025-01-30T10:31:45.456Z"
}
```

### 1.3 Content Regeneration & Enhancement

#### POST /regenerate
**Purpose**: Apply validation suggestions and regenerate content
```python
class RegenerationRequest(BaseModel):
    original_content: str
    validation_id: str
    selected_suggestions: List[str]  # Suggestion IDs to apply
    additional_instructions: Optional[str] = None
    platform: str
    content_type: str

class RegenerationResponse(BaseModel):
    regeneration_id: str
    original_content: str
    regenerated_content: str
    applied_suggestions: List[Dict]
    improvements: List[str]
    quality_improvement: float  # Difference in quality score
    processing_time_ms: float
    timestamp: datetime

@app.post("/regenerate", response_model=RegenerationResponse)
async def regenerate_content(
    request: RegenerationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Regenerate content by applying selected validation suggestions
    Uses ChromaDB rules to guide content improvement
    """
    
    regeneration_id = f"regen_{uuid.uuid4().hex[:8]}"
    start_time = time.time()
    
    try:
        # Retrieve original validation
        original_validation = await get_validation_by_id(request.validation_id)
        if not original_validation:
            raise HTTPException(status_code=404, detail="Original validation not found")
        
        # Get selected suggestions
        selected_suggestions = [
            sugg for sugg in original_validation.suggestions
            if sugg.get("id") in request.selected_suggestions
        ]
        
        # Apply suggestions using ChromaDB-guided regeneration
        regeneration_engine = ContentRegenerationEngine(chromadb_client)
        
        regenerated_content = await regeneration_engine.apply_suggestions(
            content=request.original_content,
            suggestions=selected_suggestions,
            platform=request.platform,
            content_type=request.content_type,
            additional_instructions=request.additional_instructions
        )
        
        # Validate regenerated content
        new_validation = await validate_content(
            content=regenerated_content,
            platform=request.platform,
            content_type=request.content_type,
            mode="comprehensive"
        )
        
        # Calculate improvement
        quality_improvement = new_validation.overall_score - original_validation.overall_score
        
        processing_time = (time.time() - start_time) * 1000
        
        response = RegenerationResponse(
            regeneration_id=regeneration_id,
            original_content=request.original_content,
            regenerated_content=regenerated_content,
            applied_suggestions=selected_suggestions,
            improvements=regeneration_engine.get_applied_improvements(),
            quality_improvement=quality_improvement,
            processing_time_ms=processing_time,
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Content regeneration failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "regeneration_failed",
                "message": "Content regeneration encountered an error",
                "regeneration_id": regeneration_id
            }
        )
```

### 1.4 Rule Management & Discovery

#### GET /rules/search
**Purpose**: Search and discover validation rules
```python
class RuleSearchRequest(BaseModel):
    query: str
    filters: Optional[Dict] = {}
    limit: int = 20
    include_metadata: bool = True

class RuleSearchResponse(BaseModel):
    query: str
    results: List[ValidationRule]
    total_results: int
    processing_time_ms: float
    filters_applied: Dict

@app.get("/rules/search", response_model=RuleSearchResponse)
async def search_rules(
    query: str,
    platform: Optional[str] = None,
    rule_type: Optional[str] = None,
    priority: Optional[str] = None,
    workflow: Optional[str] = None,
    limit: int = 20,
    current_user: str = Depends(get_current_user)
):
    """
    Search validation rules in ChromaDB collections
    Useful for rule discovery and debugging
    """
    
    start_time = time.time()
    
    # Build filters
    filters = {}
    if platform:
        filters["platform"] = {"$in": [platform, "universal"]}
    if rule_type:
        filters["rule_type"] = rule_type
    if priority:
        filters["priority"] = priority
    if workflow:
        filters["workflow"] = {"$in": [workflow, "both"]}
    
    try:
        # Search in style_editorial_rules collection
        style_collection = chromadb_client.get_collection("style_editorial_rules")
        
        results = style_collection.query(
            query_texts=[query],
            n_results=limit,
            where=filters if filters else None
        )
        
        # Convert to response format
        rules = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0]):
                metadata = results["metadatas"][0][i] if results["metadatas"] else {}
                
                rule = ValidationRule(
                    rule_id=metadata.get("rule_id", f"unknown_{i}"),
                    content=doc,
                    rule_type=metadata.get("rule_type", "unknown"),
                    priority=metadata.get("priority", "medium"),
                    platform=metadata.get("platform", "universal"),
                    confidence=results["distances"][0][i] if results.get("distances") else 1.0,
                    chromadb_metadata={
                        "collection": "style_editorial_rules",
                        "similarity_score": 1.0 - results["distances"][0][i] if results.get("distances") else 1.0,
                        "query_timestamp": datetime.now().isoformat(),
                        **metadata
                    }
                )
                rules.append(rule)
        
        processing_time = (time.time() - start_time) * 1000
        
        return RuleSearchResponse(
            query=query,
            results=rules,
            total_results=len(rules),
            processing_time_ms=processing_time,
            filters_applied=filters
        )
        
    except Exception as e:
        logger.error(f"Rule search failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "search_failed",
                "message": "Rule search encountered an error",
                "query": query
            }
        )
```

### 1.5 System Health & Monitoring

#### GET /health
**Purpose**: Comprehensive system health check
```python
class HealthCheckResponse(BaseModel):
    status: str
    service: str = "editorial-service"
    version: str = "2.0.0"
    port: int = 8040
    timestamp: datetime
    uptime_seconds: float
    
    # Component Health
    chromadb_status: str
    cache_status: str
    circuit_breaker_state: str
    
    # Performance Metrics
    total_validations: int
    average_response_time_ms: float
    current_load: float
    
    # ChromaDB Statistics
    chromadb_collections: Dict[str, int]
    total_rules_cached: int
    cache_hit_rate: float
    
    # System Resources
    memory_usage_mb: float
    cpu_usage_percent: float

@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """
    Comprehensive health check for Editorial Service
    Includes ChromaDB connectivity, cache status, and performance metrics
    """
    
    try:
        # Check ChromaDB connectivity
        chromadb_status = await check_chromadb_connectivity()
        
        # Check cache health
        cache_status = await check_cache_health()
        
        # Get circuit breaker state
        circuit_breaker_state = circuit_breaker.get_state()
        
        # Get collection statistics
        collections_stats = {}
        try:
            for collection_name in ["style_editorial_rules", "publication_platform_rules"]:
                collection = chromadb_client.get_collection(collection_name)
                collections_stats[collection_name] = collection.count()
        except Exception as e:
            collections_stats["error"] = str(e)
        
        # Get performance metrics
        perf_metrics = await get_performance_metrics()
        
        # Get system resources
        memory_usage = get_memory_usage()
        cpu_usage = get_cpu_usage()
        
        # Calculate uptime
        uptime = time.time() - service_start_time
        
        health_response = HealthCheckResponse(
            status="healthy" if chromadb_status == "connected" else "degraded",
            timestamp=datetime.now(),
            uptime_seconds=uptime,
            chromadb_status=chromadb_status,
            cache_status=cache_status,
            circuit_breaker_state=circuit_breaker_state,
            total_validations=perf_metrics.get("total_validations", 0),
            average_response_time_ms=perf_metrics.get("avg_response_time_ms", 0),
            current_load=perf_metrics.get("current_load", 0),
            chromadb_collections=collections_stats,
            total_rules_cached=await get_cached_rules_count(),
            cache_hit_rate=perf_metrics.get("cache_hit_rate", 0),
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage
        )
        
        return health_response
        
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(
            status_code=503,
            detail={
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
        )

# Example Response
{
    "status": "healthy",
    "service": "editorial-service",
    "version": "2.0.0",
    "port": 8040,
    "timestamp": "2025-01-30T10:35:22.789Z",
    "uptime_seconds": 86400.5,
    "chromadb_status": "connected",
    "cache_status": "healthy",
    "circuit_breaker_state": "closed",
    "total_validations": 15647,
    "average_response_time_ms": 142.3,
    "current_load": 0.23,
    "chromadb_collections": {
        "style_editorial_rules": 287,
        "publication_platform_rules": 78
    },
    "total_rules_cached": 365,
    "cache_hit_rate": 0.847,
    "memory_usage_mb": 234.7,
    "cpu_usage_percent": 12.4
}
```

#### GET /cache/stats
**Purpose**: Cache statistics and ChromaDB source verification
```python
class CacheStatsResponse(BaseModel):
    total_rules: int
    source: str = "chromadb"
    all_have_origin: bool
    warmup_time_ms: float
    hit_rate: float
    miss_rate: float
    cache_size_mb: float
    oldest_entry_age_hours: float
    newest_entry_age_minutes: float
    collections_cached: Dict[str, int]

@app.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_statistics(current_user: str = Depends(get_current_user)):
    """
    Get detailed cache statistics and verify ChromaDB origins
    Critical for ensuring zero hardcoded rules compliance
    """
    
    try:
        cache_stats = await cache_manager.get_detailed_stats()
        
        # Verify all cached rules have ChromaDB origin
        all_origins_valid = await verify_all_cached_rules_have_chromadb_origin()
        
        return CacheStatsResponse(
            total_rules=cache_stats["total_rules"],
            all_have_origin=all_origins_valid,
            warmup_time_ms=cache_stats["warmup_duration_ms"],
            hit_rate=cache_stats["hit_rate"],
            miss_rate=1.0 - cache_stats["hit_rate"],
            cache_size_mb=cache_stats["cache_size_mb"],
            oldest_entry_age_hours=cache_stats["oldest_entry_age_hours"],
            newest_entry_age_minutes=cache_stats["newest_entry_age_minutes"],
            collections_cached=cache_stats["collections_breakdown"]
        )
        
    except Exception as e:
        logger.error(f"Cache stats retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail="Failed to retrieve cache statistics"
        )
```

---

## 🎯 2. Topic Manager API (Port 8041)
**Topic database management with AI-powered suggestions and auto-scraping**

### 2.1 Manual Topic Management

#### POST /topics/manual
**Purpose**: Add manually curated topics to the database
```python
class ManualTopicRequest(BaseModel):
    title: str
    description: str
    keywords: List[str]
    content_type: str
    domain: Optional[str] = None
    complexity_level: str = "intermediate"
    target_audience: List[str] = []
    platform_preferences: Optional[Dict[str, bool]] = None

class TopicCreationResponse(BaseModel):
    topic_id: str
    status: str = "created"
    title: str
    platform_assignment: Dict[str, float]  # AI-generated suitability scores
    engagement_prediction: float
    processing_time_ms: float
    timestamp: datetime

@app.post("/topics/manual", response_model=TopicCreationResponse)
async def add_manual_topic(
    request: ManualTopicRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Add manually curated topic with AI-powered platform assignment
    """
    
    start_time = time.time()
    topic_id = f"manual_{uuid.uuid4().hex[:12]}"
    
    try:
        # Generate AI-powered platform assignment
        platform_analyzer = PlatformAssignmentAnalyzer(chromadb_client)
        platform_scores = await platform_analyzer.analyze_topic_suitability(
            title=request.title,
            description=request.description,
            keywords=request.keywords,
            content_type=request.content_type,
            user_preferences=request.platform_preferences
        )
        
        # Predict engagement potential
        engagement_predictor = EngagementPredictor(chromadb_client)
        engagement_score = await engagement_predictor.predict_engagement(
            request.title,
            request.description,
            request.keywords,
            platform_scores
        )
        
        # Store in ChromaDB topics collection
        topics_collection = chromadb_client.get_collection("topics")
        
        topic_document = {
            "content": f"{request.title} {request.description} {' '.join(request.keywords)}",
            "metadata": {
                "topic_id": topic_id,
                "title": request.title,
                "description": request.description,
                "keywords": request.keywords,
                "content_type": request.content_type,
                "domain": request.domain,
                "complexity_level": request.complexity_level,
                "target_audience": request.target_audience,
                "platform_assignment": {
                    platform: score > 0.6 for platform, score in platform_scores.items()
                },
                "platform_suitability_scores": platform_scores,
                "engagement_prediction": engagement_score,
                "status": "suggested",
                "source": "manual",
                "created_date": datetime.now().isoformat(),
                "created_by": current_user,
                "usage_count": 0,
                "selection_count": 0,
                "rejection_count": 0,
                "version": 1
            }
        }
        
        # Add to ChromaDB
        topics_collection.add(
            documents=[topic_document["content"]],
            metadatas=[topic_document["metadata"]],
            ids=[topic_id]
        )
        
        processing_time = (time.time() - start_time) * 1000
        
        response = TopicCreationResponse(
            topic_id=topic_id,
            title=request.title,
            platform_assignment=platform_scores,
            engagement_prediction=engagement_score,
            processing_time_ms=processing_time,
            timestamp=datetime.now()
        )
        
        # Log topic creation for analytics
        await analytics_logger.log_topic_creation(topic_id, response, current_user)
        
        return response
        
    except Exception as e:
        logger.error(f"Manual topic creation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "topic_creation_failed",
                "message": "Failed to create manual topic",
                "topic_id": topic_id
            }
        )

# Example Request
POST /topics/manual
{
    "title": "Zero-Shot Learning in Large Language Models",
    "description": "Exploring how modern LLMs can perform tasks without specific training examples, implications for AI development and practical applications in various industries",
    "keywords": ["zero-shot learning", "LLM", "AI", "machine learning", "applications"],
    "content_type": "TUTORIAL",
    "domain": "technology", 
    "complexity_level": "advanced",
    "target_audience": ["ai_researchers", "data_scientists", "ml_engineers"],
    "platform_preferences": {
        "linkedin": true,
        "twitter": false,
        "substack": true
    }
}

# Example Response
{
    "topic_id": "manual_a1b2c3d4e5f6",
    "status": "created",
    "title": "Zero-Shot Learning in Large Language Models",
    "platform_assignment": {
        "linkedin": 0.92,
        "twitter": 0.45,
        "substack": 0.88,
        "beehiiv": 0.67,
        "ghost": 0.71
    },
    "engagement_prediction": 0.84,
    "processing_time_ms": 234.7,
    "timestamp": "2025-01-30T10:40:15.123Z"
}
```

### 2.2 Topic Suggestions & Discovery

#### GET /topics/suggestions
**Purpose**: Get AI-powered topic suggestions with platform assignments
```python
class TopicSuggestion(BaseModel):
    topic_id: str
    title: str
    description: str
    keywords: List[str]
    content_type: str
    domain: str
    suggested_platforms: List[str]
    platform_suitability_scores: Dict[str, float]
    engagement_prediction: float
    trending_score: Optional[float]
    reasoning: str
    competition_level: str
    optimal_timing: Optional[Dict[str, str]]

class TopicSuggestionsResponse(BaseModel):
    suggestions: List[TopicSuggestion]
    total_available: int
    personalized: bool
    filters_applied: Dict
    processing_time_ms: float
    timestamp: datetime

@app.get("/topics/suggestions", response_model=TopicSuggestionsResponse)
async def get_topic_suggestions(
    limit: int = 10,
    user_id: Optional[str] = None,
    content_type: Optional[str] = None,
    domain: Optional[str] = None,
    platform: Optional[str] = None,
    trending_only: bool = False,
    min_engagement_score: float = 0.6,
    current_user: str = Depends(get_current_user)
):
    """
    Get AI-powered topic suggestions with ChromaDB-based personalization
    """
    
    start_time = time.time()
    
    try:
        # Build base query filters
        filters = {
            "$and": [
                {"status": {"$in": ["suggested", "archived"]}},
                {"engagement_prediction": {"$gt": min_engagement_score}}
            ]
        }
        
        if content_type:
            filters["$and"].append({"content_type": content_type})
        
        if domain:
            filters["$and"].append({"domain": domain})
            
        if trending_only:
            filters["$and"].append({"trending_score": {"$gt": 0.7}})
        
        # Get user preferences for personalization
        user_preferences = None
        if user_id:
            user_preferences = await get_user_topic_preferences(user_id)
        
        # Query topics collection
        topics_collection = chromadb_client.get_collection("topics")
        
        # Build search query
        search_query = "trending technology innovation business"
        if user_preferences and user_preferences.get("preferred_domains"):
            search_query = " ".join(user_preferences["preferred_domains"]) + " " + search_query
        
        results = topics_collection.query(
            query_texts=[search_query],
            n_results=limit * 2,  # Get more for filtering
            where=filters
        )
        
        # Process results into suggestions
        suggestions = []
        if results["documents"] and results["documents"][0]:
            for i, doc in enumerate(results["documents"][0][:limit]):
                metadata = results["metadatas"][0][i]
                
                # Generate platform suggestions
                platform_scores = metadata.get("platform_suitability_scores", {})
                suggested_platforms = [
                    platform for platform, score in platform_scores.items()
                    if score > 0.6
                ]
                
                # Generate reasoning
                reasoning = await generate_topic_reasoning(
                    metadata, platform_scores, user_preferences
                )
                
                # Get optimal timing if available
                optimal_timing = await get_optimal_timing_for_topic(
                    metadata.get("topic_id"), suggested_platforms
                )
                
                suggestion = TopicSuggestion(
                    topic_id=metadata["topic_id"],
                    title=metadata["title"],
                    description=metadata["description"], 
                    keywords=metadata["keywords"],
                    content_type=metadata["content_type"],
                    domain=metadata.get("domain", "general"),
                    suggested_platforms=suggested_platforms,
                    platform_suitability_scores=platform_scores,
                    engagement_prediction=metadata.get("engagement_prediction", 0.5),
                    trending_score=metadata.get("trending_score"),
                    reasoning=reasoning,
                    competition_level=metadata.get("competition_level", "medium"),
                    optimal_timing=optimal_timing
                )
                
                suggestions.append(suggestion)
        
        processing_time = (time.time() - start_time) * 1000
        
        response = TopicSuggestionsResponse(
            suggestions=suggestions,
            total_available=len(results["documents"][0]) if results["documents"] else 0,
            personalized=user_preferences is not None,
            filters_applied={
                "content_type": content_type,
                "domain": domain,
                "platform": platform,
                "trending_only": trending_only,
                "min_engagement_score": min_engagement_score
            },
            processing_time_ms=processing_time,
            timestamp=datetime.now()
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Topic suggestions failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "suggestions_failed",
                "message": "Failed to generate topic suggestions"
            }
        )

# Example Response
{
    "suggestions": [
        {
            "topic_id": "auto_hackernews_001",
            "title": "GPT-5 Architecture Leaked: What It Means for AI Development",
            "description": "Analysis of the leaked GPT-5 architecture documents and implications for next-generation AI systems",
            "keywords": ["GPT-5", "AI architecture", "language models", "OpenAI"],
            "content_type": "INDUSTRY_UPDATE",
            "domain": "technology",
            "suggested_platforms": ["linkedin", "twitter", "substack"],
            "platform_suitability_scores": {
                "linkedin": 0.87,
                "twitter": 0.95,
                "substack": 0.78,
                "beehiiv": 0.62
            },
            "engagement_prediction": 0.91,
            "trending_score": 0.94,
            "reasoning": "High trending score due to recent news coverage. Strong technical content appeal for professional audience. Twitter highly suitable for breaking news discussion.",
            "competition_level": "high",
            "optimal_timing": {
                "linkedin": "Tuesday 9 AM EST",
                "twitter": "Today 2 PM EST",
                "substack": "Thursday 8 AM EST"
            }
        }
    ],
    "total_available": 47,
    "personalized": true,
    "filters_applied": {
        "content_type": null,
        "domain": "technology",
        "platform": null,
        "trending_only": true,
        "min_engagement_score": 0.6
    },
    "processing_time_ms": 187.4,
    "timestamp": "2025-01-30T10:42:33.567Z"
}
```

### 2.3 Auto-Scraping Management

#### POST /topics/scrape
**Purpose**: Trigger automated topic discovery from external sources
```python
class ScrapeRequest(BaseModel):
    scraper_types: List[str] = ["all"]  # hackernews, reddit, twitter, linkedin
    max_topics_per_source: int = 20
    min_relevance_score: float = 0.7
    content_types: Optional[List[str]] = None
    domains: Optional[List[str]] = None

class ScraperResult(BaseModel):
    scraper: str
    topics_found: int
    topics_added: int
    topics_skipped: int
    average_relevance: float
    execution_time_ms: float
    errors: List[str]

class ScrapeResponse(BaseModel):
    scrape_id: str
    total_scrapers: int
    successful_scrapers: int
    failed_scrapers: int
    scrapers_results: List[ScraperResult]
    total_topics_discovered: int
    total_topics_added: int
    processing_time_ms: float
    timestamp: datetime

@app.post("/topics/scrape", response_model=ScrapeResponse)
async def trigger_auto_scraping(
    request: ScrapeRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Trigger automated topic discovery and scoring
    """
    
    scrape_id = f"scrape_{uuid.uuid4().hex[:8]}"
    start_time = time.time()
    
    available_scrapers = {
        "hackernews": HackerNewsTopicScraper(),
        "reddit": RedditTopicScraper(),
        "twitter": TwitterTrendingScraper(),
        "linkedin": LinkedInTopicScraper()
    }
    
    scrapers_to_run = []
    if "all" in request.scraper_types:
        scrapers_to_run = list(available_scrapers.values())
    else:
        scrapers_to_run = [
            scraper for name, scraper in available_scrapers.items()
            if name in request.scraper_types
        ]
    
    scraper_results = []
    total_discovered = 0
    total_added = 0
    successful_scrapers = 0
    failed_scrapers = 0
    
    for scraper in scrapers_to_run:
        scraper_start = time.time()
        
        try:
            # Run scraper
            discovered_topics = await scraper.scrape_topics(
                max_topics=request.max_topics_per_source,
                min_relevance=request.min_relevance_score,
                content_types=request.content_types,
                domains=request.domains
            )
            
            # Score and filter topics
            relevant_topics = []
            relevance_scores = []
            
            for topic in discovered_topics:
                relevance_score = await score_topic_relevance(topic)
                if relevance_score >= request.min_relevance_score:
                    topic["engagement_prediction"] = relevance_score
                    relevant_topics.append(topic)
                    relevance_scores.append(relevance_score)
            
            # Store topics in ChromaDB
            topics_added = await store_scraped_topics(
                relevant_topics, scraper.name, scrape_id
            )
            
            scraper_time = (time.time() - scraper_start) * 1000
            
            result = ScraperResult(
                scraper=scraper.name,
                topics_found=len(discovered_topics),
                topics_added=topics_added,
                topics_skipped=len(discovered_topics) - topics_added,
                average_relevance=sum(relevance_scores) / len(relevance_scores) if relevance_scores else 0,
                execution_time_ms=scraper_time,
                errors=[]
            )
            
            scraper_results.append(result)
            total_discovered += len(discovered_topics)
            total_added += topics_added
            successful_scrapers += 1
            
        except Exception as e:
            logger.error(f"Scraper {scraper.name} failed: {e}")
            
            result = ScraperResult(
                scraper=scraper.name,
                topics_found=0,
                topics_added=0,
                topics_skipped=0,
                average_relevance=0,
                execution_time_ms=0,
                errors=[str(e)]
            )
            
            scraper_results.append(result)
            failed_scrapers += 1
    
    processing_time = (time.time() - start_time) * 1000
    
    response = ScrapeResponse(
        scrape_id=scrape_id,
        total_scrapers=len(scrapers_to_run),
        successful_scrapers=successful_scrapers,
        failed_scrapers=failed_scrapers,
        scrapers_results=scraper_results,
        total_topics_discovered=total_discovered,
        total_topics_added=total_added,
        processing_time_ms=processing_time,
        timestamp=datetime.now()
    )
    
    # Log scraping activity
    await analytics_logger.log_scraping_activity(scrape_id, response, current_user)
    
    return response

# Example Response
{
    "scrape_id": "scrape_x1y2z3a4",
    "total_scrapers": 4,
    "successful_scrapers": 3,
    "failed_scrapers": 1,
    "scrapers_results": [
        {
            "scraper": "hackernews",
            "topics_found": 15,
            "topics_added": 8,
            "topics_skipped": 7,
            "average_relevance": 0.82,
            "execution_time_ms": 2341.5,
            "errors": []
        },
        {
            "scraper": "reddit",
            "topics_found": 23,
            "topics_added": 12,
            "topics_skipped": 11,
            "average_relevance": 0.76,
            "execution_time_ms": 3892.1,
            "errors": []
        },
        {
            "scraper": "twitter",
            "topics_found": 31,
            "topics_added": 7,
            "topics_skipped": 24,
            "average_relevance": 0.73,
            "execution_time_ms": 1876.3,
            "errors": []
        },
        {
            "scraper": "linkedin",
            "topics_found": 0,
            "topics_added": 0,
            "topics_skipped": 0,
            "average_relevance": 0,
            "execution_time_ms": 0,
            "errors": ["LinkedIn API rate limit exceeded"]
        }
    ],
    "total_topics_discovered": 69,
    "total_topics_added": 27,
    "processing_time_ms": 8234.7,
    "timestamp": "2025-01-30T10:45:18.890Z"
}
```

---

## 🚀 3. Publishing Orchestrator API (Port 8080)
**Multi-platform publishing coordination with LinkedIn special handling**

### 3.1 Complete Publishing Workflow

#### POST /publish
**Purpose**: Orchestrate complete multi-platform publishing
```python
class PublicationRequest(BaseModel):
    topic: Dict[str, Any]
    platforms: Dict[str, PlatformConfig]
    global_options: Optional[GlobalPublishingOptions] = None
    webhook_url: Optional[str] = None

class PlatformConfig(BaseModel):
    enabled: bool
    account_id: str
    schedule_time: Optional[datetime] = None
    options: Optional[Dict[str, Any]] = {}

class GlobalPublishingOptions(BaseModel):
    priority: str = "normal"  # low, normal, high, urgent
    timezone: str = "UTC"
    retry_failed: bool = True
    max_retries: int = 3

class PlatformJobStatus(BaseModel):
    job_id: str
    status: str  # queued, processing, completed, failed, scheduled
    scheduled_for: Optional[datetime]
    estimated_completion: Optional[datetime]
    result: Optional[Dict] = None
    error: Optional[Dict] = None

class PublicationResponse(BaseModel):
    publication_id: str
    status: str
    platforms: Dict[str, PlatformJobStatus]
    content_generated: bool
    ai_writing_flow_used: bool
    linkedin_manual_upload: Optional[Dict] = None
    created_at: datetime

@app.post("/publish", response_model=PublicationResponse)
async def orchestrate_publication(
    request: PublicationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Complete multi-platform publishing orchestration with ChromaDB-guided content generation
    """
    
    publication_id = f"pub_{uuid.uuid4().hex[:16]}"
    start_time = time.time()
    
    try:
        # Initialize content generation for each platform
        content_generator = ChromaDBGuidedContentGenerator(
            chromadb_client, editorial_service_client
        )
        
        platform_jobs = {}
        linkedin_manual_info = None
        
        for platform, config in request.platforms.items():
            if not config.enabled:
                continue
            
            try:
                # Generate platform-specific content using Editorial Service
                content = await content_generator.generate_platform_content(
                    topic=request.topic,
                    platform=platform,
                    config=config,
                    user_id=current_user
                )
                
                # Special LinkedIn handling
                if platform == "linkedin":
                    linkedin_handler = LinkedInSpecialHandler(presentor_client)
                    
                    if linkedin_handler.should_generate_presentation(content):
                        presentation_info = await linkedin_handler.generate_presentation(content)
                        linkedin_manual_info = {
                            "requires_manual_upload": True,
                            "presentation_files": presentation_info,
                            "instructions": presentation_info.get("upload_instructions", [])
                        }
                        content["presentation"] = presentation_info
                
                # Schedule platform publication
                job_id = await schedule_platform_publication(
                    platform=platform,
                    content=content,
                    config=config,
                    publication_id=publication_id
                )
                
                # Determine status and timing
                if config.schedule_time:
                    status = "scheduled"
                    estimated_completion = config.schedule_time
                else:
                    status = "queued"
                    estimated_completion = datetime.now() + timedelta(minutes=5)
                
                platform_jobs[platform] = PlatformJobStatus(
                    job_id=job_id,
                    status=status,
                    scheduled_for=config.schedule_time,
                    estimated_completion=estimated_completion
                )
                
            except Exception as e:
                logger.error(f"Platform {platform} preparation failed: {e}")
                
                platform_jobs[platform] = PlatformJobStatus(
                    job_id=f"failed_{uuid.uuid4().hex[:8]}",
                    status="failed",
                    error={
                        "code": "preparation_failed",
                        "message": str(e),
                        "timestamp": datetime.now().isoformat()
                    }
                )
        
        response = PublicationResponse(
            publication_id=publication_id,
            status="processing" if platform_jobs else "no_platforms_enabled",
            platforms=platform_jobs,
            content_generated=True,
            ai_writing_flow_used=True,
            linkedin_manual_upload=linkedin_manual_info,
            created_at=datetime.now()
        )
        
        # Store publication record for tracking
        await store_publication_record(publication_id, request, response)
        
        # Send webhook notification if configured
        if request.webhook_url:
            await send_webhook_notification(request.webhook_url, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Publication orchestration failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "orchestration_failed",
                "message": "Publication orchestration encountered an error",
                "publication_id": publication_id,
                "platforms_attempted": list(request.platforms.keys())
            }
        )

# Example Request
POST /publish
{
    "topic": {
        "topic_id": "manual_a1b2c3d4e5f6",
        "title": "Zero-Shot Learning in Large Language Models",
        "description": "Exploring how modern LLMs can perform tasks without specific training examples",
        "keywords": ["zero-shot learning", "LLM", "AI"],
        "content_type": "TUTORIAL"
    },
    "platforms": {
        "linkedin": {
            "enabled": true,
            "account_id": "production",
            "schedule_time": null,
            "options": {
                "include_pdf": true,
                "hashtags": ["#AI", "#MachineLearning", "#Tutorial"]
            }
        },
        "twitter": {
            "enabled": true,
            "account_id": "main_account",
            "schedule_time": "2025-01-30T14:00:00Z",
            "options": {
                "thread_mode": "auto",
                "hashtags": ["#AI", "#LLM"]
            }
        },
        "substack": {
            "enabled": true,
            "account_id": "ai_newsletter",
            "schedule_time": "2025-01-30T09:00:00Z",
            "options": {
                "newsletter_subject": "Understanding Zero-Shot Learning",
                "send_to_subscribers": true
            }
        }
    },
    "global_options": {
        "priority": "normal",
        "timezone": "EST",
        "retry_failed": true,
        "max_retries": 3
    },
    "webhook_url": "https://yourapp.com/webhooks/publication-status"
}

# Example Response
{
    "publication_id": "pub_a1b2c3d4e5f6g7h8",
    "status": "processing",
    "platforms": {
        "linkedin": {
            "job_id": "linkedin_job_12345",
            "status": "queued",
            "estimated_completion": "2025-01-30T10:05:00Z"
        },
        "twitter": {
            "job_id": "twitter_job_12346",
            "status": "scheduled",
            "scheduled_for": "2025-01-30T14:00:00Z",
            "estimated_completion": "2025-01-30T14:00:00Z"
        },
        "substack": {
            "job_id": "substack_job_12347",
            "status": "scheduled",
            "scheduled_for": "2025-01-30T09:00:00Z",
            "estimated_completion": "2025-01-30T09:00:00Z"
        }
    },
    "content_generated": true,
    "ai_writing_flow_used": true,
    "linkedin_manual_upload": {
        "requires_manual_upload": true,
        "presentation_files": {
            "ppt_url": "https://storage.com/presentations/zero-shot-learning.pptx",
            "pdf_url": "https://storage.com/presentations/zero-shot-learning.pdf"
        },
        "instructions": [
            "1. Download the PPT/PDF file",
            "2. Go to LinkedIn and create new post",
            "3. Upload the downloaded file as document", 
            "4. Add the generated text as post description",
            "5. Publish manually"
        ]
    },
    "created_at": "2025-01-30T10:00:00Z"
}
```

### 3.2 Publication Status Tracking

#### GET /publication/{publication_id}
**Purpose**: Get detailed publication status across all platforms
```python
class PlatformPublicationResult(BaseModel):
    platform_post_id: Optional[str]
    post_url: Optional[str]
    published_at: Optional[datetime]
    engagement_tracking: bool = False
    metrics: Optional[Dict] = None

class PublicationStatusResponse(BaseModel):
    publication_id: str
    overall_status: str  # processing, partially_completed, completed, failed
    platforms: Dict[str, PlatformJobStatus]
    metrics: Dict[str, int]
    created_at: datetime
    last_updated: datetime
    completion_percentage: float

@app.get("/publication/{publication_id}", response_model=PublicationStatusResponse)
async def get_publication_status(
    publication_id: str,
    current_user: str = Depends(get_current_user)
):
    """
    Get comprehensive publication status with real-time updates
    """
    
    try:
        # Retrieve publication record
        publication_record = await get_publication_record(publication_id)
        if not publication_record:
            raise HTTPException(status_code=404, detail="Publication not found")
        
        # Get latest status from each platform adapter
        platform_statuses = {}
        completed_count = 0
        failed_count = 0
        scheduled_count = 0
        total_platforms = len(publication_record.platforms)
        
        for platform, job_info in publication_record.platforms.items():
            try:
                # Get latest status from platform adapter
                adapter = platform_adapter_registry.get_adapter(platform)
                current_status = await adapter.get_job_status(job_info.job_id)
                
                platform_statuses[platform] = current_status
                
                # Count statuses
                if current_status.status == "completed":
                    completed_count += 1
                elif current_status.status == "failed":
                    failed_count += 1
                elif current_status.status == "scheduled":
                    scheduled_count += 1
                    
            except Exception as e:
                logger.error(f"Failed to get status for {platform}: {e}")
                platform_statuses[platform] = PlatformJobStatus(
                    job_id=job_info.job_id,
                    status="error",
                    error={"code": "status_check_failed", "message": str(e)}
                )
                failed_count += 1
        
        # Determine overall status
        if completed_count == total_platforms:
            overall_status = "completed"
        elif failed_count == total_platforms:
            overall_status = "failed"
        elif completed_count > 0:
            overall_status = "partially_completed"
        else:
            overall_status = "processing"
        
        completion_percentage = (completed_count / total_platforms) * 100 if total_platforms > 0 else 0
        
        response = PublicationStatusResponse(
            publication_id=publication_id,
            overall_status=overall_status,
            platforms=platform_statuses,
            metrics={
                "successful_publications": completed_count,
                "failed_publications": failed_count,
                "scheduled_publications": scheduled_count,
                "total_platforms": total_platforms
            },
            created_at=publication_record.created_at,
            last_updated=datetime.now(),
            completion_percentage=completion_percentage
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Status retrieval failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "status_retrieval_failed",
                "message": "Failed to retrieve publication status",
                "publication_id": publication_id
            }
        )

# Example Response
{
    "publication_id": "pub_a1b2c3d4e5f6g7h8",
    "overall_status": "partially_completed",
    "platforms": {
        "linkedin": {
            "job_id": "linkedin_job_12345",
            "status": "completed",
            "result": {
                "platform_post_id": "linkedin_post_abc123",
                "post_url": "https://linkedin.com/posts/user/activity-abc123",
                "published_at": "2025-01-30T10:03:42Z",
                "engagement_tracking": true
            }
        },
        "twitter": {
            "job_id": "twitter_job_12346",
            "status": "scheduled",
            "scheduled_for": "2025-01-30T14:00:00Z",
            "thread_preview": {
                "tweet_count": 4,
                "preview": [
                    "🧵 Thread about Zero-Shot Learning in LLMs 1/4",
                    "Zero-shot learning allows models to perform tasks without specific training examples...",
                    "This capability has revolutionary implications for AI development...",
                    "Want to learn more about implementing zero-shot learning? Let me know! 4/4"
                ]
            }
        },
        "substack": {
            "job_id": "substack_job_12347",
            "status": "failed",
            "error": {
                "code": "SESSION_EXPIRED",
                "message": "Substack session expired, manual renewal required",
                "retry_possible": true,
                "next_retry": "2025-01-30T11:00:00Z"
            }
        }
    },
    "metrics": {
        "successful_publications": 1,
        "failed_publications": 1,
        "scheduled_publications": 1,
        "total_platforms": 3
    },
    "created_at": "2025-01-30T10:00:00Z",
    "last_updated": "2025-01-30T10:03:42Z",
    "completion_percentage": 33.3
}
```

---

## 🎨 4. Presentor Service API (Port 8089)
**PPT/PDF generation for LinkedIn manual uploads**

### 4.1 Presentation Generation

#### POST /generate-presentation
**Purpose**: Generate PPT/PDF presentations for LinkedIn content
```python
class PresentationRequest(BaseModel):
    title: str
    content: str
    template: str = "linkedin_post"  # linkedin_post, tutorial, case_study
    format: str = "both"  # ppt, pdf, both
    branding: Optional[Dict] = None
    custom_styling: Optional[Dict] = None

class PresentationResponse(BaseModel):
    presentation_id: str
    status: str
    formats_generated: List[str]
    download_urls: Dict[str, str]
    metadata: Dict[str, Any]
    processing_time_ms: float
    expires_at: datetime

@app.post("/generate-presentation", response_model=PresentationResponse)
async def generate_presentation(
    request: PresentationRequest,
    current_user: str = Depends(get_current_user)
):
    """
    Generate professional presentations for LinkedIn manual upload
    """
    
    presentation_id = f"pres_{uuid.uuid4().hex[:12]}"
    start_time = time.time()
    
    try:
        # Initialize presentation generator
        generator = PresentationGenerator(
            template_engine=template_engine,
            content_analyzer=content_analyzer
        )
        
        # Analyze content structure
        content_structure = await generator.analyze_content_structure(
            title=request.title,
            content=request.content,
            template=request.template
        )
        
        # Generate presentation files
        generated_files = {}
        formats_to_generate = []
        
        if request.format in ["ppt", "both"]:
            formats_to_generate.append("ppt")
        if request.format in ["pdf", "both"]:
            formats_to_generate.append("pdf")
        
        for format_type in formats_to_generate:
            try:
                file_info = await generator.generate_format(
                    presentation_id=presentation_id,
                    content_structure=content_structure,
                    format_type=format_type,
                    template=request.template,
                    branding=request.branding,
                    custom_styling=request.custom_styling
                )
                
                generated_files[format_type] = file_info
                
            except Exception as e:
                logger.error(f"Failed to generate {format_type}: {e}")
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to generate {format_type} format"
                )
        
        # Upload files to storage and generate download URLs
        download_urls = {}
        for format_type, file_info in generated_files.items():
            upload_result = await file_storage.upload_presentation(
                presentation_id, format_type, file_info
            )
            download_urls[format_type + "_url"] = upload_result["download_url"]
        
        processing_time = (time.time() - start_time) * 1000
        
        # Set expiration time (7 days)
        expires_at = datetime.now() + timedelta(days=7)
        
        response = PresentationResponse(
            presentation_id=presentation_id,
            status="completed",
            formats_generated=list(generated_files.keys()),
            download_urls=download_urls,
            metadata={
                "slide_count": content_structure.get("estimated_slides", 0),
                "template_used": request.template,
                "content_length": len(request.content),
                "generation_time_ms": processing_time
            },
            processing_time_ms=processing_time,
            expires_at=expires_at
        )
        
        # Store presentation record
        await store_presentation_record(presentation_id, request, response)
        
        return response
        
    except Exception as e:
        logger.error(f"Presentation generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "generation_failed",
                "message": "Presentation generation encountered an error",
                "presentation_id": presentation_id
            }
        )

# Example Request
POST /generate-presentation
{
    "title": "Zero-Shot Learning in Large Language Models",
    "content": "Zero-shot learning represents a paradigm shift in AI... [full content]",
    "template": "tutorial",
    "format": "both",
    "branding": {
        "company_name": "AI Insights",
        "logo_url": "https://example.com/logo.png",
        "primary_color": "#1E88E5",
        "secondary_color": "#424242"
    },
    "custom_styling": {
        "font_family": "Roboto",
        "slide_layout": "content_focused"
    }
}

# Example Response
{
    "presentation_id": "pres_a1b2c3d4e5f6",
    "status": "completed",
    "formats_generated": ["ppt", "pdf"],
    "download_urls": {
        "ppt_url": "https://storage.presentor.com/pres_a1b2c3d4e5f6.pptx?expires=1706616000",
        "pdf_url": "https://storage.presentor.com/pres_a1b2c3d4e5f6.pdf?expires=1706616000"
    },
    "metadata": {
        "slide_count": 8,
        "template_used": "tutorial",
        "content_length": 2847,
        "generation_time_ms": 3421.7
    },
    "processing_time_ms": 3421.7,
    "expires_at": "2025-02-06T10:47:15.123Z"
}
```

---

## 🤖 5. CrewAI Orchestrator API (Port 8042)
**CrewAI agent orchestration and flow execution**

### 5.1 Flow Execution

#### POST /crews/execute
**Purpose**: Execute complete CrewAI flow with all agents
```python
class CrewExecutionRequest(BaseModel):
    workflow_type: Literal["ai_first", "human_assisted"]
    topic: str
    platform: str
    audience_type: str = "professionals"
    checkpoint_callbacks: Optional[bool] = False

class CrewExecutionResponse(BaseModel):
    execution_id: str
    workflow_type: str
    status: str
    agents_executed: List[str]
    content_generated: str
    quality_score: float
    execution_time_ms: float
```

#### GET /agents/status
**Purpose**: Get status of all CrewAI agents
```python
class AgentStatus(BaseModel):
    agent_name: str
    status: Literal["ready", "executing", "error"]
    last_execution: Optional[datetime]
    tasks_completed: int
    average_execution_time_ms: float

class AgentsStatusResponse(BaseModel):
    agents: List[AgentStatus]
    orchestrator_status: str
```

#### POST /flows/{workflow_type}
**Purpose**: Execute specific workflow type
```python
# Path parameter: workflow_type = "ai_first" | "human_assisted"

class FlowExecutionRequest(BaseModel):
    topic: str
    platform: str
    checkpoints: Optional[List[str]] = None

class FlowExecutionResponse(BaseModel):
    flow_id: str
    workflow_type: str
    checkpoints_executed: List[str]
    content: str
    validation_results: Dict[str, Any]
```

#### POST /agents/{agent_name}/execute
**Purpose**: Execute individual CrewAI agent
```python
# Path parameter: agent_name = "research" | "audience" | "writer" | "style" | "quality"

class AgentExecutionRequest(BaseModel):
    input_data: Dict[str, Any]
    context: Optional[Dict[str, Any]] = None
    use_chromadb: bool = True

class AgentExecutionResponse(BaseModel):
    agent_name: str
    execution_id: str
    output: Dict[str, Any]
    chromadb_queries_made: int
    execution_time_ms: float
```

---

## 📊 6. Analytics Blackbox API (Port 8090)
**Performance tracking and user learning (placeholder implementation)**

### 5.1 Publication Performance Tracking

#### POST /track-publication
**Purpose**: Track publication performance for learning system
```python
class PublicationMetrics(BaseModel):
    platform: str
    publication_id: str
    platform_post_id: str
    metrics: Dict[str, Union[int, float]]
    engagement_data: Optional[Dict] = None
    timestamp: datetime

class TrackingResponse(BaseModel):
    status: str
    publication_id: str
    metrics_stored: bool
    learning_updated: bool
    insights_generated: bool
    note: str

@app.post("/track-publication", response_model=TrackingResponse)
async def track_publication_performance(
    metrics: PublicationMetrics,
    current_user: str = Depends(get_current_user)
):
    """
    Track publication performance metrics for future analytics integration
    Currently a placeholder that stores data for future AI learning systems
    """
    
    try:
        # Store publication performance data
        # This is a placeholder implementation
        performance_record = {
            "publication_id": metrics.publication_id,
            "platform": metrics.platform,
            "platform_post_id": metrics.platform_post_id,
            "metrics": metrics.metrics,
            "engagement_data": metrics.engagement_data,
            "tracked_at": datetime.now().isoformat(),
            "tracked_by": current_user
        }
        
        # Future: Store in analytics database
        # Future: Update user preference learning
        # Future: Feed into recommendation algorithms
        # Future: Update topic performance predictions
        
        await placeholder_store_performance_data(performance_record)
        
        response = TrackingResponse(
            status="tracked_placeholder",
            publication_id=metrics.publication_id,
            metrics_stored=True,
            learning_updated=False,  # Future implementation
            insights_generated=False,  # Future implementation
            note="Analytics integration coming in future release. Data stored for when analytics system is implemented."
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Performance tracking failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "tracking_failed",
                "message": "Performance tracking encountered an error",
                "publication_id": metrics.publication_id
            }
        )

# Example Request
POST /track-publication
{
    "platform": "linkedin",
    "publication_id": "pub_a1b2c3d4e5f6g7h8",
    "platform_post_id": "linkedin_post_abc123",
    "metrics": {
        "views": 1247,
        "likes": 89,
        "comments": 23,
        "shares": 15,
        "clicks": 156,
        "engagement_rate": 0.103
    },
    "engagement_data": {
        "top_performing_time": "2025-01-30T14:30:00Z",
        "audience_demographics": {
            "industries": ["Technology", "Marketing", "Consulting"],
            "seniority_levels": ["Manager", "Director", "VP"]
        }
    },
    "timestamp": "2025-01-30T15:00:00Z"
}

# Example Response
{
    "status": "tracked_placeholder",
    "publication_id": "pub_a1b2c3d4e5f6g7h8",
    "metrics_stored": true,
    "learning_updated": false,
    "insights_generated": false,
    "note": "Analytics integration coming in future release. Data stored for when analytics system is implemented."
}
```

#### GET /insights/{user_id}
**Purpose**: Get personalized publishing insights (placeholder)
```python
class UserInsights(BaseModel):
    user_id: str
    insights: Dict[str, Any]
    recommendations: List[str]
    performance_summary: Dict[str, float]
    prediction_accuracy: Optional[float]
    last_updated: datetime

@app.get("/insights/{user_id}", response_model=UserInsights)
async def get_user_insights(
    user_id: str,
    time_period: str = "30d",  # 7d, 30d, 90d, 1y
    platforms: Optional[List[str]] = None,
    current_user: str = Depends(get_current_user)
):
    """
    Get personalized publishing insights and recommendations
    Currently returns placeholder data for future analytics implementation
    """
    
    try:
        # Future: Generate AI-powered insights
        # Future: Performance analysis and recommendations
        # Future: Predictive analytics for optimal timing
        # Future: Content performance patterns
        
        # Placeholder implementation
        placeholder_insights = {
            "user_id": user_id,
            "insights": {
                "message": "Advanced analytics insights coming soon",
                "data_collected": "Performance data is being collected for future analysis",
                "estimated_launch": "Q2 2025",
                "placeholder_data": {
                    "best_performing_platforms": ["linkedin", "twitter"],
                    "optimal_posting_times": {
                        "linkedin": "Tuesday 9:00 AM EST",
                        "twitter": "Wednesday 2:00 PM EST"
                    },
                    "content_type_performance": {
                        "tutorial": "High engagement (avg 0.12 rate)",
                        "thought_leadership": "Medium engagement (avg 0.08 rate)",
                        "industry_update": "Variable engagement (0.05-0.15 rate)"
                    }
                }
            },
            "recommendations": [
                "Post more tutorial content on LinkedIn for higher engagement",
                "Schedule Twitter posts for Wednesday afternoons",
                "Consider adding more data-driven insights to thought leadership pieces",
                "Experiment with video content for better reach"
            ],
            "performance_summary": {
                "avg_engagement_rate": 0.089,
                "total_publications": 42,
                "best_performing_platform": "linkedin",
                "content_improvement_trend": 0.15
            },
            "prediction_accuracy": None,  # Will be available when AI system is implemented
            "last_updated": datetime.now()
        }
        
        return UserInsights(**placeholder_insights)
        
    except Exception as e:
        logger.error(f"Insights generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "insights_failed",
                "message": "Insights generation encountered an error",
                "user_id": user_id,
                "note": "This is a placeholder implementation"
            }
        )

# Example Response
{
    "user_id": "user_123",
    "insights": {
        "message": "Advanced analytics insights coming soon",
        "data_collected": "Performance data is being collected for future analysis",
        "estimated_launch": "Q2 2025",
        "placeholder_data": {
            "best_performing_platforms": ["linkedin", "twitter"],
            "optimal_posting_times": {
                "linkedin": "Tuesday 9:00 AM EST",
                "twitter": "Wednesday 2:00 PM EST"
            },
            "content_type_performance": {
                "tutorial": "High engagement (avg 0.12 rate)",
                "thought_leadership": "Medium engagement (avg 0.08 rate)",
                "industry_update": "Variable engagement (0.05-0.15 rate)"
            }
        }
    },
    "recommendations": [
        "Post more tutorial content on LinkedIn for higher engagement",
        "Schedule Twitter posts for Wednesday afternoons",
        "Consider adding more data-driven insights to thought leadership pieces",
        "Experiment with video content for better reach"
    ],
    "performance_summary": {
        "avg_engagement_rate": 0.089,
        "total_publications": 42,
        "best_performing_platform": "linkedin",
        "content_improvement_trend": 0.15
    },
    "prediction_accuracy": null,
    "last_updated": "2025-01-30T10:50:22.123Z"
}
```

---

## 🔧 6. Supporting APIs & Integrations

### 6.1 ChromaDB Direct Access (Port 8000)
**Direct ChromaDB server API for advanced operations**

```yaml
# ChromaDB Native API Endpoints
base_url: "http://localhost:8000/api/v1"

collections:
  - GET /collections
  - POST /collections
  - GET /collections/{collection_name}
  - DELETE /collections/{collection_name}

documents:
  - POST /collections/{collection_name}/add
  - POST /collections/{collection_name}/query
  - POST /collections/{collection_name}/get
  - POST /collections/{collection_name}/update
  - POST /collections/{collection_name}/delete

system:
  - GET /heartbeat
  - GET /version
  - POST /reset

# Usage in Vector Wave services
authentication: "Not required for internal services"
rate_limiting: "Handled by individual services"
```

### 6.2 Health Monitoring Across All Services

#### GET /_health (All Services)
**Purpose**: Standardized health check across all Vector Wave services
```python
# Standardized health check response format
{
    "status": "healthy|degraded|unhealthy",
    "service": "service-name",
    "version": "x.y.z",
    "port": 8000,
    "timestamp": "2025-01-30T10:00:00Z",
    "uptime_seconds": 86400,
    "dependencies": {
        "chromadb": "connected|disconnected",
        "redis": "connected|disconnected",
        "external_apis": "operational|limited|down"
    },
    "metrics": {
        "request_count": 15647,
        "error_rate": 0.02,
        "avg_response_time_ms": 150,
        "memory_usage_mb": 245,
        "cpu_usage_percent": 15
    }
}
```

### 6.3 Error Response Standardization

```python
# Standardized error response format across all APIs
class StandardErrorResponse(BaseModel):
    error: str  # Error code
    message: str  # Human-readable message
    details: Optional[Dict] = None  # Additional error context
    timestamp: datetime
    request_id: str  # For tracing
    service: str  # Which service generated the error

# Common error codes
ERROR_CODES = {
    "validation_failed": "Content validation encountered an error",
    "chromadb_unavailable": "ChromaDB service is unavailable",
    "authentication_required": "Valid authentication is required",
    "rate_limit_exceeded": "Request rate limit has been exceeded",
    "resource_not_found": "Requested resource was not found",
    "generation_failed": "Content generation encountered an error",
    "publication_failed": "Publication orchestration failed",
    "internal_error": "An internal server error occurred"
}

# Example error response
{
    "error": "validation_failed",
    "message": "Content validation encountered an error",
    "details": {
        "validation_id": "comp_a1b2c3d4e5f6",
        "chromadb_status": "connected",
        "rules_attempted": 8,
        "failure_point": "style_analysis"
    },
    "timestamp": "2025-01-30T10:30:15.123Z",
    "request_id": "req_x1y2z3a4b5c6",
    "service": "editorial-service"
}
```

---

## 🚀 7. Integration Examples

### 7.1 Complete User Workflow Integration

```python
# Example: Complete content generation and publishing workflow
class VectorWaveWorkflowClient:
    def __init__(self):
        self.editorial_service = EditorialServiceClient("http://localhost:8040")
        self.topic_manager = TopicManagerClient("http://localhost:8041")
        self.publishing_orchestrator = PublishingOrchestratorClient("http://localhost:8080")
        self.presentor_service = PresentorServiceClient("http://localhost:8089")
    
    async def complete_workflow(self, user_id: str):
        """Execute complete Vector Wave workflow"""
        
        # 1. Get topic suggestions
        topics_response = await self.topic_manager.get_suggestions(
            user_id=user_id,
            limit=5,
            trending_only=True
        )
        
        # 2. User selects topic (simulated)
        selected_topic = topics_response.suggestions[0]
        
        # 3. Generate content using AI Writing Flow with selective validation
        content = await self._generate_content_with_checkpoints(
            selected_topic, user_id
        )
        
        # 4. Final comprehensive validation
        final_validation = await self.editorial_service.validate_comprehensive(
            content=content,
            platform="linkedin",
            content_type=selected_topic.content_type,
            user_id=user_id
        )
        
        # 5. Apply any critical suggestions
        if final_validation.violations:
            content = await self.editorial_service.regenerate_content(
                original_content=content,
                validation_id=final_validation.validation_id,
                selected_suggestions=[v.rule_id for v in final_validation.violations[:3]]
            )
        
        # 6. Orchestrate publication
        publication_response = await self.publishing_orchestrator.publish(
            topic=selected_topic.dict(),
            platforms={
                "linkedin": {
                    "enabled": True,
                    "account_id": "production",
                    "options": {"include_pdf": True}
                },
                "twitter": {
                    "enabled": True,
                    "account_id": "main_account",
                    "schedule_time": "2025-01-30T14:00:00Z"
                }
            }
        )
        
        # 7. Handle LinkedIn manual upload if required
        if publication_response.linkedin_manual_upload:
            manual_info = publication_response.linkedin_manual_upload
            print("Manual LinkedIn upload required:")
            print(f"PPT: {manual_info['presentation_files']['ppt_url']}")
            print(f"PDF: {manual_info['presentation_files']['pdf_url']}")
            for instruction in manual_info['instructions']:
                print(f"  {instruction}")
        
        return publication_response
    
    async def _generate_content_with_checkpoints(self, topic, user_id):
        """Generate content with AI Writing Flow checkpoints"""
        
        # Pre-writing checkpoint
        pre_validation = await self.editorial_service.validate_selective(
            content=f"Planning to write about: {topic.title}. {topic.description}",
            platform="linkedin",
            content_type=topic.content_type,
            checkpoint="pre_writing",
            user_id=user_id
        )
        
        # Generate initial content based on pre-writing validation
        content = await self._generate_initial_content(topic, pre_validation)
        
        # Mid-writing checkpoint
        mid_validation = await self.editorial_service.validate_selective(
            content=content,
            platform="linkedin",
            content_type=topic.content_type,
            checkpoint="mid_writing",
            user_id=user_id
        )
        
        # Apply mid-writing improvements
        if mid_validation.violations:
            content = await self._apply_improvements(content, mid_validation.suggestions[:2])
        
        # Post-writing checkpoint
        post_validation = await self.editorial_service.validate_selective(
            content=content,
            platform="linkedin",
            content_type=topic.content_type,
            checkpoint="post_writing",
            user_id=user_id
        )
        
        # Final polish
        if post_validation.violations:
            content = await self._apply_improvements(content, post_validation.suggestions[:1])
        
        return content
```

### 7.2 Zero Hardcoded Rules Verification

```python
# Verification script to ensure zero hardcoded rules
async def verify_zero_hardcoded_rules():
    """Comprehensive verification that no hardcoded rules exist"""
    
    verification_results = {
        "file_scan": await scan_files_for_hardcoded_patterns(),
        "cache_verification": await verify_cache_chromadb_origins(),
        "api_validation": await validate_api_rule_sources(),
        "database_integrity": await check_chromadb_rule_counts()
    }
    
    all_clean = all(result.get("clean", False) for result in verification_results.values())
    
    return {
        "zero_hardcoded_confirmed": all_clean,
        "details": verification_results,
        "timestamp": datetime.now(),
        "compliance_score": 100 if all_clean else 0
    }

# Example verification result
{
    "zero_hardcoded_confirmed": true,
    "details": {
        "file_scan": {
            "clean": true,
            "files_scanned": 247,
            "patterns_searched": ["forbidden_phrases", "required_elements", "style_patterns", "default_rules"],
            "matches_found": 0
        },
        "cache_verification": {
            "clean": true,
            "cached_rules": 365,
            "rules_with_chromadb_origin": 365,
            "origin_compliance_rate": 1.0
        },
        "api_validation": {
            "clean": true,
            "endpoints_tested": 12,
            "all_use_chromadb": true,
            "response_sources_verified": true
        },
        "database_integrity": {
            "clean": true,
            "total_rules_in_chromadb": 378,
            "meets_minimum_target": true,
            "collections_healthy": true
        }
    },
    "timestamp": "2025-01-30T10:55:00.000Z",
    "compliance_score": 100
}
```

---

## 📋 8. OpenAPI Documentation

### 8.1 Complete OpenAPI Specification

```yaml
# Vector Wave Complete OpenAPI Specification
openapi: 3.0.3
info:
  title: Vector Wave API Suite
  description: |
    Complete API documentation for Vector Wave ChromaDB-centric content generation and publishing platform.
    
    ## Architecture
    Vector Wave consists of multiple specialized microservices:
    - **Editorial Service** (8040): ChromaDB-centric content validation
    - **Topic Manager** (8041): AI-powered topic suggestions and management  
    - **Publishing Orchestrator** (8080): Multi-platform publishing coordination
    - **Presentor Service** (8089): PPT/PDF generation for LinkedIn
    - **Analytics Blackbox** (8090): Performance tracking (placeholder)
    
    ## Key Features
    - Zero hardcoded rules (100% ChromaDB-sourced)
    - Dual workflow support (comprehensive vs selective validation)
    - LinkedIn special handling with manual PPT uploads
    - Real-time topic discovery with auto-scraping
    - Multi-platform publishing orchestration
    
  version: 2.0.0
  contact:
    name: Vector Wave API Support
    url: https://vectorwave.ai/support
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: http://localhost:8040
    description: Editorial Service
  - url: http://localhost:8041
    description: Topic Manager
  - url: http://localhost:8080
    description: Publishing Orchestrator
  - url: http://localhost:8089
    description: Presentor Service
  - url: http://localhost:8090
    description: Analytics Blackbox

security:
  - bearerAuth: []
  - apiKeyAuth: []

components:
  securitySchemes:
    bearerAuth:
      type: http
      scheme: bearer
      bearerFormat: JWT
    apiKeyAuth:
      type: apiKey
      in: header
      name: X-API-Key

  schemas:
    # Common schemas used across all services
    ValidationRule:
      type: object
      properties:
        rule_id:
          type: string
          example: "style_001_buzzwords"
        content:
          type: string
          example: "Avoid overusing buzzwords like 'paradigm', 'leverage', 'synergy'"
        rule_type:
          type: string
          enum: [style, structure, quality, editorial, grammar, tone, engagement]
        priority:
          type: string
          enum: [critical, high, medium, low]
        platform:
          type: string
          enum: [universal, linkedin, twitter, substack, beehiiv, ghost]
        confidence:
          type: number
          minimum: 0
          maximum: 1
        chromadb_metadata:
          type: object
          properties:
            collection:
              type: string
            similarity_score:
              type: number
            query_timestamp:
              type: string
              format: date-time

    ErrorResponse:
      type: object
      properties:
        error:
          type: string
          example: "validation_failed"
        message:
          type: string
          example: "Content validation encountered an error"
        details:
          type: object
        timestamp:
          type: string
          format: date-time
        request_id:
          type: string
        service:
          type: string

paths:
  # Editorial Service Endpoints
  /validate/comprehensive:
    post:
      tags: [Editorial Service]
      summary: Comprehensive content validation
      description: |
        Full validation using 8-12 ChromaDB rules for Kolegium AI-first workflow.
        This endpoint provides complete content analysis with all relevant validation rules.
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [content, platform, content_type]
              properties:
                content:
                  type: string
                  example: "AI is revolutionizing marketing..."
                platform:
                  type: string
                  enum: [linkedin, twitter, substack, beehiiv, ghost]
                content_type:
                  type: string
                  enum: [THOUGHT_LEADERSHIP, INDUSTRY_UPDATE, TUTORIAL, ANNOUNCEMENT]
                context:
                  type: object
                user_id:
                  type: string
      responses:
        200:
          description: Validation completed successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  validation_id:
                    type: string
                  mode:
                    type: string
                    example: "comprehensive"
                  rules_applied:
                    type: array
                    items:
                      $ref: '#/components/schemas/ValidationRule'
                  violations:
                    type: array
                    items:
                      type: object
                  suggestions:
                    type: array
                    items:
                      type: object
                  overall_score:
                    type: number
                    minimum: 0
                    maximum: 1
                  processing_time_ms:
                    type: number
                  chromadb_sourced:
                    type: boolean
                    example: true
        401:
          $ref: '#/components/responses/UnauthorizedError'
        500:
          $ref: '#/components/responses/InternalServerError'

  /validate/selective:
    post:
      tags: [Editorial Service]
      summary: Selective content validation
      description: |
        Checkpoint-based validation using 3-4 critical ChromaDB rules for AI Writing Flow human-assisted workflow.
        Designed for specific checkpoints in the content creation process.
      security:
        - bearerAuth: []
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              required: [content, platform, content_type, checkpoint]
              properties:
                content:
                  type: string
                platform:
                  type: string
                content_type:
                  type: string
                checkpoint:
                  type: string
                  enum: [pre_writing, mid_writing, post_writing]
                context:
                  type: object
                user_id:
                  type: string
      responses:
        200:
          description: Selective validation completed
          content:
            application/json:
              schema:
                type: object
                properties:
                  validation_id:
                    type: string
                  mode:
                    type: string
                    example: "selective"
                  rules_applied:
                    type: array
                    items:
                      $ref: '#/components/schemas/ValidationRule'
                  overall_score:
                    type: number
                  processing_time_ms:
                    type: number

  /health:
    get:
      tags: [System]
      summary: Service health check
      description: Comprehensive health check for Editorial Service including ChromaDB connectivity
      responses:
        200:
          description: Service is healthy
          content:
            application/json:
              schema:
                type: object
                properties:
                  status:
                    type: string
                    example: "healthy"
                  service:
                    type: string
                    example: "editorial-service"
                  version:
                    type: string
                    example: "2.0.0"
                  chromadb_status:
                    type: string
                    example: "connected"
                  total_rules_cached:
                    type: integer
        503:
          description: Service is unhealthy
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'

  responses:
    UnauthorizedError:
      description: Authentication required
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'
    InternalServerError:
      description: Internal server error
      content:
        application/json:
          schema:
            $ref: '#/components/schemas/ErrorResponse'

tags:
  - name: Editorial Service
    description: ChromaDB-centric content validation and rule management
  - name: Topic Manager
    description: AI-powered topic suggestions and database management
  - name: Publishing Orchestrator
    description: Multi-platform publishing coordination
  - name: Presentor Service
    description: PPT/PDF generation for LinkedIn manual uploads
  - name: Analytics Blackbox
    description: Performance tracking and user learning (placeholder)
  - name: System
    description: System health and monitoring endpoints
```

---

## 🎯 Summary & Usage Guidelines

### API Integration Checklist

✅ **Authentication**: All services support JWT Bearer tokens and API keys
✅ **Rate Limiting**: Built-in protection with configurable limits per endpoint
✅ **Error Handling**: Standardized error responses across all services
✅ **Health Monitoring**: Consistent health check endpoints for all services
✅ **ChromaDB Integration**: Zero hardcoded rules, 100% vector database sourced
✅ **Performance Monitoring**: Built-in metrics and performance tracking
✅ **Security**: Input validation, sanitization, and security headers
✅ **Documentation**: Complete OpenAPI 3.0 specifications with examples

### Quick Start Integration

```python
# Install Vector Wave API client
pip install vectorwave-api-client

# Initialize clients
from vectorwave import (
    EditorialServiceClient,
    TopicManagerClient, 
    PublishingOrchestratorClient
)

# Configure clients
editorial = EditorialServiceClient(
    base_url="http://localhost:8040",
    api_key="your_api_key"
)

topic_manager = TopicManagerClient(
    base_url="http://localhost:8041",
    api_key="your_api_key"  
)

publisher = PublishingOrchestratorClient(
    base_url="http://localhost:8080",
    api_key="your_api_key"
)

# Execute complete workflow
async def publish_content():
    # Get topic suggestions
    topics = await topic_manager.get_suggestions(limit=5)
    
    # Validate content
    validation = await editorial.validate_comprehensive(
        content="Your content here",
        platform="linkedin",
        content_type="THOUGHT_LEADERSHIP"
    )
    
    # Publish across platforms
    publication = await publisher.publish(
        topic=topics.suggestions[0],
        platforms={
            "linkedin": {"enabled": True, "account_id": "main"},
            "twitter": {"enabled": True, "account_id": "main"}
        }
    )
    
    return publication
```

**API Specifications Status**: ✅ **COMPLETE AND READY FOR IMPLEMENTATION**
**Services Covered**: 5 core services with full endpoint specifications
**Integration Examples**: Complete workflow examples and client libraries
**Security**: Production-ready authentication and rate limiting
**Documentation**: OpenAPI 3.0 compliant with interactive documentation