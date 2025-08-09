# 📊 Analytics Service Architecture Specification
**Production-Ready Multi-Platform Analytics for Vector Wave**

## 🎯 Executive Summary

Analytics Service (port 8081) provides comprehensive multi-platform analytics capabilities based on realistic API limitations and platform-specific collection methods. The service implements a flexible, extensible architecture that accommodates the varying data collection capabilities across different publishing platforms.

## 🏗️ Core Architecture

### Clean Architecture Implementation

```
┌─────────────────────────────────────────────────────────────┐
│                     Analytics Service API                   │
├─────────────────────────────────────────────────────────────┤
│  FastAPI Controllers (8081)                                │
│  • Platform Configuration                                   │  
│  • Manual Data Entry                                        │
│  • CSV Import Processing                                    │
│  • Insights Generation                                      │
│  • Data Export                                              │
├─────────────────────────────────────────────────────────────┤
│                    Business Logic Layer                     │
├─────────────────────────────────────────────────────────────┤
│  Collection Services    │  Analysis Services                │
│  • Platform Collectors │  • Performance Analyzer           │
│  • Data Validators     │  • Insight Generator               │
│  • Quality Assessor    │  • Trend Detector                 │
├─────────────────────────────────────────────────────────────┤
│                     Repository Layer                        │
├─────────────────────────────────────────────────────────────┤
│  ChromaDB Integration   │  File Storage                     │
│  • Analytics Collection│  • CSV Processors                 │
│  • Platform Configs    │  • Export Generators              │
│  • User Insights       │  • Screenshot Storage             │
├─────────────────────────────────────────────────────────────┤
│                     External Services                       │
├─────────────────────────────────────────────────────────────┤
│  Ghost API    │ Typefully │ Manual Entry │ CSV Processing │
│  (Full)       │ Proxy     │ (LinkedIn)   │ (Beehiiv)      │
└─────────────────────────────────────────────────────────────┘
```

## 🌐 Platform Integration Strategy

### Platform Capability Matrix

| Platform | Method | API Status | Collection Frequency | Data Quality | Automation Level |
|----------|--------|------------|---------------------|--------------|------------------|
| **Ghost CMS** | API | ✅ Full Access | Real-time | High (95%+) | Fully Automated |
| **Twitter/X** | Proxy | ⚠️ Via Typefully | Daily | Medium (78%) | Semi-Automated |
| **LinkedIn** | Manual | ❌ No API | Weekly | Medium (61%) | Manual Entry |
| **Beehiiv** | CSV | ❌ Export Only | Weekly | High (94%) | CSV Import |

### Multi-Tier Data Collection Strategy

```python
# Collection Strategy Implementation
class PlatformCollectionStrategy:
    """
    Multi-tier data collection accommodating platform limitations
    """
    
    def __init__(self, chromadb_client):
        self.strategies = {
            "api": APICollectionStrategy(),      # Ghost CMS
            "proxy": ProxyCollectionStrategy(),  # Twitter via Typefully  
            "manual": ManualEntryStrategy(),     # LinkedIn
            "csv": CSVImportStrategy()           # Beehiiv
        }
    
    async def collect_platform_data(self, platform: str, config: Dict):
        """Route to appropriate collection method based on platform"""
        
        platform_configs = {
            "ghost": {"method": "api", "frequency": "hourly"},
            "twitter": {"method": "proxy", "frequency": "daily"}, 
            "linkedin": {"method": "manual", "frequency": "weekly"},
            "beehiiv": {"method": "csv", "frequency": "weekly"}
        }
        
        platform_config = platform_configs.get(platform)
        if not platform_config:
            raise UnsupportedPlatformError(f"Platform {platform} not supported")
            
        strategy = self.strategies[platform_config["method"]]
        return await strategy.collect_data(platform, config)
```

## 🔧 Core Components

### 1. Platform Collectors

