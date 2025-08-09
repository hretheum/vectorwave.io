#!/usr/bin/env python3
"""
Platform Optimizer - AI Writing Flow Enhanced Integration
PHASE 4.5.3: AI WRITING FLOW INTEGRATION (Week 2)

Generate platform-specific content variations for multi-platform publishing.
Integrates with Publisher Orchestrator for enhanced content distribution.
"""

import os
import time
import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

# Import existing AI Writing Flow components
try:
    from ai_writing_flow.crews.writer_crew import WriterCrew
    from ai_writing_flow.crews.quality_crew import QualityCrew
    from ai_writing_flow.ai_writing_flow_v2 import AIWritingFlowV2
    AI_WRITING_FLOW_AVAILABLE = True
except ImportError:
    # Fallback if AI Writing Flow or crewai not available
    WriterCrew = None
    QualityCrew = None
    AIWritingFlowV2 = None
    AI_WRITING_FLOW_AVAILABLE = False

logger = logging.getLogger(__name__)


class Topic(BaseModel):
    """Topic model for platform content generation"""
    title: str = Field(..., description="Content title")
    description: str = Field(..., description="Content description")
    keywords: Optional[List[str]] = Field(default=[], description="Content keywords")
    target_audience: Optional[str] = Field(default="general", description="Target audience")


class PlatformConfig(BaseModel):
    """Configuration for specific platform content generation"""
    enabled: bool = Field(default=True, description="Whether platform is enabled")
    direct_content: Optional[bool] = Field(default=None, description="Force direct content mode")
    custom_params: Optional[Dict[str, Any]] = Field(default={}, description="Platform-specific parameters")


class PlatformOptimizedContent(BaseModel):
    """Platform-optimized content result"""
    platform: str = Field(..., description="Target platform")
    content: str = Field(..., description="Generated content")
    content_type: str = Field(..., description="Content type (direct/prompt)")
    metadata: Dict[str, Any] = Field(default={}, description="Content metadata")
    ready_for_presenton: bool = Field(default=False, description="Ready for Presenton service")
    generation_time: float = Field(..., description="Generation time in seconds")
    quality_score: float = Field(default=0.0, description="Content quality score")


