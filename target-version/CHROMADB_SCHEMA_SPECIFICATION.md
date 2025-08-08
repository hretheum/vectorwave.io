# 🗄️ ChromaDB Schema Specification
**Vector Wave Complete Database Architecture**

## 📊 Overview

### Database Architecture
- **Database System**: ChromaDB (Vector Database)
- **Collections Count**: 5 specialized collections
- **Total Rule Capacity**: 500+ rules (355+ migrated from hardcoded sources)
- **Embedding Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Query Performance Target**: P95 < 100ms, P99 < 300ms
- **Concurrent Users**: 100+ simultaneous queries

### Design Principles
✅ **Zero Hardcoded Data**: All business logic in vector database
✅ **Semantic Search**: Vector similarity for intelligent rule matching
✅ **Metadata Rich**: Comprehensive metadata for filtering and routing
✅ **Workflow Aware**: Support for comprehensive vs selective validation modes
✅ **User Centric**: User preference learning and personalization
✅ **Platform Optimized**: Platform-specific rule organization

---

## 🏗️ Collection Architecture

### Collection 1: style_editorial_rules
**Purpose**: Content style and editorial validation rules
**Source**: Migrated from hardcoded styleguide arrays across multiple services
**Target Size**: 280+ documents

```python
# Collection Schema
{
    "collection_name": "style_editorial_rules",
    "embedding_model": "all-MiniLM-L6-v2",
    "document_schema": {
        "content": "str",  # Rule description in natural language
        "metadata": {
            # Core Identification
            "rule_id": "str",  # Unique identifier (e.g., "style_001")
            "rule_type": "enum[style|structure|quality|editorial|grammar|tone|engagement]",
            
            # Platform Targeting
            "platform": "enum[universal|linkedin|twitter|substack|beehiiv|ghost|youtube]",
            "platform_specific": "bool",  # True if rule only applies to specific platform
            
            # Validation Workflow
            "workflow": "enum[comprehensive|selective|both]",  # Which validation mode uses this rule
            "priority": "enum[critical|high|medium|low]",  # Rule importance for workflow selection
            "checkpoint": "optional[enum[pre_writing|mid_writing|post_writing]]",  # For selective workflow
            
            # Rule Behavior  
            "rule_action": "enum[forbid|require|suggest|optimize]",  # What the rule does
            "confidence_threshold": "float",  # Minimum similarity score to apply rule (0.0-1.0)
            "auto_fix": "bool",  # Whether rule can be auto-applied
            
            # Content Targeting
            "applies_to": "list[str]",  # Content types this rule targets
            "content_length_range": "optional[tuple[int, int]]",  # Min/max content length
            "audience_type": "optional[enum[professional|casual|technical|general]]",
            
            # Metadata Management
            "created_at": "datetime",
            "updated_at": "datetime", 
            "source": "enum[kolegium_migration|ai_writing_flow_migration|publisher_migration|manual|auto_generated]",
            "migrated_from": "optional[str]",  # Original file path for migrated rules
            "version": "int",  # Rule version for updates
            
            # Learning & Performance
            "usage_count": "int",  # How often rule has been applied
            "success_rate": "float",  # User acceptance rate of this rule
            "last_used": "optional[datetime]",
            
            # Relationships
            "related_rules": "optional[list[str]]",  # Related rule IDs
            "conflicts_with": "optional[list[str]]",  # Conflicting rule IDs
            "supersedes": "optional[list[str]]"  # Rules this one replaces
        }
    },
    
    # Sample Documents
    "sample_documents": [
        {
            "content": "Avoid overusing buzzwords like 'paradigm', 'leverage', 'synergy', 'disrupt' as they reduce content authenticity and engagement",
            "metadata": {
                "rule_id": "style_001_buzzwords",
                "rule_type": "style",
                "platform": "universal",
                "workflow": "both",
                "priority": "high",
                "rule_action": "forbid",
                "confidence_threshold": 0.8,
                "auto_fix": True,
                "applies_to": ["thought_leadership", "industry_update", "tutorial"],
                "audience_type": "professional",
                "created_at": "2025-01-30T10:00:00Z",
                "source": "kolegium_migration",
                "migrated_from": "/kolegium/ai_writing_flow/src/ai_writing_flow/crews/style_crew.py",
                "usage_count": 0,
                "success_rate": 0.0
            }
        },
        {
            "content": "LinkedIn posts should have engaging hooks in the first 2 lines to capture attention in the feed",
            "metadata": {
                "rule_id": "editorial_002_linkedin_hooks",
                "rule_type": "engagement", 
                "platform": "linkedin",
                "platform_specific": True,
                "workflow": "both",
                "priority": "critical",
                "checkpoint": "pre_writing",
                "rule_action": "require",
                "confidence_threshold": 0.7,
                "auto_fix": False,
                "applies_to": ["thought_leadership", "announcement"],
                "content_length_range": [100, 3000],
                "audience_type": "professional",
                "created_at": "2025-01-30T10:00:00Z",
                "source": "manual",
                "usage_count": 0,
                "success_rate": 0.0
            }
        },
        {
            "content": "Use data points and specific metrics instead of vague claims to build credibility",
            "metadata": {
                "rule_id": "quality_003_data_driven",
                "rule_type": "quality",
                "platform": "universal",
                "workflow": "comprehensive",
                "priority": "medium",
                "rule_action": "suggest",
                "confidence_threshold": 0.6,
                "auto_fix": False,
                "applies_to": ["thought_leadership", "industry_update"],
                "audience_type": "professional",
                "created_at": "2025-01-30T10:00:00Z",
                "source": "ai_writing_flow_migration",
                "migrated_from": "/kolegium/ai_writing_flow/src/ai_writing_flow/tools/styleguide_loader.py",
                "usage_count": 0,
                "success_rate": 0.0,
                "related_rules": ["quality_004_metrics", "style_005_credibility"]
            }
        }
    ]
}
```

### Collection 2: publication_platform_rules
**Purpose**: Platform-specific formatting, optimization and constraint rules
**Source**: Extracted from publisher adapters and platform documentation
**Target Size**: 75+ documents

```python
{
    "collection_name": "publication_platform_rules",
    "embedding_model": "all-MiniLM-L6-v2",
    "document_schema": {
        "content": "str",  # Platform rule description
        "metadata": {
            # Core Identification
            "rule_id": "str",
            "platform": "enum[linkedin|twitter|substack|beehiiv|ghost|youtube|facebook|instagram]",
            "rule_category": "enum[formatting|optimization|constraints|scheduling|media|api_limits]",
            
            # Platform Constraints
            "character_limits": "optional[dict]",  # {"min": 10, "max": 3000}
            "media_requirements": "optional[dict]",  # Image/video specs
            "posting_frequency": "optional[dict]",  # Rate limits
            "api_limitations": "optional[dict]",  # API-specific constraints
            
            # Optimization Rules
            "optimal_times": "optional[list[str]]",  # Best posting times
            "engagement_factors": "optional[list[str]]",  # What drives engagement
            "algorithm_preferences": "optional[dict]",  # Platform algorithm insights
            
            # Content Formatting
            "hashtag_rules": "optional[dict]",  # Hashtag usage guidelines
            "mention_rules": "optional[dict]",  # @mention guidelines
            "link_handling": "optional[dict]",  # How links are processed
            "formatting_options": "optional[list[str]]",  # Bold, italic, etc.
            
            # Audience Targeting
            "primary_audience": "optional[str]",  # Platform's primary user base
            "content_types_favored": "optional[list[str]]",  # What works best
            "demographic_insights": "optional[dict]",  # User demographics
            
            # Technical Details
            "api_version": "optional[str]",  # Which API version
            "auth_requirements": "optional[dict]",  # Authentication needs
            "rate_limits": "optional[dict]",  # API rate limiting
            "webhook_support": "optional[bool]",  # Webhook availability
            
            # Metadata
            "created_at": "datetime",
            "updated_at": "datetime",
            "source": "enum[platform_documentation|adapter_migration|manual|api_discovery]",
            "confidence": "float",  # How reliable is this rule
            "last_verified": "datetime"  # When rule was last checked
        }
    },
    
    "sample_documents": [
        {
            "content": "LinkedIn posts perform best when kept under 3000 characters with line breaks every 2-3 sentences for readability",
            "metadata": {
                "rule_id": "linkedin_format_001",
                "platform": "linkedin",
                "rule_category": "formatting",
                "character_limits": {"min": 100, "max": 3000, "optimal": 1500},
                "engagement_factors": ["line_breaks", "readability", "professional_tone"],
                "optimal_times": ["09:00", "12:00", "17:00"],
                "algorithm_preferences": {
                    "favors_engagement": True,
                    "text_length_impact": "medium",
                    "media_boost": "high"
                },
                "hashtag_rules": {
                    "max_hashtags": 5,
                    "placement": "end_of_post",
                    "effectiveness": "medium"
                },
                "primary_audience": "professionals",
                "content_types_favored": ["thought_leadership", "industry_insights", "career_advice"],
                "created_at": "2025-01-30T10:00:00Z",
                "source": "platform_documentation",
                "confidence": 0.9,
                "last_verified": "2025-01-30T10:00:00Z"
            }
        },
        {
            "content": "Twitter threads should use the 4/4 rule: hook in tweet 1, context in tweet 2, insight in tweet 3, call-to-action in tweet 4",
            "metadata": {
                "rule_id": "twitter_thread_001", 
                "platform": "twitter",
                "rule_category": "optimization",
                "character_limits": {"per_tweet": 280, "thread_max_tweets": 25},
                "engagement_factors": ["thread_structure", "hooks", "cta"],
                "optimal_times": ["08:00", "14:00", "19:00"],
                "hashtag_rules": {
                    "max_hashtags": 2,
                    "placement": "within_content",
                    "effectiveness": "high"
                },
                "formatting_options": ["bold_text", "line_breaks", "emojis"],
                "api_limitations": {
                    "max_requests_per_hour": 300,
                    "media_upload_size": "5MB"
                },
                "created_at": "2025-01-30T10:00:00Z",
                "source": "adapter_migration",
                "confidence": 0.85,
                "last_verified": "2025-01-30T10:00:00Z"
            }
        },
        {
            "content": "Substack newsletters should have compelling subject lines under 60 characters and preview text that complements the subject",
            "metadata": {
                "rule_id": "substack_newsletter_001",
                "platform": "substack",
                "rule_category": "optimization",
                "character_limits": {
                    "subject_line": 60,
                    "preview_text": 140,
                    "content_optimal": 1500
                },
                "engagement_factors": ["subject_line", "preview_text", "send_time"],
                "optimal_times": ["09:00", "18:00"],
                "primary_audience": "newsletter_subscribers",
                "content_types_favored": ["long_form", "analysis", "tutorials"],
                "api_limitations": {
                    "rate_limit": "10_requests_per_minute",
                    "batch_send_limit": 1000
                },
                "created_at": "2025-01-30T10:00:00Z",
                "source": "adapter_migration",
                "confidence": 0.8,
                "last_verified": "2025-01-30T10:00:00Z",
                "crewai_metadata": {
                    "crew_execution_id": null,
                    "agents_applied": [],
                    "workflow_type": null,
                    "task_sequence": null,
                    "last_used_by_agent": null
                }
            }
        }
    ]
}
```