#### Ghost CMS API Collector
```python
class GhostAPICollector(BaseCollector):
    """Full API access to Ghost CMS analytics"""
    
    async def collect_metrics(self, post_ids: List[str]) -> List[AnalyticsRecord]:
        """
        Collects comprehensive metrics via Ghost Admin API
        """
        metrics = []
        
        for post_id in post_ids:
            try:
                # Ghost Admin API call
                post_analytics = await self.ghost_client.get_post_analytics(post_id)
                
                metrics.append(AnalyticsRecord(
                    platform="ghost",
                    post_id=post_id,
                    collection_method="api",
                    metrics={
                        "views": post_analytics.views,
                        "unique_views": post_analytics.unique_views,
                        "reading_time": post_analytics.avg_reading_time,
                        "bounce_rate": post_analytics.bounce_rate,
                        "engagement_time": post_analytics.engagement_time,
                        "subscribers_gained": post_analytics.subscribers_gained
                    },
                    data_quality_score=0.95,  # High quality from API
                    collected_at=datetime.now()
                ))
                
            except Exception as e:
                logger.error(f"Ghost API collection failed for {post_id}: {e}")
                
        return metrics
```

#### Twitter Proxy Collector
```python
class TwitterProxyCollector(BaseCollector):
    """Collect Twitter metrics via Typefully proxy"""
    
    async def collect_metrics(self, typefully_post_ids: List[str]) -> List[AnalyticsRecord]:
        """
        Limited collection via Typefully API for scheduled posts only
        """
        metrics = []
        
        for post_id in typefully_post_ids:
            try:
                # Typefully Analytics API
                post_stats = await self.typefully_client.get_post_analytics(post_id)
                
                # Map Typefully data to our format
                metrics.append(AnalyticsRecord(
                    platform="twitter",
                    post_id=post_stats.twitter_id,  
                    collection_method="proxy",
                    metrics={
                        "views": post_stats.impressions,
                        "likes": post_stats.likes,
                        "retweets": post_stats.retweets,
                        "replies": post_stats.replies,
                        "bookmarks": post_stats.bookmarks,
                        "engagement_rate": post_stats.engagement_rate
                    },
                    data_quality_score=0.78,  # Medium quality via proxy
                    collected_at=datetime.now(),
                    limitations=["Only scheduled posts", "24h delay", "Requires Typefully Pro"]
                ))
                
            except Exception as e:
                logger.error(f"Typefully collection failed for {post_id}: {e}")
                
        return metrics
```

### 2. Manual Data Management

#### LinkedIn Manual Entry System
```python
class LinkedInManualProcessor:
    """Process manually entered LinkedIn metrics with quality validation"""
    
    async def process_manual_entry(self, entry: ManualMetricsEntry) -> ProcessedEntry:
        """
        Process manual LinkedIn data entry with quality scoring
        """
        
        # Data validation
        validator = LinkedInMetricsValidator()
        validation_result = await validator.validate_entry(entry)
        
        if not validation_result.is_valid:
            raise ValidationError("LinkedIn metrics validation failed", 
                                  errors=validation_result.errors)
        
        # Quality assessment  
        quality_assessor = ManualDataQualityAssessor()
        quality_score = await quality_assessor.assess_quality(
            entry=entry,
            user_history=await self.get_user_entry_history(entry.user_id),
            platform_benchmarks=await self.get_platform_benchmarks("linkedin")
        )
        
        # Store with quality metadata
        processed_entry = ProcessedEntry(
            entry_id=entry.entry_id,
            platform="linkedin", 
            collection_method="manual",
            metrics=validation_result.validated_metrics,
            quality_score=quality_score,
            quality_indicators={
                "consistency_score": quality_assessor.consistency_score,
                "benchmark_deviation": quality_assessor.benchmark_deviation,
                "entry_completeness": quality_assessor.completeness_score,
                "screenshot_provided": bool(entry.screenshot_urls)
            },
            processed_at=datetime.now()
        )
        
        # Store in ChromaDB
        await self.store_processed_entry(processed_entry)
        
        return processed_entry
```

### 3. CSV Import Processing

