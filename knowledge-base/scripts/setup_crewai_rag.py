#!/usr/bin/env python3
"""
Setup CrewAI RAGTool with documentation
"""

import os
from pathlib import Path
from crewai_tools import RagTool
import structlog

logger = structlog.get_logger(__name__)

def setup_crewai_knowledge_base():
    """Setup RAGTool with CrewAI documentation"""
    
    # Initialize RAGTool
    rag_tool = RagTool()
    
    # Path to documentation
    docs_path = Path(__file__).parent.parent / "data" / "crewai-docs" / "docs" / "en"
    
    if not docs_path.exists():
        logger.error(f"Documentation path not found: {docs_path}")
        return None
    
    logger.info(f"Setting up RAGTool with documentation from: {docs_path}")
    
    # Add entire documentation directory
    try:
        # Add the documentation directory
        rag_tool.add(
            data_type="dir",
            path=str(docs_path)
        )
        logger.info("Successfully added documentation directory to RAGTool")
        
        # Test with a sample query
        result = rag_tool._run("How do I create a crew in CrewAI?")
        logger.info(f"Test query result: {result[:200]}...")
        
        return rag_tool
        
    except Exception as e:
        logger.error(f"Failed to setup RAGTool: {e}")
        return None


def main():
    """Main entry point"""
    # Configure logging
    structlog.configure(
        processors=[
            structlog.dev.ConsoleRenderer()
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Setup knowledge base
    rag_tool = setup_crewai_knowledge_base()
    
    if rag_tool:
        logger.info("CrewAI RAGTool setup complete!")
        
        # Save the tool configuration for later use
        import pickle
        with open("crewai_rag_tool.pkl", "wb") as f:
            pickle.dump(rag_tool, f)
        logger.info("RAGTool saved to crewai_rag_tool.pkl")
    else:
        logger.error("Failed to setup RAGTool")


if __name__ == "__main__":
    main()