### Collection 3: topics
**Purpose**: Topic repository with manual curation and auto-scraped content intelligence
**Source**: Manual user input + automated web scraping from various sources
**Target Size**: 500+ documents

```python
{
    "collection_name": "topics",
    "embedding_model": "all-MiniLM-L6-v2", 
    "document_schema": {
        "content": "str",  # Topic title + description + keywords combined
        "metadata": {
            # Topic Identification
            "topic_id": "str",  # Unique identifier
            "title": "str",  # Human-readable topic title
            "description": "str",  # Detailed topic description
            "keywords": "list[str]",  # Associated keywords and tags
            "aliases": "optional[list[str]]",  # Alternative topic names
            
            # Content Classification
            "content_type": "enum[THOUGHT_LEADERSHIP|INDUSTRY_UPDATE|TUTORIAL|ANNOUNCEMENT|OPINION|CASE_STUDY|RESEARCH|NEWS]",
            "domain": "optional[enum[technology|marketing|business|ai|health|finance|education|entertainment]]",
            "complexity_level": "enum[beginner|intermediate|advanced|expert]",
            "target_audience": "list[str]",  # Who this interests
            
            # Platform Intelligence
            "platform_assignment": "dict",  # {"linkedin": True, "twitter": False, ...}
            "platform_suitability_scores": "dict",  # {"linkedin": 0.9, "twitter": 0.3}
            "optimal_content_length": "dict",  # Per-platform optimal length
            "suggested_format": "dict",  # Per-platform format suggestions
            
            # Engagement Intelligence
            "engagement_prediction": "float",  # Predicted engagement score 0-1
            "trending_score": "optional[float]",  # How trending this topic is
            "seasonality": "optional[dict]",  # When this topic performs best
            "competition_level": "enum[low|medium|high]",  # How saturated
            
            # Topic Lifecycle
            "status": "enum[suggested|selected|in_progress|generated|published|archived]",
            "created_date": "datetime",
            "last_used_date": "optional[datetime]",
            "expiry_date": "optional[datetime]",  # When topic becomes stale
            "usage_count": "int",  # How many times used for content
            
            # Source Attribution
            "source": "enum[manual|auto_scraping_hackernews|auto_scraping_reddit|auto_scraping_twitter|auto_scraping_linkedin|user_submission|ai_generated]",
            "source_url": "optional[str]",  # Original URL if scraped
            "source_metadata": "optional[dict]",  # Additional source info
            "discovery_date": "datetime",
            
            # User Interaction
            "user_rating": "optional[int]",  # 1-5 star user rating
            "user_feedback": "optional[list[str]]",  # User comments
            "selection_count": "int",  # How often users select this topic
            "rejection_count": "int",  # How often users skip this
            "edit_frequency": "int",  # How often content gets edited
            
            # Performance Tracking
            "performance_metrics": "optional[dict]",  # Actual performance data
            "best_performing_platform": "optional[str]",
            "average_engagement": "optional[float]",
            "content_variations": "optional[int]",  # How many versions created
            
            # AI Enhancement
            "ai_enhancement_applied": "bool",
            "ai_suggestions": "optional[list[str]]",  # AI topic improvements
            "related_topics": "optional[list[str]]",  # Related topic IDs
            "topic_clusters": "optional[list[str]]",  # Topic clustering info
            
            # Metadata Management
            "created_by": "optional[str]",  # User ID who created/selected
            "last_updated": "datetime",
            "version": "int"
        }
    },
    
    "sample_documents": [
        {
            "content": "AI Revolution in Marketing Automation: How artificial intelligence is transforming digital marketing strategies, customer segmentation, and personalized content delivery in 2025",
            "metadata": {
                "topic_id": "topic_001_ai_marketing",
                "title": "AI Revolution in Marketing Automation",
                "description": "How artificial intelligence is transforming digital marketing strategies, customer segmentation, and personalized content delivery in 2025",
                "keywords": ["AI", "marketing", "automation", "personalization", "digital marketing", "customer segmentation"],
                "content_type": "THOUGHT_LEADERSHIP",
                "domain": "marketing",
                "complexity_level": "intermediate",
                "target_audience": ["marketing_professionals", "business_owners", "tech_enthusiasts"],
                "platform_assignment": {
                    "linkedin": True,
                    "twitter": True,
                    "substack": True,
                    "beehiiv": False
                },
                "platform_suitability_scores": {
                    "linkedin": 0.95,
                    "twitter": 0.8,
                    "substack": 0.9,
                    "beehiiv": 0.6
                },
                "optimal_content_length": {
                    "linkedin": 1500,
                    "twitter": 280,
                    "substack": 2500
                },
                "engagement_prediction": 0.85,
                "trending_score": 0.9,
                "competition_level": "medium",
                "status": "suggested",
                "created_date": "2025-01-30T10:00:00Z",
                "source": "auto_scraping_hackernews",
                "source_url": "https://news.ycombinator.com/item?id=123456",
                "discovery_date": "2025-01-30T09:30:00Z",
                "selection_count": 0,
                "rejection_count": 0,
                "ai_enhancement_applied": True,
                "ai_suggestions": [
                    "Add specific case studies from 2025",
                    "Include ROI metrics and statistics", 
                    "Mention specific AI tools and platforms"
                ],
                "created_by": "auto_scraper",
                "last_updated": "2025-01-30T10:00:00Z",
                "version": 1
            }
        },
        {
            "content": "Remote Work Productivity Hacks: 15 proven strategies for maintaining focus and efficiency while working from home, including time management, workspace setup, and communication tips",
            "metadata": {
                "topic_id": "topic_002_remote_productivity",
                "title": "Remote Work Productivity Hacks",
                "description": "15 proven strategies for maintaining focus and efficiency while working from home, including time management, workspace setup, and communication tips",
                "keywords": ["remote work", "productivity", "work from home", "time management", "efficiency"],
                "content_type": "TUTORIAL",
                "domain": "business", 
                "complexity_level": "beginner",
                "target_audience": ["remote_workers", "freelancers", "entrepreneurs"],
                "platform_assignment": {
                    "linkedin": True,
                    "twitter": False,
                    "substack": False,
                    "beehiiv": True
                },
                "platform_suitability_scores": {
                    "linkedin": 0.9,
                    "twitter": 0.4,
                    "beehiiv": 0.85
                },
                "engagement_prediction": 0.75,
                "trending_score": 0.6,
                "competition_level": "high",
                "status": "selected",
                "created_date": "2025-01-29T15:00:00Z",
                "last_used_date": "2025-01-30T08:00:00Z",
                "usage_count": 1,
                "source": "manual",
                "user_rating": 4,
                "selection_count": 1,
                "rejection_count": 0,
                "created_by": "user_123",
                "last_updated": "2025-01-30T08:00:00Z",
                "version": 2
            }
        }
    ]
}
```