class PlatformOptimizer:
    """
    Generate platform-specific content variations for multi-platform publishing
    
    Integrates with existing AI Writing Flow agents to create optimized content
    for different social media platforms and publishing channels.
    """
    
    def __init__(self):
        """Initialize platform optimizer with configurations"""
        
        logger.info("🚀 Initializing PlatformOptimizer...")
        
        # Platform-specific configurations
        self.platform_configs = {
            "linkedin": {
                "prompt_mode": True,  # Default for LinkedIn = carousel prompts
                "max_length": 3000,
                "focus": "professional, slide-friendly",
                "structure": "presentation_outline",
                "slides_count": 5,
                "content_type": "carousel_prompt"
            },
            "twitter": {
                "prompt_mode": False,
                "max_length": 280,
                "focus": "viral, engaging",
                "structure": "thread_ready",
                "content_type": "thread"
            },
            "ghost": {
                "prompt_mode": False,
                "max_length": 10000,
                "focus": "detailed, SEO-friendly",
                "structure": "blog_article",
                "content_type": "article"
            },
            "substack": {
                "prompt_mode": False,
                "max_length": 8000,
                "focus": "newsletter, personal",
                "structure": "newsletter_format",
                "content_type": "newsletter"
            }
        }
        
        # Initialize AI Writing Flow V2 for content generation
        if not AI_WRITING_FLOW_AVAILABLE or not AIWritingFlowV2:
            raise ImportError("AI Writing Flow V2 and crewai are required for PlatformOptimizer")
        
        self.ai_writing_flow = AIWritingFlowV2(
            monitoring_enabled=True,
            alerting_enabled=False,  # Disable alerts for individual content generation
            quality_gates_enabled=True
        )
        
        # Initialize existing CrewAI crews
        if WriterCrew and QualityCrew:
            try:
                self.writer_crew = WriterCrew()
                self.quality_crew = QualityCrew()
                logger.info("✅ CrewAI crews initialized")
            except Exception as e:
                logger.warning(f"⚠️ CrewAI crews initialization failed: {e}")
                self.writer_crew = None
                self.quality_crew = None
        else:
            logger.info("⚠️ CrewAI crews not available")
            self.writer_crew = None
            self.quality_crew = None
        
        logger.info(f"✅ PlatformOptimizer initialized with {len(self.platform_configs)} platform configurations")
    
    async def generate_for_platform(
        self, 
        topic: Topic, 
        platform: str, 
        direct_content: Optional[bool] = None
    ) -> PlatformOptimizedContent:
        """
        Generate optimized content for a specific platform
        
        Args:
            topic: Content topic and metadata
            platform: Target platform (linkedin, twitter, ghost, substack)
            direct_content: Override for content mode (True=direct, False=prompt, None=platform default)
            
        Returns:
            PlatformOptimizedContent: Generated content with metadata
        """
        
        start_time = time.time()
        
        logger.info(f"🎯 Generating content for {platform}: {topic.title}")
        
        # Get platform configuration
        platform_config = self.platform_configs.get(platform)
        if not platform_config:
            raise ValueError(f"Unsupported platform: {platform}")
        
        # Determine content mode (prompt vs direct)
        prompt_mode = platform_config.get("prompt_mode", False)
        if direct_content is not None:
            prompt_mode = not direct_content
        
        content_type = "prompt" if prompt_mode else "direct"
        
        try:
            # Generate platform-specific content
            if prompt_mode:
                content = await self._generate_prompt_content(topic, platform, platform_config)
                ready_for_presenton = platform == "linkedin"  # LinkedIn prompts go to Presenton
            else:
                content = await self._generate_direct_content(topic, platform, platform_config)
                ready_for_presenton = False
            
            # Calculate quality score
            quality_score = await self._calculate_quality_score(content, platform_config)
            
            generation_time = time.time() - start_time
            
            # Build metadata
            metadata = {
                "platform": platform,
                "content_length": len(content),
                "target_audience": topic.target_audience,
                "keywords": topic.keywords,
                "generation_timestamp": datetime.now().isoformat(),
                "prompt_mode": prompt_mode,
                "max_length": platform_config.get("max_length"),
                "focus": platform_config.get("focus"),
                "structure": platform_config.get("structure")
            }
            
            # Add platform-specific metadata
            if platform == "linkedin" and prompt_mode:
                metadata["slides_count"] = platform_config.get("slides_count", 5)
                metadata["template_suggestion"] = "business"
            
            result = PlatformOptimizedContent(
                platform=platform,
                content=content,
                content_type=content_type,
                metadata=metadata,
                ready_for_presenton=ready_for_presenton,
                generation_time=generation_time,
                quality_score=quality_score
            )
            
            logger.info(f"✅ Generated {platform} content: {len(content)} chars, quality: {quality_score:.2f}, time: {generation_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Content generation failed for {platform}: {e}")
            raise
    
    async def generate_multi_platform(
        self, 
        topic: Topic, 
        platforms: Dict[str, PlatformConfig]
    ) -> Dict[str, Union[PlatformOptimizedContent, Dict[str, str]]]:
        """
        Generate content for multiple platforms simultaneously
        
        Args:
            topic: Content topic and metadata
            platforms: Dictionary of platform configs
            
        Returns:
            Dictionary with platform results (success or error)
        """
        
        logger.info(f"🚀 Multi-platform generation for: {topic.title}")
        logger.info(f"📋 Platforms: {list(platforms.keys())}")
        
        # Create tasks for all enabled platforms
        tasks = []
        for platform, config in platforms.items():
            if config.enabled:
                task = self._generate_platform_with_error_handling(
                    topic, platform, config.direct_content
                )
                tasks.append((platform, task))
        
        # Execute all platforms concurrently
        results = {}
        task_results = await asyncio.gather(*[task for _, task in tasks], return_exceptions=True)
        
        # Process results
        for (platform, _), result in zip(tasks, task_results):
            if isinstance(result, Exception):
                logger.error(f"❌ {platform} generation failed: {result}")
                results[platform] = {"error": str(result)}
            else:
                results[platform] = result
        
        # Summary logging
        success_count = sum(1 for r in results.values() if not isinstance(r, dict) or "error" not in r)
        total_count = len(results)
        
        logger.info(f"✅ Multi-platform generation complete: {success_count}/{total_count} successful")
        
        return results
    
    async def _generate_platform_with_error_handling(
        self, 
        topic: Topic, 
        platform: str, 
        direct_content: Optional[bool]
    ) -> Union[PlatformOptimizedContent, Dict[str, str]]:
        """Generate content for platform with error handling"""
        try:
            return await self.generate_for_platform(topic, platform, direct_content)
        except Exception as e:
            return {"error": str(e)}
    
    async def _generate_prompt_content(
        self, 
        topic: Topic, 
        platform: str, 
        platform_config: Dict[str, Any]
    ) -> str:
        """Generate prompt-based content (for carousel presentations)"""
        
        logger.info(f"🤖 Generating prompt content for {platform}")
        
        # Special handling for LinkedIn carousel prompts
        if platform == "linkedin":
            slides_count = platform_config.get("slides_count", 5)
            
            prompt = f"""Create a detailed presentation prompt for "{topic.title}".

Topic: {topic.title}
Description: {topic.description}
Target Audience: {topic.target_audience}
Slides Count: {slides_count}

Generate a comprehensive prompt that includes:
1. Clear presentation structure with {slides_count} slides
2. Professional business focus
3. Slide-by-slide content outline
4. Visual suggestions for each slide
5. Key takeaways and call-to-action

The prompt should be ready for AI presentation generation services."""
            
            # Write content to file for AI Writing Flow V2
            content_file = f"/tmp/content_{hash(topic.title)}.md"
            with open(content_file, 'w') as f:
                f.write(f"# {topic.title}\n\n{topic.description}\n\n{prompt}")
            
            # Use AI Writing Flow to generate the prompt
            flow_inputs = {
                "topic_title": f"LinkedIn Carousel Prompt: {topic.title}",
                "platform": "LinkedIn",
                "content_type": "STANDALONE",  # Use accepted type instead of CAROUSEL_PROMPT
                "content_ownership": "ORIGINAL",
                "viral_score": 8.0,
                "editorial_recommendations": prompt,
                "file_path": content_file
            }
            
            result = self.ai_writing_flow.kickoff(flow_inputs)
            
            # Extract content from WritingFlowState result
            content = None
            if hasattr(result, 'final_draft') and result.final_draft:
                content = result.final_draft
            elif hasattr(result, 'current_draft') and result.current_draft:
                content = result.current_draft
            elif hasattr(result, 'draft_versions') and result.draft_versions:
                # Get the latest draft version
                content = result.draft_versions[-1] if result.draft_versions else None
            
            if content:
                return content
            else:
                raise ValueError("AI Writing Flow returned no content for LinkedIn prompt generation")
        
        else:
            # Generic prompt generation for other platforms
            return f"Generate {platform_config.get('structure', 'content')} about: {topic.title}\n\nDescription: {topic.description}"
    
    async def _generate_direct_content(
        self, 
        topic: Topic, 
        platform: str, 
        platform_config: Dict[str, Any]
    ) -> str:
        """Generate direct publishable content"""
        
        logger.info(f"📝 Generating direct content for {platform}")
        
        # Write content to file for AI Writing Flow V2
        content_file = f"/tmp/content_{platform}_{hash(topic.title)}.md"
        with open(content_file, 'w') as f:
            f.write(f"# {topic.title}\n\n{topic.description}\n\nKeywords: {', '.join(topic.keywords)}\nTarget Audience: {topic.target_audience}")
        
        # Prepare AI Writing Flow inputs
        # Map all platform-specific content types to accepted AI Writing Flow V2 types
        content_type_mapping = {
            "THREAD": "STANDALONE",
            "ARTICLE": "STANDALONE", 
            "NEWSLETTER": "SERIES",
            "CAROUSEL_PROMPT": "STANDALONE"
        }
        
        platform_content_type = platform_config.get("content_type", "standalone").upper()
        mapped_content_type = content_type_mapping.get(platform_content_type, platform_content_type)
        
        flow_inputs = {
            "topic_title": topic.title,
            "platform": platform.capitalize(),
            "content_type": mapped_content_type,  # Use mapped type
            "content_ownership": "ORIGINAL",
            "viral_score": 7.5,
            "editorial_recommendations": f"Create {platform_config.get('focus', 'engaging')} content for {platform}. {topic.description}",
            "max_length": platform_config.get("max_length", 1000),
            "target_structure": platform_config.get("structure", "general"),
            "file_path": content_file
        }
        
        # Execute AI Writing Flow
        result = self.ai_writing_flow.kickoff(flow_inputs)
        
        # Extract content from WritingFlowState result
        content = None
        if hasattr(result, 'final_draft') and result.final_draft:
            content = result.final_draft
        elif hasattr(result, 'current_draft') and result.current_draft:
            content = result.current_draft
        elif hasattr(result, 'draft_versions') and result.draft_versions:
            # Get the latest draft version
            content = result.draft_versions[-1] if result.draft_versions else None
        
        if content:
            # Platform-specific post-processing
            content = await self._post_process_content(content, platform, platform_config)
            return content
        else:
            raise ValueError(f"AI Writing Flow returned no content for {platform} generation")
    
    async def _post_process_content(
        self, 
        content: str, 
        platform: str, 
        platform_config: Dict[str, Any]
    ) -> str:
        """Post-process content for platform-specific requirements"""
        
        # Length constraints
        max_length = platform_config.get("max_length")
        if max_length and len(content) > max_length:
            # Truncate intelligently at sentence boundaries
            sentences = content.split('. ')
            truncated = ""
            for sentence in sentences:
                if len(truncated + sentence + '. ') <= max_length - 10:  # Leave buffer
                    truncated += sentence + '. '
                else:
                    break
            
            if truncated:
                content = truncated.rstrip('. ') + "..."
            else:
                content = content[:max_length-3] + "..."
        
        # Platform-specific formatting
        if platform == "twitter":
            # Ensure Twitter thread format
            if len(content) > 280 and "\n\n" not in content:
                # Convert to thread format
                words = content.split()
                threads = []
                current_thread = ""
                
                for word in words:
                    if len(current_thread + " " + word) <= 270:  # Leave space for thread numbering
                        current_thread += (" " if current_thread else "") + word
                    else:
                        if current_thread:
                            threads.append(current_thread)
                        current_thread = word
                
                if current_thread:
                    threads.append(current_thread)
                
                # Format as numbered threads
                content = "\n\n".join([f"{i+1}/{len(threads)} {thread}" for i, thread in enumerate(threads)])
        
        elif platform == "linkedin":
            # Ensure professional LinkedIn format
            if not content.startswith(("🚀", "💡", "🎯", "✨")):
                content = "💡 " + content
        
        elif platform == "ghost":
            # Ensure proper blog format with headings
            if "##" not in content and "# " not in content:
                # Add basic structure
                lines = content.split('\n')
                if len(lines) > 3:
                    lines[0] = f"# {lines[0]}" if not lines[0].startswith('#') else lines[0]
                    content = '\n'.join(lines)
        
        return content
    
    async def _calculate_quality_score(self, content: str, platform_config: Dict[str, Any]) -> float:
        """Calculate content quality score based on platform requirements"""
        
        score = 0.0
        max_score = 10.0
        
        # Length appropriateness (30% of score)
        max_length = platform_config.get("max_length", 1000)
        length_ratio = len(content) / max_length
        
        if 0.3 <= length_ratio <= 0.9:  # Optimal length range
            score += 3.0
        elif 0.1 <= length_ratio <= 1.0:  # Acceptable range
            score += 2.0
        else:  # Too short or too long
            score += 1.0
        
        # Content structure (20% of score)
        if "\n" in content:  # Has structure
            score += 2.0
        
        # Engagement elements (25% of score) 
        engagement_elements = ["?", "!", "#", "@", "👇", "💡", "🚀", "🎯", "✨"]
        found_elements = sum(1 for element in engagement_elements if element in content)
        score += min(2.5, found_elements * 0.5)
        
        # Topic relevance (25% of score) - simplified check
        if len(content.strip()) > 50:  # Has substantial content
            score += 2.5
        
        return min(max_score, score)
    
    def get_platform_configs(self) -> Dict[str, Dict[str, Any]]:
        """Get all platform configurations"""
        return self.platform_configs.copy()
    
    def get_supported_platforms(self) -> List[str]:
        """Get list of supported platforms"""
        return list(self.platform_configs.keys())