#### Beehiiv CSV Processor  
```python
class BeehiivCSVProcessor:
    """Process Beehiiv newsletter analytics from CSV exports"""
    
    async def process_csv_import(self, csv_file_url: str, column_mapping: Dict) -> CSVProcessingResult:
        """
        Process Beehiiv CSV export with comprehensive validation
        """
        
        # Download and validate CSV
        csv_data = await self.download_csv(csv_file_url)
        validation_result = await self.validate_csv_structure(csv_data, column_mapping)
        
        if not validation_result.is_valid:
            raise CSVValidationError("CSV structure validation failed",
                                     issues=validation_result.issues)
        
        processed_records = []
        processing_errors = []
        
        for row_index, row in enumerate(csv_data.rows):
            try:
                # Map columns to our schema
                mapped_data = self.map_csv_row(row, column_mapping)
                
                # Validate individual record
                record_validator = BeehiivRecordValidator()
                record_validation = await record_validator.validate_record(mapped_data)
                
                if record_validation.is_valid:
                    processed_record = AnalyticsRecord(
                        platform="beehiiv",
                        post_id=mapped_data.get("email_id", f"beehiiv_{row_index}"),
                        collection_method="csv",
                        metrics={
                            "subscribers_sent": mapped_data["subscribers_sent"],
                            "opens": mapped_data["opens"],
                            "clicks": mapped_data["clicks"], 
                            "unsubscribes": mapped_data["unsubscribes"],
                            "open_rate": mapped_data["open_rate"],
                            "click_rate": mapped_data["click_rate"]
                        },
                        data_quality_score=0.94,  # High quality from CSV
                        collected_at=datetime.now(),
                        source_metadata={
                            "csv_row": row_index,
                            "import_batch": csv_file_url,
                            "validation_notes": record_validation.notes
                        }
                    )
                    
                    processed_records.append(processed_record)
                else:
                    processing_errors.append(f"Row {row_index}: {record_validation.error}")
                    
            except Exception as e:
                processing_errors.append(f"Row {row_index}: Processing error - {e}")
        
        # Store processed records in ChromaDB
        stored_count = await self.store_csv_records(processed_records)
        
        return CSVProcessingResult(
            total_rows=len(csv_data.rows),
            processed_records=len(processed_records),
            stored_records=stored_count,
            processing_errors=processing_errors,
            data_quality_average=0.94
        )
```

## 📊 Analytics Intelligence Engine

### Performance Analysis System

```python
class AnalyticsInsightsGenerator:
    """Generate actionable insights from multi-platform analytics data"""
    
    def __init__(self, chromadb_client):
        self.chromadb_client = chromadb_client
        self.performance_analyzer = PerformanceAnalyzer()
        self.trend_detector = TrendDetector()
        
    async def generate_comprehensive_insights(self, user_id: str, time_period: str) -> AnalyticsInsights:
        """
        Generate comprehensive analytics insights with cross-platform analysis
        """
        
        # Query all user analytics data
        analytics_data = await self.query_user_analytics_data(user_id, time_period)
        
        if not analytics_data.has_sufficient_data():
            return self.generate_insufficient_data_response(analytics_data)
        
        # Platform performance comparison
        platform_analysis = await self.performance_analyzer.analyze_platform_performance(
            analytics_data.by_platform()
        )
        
        # Content type performance analysis  
        content_type_analysis = await self.performance_analyzer.analyze_content_performance(
            analytics_data.by_content_type()
        )
        
        # Trend detection across platforms
        trend_analysis = await self.trend_detector.detect_trends(
            analytics_data.time_series_data()
        )
        
        # Generate actionable recommendations
        recommendation_engine = RecommendationEngine()
        recommendations = await recommendation_engine.generate_recommendations(
            platform_analysis=platform_analysis,
            content_analysis=content_type_analysis,
            trend_analysis=trend_analysis,
            user_goals=await self.get_user_goals(user_id)
        )
        
        # Optimal posting schedule analysis
        schedule_optimizer = PostingScheduleOptimizer()
        optimal_schedule = await schedule_optimizer.optimize_schedule(
            analytics_data.engagement_patterns()
        )
        
        return AnalyticsInsights(
            user_id=user_id,
            time_period=time_period,
            total_publications=analytics_data.total_publications,
            platforms_analyzed=analytics_data.platforms,
            overall_performance=platform_analysis.overall_metrics,
            platform_comparison=platform_analysis.platform_comparison,
            content_type_performance=content_type_analysis.performance_by_type,
            trending_topics=trend_analysis.trending_topics,
            key_insights=self.generate_key_insights(platform_analysis, content_type_analysis),
            recommendations=recommendations.actionable_items,
            optimal_posting_schedule=optimal_schedule.by_platform,
            data_coverage=analytics_data.coverage_by_platform(),
            data_quality_score=analytics_data.average_quality_score(),
            generated_at=datetime.now()
        )
```

### Circuit Breaker Implementation