### Collection 4: scheduling_optimization
**Purpose**: Time slot optimization and scheduling intelligence rules
**Source**: Analytics data, platform research, and user behavior patterns
**Target Size**: 50+ documents

```python
{
    "collection_name": "scheduling_optimization", 
    "embedding_model": "all-MiniLM-L6-v2",
    "document_schema": {
        "content": "str",  # Scheduling rule or insight description
        "metadata": {
            # Rule Identification
            "rule_id": "str",
            "rule_type": "enum[optimal_timing|audience_activity|content_type_timing|platform_algorithm|seasonal_pattern]",
            
            # Platform Targeting
            "platform": "enum[universal|linkedin|twitter|substack|beehiiv|ghost]",
            "applies_globally": "bool",  # True if rule applies to all platforms
            
            # Time Intelligence
            "optimal_hours": "list[int]",  # Hours of day (0-23)
            "optimal_days": "list[str]",  # Days of week
            "time_zone": "str",  # Reference timezone (UTC, EST, PST, etc.)
            "seasonal_factors": "optional[dict]",  # Monthly/seasonal variations
            
            # Audience Insights
            "audience_activity": "dict",  # When audience is most active
            "demographic_targeting": "optional[dict]",  # Age, profession specific timing
            "geographic_considerations": "optional[dict]",  # Geographic timing differences
            
            # Content Type Correlation
            "content_type_affinity": "dict",  # Which content types work when
            "content_length_impact": "optional[dict]",  # How length affects timing
            "engagement_multiplier": "float",  # Expected engagement boost
            
            # Algorithm Intelligence
            "algorithm_factors": "optional[dict]",  # Platform algorithm preferences
            "competition_analysis": "optional[dict]",  # When competition posts
            "trending_windows": "optional[dict]",  # When content can trend
            
            # Performance Data
            "confidence_score": "float",  # How confident we are in this rule
            "data_sample_size": "optional[int]",  # How much data this is based on
            "last_validated": "datetime",  # When rule was last checked
            "performance_impact": "dict",  # Measured impact on engagement
            
            # Contextual Factors
            "industry_specific": "optional[list[str]]",  # Which industries this applies to
            "event_considerations": "optional[dict]",  # Impact of events, holidays
            "news_cycle_impact": "optional[dict]",  # How news affects timing
            
            # Learning Data
            "user_override_frequency": "float",  # How often users ignore this
            "success_rate": "float",  # How often following this rule helps
            "adaptation_rate": "float",  # How fast this rule changes
            
            # Metadata
            "created_at": "datetime",
            "updated_at": "datetime",
            "source": "enum[analytics_data|platform_research|user_behavior|ai_analysis|manual]",
            "reliability": "enum[high|medium|low]"
        }
    },
    
    "sample_documents": [
        {
            "content": "LinkedIn posts perform 2.3x better when published Tuesday-Thursday between 9-11 AM EST, targeting professional audience during work hours",
            "metadata": {
                "rule_id": "linkedin_optimal_001",
                "rule_type": "optimal_timing",
                "platform": "linkedin",
                "applies_globally": False,
                "optimal_hours": [9, 10, 11],
                "optimal_days": ["tuesday", "wednesday", "thursday"],
                "time_zone": "EST",
                "audience_activity": {
                    "peak_hours": [9, 12, 17],
                    "active_days": ["monday", "tuesday", "wednesday", "thursday"],
                    "weekend_activity": 0.3
                },
                "demographic_targeting": {
                    "professionals": {"peak": [9, 12]},
                    "executives": {"peak": [7, 17]},
                    "entrepreneurs": {"peak": [6, 22]}
                },
                "content_type_affinity": {
                    "thought_leadership": 1.4,
                    "industry_update": 1.2,
                    "tutorial": 0.9
                },
                "engagement_multiplier": 2.3,
                "algorithm_factors": {
                    "recency_boost": "6_hours",
                    "engagement_window": "24_hours"
                },
                "confidence_score": 0.85,
                "data_sample_size": 10000,
                "last_validated": "2025-01-30T10:00:00Z",
                "performance_impact": {
                    "likes_increase": 1.8,
                    "comments_increase": 2.1,
                    "shares_increase": 2.6
                },
                "industry_specific": ["technology", "business", "marketing"],
                "user_override_frequency": 0.15,
                "success_rate": 0.87,
                "created_at": "2025-01-30T10:00:00Z",
                "source": "analytics_data",
                "reliability": "high"
            }
        },
        {
            "content": "Twitter threads see maximum engagement when first tweet is posted during commute hours (7-9 AM, 5-7 PM) across all time zones",
            "metadata": {
                "rule_id": "twitter_thread_timing_001",
                "rule_type": "optimal_timing",
                "platform": "twitter", 
                "applies_globally": True,
                "optimal_hours": [7, 8, 17, 18],
                "optimal_days": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "time_zone": "user_local",
                "audience_activity": {
                    "commute_hours": [7, 8, 17, 18, 19],
                    "lunch_hours": [12, 13],
                    "evening_hours": [20, 21, 22]
                },
                "content_type_affinity": {
                    "thread": 2.1,
                    "single_tweet": 1.0,
                    "media_tweet": 1.3
                },
                "engagement_multiplier": 1.9,
                "trending_windows": {
                    "minimum_engagement_period": "30_minutes",
                    "trend_potential_hours": [7, 12, 17, 20]
                },
                "confidence_score": 0.8,
                "data_sample_size": 50000,
                "last_validated": "2025-01-30T10:00:00Z",
                "performance_impact": {
                    "retweets_increase": 2.1,
                    "replies_increase": 1.7,
                    "likes_increase": 1.5
                },
                "user_override_frequency": 0.25,
                "success_rate": 0.78,
                "created_at": "2025-01-30T10:00:00Z",
                "source": "platform_research",
                "reliability": "medium"
            }
        }
    ]
}
```

### Collection 5: user_preferences  
**Purpose**: User behavior learning and preference tracking for personalization
**Source**: User interaction data, selection patterns, and performance feedback
**Target Size**: 100+ documents (grows with user base)

