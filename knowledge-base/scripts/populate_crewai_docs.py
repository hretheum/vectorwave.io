#!/usr/bin/env python3
"""
Script to populate Knowledge Base with CrewAI documentation
"""

import os
import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any
import frontmatter
import structlog

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from src.knowledge_engine import CrewAIKnowledgeBase
from src.storage import ChromaDocument

logger = structlog.get_logger(__name__)

class CrewAIDocsLoader:
    """Loads CrewAI documentation into Knowledge Base"""
    
    def __init__(self, docs_path: Path, knowledge_base: CrewAIKnowledgeBase):
        self.docs_path = docs_path
        self.kb = knowledge_base
        self.documents: List[ChromaDocument] = []
        
    def process_file(self, file_path: Path) -> ChromaDocument:
        """Process a single documentation file"""
        try:
            # Read file content
            content = file_path.read_text(encoding='utf-8')
            
            # Try to parse frontmatter
            if file_path.suffix == '.mdx':
                post = frontmatter.loads(content)
                metadata = post.metadata
                content = post.content
            else:
                metadata = {}
            
            # Generate relative path for ID
            relative_path = file_path.relative_to(self.docs_path)
            doc_id = str(relative_path).replace(os.sep, '/').replace('.mdx', '').replace('.md', '')
            
            # Extract title from metadata or first heading
            title = metadata.get('title', '')
            if not title:
                lines = content.split('\n')
                for line in lines:
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
                    'title': title,
                    'description': metadata.get('description', ''),
                    'section': str(relative_path.parts[0]) if relative_path.parts else 'root',
                    **metadata
                }
            )
            
            logger.info(f"Processed document", doc_id=doc_id, title=title)
            return doc
            
        except Exception as e:
            logger.error(f"Error processing file", path=str(file_path), error=str(e))
            raise
    
    def scan_directory(self, directory: Path) -> List[ChromaDocument]:
        """Recursively scan directory for documentation files"""
        documents = []
        
        for file_path in directory.rglob('*.mdx'):
            if not file_path.name.startswith('.'):
                doc = self.process_file(file_path)
                documents.append(doc)
                
        for file_path in directory.rglob('*.md'):
            if not file_path.name.startswith('.'):
                doc = self.process_file(file_path)
                documents.append(doc)
                
        return documents
    
    async def load_to_kb(self):
        """Load all documents to Knowledge Base"""
        logger.info("Starting CrewAI docs loading process")
        
        # Scan for documents
        self.documents = self.scan_directory(self.docs_path)
        logger.info(f"Found {len(self.documents)} documents to load")
        
        # Load documents in batches
        batch_size = 10
        for i in range(0, len(self.documents), batch_size):
            batch = self.documents[i:i+batch_size]
            
            # Add documents to KB
            add_tasks = []
            for doc in batch:
                add_tasks.append(self.kb.add_document(doc))
            
            # Wait for batch to complete
            await asyncio.gather(*add_tasks)
            logger.info(f"Loaded batch {i//batch_size + 1}/{(len(self.documents) + batch_size - 1)//batch_size}")
        
        logger.info("Completed loading CrewAI documentation")
        
        # Print statistics
        stats = await self.kb.get_statistics()
        logger.info("Knowledge Base statistics", stats=stats)


async def main():
    """Main entry point"""
    # Paths
    current_dir = Path(__file__).parent.parent
    docs_path = current_dir / "data" / "crewai-docs" / "docs" / "en"
    
    if not docs_path.exists():
        logger.error(f"Docs path not found: {docs_path}")
        sys.exit(1)
    
    # Initialize Knowledge Base
    kb = CrewAIKnowledgeBase()
    
    # Initialize loader
    loader = CrewAIDocsLoader(docs_path, kb)
    
    # Load documents
    await loader.load_to_kb()
    
    # Test query
    logger.info("Testing knowledge base with sample query")
    result = await kb.query("how to create a crew in crewai")
    logger.info("Query result", result=result)


if __name__ == "__main__":
    asyncio.run(main())