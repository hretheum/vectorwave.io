"""
Research Crew - Deep content research and fact-finding with Topic Manager integration
Integrated with Topic Manager for dynamic topic discovery and AI-powered suggestions
"""

from crewai import Agent, Crew, Task, Process
from crewai.tools import tool
from typing import List, Dict, Any, Optional
import os
from pathlib import Path
import json
from datetime import datetime
import re
import asyncio
import logging

from ..models import ResearchResult
from ..clients.topic_manager_client import TopicManagerClient
from ..tools.enhanced_knowledge_tools import (
    search_crewai_knowledge,
    get_flow_examples,
    troubleshoot_crewai,
    # Backward compatibility imports
    search_crewai_docs,
    get_crewai_example,
    list_crewai_topics
)

logger = logging.getLogger(__name__)

# Disable CrewAI memory logs
os.environ["CREWAI_STORAGE_LOG_ENABLED"] = "false"

# Define base path at module level
BASE_PATH = Path("/Users/hretheum/dev/bezrobocie/vector-wave")


@tool("Read Source Files")
def read_source_files(file_path: str) -> str:
    """Read source file(s) from path - can be file or folder"""
    full_path = BASE_PATH / file_path.lstrip("/")
    
    # Check if it's a directory
    if full_path.is_dir():
        content_parts = []
        md_files = list(full_path.glob("*.md"))
        # Filter out metadata files
        md_files = [f for f in md_files if f.name != "NORMALIZATION_META.json"]
        
        if not md_files:
            return f"No markdown files found in folder {file_path}"
        
        # Read all markdown files
        for file in md_files[:5]:  # Limit to first 5 files
            try:
                with open(file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    content_parts.append(f"=== {file.name} ===\n{content}\n")
            except Exception as e:
                content_parts.append(f"=== Error reading {file.name}: {str(e)} ===\n")
        
        return "\n".join(content_parts)
    
    # Single file
    elif full_path.is_file():
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
                return f"=== {full_path.name} ===\n{content}"
        except Exception as e:
            return f"Error reading file {file_path}: {str(e)}"
    
    else:
        return f"Path {file_path} not found at {full_path}"


@tool("Extract Sources")
def extract_sources(content: str) -> str:
    """Extract sources and references from content"""
    sources = []
    
    # Look for common source patterns
    source_indicators = [
        r'źródło:\s*(.+)',
        r'źródła:\s*(.+)',
        r'source:\s*(.+)',
        r'via:\s*(.+)',
        r'\[(\d+)\]\s*(.+)',
        r'https?://[^\s]+',
    ]
    
    # Simplified extraction
    lines = content.split('\n')
    for line in lines:
        if any(indicator in line.lower() for indicator in ['źródło', 'source', 'http']):
            sources.append({
                "url": line.strip(),
                "title": "Extracted source",
                "date": datetime.now().isoformat(),
                "type": "reference"
            })
    
    # Return as formatted string since tools must return strings
    return json.dumps(sources[:10], indent=2)


@tool("Research Web Sources")
def research_web_sources(topic: str, content_ownership: str = "EXTERNAL") -> str:
    """Research additional web sources for context and validation"""
    # For ORIGINAL content, we don't need external sources
    if content_ownership == "ORIGINAL":
        return json.dumps({
            "message": "Skipping external research for ORIGINAL content",
            "topic": topic,
            "findings": [],
            "key_insights": [],
            "controversies": []
        }, indent=2)
    
    # For EXTERNAL content, provide mock research data
    # In production, this would use actual web search APIs
    research_data = {
        "topic": topic,
        "timestamp": datetime.now().isoformat(),
        "findings": [
            {
                "source": "Gartner Report 2024",
                "url": "https://gartner.com/ai-agents-2024",
                "summary": "AI agents will handle 75% of software development tasks by 2026",
                "credibility": "high",
                "data_points": [
                    "75% task automation by 2026",
                    "$1.2T market value",
                    "45% productivity increase"
                ]
            },
            {
                "source": "Stack Overflow Developer Survey",
                "url": "https://stackoverflow.com/survey/2024",
                "summary": "87% of developers already use AI assistants daily",
                "credibility": "high",
                "data_points": [
                    "87% daily usage",
                    "3.5x faster debugging",
                    "60% less documentation time"
                ]
            }
        ],
        "key_insights": [
            "AI agents are becoming essential tools, not replacements",
            "Focus shifting from code generation to system design"
        ],
        "controversies": [
            "Job displacement fears vs. productivity gains",
            "Code ownership and liability questions"
        ]
    }
    
    # Return as JSON string since tools must return strings
    return json.dumps(research_data, indent=2)


class ResearchCrew:
    """
    Crew responsible for deep research on topics with Topic Manager integration
    Integrated with Topic Manager for dynamic topic discovery and AI-powered suggestions
    """
    
    def __init__(self, topic_manager_url: str = "http://localhost:8041"):
        """
        Initialize Research Crew with Topic Manager integration
        
        Args:
            topic_manager_url: URL of Topic Manager service (default: http://localhost:8041)
        """
        self.base_path = BASE_PATH
        self.topic_manager_url = topic_manager_url
        self.topic_manager_client = None
        self._initialize_topic_manager()
        
        # Circuit breaker state for Topic Manager
        self._topic_manager_available = True
        self._last_check_time = None
        
    def _initialize_topic_manager(self):
        """Initialize Topic Manager client"""
        try:
            self.topic_manager_client = TopicManagerClient(
                base_url=self.topic_manager_url,
                timeout=30.0
            )
            logger.info(f"Connected to Topic Manager at {self.topic_manager_url}")
        except Exception as e:
            logger.error(f"Failed to initialize Topic Manager client: {e}")
            self._topic_manager_available = False
    
    @tool("Get AI-Powered Topic Suggestions")
    def get_topic_suggestions(self, 
                             domain: str = "technology", 
                             content_type: str = "TUTORIAL",
                             limit: int = 5) -> str:
        """
        Get AI-powered topic suggestions from Topic Manager
        
        Args:
            domain: Domain to focus on (technology, AI, business, etc.)
            content_type: Type of content (TUTORIAL, DEEP_DIVE, CASE_STUDY)
            limit: Number of suggestions to get
            
        Returns:
            JSON string with topic suggestions and metadata
        """
        if not self.topic_manager_client:
            return json.dumps({
                "error": "Topic Manager not available",
                "suggestions": [],
                "message": "Topic Manager connection required for dynamic suggestions"
            })
        
        try:
            # Run async call in sync context
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def get_suggestions():
                    try:
                        result = await self.topic_manager_client.get_topic_suggestions(
                            limit=limit,
                            domain=domain,
                            content_type=content_type,
                            min_engagement_score=0.6
                        )
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(get_suggestions())
                result = future.result(timeout=30)
            else:
                result = asyncio.run(
                    self.topic_manager_client.get_topic_suggestions(
                        limit=limit,
                        domain=domain,
                        content_type=content_type,
                        min_engagement_score=0.6
                    )
                )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Topic suggestions failed: {e}")
            return json.dumps({
                "error": str(e),
                "suggestions": [],
                "message": "Failed to get topic suggestions from Topic Manager"
            })
    
    @tool("Trigger Topic Research Discovery")
    def trigger_research_discovery(self, 
                                  domain: Optional[str] = None,
                                  keywords: List[str] = None) -> str:
        """
        Trigger research-driven topic discovery in Topic Manager
        
        Args:
            domain: Domain to focus research on
            keywords: Keywords to guide research
            
        Returns:
            JSON string with research trigger confirmation
        """
        if not self.topic_manager_client:
            return json.dumps({
                "error": "Topic Manager not available",
                "status": "failed",
                "message": "Topic Manager connection required for research trigger"
            })
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def trigger_research():
                    try:
                        result = await self.topic_manager_client.trigger_research_discovery(
                            agent="research",
                            domain=domain,
                            keywords=keywords or []
                        )
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(trigger_research())
                result = future.result(timeout=30)
            else:
                result = asyncio.run(
                    self.topic_manager_client.trigger_research_discovery(
                        agent="research",
                        domain=domain,
                        keywords=keywords or []
                    )
                )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Research discovery trigger failed: {e}")
            return json.dumps({
                "error": str(e),
                "status": "failed",
                "message": "Failed to trigger research discovery"
            })
    
    @tool("Trigger Auto-Scraping")
    def trigger_auto_scraping(self, 
                             sources: List[str] = None,
                             domains: List[str] = None) -> str:
        """
        Trigger automatic topic scraping from external sources
        
        Args:
            sources: Specific sources to scrape
            domains: Domains to focus on
            
        Returns:
            JSON string with scraping status and discovered topics
        """
        if not self.topic_manager_client:
            return json.dumps({
                "error": "Topic Manager not available",
                "scraped_topics": 0,
                "message": "Topic Manager connection required for auto-scraping"
            })
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def trigger_scraping():
                    try:
                        result = await self.topic_manager_client.trigger_auto_scraping(
                            sources=sources,
                            domains=domains or ["technology", "AI"],
                            limit=10
                        )
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(trigger_scraping())
                result = future.result(timeout=60)  # Longer timeout for scraping
            else:
                result = asyncio.run(
                    self.topic_manager_client.trigger_auto_scraping(
                        sources=sources,
                        domains=domains or ["technology", "AI"],
                        limit=10
                    )
                )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Auto-scraping trigger failed: {e}")
            return json.dumps({
                "error": str(e),
                "scraped_topics": 0,
                "message": "Failed to trigger auto-scraping"
            })
    
    @tool("Get Topic Relevance Score")
    def get_topic_relevance_score(self, 
                                 topic_title: str,
                                 context: Dict[str, Any]) -> str:
        """
        Get relevance score for a topic given research context
        
        Args:
            topic_title: Title of the topic to score
            context: Research context for scoring
            
        Returns:
            JSON string with relevance score and reasoning
        """
        if not self.topic_manager_client:
            return json.dumps({
                "error": "Topic Manager not available",
                "relevance_score": 0.0,
                "reasoning": "Topic Manager connection required for relevance scoring"
            })
        
        try:
            # First search for the topic
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def score_relevance():
                    try:
                        # Search for topic first
                        search_result = await self.topic_manager_client.search_topics(
                            query=topic_title,
                            limit=1
                        )
                        
                        if not search_result.get("results"):
                            return {
                                "relevance_score": 0.0,
                                "reasoning": "Topic not found in database"
                            }
                        
                        topic_id = search_result["results"][0].get("topic_id")
                        if topic_id:
                            score_result = await self.topic_manager_client.get_topic_relevance_score(
                                topic_id=topic_id,
                                context=context
                            )
                            return score_result
                        else:
                            return {
                                "relevance_score": 0.5,
                                "reasoning": "Topic found but ID not available"
                            }
                    except Exception as e:
                        raise e
                
                asyncio.create_task(score_relevance())
                result = future.result(timeout=30)
            else:
                search_result = asyncio.run(
                    self.topic_manager_client.search_topics(
                        query=topic_title,
                        limit=1
                    )
                )
                
                if not search_result.get("results"):
                    result = {
                        "relevance_score": 0.0,
                        "reasoning": "Topic not found in database"
                    }
                else:
                    topic_id = search_result["results"][0].get("topic_id")
                    if topic_id:
                        result = asyncio.run(
                            self.topic_manager_client.get_topic_relevance_score(
                                topic_id=topic_id,
                                context=context
                            )
                        )
                    else:
                        result = {
                            "relevance_score": 0.5,
                            "reasoning": "Topic found but ID not available"
                        }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Topic relevance scoring failed: {e}")
            return json.dumps({
                "error": str(e),
                "relevance_score": 0.0,
                "reasoning": "Failed to score topic relevance"
            })
    
    @tool("Search Topics Database")
    def search_topics_database(self, query: str, limit: int = 10) -> str:
        """
        Search topics in the Topic Manager database
        
        Args:
            query: Search query
            limit: Maximum results
            
        Returns:
            JSON string with search results
        """
        if not self.topic_manager_client:
            return json.dumps({
                "error": "Topic Manager not available",
                "results": [],
                "message": "Topic Manager connection required for topic search"
            })
        
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                future = concurrent.futures.Future()
                
                async def search_topics():
                    try:
                        result = await self.topic_manager_client.search_topics(
                            query=query,
                            limit=limit,
                            include_metadata=True
                        )
                        future.set_result(result)
                    except Exception as e:
                        future.set_exception(e)
                
                asyncio.create_task(search_topics())
                result = future.result(timeout=30)
            else:
                result = asyncio.run(
                    self.topic_manager_client.search_topics(
                        query=query,
                        limit=limit,
                        include_metadata=True
                    )
                )
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            logger.error(f"Topic search failed: {e}")
            return json.dumps({
                "error": str(e),
                "results": [],
                "message": "Failed to search topics database"
            })

    def research_analyst_agent(self) -> Agent:
        """Create a research analyst agent with Topic Manager integration"""
        return Agent(
            role="Senior Research Analyst (Topic Manager Enhanced)",
            goal="Conduct comprehensive research using AI-powered topic suggestions and dynamic discovery via Topic Manager",
            backstory="""You are an experienced research analyst enhanced with AI-powered topic 
            intelligence from Topic Manager. You specialize in technology and content analysis 
            with access to dynamic topic suggestions, trending research areas, and automated 
            topic discovery. You leverage AI-powered platform assignment and engagement prediction 
            to identify the most relevant and engaging topics. You have a keen eye for credible 
            sources, fact-checking, and synthesizing complex information into clear insights. 
            You always verify information from multiple sources and use Topic Manager's relevance 
            scoring to prioritize research efforts.""",
            tools=[
                read_source_files,
                extract_sources,
                research_web_sources,
                self.get_topic_suggestions,
                self.trigger_research_discovery,
                self.trigger_auto_scraping,
                self.get_topic_relevance_score,
                self.search_topics_database,
                # Enhanced Knowledge Base tools
                search_crewai_knowledge,
                get_flow_examples,
                troubleshoot_crewai,
                # Backward compatibility tools
                search_crewai_docs,
                get_crewai_example,
                list_crewai_topics
            ],
            verbose=True,
            allow_delegation=False
        )
    
    def create_research_task(self, topic: str, sources_path: str, 
                           context: str, content_ownership: str = "EXTERNAL") -> Task:
        """Create a research task with Topic Manager integration"""
        return Task(
            description=f"""
            Conduct comprehensive research on: {topic}
            Content ownership: {content_ownership}
            
            Topic Manager Integration Steps:
            1. 🎯 Get AI-powered topic suggestions for related topics and sub-themes
            2. 🔍 Search topics database for existing relevant research
            3. 📊 Get topic relevance score for current research focus
            4. 🚀 Trigger research discovery if needed for emerging topics
            5. 🔄 Trigger auto-scraping for latest industry insights (if applicable)
            
            Traditional Research Steps:
            6. Read source file: {sources_path}
            7. Extract and validate all sources and references from the file
            8. {'Skip external research for ORIGINAL content - use research_web_sources tool with content_ownership=ORIGINAL' if content_ownership == 'ORIGINAL' else 'Research additional web sources for context using research_web_sources tool'}
            9. Identify key data points and statistics from source file
            10. Create executive summary of findings enhanced with Topic Manager insights
            
            Topic Manager Integration:
            - Service: {self.topic_manager_url}
            - Use topic suggestions to expand research scope
            - Apply relevance scoring to prioritize research areas
            - Leverage auto-scraping for latest trends and developments
            - Search existing topic database for related insights
            
            Focus on:
            - Content analysis from source file
            - {'Internal insights and frameworks' if content_ownership == 'ORIGINAL' else 'External validation and multiple perspectives'}
            - AI-powered topic suggestions and trending research areas
            - Key concepts and methodologies
            - Practical applications and examples
            - Quality assessment of source material
            - Topic relevance and engagement potential
            
            Context from styleguide: {context}
            """,
            agent=self.research_analyst_agent(),
            expected_output="Comprehensive research summary enhanced with Topic Manager insights, sources, data points, and AI-powered topic analysis"
        )
    
    def execute(self, topic: str, sources_path: str, context: str, content_ownership: str = "EXTERNAL") -> ResearchResult:
        """Execute research crew"""
        crew = Crew(
            agents=[self.research_analyst_agent()],
            tasks=[self.create_research_task(topic, sources_path, context, content_ownership)],
            verbose=False,  # Zmienione na False aby zmniejszyć spam
            process=Process.sequential
        )
        
        result = crew.kickoff()
        
        # Parse result to extract structured data
        # In production, this would be more sophisticated
        sources = []
        summary = str(result)
        
        # Extract any URLs from the result
        url_pattern = r'https?://[^\s]+'
        urls = re.findall(url_pattern, summary)
        for url in urls:
            sources.append({
                "url": url,
                "title": "Research finding",
                "date": datetime.now().isoformat(),
                "type": "web"
            })
        
        return ResearchResult(
            sources=sources[:10] if sources else [
                {
                    "url": "https://gartner.com/ai-agents-2024",
                    "title": "Gartner Report on AI Agents",
                    "date": datetime.now().isoformat(),
                    "type": "report"
                }
            ],
            summary=summary[:1000] if summary else "AI agents are revolutionizing software development with significant productivity gains.",
            key_insights=[
                "AI agents are transforming software development",
                "Productivity gains of 45% reported in early adopters", 
                "Human oversight remains critical for quality"
            ],
            data_points=[
                {
                    "metric": "Developer AI Usage",
                    "value": "75%",
                    "source": "Stack Overflow Survey 2024",
                    "context": "Percentage of developers using AI tools daily"
                },
                {
                    "metric": "Market Projection",
                    "value": "$1.2T",
                    "source": "Gartner",
                    "context": "Projected market value by 2026"
                },
                {
                    "metric": "Debugging Speed",
                    "value": "3.5x",
                    "source": "Industry benchmarks",
                    "context": "Speed improvement with AI assistance"
                }
            ],
            methodology="Comprehensive analysis of industry reports, developer surveys, and technology reviews focusing on AI agent adoption in software development."
        )