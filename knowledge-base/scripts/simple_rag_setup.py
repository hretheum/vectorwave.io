#!/usr/bin/env python3
"""
Simple RAG setup using our existing Knowledge Base
"""

import asyncio
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.knowledge_engine import CrewAIKnowledgeBase
from src.storage import ChromaDocument
import structlog

logger = structlog.get_logger(__name__)


class SimpleRAGTool:
    """Simple RAG tool using our Knowledge Base"""
    
    def __init__(self, kb: CrewAIKnowledgeBase):
        self.kb = kb
        
    def _run(self, query: str) -> str:
        """Run a query (sync wrapper for async query)"""
        return asyncio.run(self.run(query))
    
    async def run(self, query: str) -> str:
        """Run a query asynchronously"""
        response = await self.kb.query(query)
        
        if not response.results:
            return f"No information found for: {query}"
        
        # Format results
        result_text = []
        for i, result in enumerate(response.results[:3]):  # Top 3 results
            result_text.append(f"**{result.title}**\n{result.content}\n")
        
        return "\n\n".join(result_text)


async def load_documentation():
    """Load CrewAI documentation into Knowledge Base"""
    kb = CrewAIKnowledgeBase()
    docs_path = Path(__file__).parent.parent / "data" / "crewai-docs" / "docs" / "en"
    
    if not docs_path.exists():
        logger.error(f"Documentation path not found: {docs_path}")
        return None
    
    logger.info(f"Loading documentation from: {docs_path}")
    
    # Process all MDX files
    docs_loaded = 0
    for mdx_file in docs_path.rglob("*.mdx"):
        try:
            content = mdx_file.read_text(encoding='utf-8')
            relative_path = mdx_file.relative_to(docs_path)
            doc_id = str(relative_path).replace(os.sep, '/').replace('.mdx', '')
            
            # Extract title from content
            title = doc_id.replace('/', ' > ').title()
            for line in content.split('\n'):
                if line.startswith('# '):
                    title = line[2:].strip()
                    break
            
            # Create document
            doc = ChromaDocument(
                id=doc_id,
                content=content,
                metadata={
                    'source': 'crewai-docs',
                    'type': 'documentation',
                    'path': str(relative_path),
                    'title': title
                }
            )
            
            # Add to KB
            await kb.add_document(doc)
            docs_loaded += 1
            
            if docs_loaded % 10 == 0:
                logger.info(f"Loaded {docs_loaded} documents...")
                
        except Exception as e:
            logger.error(f"Error loading {mdx_file}: {e}")
    
    logger.info(f"Total documents loaded: {docs_loaded}")
    
    # Create RAG tool
    rag_tool = SimpleRAGTool(kb)
    
    # Test query
    test_result = await rag_tool.run("How do I create a crew in CrewAI?")
    logger.info(f"Test query result:\n{test_result[:500]}...")
    
    return rag_tool, kb


async def main():
    """Main entry point"""
    # Configure logging
    structlog.configure(
        processors=[
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Load documentation and create RAG tool
    rag_tool, kb = await load_documentation()
    
    if rag_tool:
        logger.info("Simple RAG tool setup complete!")
        
        # Interactive test
        while True:
            query = input("\nEnter a query (or 'quit' to exit): ")
            if query.lower() == 'quit':
                break
            
            result = await rag_tool.run(query)
            print(f"\nResult:\n{result}")
    else:
        logger.error("Failed to setup RAG tool")


if __name__ == "__main__":
    asyncio.run(main())