```python
{
    "collection_name": "user_preferences",
    "embedding_model": "all-MiniLM-L6-v2",
    "document_schema": {
        "content": "str",  # User preference description in natural language
        "metadata": {
            # User Identification
            "preference_id": "str",  # Unique preference identifier
            "user_id": "str",  # User identifier (anonymized)
            "user_segment": "optional[str]",  # User category/segment
            
            # Preference Type
            "preference_type": "enum[style|platform|timing|topic|content_type|workflow|editing]",
            "preference_category": "enum[explicit|implicit|derived|learned]",  # How preference was determined
            
            # Preference Data
            "preference_value": "dict",  # The actual preference data
            "preference_strength": "float",  # How strong this preference is (0-1)
            "preference_stability": "float",  # How consistent this preference is
            
            # Learning Source
            "learned_from": "enum[topic_selections|content_edits|platform_choices|timing_preferences|style_feedback|rejection_patterns]",
            "learning_confidence": "float",  # How confident the learning is
            "sample_size": "int",  # How many data points support this
            
            # Temporal Aspects
            "created_at": "datetime",
            "last_updated": "datetime",
            "last_reinforced": "datetime",  # When preference was last confirmed
            "usage_frequency": "float",  # How often this preference is relevant
            
            # Preference Decay
            "decay_factor": "float",  # How fast this preference becomes stale
            "half_life_days": "int",  # Days until preference loses half strength
            "refresh_needed": "bool",  # Whether preference needs validation
            
            # Context Data
            "context": "dict",  # When/where this preference applies
            "conditions": "optional[list[str]]",  # Conditions for preference activation
            "exceptions": "optional[list[str]]",  # When this preference doesn't apply
            
            # Performance Data
            "success_rate": "float",  # How often acting on this preference succeeds
            "user_satisfaction": "optional[float]",  # User satisfaction when followed
            "business_impact": "optional[dict]",  # Impact on engagement/performance
            
            # Relationship Data
            "conflicts_with": "optional[list[str]]",  # Conflicting preference IDs
            "reinforces": "optional[list[str]]",  # Supporting preference IDs
            "derived_from": "optional[list[str]]",  # Parent preference IDs
            
            # Privacy & Compliance
            "anonymized": "bool",
            "consent_level": "enum[full|limited|minimal]",
            "retention_period": "int",  # Days to retain this preference
            "can_be_shared": "bool"  # Whether preference can inform global patterns
        }
    },
    
    "sample_documents": [
        {
            "content": "User prefers LinkedIn posts with data-driven content and professional tone, avoiding casual language and personal anecdotes",
            "metadata": {
                "preference_id": "pref_001_user_123_style",
                "user_id": "user_123_anon",
                "user_segment": "technology_professional",
                "preference_type": "style",
                "preference_category": "learned",
                "preference_value": {
                    "preferred_tone": "professional",
                    "data_driven": True,
                    "personal_anecdotes": False,
                    "casual_language": False,
                    "technical_depth": "high",
                    "preferred_length": "medium_long"
                },
                "preference_strength": 0.85,
                "preference_stability": 0.9,
                "learned_from": "content_edits",
                "learning_confidence": 0.8,
                "sample_size": 15,
                "created_at": "2025-01-25T10:00:00Z",
                "last_updated": "2025-01-30T10:00:00Z",
                "last_reinforced": "2025-01-30T08:00:00Z",
                "usage_frequency": 0.7,
                "decay_factor": 0.95,
                "half_life_days": 90,
                "refresh_needed": False,
                "context": {
                    "platforms": ["linkedin"],
                    "content_types": ["thought_leadership", "industry_update"],
                    "audience": "professional"
                },
                "success_rate": 0.87,
                "user_satisfaction": 4.2,
                "business_impact": {
                    "engagement_increase": 1.3,
                    "edit_reduction": 0.6
                },
                "anonymized": True,
                "consent_level": "full",
                "retention_period": 365,
                "can_be_shared": True
            }
        },
        {
            "content": "User consistently selects AI and technology topics, avoids marketing and business topics, prefers tutorial and case study content types",
            "metadata": {
                "preference_id": "pref_002_user_123_topics",
                "user_id": "user_123_anon",
                "user_segment": "technology_professional",
                "preference_type": "topic",
                "preference_category": "implicit",
                "preference_value": {
                    "preferred_domains": ["technology", "ai", "programming"],
                    "avoided_domains": ["marketing", "business_general"],
                    "preferred_content_types": ["tutorial", "case_study", "technical_analysis"],
                    "complexity_preference": "intermediate_to_advanced",
                    "trending_vs_evergreen": "evergreen_preferred"
                },
                "preference_strength": 0.9,
                "preference_stability": 0.85,
                "learned_from": "topic_selections",
                "learning_confidence": 0.92,
                "sample_size": 25,
                "created_at": "2025-01-20T10:00:00Z",
                "last_updated": "2025-01-30T10:00:00Z",
                "last_reinforced": "2025-01-30T09:00:00Z",
                "usage_frequency": 0.9,
                "decay_factor": 0.98,
                "half_life_days": 120,
                "refresh_needed": False,
                "context": {
                    "all_platforms": True,
                    "time_periods": "consistent"
                },
                "success_rate": 0.95,
                "user_satisfaction": 4.5,
                "business_impact": {
                    "selection_rate": 0.9,
                    "completion_rate": 0.95
                },
                "anonymized": True,
                "consent_level": "full",  
                "retention_period": 365,
                "can_be_shared": True
            }
        },
        {
            "content": "User prefers publishing content Tuesday-Thursday mornings, avoids weekend posting, consistently overrides AI suggestions for Friday scheduling",
            "metadata": {
                "preference_id": "pref_003_user_123_timing", 
                "user_id": "user_123_anon",
                "user_segment": "technology_professional",
                "preference_type": "timing",
                "preference_category": "explicit",
                "preference_value": {
                    "preferred_days": ["tuesday", "wednesday", "thursday"],
                    "preferred_hours": [9, 10, 11],
                    "avoided_days": ["saturday", "sunday"],
                    "avoided_hours": [22, 23, 0, 1, 2, 3, 4, 5, 6],
                    "timezone": "EST",
                    "flexibility": "low"
                },
                "preference_strength": 0.95,
                "preference_stability": 0.95,
                "learned_from": "timing_preferences", 
                "learning_confidence": 0.98,
                "sample_size": 30,
                "created_at": "2025-01-15T10:00:00Z",
                "last_updated": "2025-01-30T10:00:00Z",
                "last_reinforced": "2025-01-30T07:00:00Z",
                "usage_frequency": 1.0,
                "decay_factor": 1.0,
                "half_life_days": 365,
                "refresh_needed": False,
                "context": {
                    "all_platforms": True,
                    "work_schedule_aligned": True
                },
                "conditions": ["workday_schedule", "professional_content"],
                "exceptions": ["urgent_announcements", "breaking_news"],
                "success_rate": 0.93,
                "user_satisfaction": 4.8,
                "business_impact": {
                    "scheduling_accuracy": 0.97,
                    "user_override_rate": 0.05
                },
                "anonymized": True,
                "consent_level": "full",
                "retention_period": 365,
                "can_be_shared": False
            }
        }
    ]
}
```

---

## 🔍 Query Patterns & Optimization

### Query Strategy by Workflow

#### Comprehensive Validation Queries (Kolegium)
```python
class ComprehensiveQueryPatterns:
    """Query patterns for full AI validation workflow"""
    
    def get_style_rules(self, content: str, platform: str):
        """Get comprehensive style rules"""
        return {
            "collection": "style_editorial_rules",
            "query_texts": [content],
            "n_results": 8,
            "where": {
                "$and": [
                    {"workflow": {"$in": ["comprehensive", "both"]}},
                    {"platform": {"$in": [platform, "universal"]}},
                    {"priority": {"$in": ["critical", "high", "medium"]}}
                ]
            },
            "where_document": {
                "$or": [
                    {"$contains": "style"},
                    {"$contains": "quality"},
                    {"$contains": "engagement"}
                ]
            }
        }
    
    def get_platform_optimization_rules(self, content: str, platform: str):
        """Get platform-specific optimization rules"""
        return {
            "collection": "publication_platform_rules",
            "query_texts": [f"optimize content for {platform}"],
            "n_results": 4,
            "where": {
                "platform": platform,
                "rule_category": {"$in": ["optimization", "formatting"]}
            }
        }
    
    def get_editorial_structure_rules(self, content: str, content_type: str):
        """Get editorial structure validation rules"""
        return {
            "collection": "style_editorial_rules",
            "query_texts": [f"editorial structure {content_type}"],
            "n_results": 6,
            "where": {
                "rule_type": {"$in": ["structure", "editorial"]},
                "applies_to": {"$contains": content_type.lower()}
            }
        }
```

#### Selective Validation Queries (AI Writing Flow)
```python
class SelectiveQueryPatterns:
    """Query patterns for human-assisted workflow checkpoints"""
    
    def get_checkpoint_rules(self, content: str, platform: str, checkpoint: str):
        """Get rules for specific checkpoint"""
        
        checkpoint_focus = {
            "pre_writing": ["structure", "audience", "platform_format"],
            "mid_writing": ["style", "flow", "engagement"],
            "post_writing": ["quality", "optimization", "final_polish"]
        }
        
        focus_areas = checkpoint_focus.get(checkpoint, ["general"])
        
        return {
            "collection": "style_editorial_rules",
            "query_texts": [content],
            "n_results": 4,
            "where": {
                "$and": [
                    {"workflow": {"$in": ["selective", "both"]}},
                    {"priority": {"$in": ["critical", "high"]}},
                    {
                        "$or": [
                            {"checkpoint": checkpoint},
                            {"rule_type": {"$in": focus_areas}}
                        ]
                    }
                ]
            }
        }
    
    def get_critical_platform_rules(self, platform: str):
        """Get only critical platform-specific rules"""
        return {
            "collection": "publication_platform_rules", 
            "query_texts": [f"critical requirements {platform}"],
            "n_results": 2,
            "where": {
                "platform": platform,
                "rule_category": {"$in": ["constraints", "critical_formatting"]}
            }
        }
```

#### Topic Intelligence Queries
```python
class TopicQueryPatterns:
    """Query patterns for topic discovery and suggestions"""
    
    def get_topic_suggestions(self, user_preferences: dict = None, limit: int = 10):
        """Get personalized topic suggestions"""
        
        base_query = {
            "collection": "topics",
            "query_texts": ["trending technology innovation"],
            "n_results": limit * 2,  # Get more for filtering
            "where": {
                "$and": [
                    {"status": {"$in": ["suggested", "archived"]}},
                    {"engagement_prediction": {"$gt": 0.6}}
                ]
            }
        }
        
        # Add user preference filtering
        if user_preferences:
            if "preferred_domains" in user_preferences:
                base_query["where"]["$and"].append({
                    "domain": {"$in": user_preferences["preferred_domains"]}
                })
                
            if "avoided_domains" in user_preferences:
                base_query["where"]["$and"].append({
                    "domain": {"$not": {"$in": user_preferences["avoided_domains"]}}
                })
        
        return base_query
    
    def get_trending_topics(self, platform: str = None, timeframe: str = "week"):
        """Get currently trending topics"""
        
        query = {
            "collection": "topics",
            "query_texts": ["trending viral popular"],
            "n_results": 20,
            "where": {
                "$and": [
                    {"trending_score": {"$gt": 0.7}},
                    {"created_date": {"$gt": self._get_timeframe_date(timeframe)}}
                ]
            }
        }
        
        if platform:
            query["where"]["$and"].append({
                f"platform_assignment.{platform}": True
            })
        
        return query
    
    def search_topics_by_keywords(self, keywords: list, content_type: str = None):
        """Search topics by specific keywords"""
        
        search_text = " ".join(keywords)
        
        query = {
            "collection": "topics",
            "query_texts": [search_text],
            "n_results": 15,
            "where": {
                "keywords": {"$contains_any": keywords}
            }
        }
        
        if content_type:
            query["where"]["content_type"] = content_type
        
        return query
```