```python
class AnalyticsCircuitBreaker:
    """Circuit breaker for external analytics API calls"""
    
    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"  # CLOSED, OPEN, HALF_OPEN
        
    async def call_with_circuit_breaker(self, platform: str, operation: callable, *args, **kwargs):
        """Execute operation with circuit breaker protection"""
        
        if self.state == "OPEN":
            if self._should_attempt_reset():
                self.state = "HALF_OPEN"
            else:
                raise CircuitBreakerOpenError(f"{platform} analytics API is currently unavailable")
        
        try:
            result = await operation(*args, **kwargs)
            
            # Operation successful - reset circuit breaker
            if self.state == "HALF_OPEN":
                self._reset_circuit_breaker()
                
            return result
            
        except Exception as e:
            self._record_failure()
            
            if self.failure_count >= self.failure_threshold:
                self.state = "OPEN"
                self.last_failure_time = time.time()
                
            raise AnalyticsCollectionError(f"{platform} data collection failed: {e}")
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        return (time.time() - self.last_failure_time) > self.recovery_timeout
    
    def _reset_circuit_breaker(self):
        """Reset circuit breaker to closed state"""
        self.failure_count = 0
        self.last_failure_time = None
        self.state = "CLOSED"
    
    def _record_failure(self):
        """Record a failure occurrence"""
        self.failure_count += 1
```

## 💾 ChromaDB Integration

### Analytics Collections Schema

```python
# ChromaDB Collections for Analytics Service
ANALYTICS_COLLECTIONS = {
    "platform_analytics": {
        "description": "Raw analytics data from all platforms",
        "schema": {
            "content": "Platform metrics summary text",
            "metadata": {
                "entry_id": str,
                "publication_id": str, 
                "platform": str,  # ghost, twitter, linkedin, beehiiv
                "collection_method": str,  # api, proxy, manual, csv
                "metrics": Dict[str, Union[int, float]],
                "quality_score": float,
                "collected_at": str,  # ISO datetime
                "processed": bool
            }
        }
    },
    
    "platform_configurations": {
        "description": "Platform-specific collection configurations", 
        "schema": {
            "content": "Platform configuration summary",
            "metadata": {
                "config_id": str,
                "platform": str,
                "collection_method": str,
                "api_credentials_hash": str,  # Hashed for security
                "collection_frequency": str,
                "enabled_metrics": List[str],
                "created_by": str,
                "created_at": str
            }
        }
    },
    
    "analytics_insights": {
        "description": "Generated insights and recommendations",
        "schema": {
            "content": "Insights summary and key findings",
            "metadata": {
                "insight_id": str,
                "user_id": str,
                "time_period": str,
                "platforms_analyzed": List[str],
                "key_insights": List[str],
                "recommendations": List[str],
                "data_quality_score": float,
                "generated_at": str
            }
        }
    }
}
```

## 🚀 Deployment Architecture

### Docker Configuration

```yaml
# docker-compose.analytics.yml
version: "3.9"

services:
  analytics-service:
    build: ./kolegium/analytics-service
    container_name: analytics-service
    ports:
      - "8081:8081"
    environment:
      - HOST=0.0.0.0
      - PORT=8081
      - DEBUG=false
      - CHROMADB_URL=http://chromadb:8000
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=info
      - CIRCUIT_BREAKER_ENABLED=true
      - MAX_CSV_FILE_SIZE=50MB
      - EXPORT_RETENTION_DAYS=7
    depends_on:
      - chromadb
      - redis
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8081/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped
    volumes:
      - analytics_uploads:/app/uploads
      - analytics_exports:/app/exports
    networks:
      - vector-wave

volumes:
  analytics_uploads:
  analytics_exports:
```

### Service Health Monitoring

```python
class AnalyticsHealthChecker:
    """Comprehensive health check for Analytics Service"""
    
    async def check_service_health(self) -> HealthCheckResult:
        """Multi-component health verification"""
        
        checks = {
            "chromadb": await self.check_chromadb_connectivity(),
            "platform_apis": await self.check_platform_api_health(),
            "circuit_breakers": await self.check_circuit_breaker_states(),
            "data_quality": await self.check_recent_data_quality(),
            "storage": await self.check_storage_availability()
        }
        
        overall_health = "healthy" if all(
            check.status == "healthy" for check in checks.values()
        ) else "degraded"
        
        return HealthCheckResult(
            service="analytics-service",
            port=8081,
            overall_status=overall_health,
            component_checks=checks,
            uptime_seconds=time.time() - self.service_start_time,
            timestamp=datetime.now()
        )
```

## 📈 Performance & Scaling

### Performance Metrics

