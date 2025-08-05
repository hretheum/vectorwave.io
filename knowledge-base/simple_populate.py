#\!/usr/bin/env python3
"""
Simple script to populate Knowledge Base with markdown documents
"""

import asyncio
import os
import sys
from pathlib import Path
import uuid
from typing import List

# Configuration
KNOWLEDGE_BASE_HOST = os.getenv("CHROMA_HOST", "chroma")
KNOWLEDGE_BASE_PORT = int(os.getenv("CHROMA_PORT", "8000"))
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379")

# Simple document class
class SimpleDocument:
    def __init__(self, id: str, content: str, metadata: dict):
        self.id = id
        self.content = content
        self.metadata = metadata

async def populate_kb():
    """Populate knowledge base with sample documents"""
    try:
        # Import inside function to handle missing modules gracefully
        sys.path.append('/app')
        from src.knowledge_engine import CrewAIKnowledgeBase
        from src.cache import CacheConfig
        from src.storage import ChromaDocument
        
        print("Initializing Knowledge Base...")
        
        # Create cache config
        cache_config = CacheConfig(
            memory_enabled=True,
            redis_enabled=True,
            memory_ttl=300,
            redis_ttl=3600
        )
        
        # Initialize knowledge base
        kb = CrewAIKnowledgeBase(
            cache_config=cache_config,
            chroma_host=KNOWLEDGE_BASE_HOST,
            chroma_port=KNOWLEDGE_BASE_PORT,
            redis_url=REDIS_URL
        )
        
        await kb.initialize()
        print("Knowledge Base initialized successfully\!")
        
        # Read documents from docs directory
        docs_path = Path("/app/docs")
        documents = []
        
        if docs_path.exists():
            for md_file in docs_path.rglob("*.md"):
                try:
                    content = md_file.read_text(encoding='utf-8')
                    if content.strip():
                        # Extract category from path
                        category = md_file.parent.name
                        
                        doc = ChromaDocument(
                            id=str(uuid.uuid4()),
                            content=content,
                            metadata={
                                "title": md_file.stem.replace('-', ' ').title(),
                                "file_path": str(md_file),
                                "category": category,
                                "source_type": "markdown",
                                "vector_wave_specific": "vector-wave" in str(md_file)
                            }
                        )
                        documents.append(doc)
                        print(f"Loaded: {md_file.name}")
                        
                except Exception as e:
                    print(f"Error loading {md_file}: {e}")
        
        if documents:
            print(f"\nAdding {len(documents)} documents to vector store...")
            
            # Add documents to vector store
            for doc in documents:
                try:
                    await kb.vector_store.add_document(doc)
                    print(f"Added: {doc.metadata.get('title', 'Unknown')}")
                except Exception as e:
                    print(f"Error adding document: {e}")
                    
            print(f"\nSuccessfully populated Knowledge Base with {len(documents)} documents\!")
            
            # Test search
            print("\nTesting search functionality...")
            from src.knowledge_engine import QueryParams, QuerySource
            
            test_query = QueryParams(
                query="What is CrewAI?",
                limit=3,
                sources=[QuerySource.VECTOR]
            )
            
            results = await kb.query(test_query)
            print(f"Test query returned {len(results.results)} results")
            
            for result in results.results:
                print(f"- {result.title} (score: {result.score:.3f})")
                
        else:
            print("No markdown documents found in /app/docs")
            
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(populate_kb())
EOF < /dev/null