# Convenience functions for external usage
async def generate_linkedin_prompt(topic: Topic, slides_count: int = 5) -> str:
    """Generate LinkedIn carousel prompt"""
    optimizer = PlatformOptimizer()
    result = await optimizer.generate_for_platform(topic, "linkedin", direct_content=False)
    return result.content


async def generate_multi_platform_content(topic: Topic, platforms: List[str]) -> Dict[str, Any]:
    """Generate content for multiple platforms"""
    optimizer = PlatformOptimizer()
    platform_configs = {platform: PlatformConfig(enabled=True) for platform in platforms}
    return await optimizer.generate_multi_platform(topic, platform_configs)


if __name__ == "__main__":
    # Test the platform optimizer
    import asyncio
    
    async def test_platform_optimizer():
        optimizer = PlatformOptimizer()
        
        test_topic = Topic(
            title="AI-Powered Content Generation Revolution",
            description="How artificial intelligence is transforming content creation and marketing strategies across industries.",
            keywords=["AI", "content", "marketing", "automation"],
            target_audience="marketing professionals"
        )
        
        # Test LinkedIn prompt generation
        linkedin_result = await optimizer.generate_for_platform(test_topic, "linkedin", direct_content=False)
        print(f"LinkedIn Prompt ({linkedin_result.generation_time:.2f}s):")
        print(linkedin_result.content[:200] + "...")
        print()
        
        # Test Twitter direct content
        twitter_result = await optimizer.generate_for_platform(test_topic, "twitter", direct_content=True)
        print(f"Twitter Content ({twitter_result.generation_time:.2f}s):")
        print(twitter_result.content)
        print()
        
        # Test multi-platform
        platforms = {
            "linkedin": PlatformConfig(enabled=True, direct_content=False),
            "twitter": PlatformConfig(enabled=True, direct_content=True),
            "ghost": PlatformConfig(enabled=True, direct_content=True)
        }
        
        multi_results = await optimizer.generate_multi_platform(test_topic, platforms)
        print("Multi-platform results:")
        for platform, result in multi_results.items():
            if isinstance(result, dict) and "error" in result:
                print(f"  {platform}: ERROR - {result['error']}")
            else:
                print(f"  {platform}: {len(result.content)} chars, quality: {result.quality_score:.2f}")
    
    # Run test
    asyncio.run(test_platform_optimizer())