#### User Preference Queries
```python
class UserPreferenceQueryPatterns:
    """Query patterns for user preference learning"""
    
    def get_user_style_preferences(self, user_id: str):
        """Get user's style preferences"""
        return {
            "collection": "user_preferences",
            "query_texts": [f"user style preferences writing tone"],
            "n_results": 5,
            "where": {
                "$and": [
                    {"user_id": user_id},
                    {"preference_type": "style"},
                    {"preference_strength": {"$gt": 0.7}}
                ]
            }
        }
    
    def get_user_topic_preferences(self, user_id: str):
        """Get user's topic preferences"""
        return {
            "collection": "user_preferences",
            "query_texts": [f"user topic interests domains"],
            "n_results": 10,
            "where": {
                "$and": [
                    {"user_id": user_id},
                    {"preference_type": {"$in": ["topic", "content_type"]}},
                    {"last_reinforced": {"$gt": self._get_recent_date()}}
                ]
            }
        }
    
    def get_user_scheduling_preferences(self, user_id: str):
        """Get user's scheduling and timing preferences"""
        return {
            "collection": "user_preferences", 
            "query_texts": [f"user timing schedule posting preferences"],
            "n_results": 3,
            "where": {
                "$and": [
                    {"user_id": user_id},
                    {"preference_type": "timing"},
                    {"preference_stability": {"$gt": 0.8}}
                ]
            }
        }
```

### Indexing & Performance Optimization

#### Collection Indexing Strategy
```python
# ChromaDB Index Optimization Configuration
indexing_config = {
    "style_editorial_rules": {
        "primary_indexes": [
            "metadata.platform",
            "metadata.workflow", 
            "metadata.priority",
            "metadata.rule_type"
        ],
        "composite_indexes": [
            ["metadata.platform", "metadata.workflow"],
            ["metadata.priority", "metadata.rule_type"],
            ["metadata.workflow", "metadata.checkpoint"]
        ],
        "text_search_optimization": {
            "boost_fields": ["content", "metadata.applies_to"],
            "minimum_similarity": 0.5
        }
    },
    
    "publication_platform_rules": {
        "primary_indexes": [
            "metadata.platform",
            "metadata.rule_category"
        ],
        "composite_indexes": [
            ["metadata.platform", "metadata.rule_category"]
        ],
        "performance_tuning": {
            "cache_frequent_queries": True,
            "precompute_platform_rules": True
        }
    },
    
    "topics": {
        "primary_indexes": [
            "metadata.status",
            "metadata.domain",
            "metadata.content_type",
            "metadata.source"
        ],
        "composite_indexes": [
            ["metadata.status", "metadata.engagement_prediction"],
            ["metadata.domain", "metadata.content_type"],
            ["metadata.trending_score", "metadata.created_date"]
        ],
        "search_optimization": {
            "keyword_boosting": True,
            "trending_score_weight": 2.0,
            "engagement_prediction_weight": 1.5
        }
    },
    
    "scheduling_optimization": {
        "primary_indexes": [
            "metadata.platform",
            "metadata.rule_type"
        ],
        "time_based_optimization": {
            "timezone_aware_queries": True,
            "cache_optimal_times": True
        }
    },
    
    "user_preferences": {
        "primary_indexes": [
            "metadata.user_id",
            "metadata.preference_type",
            "metadata.preference_strength"
        ],
        "privacy_indexes": [
            "metadata.anonymized",
            "metadata.consent_level"
        ],
        "performance_optimization": {
            "user_data_caching": True,
            "preference_aggregation": True
        }
    }
}
```

#### Query Performance Monitoring
```python
class ChromaDBPerformanceMonitor:
    """Monitor and optimize ChromaDB query performance"""
    
    def __init__(self):
        self.performance_targets = {
            "p50_latency_ms": 50,
            "p95_latency_ms": 100, 
            "p99_latency_ms": 300,
            "error_rate": 0.01,
            "cache_hit_rate": 0.8
        }
        
        self.query_patterns = {
            "comprehensive_validation": {
                "expected_frequency": 0.3,  # 30% of queries
                "target_latency_ms": 80,
                "complexity": "high"
            },
            "selective_validation": {
                "expected_frequency": 0.4,  # 40% of queries
                "target_latency_ms": 60,
                "complexity": "medium"
            },
            "topic_suggestions": {
                "expected_frequency": 0.2,  # 20% of queries
                "target_latency_ms": 100,
                "complexity": "medium"
            },
            "user_preferences": {
                "expected_frequency": 0.1,  # 10% of queries
                "target_latency_ms": 40,
                "complexity": "low"
            }
        }
    
    async def monitor_query_performance(self, query_type: str, execution_time_ms: float):
        """Monitor individual query performance"""
        
        target = self.query_patterns.get(query_type, {}).get("target_latency_ms", 100)
        
        if execution_time_ms > target * 1.5:
            await self._trigger_performance_alert(query_type, execution_time_ms, target)
        
        # Store metrics for analysis
        await self._record_performance_metric(query_type, execution_time_ms)
    
    async def optimize_slow_queries(self):
        """Identify and optimize slow query patterns"""
        
        slow_queries = await self._identify_slow_queries()
        
        for query in slow_queries:
            optimization_suggestions = await self._generate_optimization_suggestions(query)
            await self._apply_optimizations(query, optimization_suggestions)
    
    async def _generate_optimization_suggestions(self, slow_query: dict) -> list:
        """Generate optimization suggestions for slow queries"""
        
        suggestions = []
        
        # Index optimization
        if slow_query.get("filter_usage", 0) > 0.5:
            suggestions.append({
                "type": "add_index",
                "fields": slow_query["most_filtered_fields"],
                "expected_improvement": "50-70% latency reduction"
            })
        
        # Query restructuring
        if slow_query.get("result_count", 0) > 50:
            suggestions.append({
                "type": "reduce_result_count",
                "recommendation": "Use more specific filters",
                "expected_improvement": "20-30% latency reduction"
            })
        
        # Caching opportunities
        if slow_query.get("frequency", 0) > 0.1:
            suggestions.append({
                "type": "add_caching", 
                "strategy": "query_result_cache",
                "expected_improvement": "80-90% latency reduction for repeated queries"
            })
        
        return suggestions
```

---

## 🔧 Migration Scripts