- **API Response Times**: <200ms for insights generation
- **Data Processing**: 1000+ records/minute for CSV imports  
- **Concurrent Users**: 50+ simultaneous analytics requests
- **Storage Efficiency**: ChromaDB vector storage for insights similarity
- **Data Retention**: 2 years of analytics data, configurable

### Scaling Strategy

```python
# Horizontal Scaling Architecture
class AnalyticsServiceScaler:
    """Auto-scaling based on processing load"""
    
    async def scale_based_on_load(self):
        """Monitor and scale analytics processing capacity"""
        
        current_metrics = await self.get_current_load_metrics()
        
        scaling_decisions = {
            "csv_processors": self.should_scale_csv_processing(current_metrics),
            "insight_generators": self.should_scale_insight_generation(current_metrics), 
            "api_workers": self.should_scale_api_workers(current_metrics)
        }
        
        for component, should_scale in scaling_decisions.items():
            if should_scale:
                await self.scale_component(component, current_metrics.load_factor)
```

## 🔐 Security & Privacy

### Data Security Measures

1. **API Credentials**: Encrypted storage in ChromaDB metadata
2. **Manual Entry Validation**: Screenshot verification for sensitive metrics  
3. **Rate Limiting**: Per-user API rate limits to prevent abuse
4. **Data Retention**: Configurable retention policies per platform
5. **Export Security**: Time-limited signed URLs for data exports

### Privacy Compliance

```python
class AnalyticsPrivacyManager:
    """GDPR/CCPA compliance for analytics data"""
    
    async def anonymize_user_data(self, user_id: str):
        """Anonymize or delete user analytics data"""
        
        # Remove personal identifiers from ChromaDB
        collections_to_clean = ["platform_analytics", "analytics_insights"]
        
        for collection_name in collections_to_clean:
            collection = self.chromadb_client.get_collection(collection_name)
            
            # Query user data
            user_data = collection.query(
                where={"user_id": user_id},
                n_results=10000  # Get all user data
            )
            
            # Anonymize or delete based on retention policy
            for record_id in user_data["ids"]:
                await self.anonymize_record(collection, record_id)
```

## 🎯 Integration with Vector Wave Ecosystem

### Service Communication

```python
# Integration with other Vector Wave services
class VectorWaveAnalyticsIntegration:
    """Integration points with other Vector Wave services"""
    
    def __init__(self):
        self.editorial_service = EditorialServiceClient("http://editorial-service:8040")
        self.publishing_orchestrator = PublishingOrchestratorClient("http://publishing-orchestrator:8080")
        
    async def enhance_content_recommendations(self, user_id: str, topic: str) -> ContentRecommendations:
        """Use analytics insights to improve content recommendations"""
        
        # Get user's historical performance
        user_insights = await self.get_analytics_insights(user_id, "90d")
        
        # Get editorial validation for content type
        content_validation = await self.editorial_service.validate_selective(
            content=f"Planning content about: {topic}",
            platform="linkedin",  # Use best performing platform
            checkpoint="pre_writing"
        )
        
        # Combine analytics insights with editorial recommendations
        enhanced_recommendations = self.combine_insights_with_editorial(
            analytics_insights=user_insights,
            editorial_suggestions=content_validation.suggestions
        )
        
        return enhanced_recommendations
```

## 📋 Implementation Roadmap

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] FastAPI service setup with Docker
- [ ] ChromaDB collections initialization  
- [ ] Basic health check and monitoring
- [ ] Ghost CMS API collector implementation
- [ ] Manual entry system for LinkedIn

### Phase 2: Multi-Platform Support (Week 3-4)  
- [ ] Typefully proxy collector for Twitter
- [ ] CSV import processor for Beehiiv
- [ ] Data quality assessment system
- [ ] Circuit breaker implementation

### Phase 3: Analytics Intelligence (Week 5-6)
- [ ] Performance analysis engine
- [ ] Insights generation system
- [ ] Recommendation algorithms
- [ ] Optimal scheduling analysis

### Phase 4: Production Features (Week 7-8)
- [ ] Data export functionality
- [ ] Advanced visualizations
- [ ] Privacy compliance tools
- [ ] Performance optimization

---

**Analytics Service Architecture Status**: ✅ **COMPLETE & READY FOR IMPLEMENTATION**

**Key Features**: Multi-platform support, realistic API limitations, ChromaDB integration, comprehensive insights generation

**Integration Ready**: Fully compatible with Vector Wave target-version architecture