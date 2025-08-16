"""
Platform Collectors Manager for Analytics Service
Manages data collection from different platforms with realistic API limitations
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid
from dataclasses import dataclass

from models import ManualMetricsEntry

logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of manual entry processing"""
    accepted_metrics: Dict[str, bool]
    quality_score: float
    validation_errors: List[str] = None
    processing_notes: List[str] = None


class PlatformCollectorManager:
    """
    Manages all platform-specific data collectors
    Implements multi-tier collection strategy based on platform capabilities
    """
    
    def __init__(self, chromadb_manager):
        self.chromadb_manager = chromadb_manager
        self.collectors = {}
        self.platform_capabilities = {
            "ghost": {
                "method": "api",
                "metrics": ["views", "likes", "comments", "subscribers", "email_opens"],
                "limitations": [],
                "automation_level": "full"
            },
            "twitter": {
                "method": "proxy",
                "metrics": ["views", "likes", "retweets", "replies", "bookmarks"],
                "limitations": ["Requires Typefully Pro subscription", "Limited to scheduled posts only"],
                "automation_level": "semi"
            },
            "linkedin": {
                "method": "manual",
                "metrics": ["views", "reactions", "comments", "shares"],
                "limitations": ["No API access", "Manual data entry required", "Limited to public metrics"],
                "automation_level": "manual"
            },
            "beehiiv": {
                "method": "csv",
                "metrics": ["subscribers", "opens", "clicks", "unsubscribes"],
                "limitations": ["CSV export only", "Weekly data updates maximum"],
                "automation_level": "batch"
            }
        }
        
        # Quality scoring rules for manual entry
        self.quality_scoring_rules = {
            "linkedin": {
                "required_metrics": ["views", "reactions"],
                "optional_metrics": ["comments", "shares", "profile_visits"],
                "screenshot_bonus": 0.1,
                "notes_bonus": 0.05,
                "consistency_weight": 0.3,
                "completeness_weight": 0.4,
                "benchmark_weight": 0.3
            }
        }
    
    async def configure_platform_collector(self, platform: str, method: str, 
                                          config: Dict[str, Any], user_id: str) -> Dict[str, Any]:
        """Configure collector for specific platform"""
        try:
            logger.info(f"🔧 Configuring {platform} collector with method: {method}")
            
            if platform not in self.platform_capabilities:
                raise ValueError(f"Unsupported platform: {platform}")
            
            platform_config = self.platform_capabilities[platform]
            
            if method != platform_config["method"]:
                raise ValueError(f"Method {method} not supported for {platform}")
            
            # Store collector configuration
            collector_config = {
                "platform": platform,
                "method": method,
                "config": config,
                "user_id": user_id,
                "configured_at": datetime.now().isoformat(),
                "status": "active"
            }
            
            self.collectors[f"{platform}_{user_id}"] = collector_config
            
            logger.info(f"✅ {platform} collector configured successfully")
            return {
                "status": "configured",
                "platform": platform,
                "method": method,
                "capabilities": platform_config
            }
            
        except Exception as e:
            logger.error(f"❌ Platform collector configuration failed: {e}")
            raise
    
    async def process_manual_entry(self, entry: ManualMetricsEntry, 
                                  entry_id: str, user_id: str) -> ProcessingResult:
        """Process manual metrics entry with quality validation"""
        try:
            platform = entry.platform.value
            logger.info(f"📝 Processing manual entry for {platform}: {entry_id}")
            
            # Validate platform support
            if platform not in self.platform_capabilities:
                raise ValueError(f"Platform {platform} not supported for manual entry")
            
            if self.platform_capabilities[platform]["method"] != "manual":
                raise ValueError(f"Platform {platform} does not support manual entry")
            
            # Validate metrics
            validation_result = await self._validate_manual_metrics(platform, entry.metrics)
            
            # Calculate data quality score
            quality_score = await self._calculate_quality_score(platform, entry, user_id)
            
            # Store in ChromaDB
            additional_metadata = {
                "screenshot_urls": entry.screenshot_urls,
                "entry_date": entry.entry_date.isoformat(),
                "notes": entry.notes,
                "validation_status": "validated" if validation_result.all_valid else "partial"
            }
            
            storage_success = await self.chromadb_manager.store_analytics_data(
                entry_id=entry_id,
                platform=platform,
                collection_method="manual",
                metrics=entry.metrics,
                publication_id=entry.publication_id,
                quality_score=quality_score,
                user_id=user_id,
                additional_metadata=additional_metadata
            )
            
            if not storage_success:
                raise Exception("Failed to store manual entry data")
            
            processing_result = ProcessingResult(
                accepted_metrics=validation_result.accepted_metrics,
                quality_score=quality_score,
                validation_errors=validation_result.errors,
                processing_notes=[
                    f"Entry processed for {platform}",
                    f"Quality score: {quality_score:.2f}",
                    f"Screenshot provided: {bool(entry.screenshot_urls)}"
                ]
            )
            
            logger.info(f"✅ Manual entry processed: {entry_id}, quality: {quality_score:.2f}")
            return processing_result
            
        except Exception as e:
            logger.error(f"❌ Manual entry processing failed: {e}")
            raise
    
    async def _validate_manual_metrics(self, platform: str, metrics: Dict[str, Any]):
        """Validate manual metrics against platform requirements"""
        
        @dataclass
        class ValidationResult:
            accepted_metrics: Dict[str, bool]
            all_valid: bool
            errors: List[str]
        
        try:
            platform_config = self.platform_capabilities[platform]
            valid_metrics = platform_config["metrics"]
            
            accepted_metrics = {}
            errors = []
            
            for metric_name, metric_value in metrics.items():
                if metric_name not in valid_metrics:
                    accepted_metrics[metric_name] = False
                    errors.append(f"Metric '{metric_name}' not supported for {platform}")
                elif not isinstance(metric_value, (int, float)):
                    accepted_metrics[metric_name] = False
                    errors.append(f"Metric '{metric_name}' must be numeric")
                elif metric_value < 0:
                    accepted_metrics[metric_name] = False
                    errors.append(f"Metric '{metric_name}' cannot be negative")
                else:
                    accepted_metrics[metric_name] = True
            
            all_valid = len(errors) == 0
            
            return ValidationResult(
                accepted_metrics=accepted_metrics,
                all_valid=all_valid,
                errors=errors
            )
            
        except Exception as e:
            logger.error(f"Metrics validation failed: {e}")
            return ValidationResult(
                accepted_metrics={},
                all_valid=False,
                errors=[f"Validation error: {e}"]
            )
    
    async def _calculate_quality_score(self, platform: str, entry: ManualMetricsEntry, 
                                     user_id: str) -> float:
        """Calculate data quality score for manual entry"""
        try:
            if platform not in self.quality_scoring_rules:
                return 0.7  # Default score for unsupported platforms
            
            rules = self.quality_scoring_rules[platform]
            score = 0.0
            
            # 1. Completeness score (40% weight)
            completeness_score = await self._calculate_completeness_score(rules, entry.metrics)
            score += completeness_score * rules["completeness_weight"]
            
            # 2. Consistency score (30% weight) - based on user's historical data
            consistency_score = await self._calculate_consistency_score(user_id, platform, entry.metrics)
            score += consistency_score * rules["consistency_weight"]
            
            # 3. Benchmark score (30% weight) - compared to platform benchmarks
            benchmark_score = await self._calculate_benchmark_score(platform, entry.metrics)
            score += benchmark_score * rules["benchmark_weight"]
            
            # Bonus points
            if entry.screenshot_urls:
                score += rules["screenshot_bonus"]
            
            if entry.notes:
                score += rules["notes_bonus"]
            
            # Ensure score is between 0 and 1
            final_score = min(max(score, 0.0), 1.0)
            
            logger.debug(f"Quality score for {platform}: {final_score:.3f}")
            return final_score
            
        except Exception as e:
            logger.error(f"Quality score calculation failed: {e}")
            return 0.5  # Default middle score
    
    async def _calculate_completeness_score(self, rules: Dict, metrics: Dict[str, Any]) -> float:
        """Calculate completeness score based on required and optional metrics"""
        required_metrics = rules.get("required_metrics", [])
        optional_metrics = rules.get("optional_metrics", [])
        
        # Check required metrics
        required_present = sum(1 for metric in required_metrics if metric in metrics)
        required_score = required_present / len(required_metrics) if required_metrics else 1.0
        
        # Check optional metrics
        optional_present = sum(1 for metric in optional_metrics if metric in metrics)
        optional_score = optional_present / len(optional_metrics) if optional_metrics else 0.0
        
        # Combine scores (required metrics are more important)
        completeness = (required_score * 0.8) + (optional_score * 0.2)
        return completeness
    
    async def _calculate_consistency_score(self, user_id: str, platform: str, 
                                         current_metrics: Dict[str, Any]) -> float:
        """Calculate consistency score based on user's historical data"""
        try:
            # Get user's historical data for this platform
            historical_data = await self.chromadb_manager.query_user_analytics(
                user_id=user_id,
                platforms=[platform]
            )
            
            if len(historical_data) < 2:
                return 0.8  # High score for new users
            
            # Analyze consistency patterns
            # This is a simplified implementation - in production, you'd have more sophisticated analysis
            
            consistency_factors = []
            
            for metric_name, metric_value in current_metrics.items():
                historical_values = []
                for record in historical_data[-5:]:  # Last 5 records
                    metadata = record.get("metadata", {})
                    historical_metrics = metadata.get("metrics", {})
                    if metric_name in historical_metrics:
                        historical_values.append(historical_metrics[metric_name])
                
                if historical_values:
                    # Calculate coefficient of variation
                    mean_val = sum(historical_values) / len(historical_values)
                    if mean_val > 0:
                        variance = sum((x - mean_val) ** 2 for x in historical_values) / len(historical_values)
                        cv = (variance ** 0.5) / mean_val
                        
                        # Higher consistency score for lower coefficient of variation
                        consistency_factor = max(0, 1 - cv)
                        consistency_factors.append(consistency_factor)
            
            if consistency_factors:
                return sum(consistency_factors) / len(consistency_factors)
            else:
                return 0.8  # Default for no historical data
                
        except Exception as e:
            logger.error(f"Consistency score calculation failed: {e}")
            return 0.7
    
    async def _calculate_benchmark_score(self, platform: str, metrics: Dict[str, Any]) -> float:
        """Calculate benchmark score compared to platform averages"""
        try:
            # Platform-specific benchmark data (would be updated regularly)
            benchmarks = {
                "linkedin": {
                    "views": {"min": 100, "avg": 1500, "max": 10000},
                    "reactions": {"min": 5, "avg": 150, "max": 1000},
                    "comments": {"min": 0, "avg": 25, "max": 200},
                    "shares": {"min": 0, "avg": 15, "max": 100}
                }
            }
            
            if platform not in benchmarks:
                return 0.8  # Default score for platforms without benchmarks
            
            platform_benchmarks = benchmarks[platform]
            scores = []
            
            for metric_name, metric_value in metrics.items():
                if metric_name in platform_benchmarks:
                    benchmark = platform_benchmarks[metric_name]
                    
                    if metric_value < benchmark["min"]:
                        # Below minimum - low score but not zero
                        score = 0.3
                    elif metric_value > benchmark["max"]:
                        # Above maximum - very good but check for outliers
                        if metric_value > benchmark["max"] * 3:
                            score = 0.4  # Possible outlier
                        else:
                            score = 0.95
                    else:
                        # Within normal range - score based on position
                        range_size = benchmark["max"] - benchmark["min"]
                        position = (metric_value - benchmark["min"]) / range_size
                        score = 0.5 + (position * 0.4)  # 0.5 to 0.9 range
                    
                    scores.append(score)
            
            return sum(scores) / len(scores) if scores else 0.8
            
        except Exception as e:
            logger.error(f"Benchmark score calculation failed: {e}")
            return 0.7
    
    async def get_status(self) -> Dict[str, str]:
        """Get status of all configured collectors"""
        status = {}
        
        for collector_key, collector_config in self.collectors.items():
            platform = collector_config["platform"]
            status[platform] = collector_config.get("status", "unknown")
        
        # Add default status for unconfigured platforms
        for platform in self.platform_capabilities:
            if platform not in status:
                status[platform] = "not_configured"
        
        return status