### ChromaDB Collection Setup
```python
#!/usr/bin/env python3
# scripts/setup_chromadb_collections.py

import chromadb
from chromadb.config import Settings
import json
from datetime import datetime
import logging

class ChromaDBSetup:
    def __init__(self, host: str = "localhost", port: int = 8000):
        self.client = chromadb.HttpClient(
            host=host,
            port=port,
            settings=Settings(allow_reset=False)
        )
        
        self.collections_config = {
            "style_editorial_rules": {
                "metadata": {"description": "Content style and editorial validation rules"},
                "expected_count": 280
            },
            "publication_platform_rules": {
                "metadata": {"description": "Platform-specific formatting and optimization rules"},
                "expected_count": 75
            },
            "topics": {
                "metadata": {"description": "Topic repository with manual and auto-scraped content"},
                "expected_count": 500
            },
            "scheduling_optimization": {
                "metadata": {"description": "Time slot optimization and scheduling intelligence"},
                "expected_count": 50
            },
            "user_preferences": {
                "metadata": {"description": "User behavior learning and preference tracking"},
                "expected_count": 100
            }
        }
    
    async def setup_all_collections(self):
        """Setup all ChromaDB collections with proper configuration"""
        
        logging.info("Starting ChromaDB collection setup...")
        
        created_collections = []
        
        for collection_name, config in self.collections_config.items():
            try:
                # Check if collection already exists
                try:
                    existing_collection = self.client.get_collection(collection_name)
                    logging.info(f"Collection {collection_name} already exists with {existing_collection.count()} documents")
                    created_collections.append(collection_name)
                    continue
                except Exception:
                    # Collection doesn't exist, create it
                    pass
                
                # Create collection
                collection = self.client.create_collection(
                    name=collection_name,
                    metadata=config["metadata"]
                )
                
                logging.info(f"✅ Created collection: {collection_name}")
                created_collections.append(collection_name)
                
                # Add sample documents for testing
                await self._add_sample_documents(collection, collection_name)
                
            except Exception as e:
                logging.error(f"❌ Failed to create collection {collection_name}: {e}")
                raise
        
        # Verify all collections
        await self._verify_collections(created_collections)
        
        logging.info(f"🎉 Successfully setup {len(created_collections)} collections")
        return created_collections
    
    async def _add_sample_documents(self, collection, collection_name: str):
        """Add sample documents to collection for testing"""
        
        sample_docs = self._get_sample_documents(collection_name)
        
        if sample_docs:
            collection.add(
                documents=[doc["content"] for doc in sample_docs],
                metadatas=[doc["metadata"] for doc in sample_docs],
                ids=[doc["metadata"]["rule_id"] for doc in sample_docs]
            )
            
            logging.info(f"Added {len(sample_docs)} sample documents to {collection_name}")
    
    def _get_sample_documents(self, collection_name: str) -> list:
        """Get sample documents for each collection type"""
        
        samples = {
            "style_editorial_rules": [
                {
                    "content": "Avoid overusing buzzwords like 'paradigm', 'leverage', 'synergy' as they reduce content authenticity",
                    "metadata": {
                        "rule_id": "sample_style_001",
                        "rule_type": "style",
                        "platform": "universal",
                        "workflow": "both",
                        "priority": "high",
                        "created_at": datetime.now().isoformat(),
                        "source": "setup_sample"
                    }
                },
                {
                    "content": "LinkedIn posts should have engaging hooks in the first 2 lines to capture attention",
                    "metadata": {
                        "rule_id": "sample_editorial_001",
                        "rule_type": "engagement",
                        "platform": "linkedin",
                        "workflow": "both", 
                        "priority": "critical",
                        "created_at": datetime.now().isoformat(),
                        "source": "setup_sample"
                    }
                }
            ],
            
            "publication_platform_rules": [
                {
                    "content": "LinkedIn posts perform best when kept under 3000 characters with line breaks for readability",
                    "metadata": {
                        "rule_id": "sample_linkedin_001",
                        "platform": "linkedin",
                        "rule_category": "formatting",
                        "character_limits": {"max": 3000, "optimal": 1500},
                        "created_at": datetime.now().isoformat(),
                        "source": "setup_sample"
                    }
                }
            ],
            
            "topics": [
                {
                    "content": "AI Revolution in Marketing: How artificial intelligence is transforming digital marketing strategies and customer personalization",
                    "metadata": {
                        "topic_id": "sample_topic_001",
                        "title": "AI Revolution in Marketing", 
                        "description": "How AI transforms digital marketing strategies",
                        "keywords": ["AI", "marketing", "personalization"],
                        "content_type": "THOUGHT_LEADERSHIP",
                        "domain": "marketing",
                        "status": "suggested",
                        "engagement_prediction": 0.85,
                        "created_date": datetime.now().isoformat(),
                        "source": "setup_sample"
                    }
                }
            ],
            
            "scheduling_optimization": [
                {
                    "content": "LinkedIn posts perform 2.3x better when published Tuesday-Thursday between 9-11 AM EST",
                    "metadata": {
                        "rule_id": "sample_schedule_001",
                        "rule_type": "optimal_timing",
                        "platform": "linkedin",
                        "optimal_hours": [9, 10, 11],
                        "optimal_days": ["tuesday", "wednesday", "thursday"],
                        "engagement_multiplier": 2.3,
                        "confidence_score": 0.85,
                        "created_at": datetime.now().isoformat(),
                        "source": "setup_sample"
                    }
                }
            ],
            
            "user_preferences": [
                {
                    "content": "User prefers professional tone with data-driven content, avoiding casual language",
                    "metadata": {
                        "preference_id": "sample_pref_001",
                        "user_id": "sample_user_001",
                        "preference_type": "style",
                        "preference_value": {
                            "tone": "professional",
                            "data_driven": True,
                            "casual_language": False
                        },
                        "preference_strength": 0.85,
                        "created_at": datetime.now().isoformat(),
                        "source": "setup_sample"
                    }
                }
            ]
        }
        
        return samples.get(collection_name, [])
    
    async def _verify_collections(self, collection_names: list):
        """Verify collections were created successfully"""
        
        all_collections = self.client.list_collections()
        collection_names_list = [col.name for col in all_collections]
        
        for name in collection_names:
            if name in collection_names_list:
                collection = self.client.get_collection(name)
                count = collection.count()
                logging.info(f"✅ Verified {name}: {count} documents")
            else:
                logging.error(f"❌ Collection {name} not found after creation")
                raise Exception(f"Collection verification failed: {name}")

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        setup = ChromaDBSetup()
        collections = await setup.setup_all_collections()
        
        print("\n🎉 ChromaDB setup completed!")
        print(f"Created collections: {', '.join(collections)}")
        print("\nNext steps:")
        print("1. Run migration scripts to populate with real data")
        print("2. Test query performance")  
        print("3. Setup Editorial Service integration")

    asyncio.run(main())
```

