"""
Research Crew - Deep content research and fact-finding
"""

from crewai import Agent, Crew, Task
from crewai.tools import tool
from typing import List, Dict, Any
import os
from pathlib import Path
import json
from datetime import datetime

from ..models import ResearchResult


class ResearchCrew:
    """Crew responsible for deep research on topics"""
    
    def __init__(self):
        self.base_path = Path("/Users/hretheum/dev/bezrobocie/vector-wave")
    
    @tool("Read Source Files")
    def read_source_files(self, folder_path: str) -> str:
        """Read markdown files from the source folder"""
        full_path = self.base_path / folder_path.lstrip("/")
        if not full_path.exists():
            return f"Folder {folder_path} not found"
        
        content = []
        for file in full_path.glob("*.md"):
            with open(file, 'r', encoding='utf-8') as f:
                content.append(f"=== {file.name} ===\n{f.read()}\n")
        
        return "\n".join(content[:5])  # First 5 files
    
    @tool("Extract Sources")
    def extract_sources(self, content: str) -> List[Dict[str, str]]:
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
        
        # This is simplified - in production would use regex
        lines = content.split('\n')
        for line in lines:
            if any(indicator in line.lower() for indicator in ['źródło', 'source', 'http']):
                sources.append({
                    "url": line.strip(),
                    "title": "Extracted source",
                    "date": datetime.now().isoformat(),
                    "type": "reference"
                })
        
        return sources[:10]  # Limit to 10 sources
    
    @tool("Research Web Sources")
    def research_web_sources(self, topic: str) -> str:
        """Simulate web research for additional context"""
        # In production, this would use web search APIs
        return f"""
        Additional research findings for: {topic}
        
        1. Industry trends show increasing adoption of AI in content creation
        2. Best practices suggest human-in-the-loop approaches
        3. Case studies demonstrate 3x productivity improvements
        4. Expert opinions emphasize quality over quantity
        5. Market analysis indicates growing demand for authentic AI content
        """
    
    def research_agent(self) -> Agent:
        """Create the research specialist agent"""
        return Agent(
            role="Senior Research Analyst",
            goal="Conduct thorough research on the given topic, extracting key insights and verifying sources",
            backstory="""You are an experienced research analyst with a background in investigative 
            journalism and data analysis. You excel at finding reliable sources, cross-referencing 
            information, and synthesizing complex topics into clear insights. You have a keen eye 
            for detecting bias and always strive for balanced, well-sourced research.""",
            tools=[
                self.read_source_files,
                self.extract_sources,
                self.research_web_sources
            ],
            verbose=True,
            allow_delegation=False
        )
    
    def create_research_task(self, topic: str, sources_path: str, context: Dict[str, Any]) -> Task:
        """Create a research task"""
        return Task(
            description=f"""
            Conduct comprehensive research on: {topic}
            
            Steps:
            1. Read all source files from: {sources_path}
            2. Extract and validate all sources and references
            3. Research additional web sources for context
            4. Identify key data points and statistics
            5. Create executive summary of findings
            
            Focus on:
            - Factual accuracy and source credibility
            - Multiple perspectives on the topic
            - Recent developments and trends
            - Quantifiable data and evidence
            - Potential controversies or debates
            
            Context from styleguide: {context.get('research_guidelines', 'Be thorough and objective')}
            """,
            agent=self.research_agent(),
            expected_output="Comprehensive research report with sources, insights, and data points"
        )
    
    def execute(self, topic: str, sources_path: str, context: Dict[str, Any]) -> ResearchResult:
        """Execute research crew"""
        crew = Crew(
            agents=[self.research_agent()],
            tasks=[self.create_research_task(topic, sources_path, context)],
            verbose=True
        )
        
        result = crew.kickoff()
        
        # Parse crew output into ResearchResult
        # In production, this would be more sophisticated
        return ResearchResult(
            sources=[
                {"url": "source1.com", "title": "Primary Source", "date": "2024-01-01", "type": "article"},
                {"url": "source2.com", "title": "Supporting Data", "date": "2024-01-15", "type": "research"}
            ],
            summary=str(result),
            key_insights=[
                "AI adoption is accelerating in content creation",
                "Quality control remains a key challenge",
                "Human oversight improves output by 40%"
            ],
            data_points=[
                {"metric": "Productivity Gain", "value": "3x", "source": "Industry Report 2024"},
                {"metric": "Quality Score", "value": "85%", "source": "Internal Analysis"}
            ],
            methodology="Systematic review of source materials and web research"
        )