### Rule Migration Script
```python
#!/usr/bin/env python3
# scripts/migrate_hardcoded_rules.py

import os
import re
import ast
import json
import chromadb
from datetime import datetime
import logging
from pathlib import Path

class HardcodedRuleMigrator:
    def __init__(self, chromadb_client):
        self.client = chromadb_client
        self.collections = {}
        self.migration_stats = {
            "total_files_processed": 0,
            "total_rules_extracted": 0,
            "successful_migrations": 0,
            "failed_migrations": 0,
            "skipped_duplicates": 0
        }
        
        # Load collections
        self.collections["style"] = client.get_collection("style_editorial_rules")
        self.collections["platform"] = client.get_collection("publication_platform_rules")
        
    async def migrate_all_hardcoded_rules(self):
        """Migrate all hardcoded rules from various sources"""
        
        migration_sources = [
            {
                "name": "kolegium_style_crew",
                "path": "/kolegium/ai_writing_flow/src/ai_writing_flow/crews/style_crew.py",
                "target_collection": "style",
                "rule_types": ["forbidden_phrases", "required_elements", "style_patterns"]
            },
            {
                "name": "ai_writing_flow_styleguide",
                "path": "/kolegium/ai_writing_flow/src/ai_writing_flow/tools/styleguide_loader.py",
                "target_collection": "style", 
                "rule_types": ["validation_rules", "replacements", "quality_checks"]
            },
            {
                "name": "publisher_platform_adapters",
                "path": "/publisher/src/adapters/",
                "target_collection": "platform",
                "rule_types": ["character_limits", "media_specs", "api_constraints"],
                "recursive": True
            }
        ]
        
        total_migrated = 0
        
        for source in migration_sources:
            try:
                migrated_count = await self._migrate_source(source)
                total_migrated += migrated_count
                logging.info(f"✅ Migrated {migrated_count} rules from {source['name']}")
                
            except Exception as e:
                logging.error(f"❌ Failed to migrate {source['name']}: {e}")
                self.migration_stats["failed_migrations"] += 1
        
        # Generate migration report
        await self._generate_migration_report()
        
        return total_migrated
    
    async def _migrate_source(self, source_config: dict) -> int:
        """Migrate rules from a specific source"""
        
        path = Path(source_config["path"])
        rules_extracted = []
        
        if source_config.get("recursive", False):
            # Process directory recursively
            for file_path in path.rglob("*.py"):
                file_rules = await self._extract_rules_from_file(file_path, source_config)
                rules_extracted.extend(file_rules)
        else:
            # Process single file
            if path.exists():
                file_rules = await self._extract_rules_from_file(path, source_config)
                rules_extracted.extend(file_rules)
            else:
                logging.warning(f"Source file not found: {path}")
        
        # Migrate rules to ChromaDB
        if rules_extracted:
            migrated_count = await self._store_rules_in_chromadb(
                rules_extracted,
                source_config["target_collection"],
                source_config["name"]
            )
            return migrated_count
        
        return 0
    
    async def _extract_rules_from_file(self, file_path: Path, source_config: dict) -> list:
        """Extract hardcoded rules from a Python file"""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logging.error(f"Failed to read file {file_path}: {e}")
            return []
        
        rules = []
        self.migration_stats["total_files_processed"] += 1
        
        # Extract different types of hardcoded rules
        for rule_type in source_config["rule_types"]:
            type_rules = await self._extract_rule_type(content, rule_type, file_path, source_config)
            rules.extend(type_rules)
        
        return rules
    
    async def _extract_rule_type(self, content: str, rule_type: str, file_path: Path, source_config: dict) -> list:
        """Extract specific type of hardcoded rules"""
        
        rules = []
        
        if rule_type == "forbidden_phrases":
            # Extract forbidden_phrases arrays
            patterns = re.findall(
                r'forbidden_phrases\s*=\s*\[(.*?)\]',
                content,
                re.DOTALL
            )
            
            for pattern in patterns:
                phrases = re.findall(r'["\']([^"\']+)["\']', pattern)
                for phrase in phrases:
                    rules.append({
                        "content": f"Avoid using the phrase: '{phrase}' as it reduces content authenticity and engagement",
                        "metadata": {
                            "rule_id": f"{source_config['name']}_forbidden_{len(rules):03d}",
                            "rule_type": "style",
                            "platform": "universal",
                            "workflow": "both",
                            "priority": "medium",
                            "rule_action": "forbid",
                            "confidence_threshold": 0.8,
                            "auto_fix": True,
                            "applies_to": ["thought_leadership", "industry_update"],
                            "created_at": datetime.now().isoformat(),
                            "source": f"{source_config['name']}_migration",
                            "migrated_from": str(file_path),
                            "original_pattern": phrase,
                            "usage_count": 0,
                            "success_rate": 0.0
                        }
                    })
        
        elif rule_type == "required_elements":
            # Extract required_elements dictionaries
            patterns = re.findall(
                r'required_elements\s*=\s*\{(.*?)\}',
                content,
                re.DOTALL
            )
            
            for pattern in patterns:
                try:
                    # Parse dictionary-like structure
                    elements_dict = ast.literal_eval(f'{{{pattern}}}')
                    
                    for element_name, element_rule in elements_dict.items():
                        rules.append({
                            "content": f"Content should include {element_name}: {element_rule}",
                            "metadata": {
                                "rule_id": f"{source_config['name']}_required_{element_name}_{len(rules):03d}",
                                "rule_type": "structure",
                                "platform": "universal",
                                "workflow": "comprehensive",
                                "priority": "high",
                                "rule_action": "require",
                                "confidence_threshold": 0.7,
                                "auto_fix": False,
                                "created_at": datetime.now().isoformat(),
                                "source": f"{source_config['name']}_migration",
                                "migrated_from": str(file_path),
                                "original_element": element_name,
                                "original_rule": str(element_rule),
                                "usage_count": 0,
                                "success_rate": 0.0
                            }
                        })
                except Exception as e:
                    logging.warning(f"Failed to parse required_elements in {file_path}: {e}")
        
        elif rule_type == "character_limits":
            # Extract character limit rules from platform adapters
            patterns = re.findall(
                r'(?:max_length|character_limit|char_limit)\s*[=:]\s*(\d+)',
                content,
                re.IGNORECASE
            )
            
            platform = self._detect_platform_from_path(file_path)
            
            for limit in patterns:
                rules.append({
                    "content": f"{platform.title()} posts should not exceed {limit} characters for optimal performance",
                    "metadata": {
                        "rule_id": f"{source_config['name']}_{platform}_charlimit_{limit}",
                        "platform": platform,
                        "rule_category": "constraints",
                        "character_limits": {"max": int(limit)},
                        "created_at": datetime.now().isoformat(),
                        "source": f"{source_config['name']}_migration",
                        "migrated_from": str(file_path),
                        "confidence": 0.9
                    }
                })
        
        self.migration_stats["total_rules_extracted"] += len(rules)
        return rules
    
    async def _store_rules_in_chromadb(self, rules: list, collection_name: str, source_name: str) -> int:
        """Store extracted rules in ChromaDB collection"""
        
        if collection_name not in self.collections:
            logging.error(f"Collection {collection_name} not found")
            return 0
        
        collection = self.collections[collection_name]
        
        # Check for duplicates
        existing_ids = set()
        try:
            # Get existing rule IDs to avoid duplicates
            existing_data = collection.get()
            existing_ids = set(existing_data["ids"]) if existing_data["ids"] else set()
        except Exception as e:
            logging.warning(f"Could not check existing rules: {e}")
        
        # Filter out duplicates
        new_rules = []
        duplicates = 0
        
        for rule in rules:
            rule_id = rule["metadata"]["rule_id"]
            if rule_id not in existing_ids:
                new_rules.append(rule)
            else:
                duplicates += 1
        
        if duplicates > 0:
            logging.info(f"Skipped {duplicates} duplicate rules from {source_name}")
            self.migration_stats["skipped_duplicates"] += duplicates
        
        # Store new rules
        if new_rules:
            try:
                collection.add(
                    documents=[rule["content"] for rule in new_rules],
                    metadatas=[rule["metadata"] for rule in new_rules],
                    ids=[rule["metadata"]["rule_id"] for rule in new_rules]
                )
                
                self.migration_stats["successful_migrations"] += len(new_rules)
                return len(new_rules)
                
            except Exception as e:
                logging.error(f"Failed to store rules in {collection_name}: {e}")
                self.migration_stats["failed_migrations"] += len(new_rules)
                return 0
        
        return 0
    
    def _detect_platform_from_path(self, file_path: Path) -> str:
        """Detect platform from file path"""
        
        path_str = str(file_path).lower()
        
        if "linkedin" in path_str:
            return "linkedin"
        elif "twitter" in path_str:
            return "twitter"
        elif "substack" in path_str:
            return "substack"
        elif "beehiiv" in path_str:
            return "beehiiv"
        elif "ghost" in path_str:
            return "ghost"
        else:
            return "universal"
    
    async def _generate_migration_report(self):
        """Generate comprehensive migration report"""
        
        report = {
            "migration_timestamp": datetime.now().isoformat(),
            "statistics": self.migration_stats,
            "collection_counts": {},
            "validation_results": {},
            "next_steps": []
        }
        
        # Get collection counts
        for name, collection in self.collections.items():
            try:
                count = collection.count()
                report["collection_counts"][name] = count
            except Exception as e:
                report["collection_counts"][name] = f"Error: {e}"
        
        # Validation checks
        total_rules = sum([
            count for count in report["collection_counts"].values()
            if isinstance(count, int)
        ])
        
        report["validation_results"] = {
            "total_rules_in_chromadb": total_rules,
            "meets_minimum_target": total_rules >= 355,
            "zero_hardcoded_check": await self._check_zero_hardcoded_rules(),
            "rule_diversity_check": await self._check_rule_diversity()
        }
        
        # Generate next steps
        if total_rules < 355:
            report["next_steps"].append("Additional rule extraction needed - target not met")
        
        if not report["validation_results"]["zero_hardcoded_check"]:
            report["next_steps"].append("Remove remaining hardcoded rules from codebase")
        
        report["next_steps"].extend([
            "Test Editorial Service integration",
            "Validate query performance",
            "Setup cache warming",
            "Run end-to-end workflow tests"
        ])
        
        # Save report
        report_path = f"migration_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        logging.info(f"📊 Migration report saved: {report_path}")
        
        # Print summary
        print("\n🎯 MIGRATION SUMMARY")
        print("=" * 50)
        print(f"Files processed: {self.migration_stats['total_files_processed']}")
        print(f"Rules extracted: {self.migration_stats['total_rules_extracted']}")
        print(f"Successfully migrated: {self.migration_stats['successful_migrations']}")
        print(f"Failed migrations: {self.migration_stats['failed_migrations']}")
        print(f"Skipped duplicates: {self.migration_stats['skipped_duplicates']}")
        print(f"Total rules in ChromaDB: {total_rules}")
        print(f"Target achieved (355+): {'✅ YES' if total_rules >= 355 else '❌ NO'}")
        
        return report
    
    async def _check_zero_hardcoded_rules(self) -> bool:
        """Check if hardcoded rules still exist in codebase"""
        
        import subprocess
        
        try:
            # Search for common hardcoded patterns
            result = subprocess.run([
                "grep", "-r", 
                "forbidden_phrases\\|required_elements\\|style_patterns\\|default_rules\\|fallback_rules",
                "src/", "cache/", "mocks/"
            ], capture_output=True, text=True, check=False)
            
            hardcoded_count = len(result.stdout.splitlines()) if result.stdout else 0
            return hardcoded_count == 0
            
        except Exception as e:
            logging.warning(f"Could not check for hardcoded rules: {e}")
            return False
    
    async def _check_rule_diversity(self) -> dict:
        """Check diversity of migrated rules"""
        
        diversity_stats = {
            "platforms_covered": set(),
            "rule_types_covered": set(),
            "workflow_coverage": set(),
            "priority_distribution": {}
        }
        
        try:
            for collection in self.collections.values():
                data = collection.get()
                
                if data and data.get("metadatas"):
                    for metadata in data["metadatas"]:
                        diversity_stats["platforms_covered"].add(metadata.get("platform", "unknown"))
                        diversity_stats["rule_types_covered"].add(metadata.get("rule_type", "unknown"))
                        diversity_stats["workflow_coverage"].add(metadata.get("workflow", "unknown"))
                        
                        priority = metadata.get("priority", "unknown")
                        diversity_stats["priority_distribution"][priority] = \
                            diversity_stats["priority_distribution"].get(priority, 0) + 1
        
        except Exception as e:
            logging.error(f"Failed to check rule diversity: {e}")
        
        # Convert sets to lists for JSON serialization
        diversity_stats["platforms_covered"] = list(diversity_stats["platforms_covered"])
        diversity_stats["rule_types_covered"] = list(diversity_stats["rule_types_covered"])
        diversity_stats["workflow_coverage"] = list(diversity_stats["workflow_coverage"])
        
        return diversity_stats

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        # Initialize ChromaDB client
        client = chromadb.HttpClient(host="localhost", port=8000)
        
        # Run migration
        migrator = HardcodedRuleMigrator(client)
        total_migrated = await migrator.migrate_all_hardcoded_rules()
        
        print(f"\n🎉 Migration completed! {total_migrated} rules migrated to ChromaDB")

    asyncio.run(main())
```

---

## 📊 Schema Validation & Testing

### Schema Validation Script
```python
#!/usr/bin/env python3
# scripts/validate_chromadb_schema.py

import chromadb
import json
from datetime import datetime
import logging

class ChromaDBSchemaValidator:
    def __init__(self, client):
        self.client = client
        self.validation_results = {}
    
    async def validate_all_collections(self):
        """Validate all collection schemas against specification"""
        
        expected_collections = [
            "style_editorial_rules",
            "publication_platform_rules", 
            "topics",
            "scheduling_optimization",
            "user_preferences"
        ]
        
        all_valid = True
        
        for collection_name in expected_collections:
            try:
                is_valid = await self._validate_collection(collection_name)
                self.validation_results[collection_name] = is_valid
                
                if not is_valid:
                    all_valid = False
                    
            except Exception as e:
                logging.error(f"Validation failed for {collection_name}: {e}")
                self.validation_results[collection_name] = {"error": str(e)}
                all_valid = False
        
        return all_valid, self.validation_results
    
    async def _validate_collection(self, collection_name: str) -> dict:
        """Validate individual collection schema"""
        
        try:
            collection = self.client.get_collection(collection_name)
        except Exception as e:
            return {"exists": False, "error": str(e)}
        
        # Get sample data
        data = collection.get(limit=10)
        
        validation_result = {
            "exists": True,
            "document_count": collection.count(),
            "sample_validation": {},
            "metadata_validation": {},
            "schema_compliance": {}
        }
        
        # Validate document structure
        if data and data.get("documents"):
            validation_result["sample_validation"] = await self._validate_documents(
                data, collection_name
            )
        
        # Validate metadata schema
        if data and data.get("metadatas"):
            validation_result["metadata_validation"] = await self._validate_metadata(
                data["metadatas"], collection_name
            )
        
        return validation_result
    
    async def _validate_documents(self, data: dict, collection_name: str) -> dict:
        """Validate document content structure"""
        
        documents = data["documents"]
        validation = {
            "total_documents": len(documents),
            "empty_documents": 0,
            "content_type_valid": True,
            "average_content_length": 0
        }
        
        total_length = 0
        
        for doc in documents:
            if not doc or not isinstance(doc, str):
                validation["empty_documents"] += 1
                validation["content_type_valid"] = False
            else:
                total_length += len(doc)
        
        if len(documents) > 0:
            validation["average_content_length"] = total_length / len(documents)
        
        return validation
    
    async def _validate_metadata(self, metadatas: list, collection_name: str) -> dict:
        """Validate metadata schema compliance"""
        
        validation = {
            "total_metadata_records": len(metadatas),
            "required_fields_present": {},
            "field_type_validation": {},
            "enum_validation": {},
            "collection_specific_validation": {}
        }
        
        # Define required fields per collection
        required_fields = {
            "style_editorial_rules": [
                "rule_id", "rule_type", "platform", "workflow", 
                "priority", "created_at", "source"
            ],
            "publication_platform_rules": [
                "rule_id", "platform", "rule_category", "created_at", "source"
            ],
            "topics": [
                "topic_id", "title", "description", "keywords", 
                "content_type", "status", "created_date", "source"
            ],
            "scheduling_optimization": [
                "rule_id", "rule_type", "platform", "optimal_hours", 
                "confidence_score", "created_at"
            ],
            "user_preferences": [
                "preference_id", "user_id", "preference_type", 
                "preference_value", "created_at", "anonymized"
            ]
        }
        
        collection_required_fields = required_fields.get(collection_name, [])
        
        # Check required fields
        for field in collection_required_fields:
            field_present_count = 0
            for metadata in metadatas:
                if field in metadata:
                    field_present_count += 1
            
            validation["required_fields_present"][field] = {
                "present_count": field_present_count,
                "total_records": len(metadatas),
                "coverage_percentage": (field_present_count / len(metadatas)) * 100 if metadatas else 0
            }
        
        # Collection-specific validations
        if collection_name == "style_editorial_rules":
            validation["collection_specific_validation"] = await self._validate_style_rules_metadata(metadatas)
        elif collection_name == "topics":
            validation["collection_specific_validation"] = await self._validate_topics_metadata(metadatas)
        
        return validation
    
    async def _validate_style_rules_metadata(self, metadatas: list) -> dict:
        """Validate style rules specific metadata"""
        
        validation = {
            "workflow_values": {},
            "priority_values": {},
            "platform_values": {},
            "rule_type_values": {}
        }
        
        for metadata in metadatas:
            # Count workflow values
            workflow = metadata.get("workflow", "unknown")
            validation["workflow_values"][workflow] = validation["workflow_values"].get(workflow, 0) + 1
            
            # Count priority values
            priority = metadata.get("priority", "unknown")
            validation["priority_values"][priority] = validation["priority_values"].get(priority, 0) + 1
            
            # Count platform values
            platform = metadata.get("platform", "unknown")
            validation["platform_values"][platform] = validation["platform_values"].get(platform, 0) + 1
            
            # Count rule type values
            rule_type = metadata.get("rule_type", "unknown")
            validation["rule_type_values"][rule_type] = validation["rule_type_values"].get(rule_type, 0) + 1
        
        return validation
    
    async def _validate_topics_metadata(self, metadatas: list) -> dict:
        """Validate topics specific metadata"""
        
        validation = {
            "content_type_values": {},
            "status_values": {},
            "source_values": {},
            "engagement_prediction_stats": {}
        }
        
        engagement_scores = []
        
        for metadata in metadatas:
            # Count content type values
            content_type = metadata.get("content_type", "unknown")
            validation["content_type_values"][content_type] = validation["content_type_values"].get(content_type, 0) + 1
            
            # Count status values
            status = metadata.get("status", "unknown")
            validation["status_values"][status] = validation["status_values"].get(status, 0) + 1
            
            # Count source values
            source = metadata.get("source", "unknown")
            validation["source_values"][source] = validation["source_values"].get(source, 0) + 1
            
            # Collect engagement scores
            engagement = metadata.get("engagement_prediction")
            if engagement is not None and isinstance(engagement, (int, float)):
                engagement_scores.append(float(engagement))
        
        # Calculate engagement statistics
        if engagement_scores:
            validation["engagement_prediction_stats"] = {
                "count": len(engagement_scores),
                "average": sum(engagement_scores) / len(engagement_scores),
                "min": min(engagement_scores),
                "max": max(engagement_scores),
                "valid_range": all(0 <= score <= 1 for score in engagement_scores)
            }
        
        return validation
    
    async def generate_validation_report(self):
        """Generate comprehensive validation report"""
        
        is_valid, results = await self.validate_all_collections()
        
        report = {
            "validation_timestamp": datetime.now().isoformat(),
            "overall_valid": is_valid,
            "collection_results": results,
            "summary": {
                "total_collections": len(results),
                "valid_collections": len([r for r in results.values() if r.get("exists", False)]),
                "total_documents": 0,
                "schema_compliance_score": 0
            },
            "recommendations": []
        }
        
        # Calculate summary statistics
        total_docs = 0
        valid_count = 0
        
        for collection_name, result in results.items():
            if isinstance(result, dict) and result.get("exists"):
                doc_count = result.get("document_count", 0)
                total_docs += doc_count
                
                # Check if collection is properly configured
                sample_validation = result.get("sample_validation", {})
                metadata_validation = result.get("metadata_validation", {})
                
                if (sample_validation.get("content_type_valid", False) and 
                    doc_count > 0):
                    valid_count += 1
        
        report["summary"]["total_documents"] = total_docs
        report["summary"]["schema_compliance_score"] = (valid_count / len(results)) * 100 if results else 0
        
        # Generate recommendations
        if total_docs < 355:
            report["recommendations"].append(f"Total document count ({total_docs}) is below target (355+)")
        
        if report["summary"]["schema_compliance_score"] < 100:
            report["recommendations"].append("Some collections have schema compliance issues")
        
        for collection_name, result in results.items():
            if isinstance(result, dict) and "error" in result:
                report["recommendations"].append(f"Fix errors in {collection_name}: {result['error']}")
        
        # Save report
        report_path = f"schema_validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"📊 Schema validation report saved: {report_path}")
        
        # Print summary
        print("\n🔍 SCHEMA VALIDATION SUMMARY")
        print("=" * 50)
        print(f"Overall Valid: {'✅ YES' if is_valid else '❌ NO'}")
        print(f"Collections: {report['summary']['valid_collections']}/{report['summary']['total_collections']}")
        print(f"Total Documents: {total_docs}")
        print(f"Schema Compliance: {report['summary']['schema_compliance_score']:.1f}%")
        
        if report["recommendations"]:
            print("\n⚠️  RECOMMENDATIONS:")
            for i, rec in enumerate(report["recommendations"], 1):
                print(f"{i}. {rec}")
        
        return report

if __name__ == "__main__":
    import asyncio
    
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        client = chromadb.HttpClient(host="localhost", port=8000)
        validator = ChromaDBSchemaValidator(client)
        
        await validator.generate_validation_report()

    asyncio.run(main())
```

---

**ChromaDB Schema Status**: ✅ **COMPLETE SPECIFICATION READY**
**Collections**: 5 specialized collections with comprehensive metadata schemas
**Total Capacity**: 500+ rules (355+ migrated from hardcoded sources)
**Query Performance**: Optimized for <100ms P95 latency
**Migration Strategy**: Automated extraction and validation scripts included