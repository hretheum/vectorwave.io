#!/usr/bin/env python
import sys
import warnings
from datetime import datetime
import asyncio
import logging

from ai_kolegium_redakcyjne.crew import AiKolegiumRedakcyjne

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run():
    """
    Run the AI Kolegium Redakcyjne editorial crew.
    """
    inputs = {
        'categories': ['AI', 'Technology', 'Digital Culture', 'Startups'],
        'current_date': datetime.now().strftime("%Y-%m-%d"),
        'max_topics': 10,
        'controversy_threshold': 0.7
    }
    
    logger.info("🚀 Starting AI Kolegium Redakcyjne editorial pipeline...")
    logger.info(f"Focus categories: {inputs['categories']}")
    
    try:
        result = AiKolegiumRedakcyjne().crew().kickoff(inputs=inputs)
        logger.info("✅ Editorial pipeline completed successfully!")
        
        # Log summary
        if isinstance(result, dict):
            approved = len(result.get('approved_topics', []))
            rejected = len(result.get('rejected_topics', []))
            human_review = len(result.get('human_review_queue', []))
            
            logger.info(f"📊 Results: {approved} approved, {rejected} rejected, {human_review} for human review")
        
        return result
        
    except Exception as e:
        logger.error(f"❌ An error occurred while running the crew: {e}")
        raise

def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        'categories': ['AI', 'Technology'],
        'current_date': datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        n_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 5
        filename = sys.argv[2] if len(sys.argv) > 2 else "training_data.json"
        
        logger.info(f"🎯 Training crew for {n_iterations} iterations...")
        AiKolegiumRedakcyjne().crew().train(
            n_iterations=n_iterations, 
            filename=filename, 
            inputs=inputs
        )
        logger.info("✅ Training completed!")

    except Exception as e:
        logger.error(f"❌ An error occurred while training the crew: {e}")
        raise

def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        if len(sys.argv) < 2:
            logger.error("Please provide a task_id to replay")
            sys.exit(1)
            
        task_id = sys.argv[1]
        logger.info(f"🔄 Replaying crew from task: {task_id}")
        
        AiKolegiumRedakcyjne().crew().replay(task_id=task_id)
        logger.info("✅ Replay completed!")

    except Exception as e:
        logger.error(f"❌ An error occurred while replaying the crew: {e}")
        raise

def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        'categories': ['AI', 'Technology'],
        'current_date': datetime.now().strftime("%Y-%m-%d")
    }
    
    try:
        n_iterations = int(sys.argv[1]) if len(sys.argv) > 1 else 3
        eval_llm = sys.argv[2] if len(sys.argv) > 2 else "gpt-4"
        
        logger.info(f"🧪 Testing crew for {n_iterations} iterations...")
        results = AiKolegiumRedakcyjne().crew().test(
            n_iterations=n_iterations, 
            eval_llm=eval_llm, 
            inputs=inputs
        )
        
        logger.info("✅ Testing completed!")
        logger.info(f"📊 Test results: {results}")
        
        return results

    except Exception as e:
        logger.error(f"❌ An error occurred while testing the crew: {e}")
        raise

def run_with_server():
    """
    Run the crew with AG-UI server for real-time monitoring.
    """
    # TODO: Implement AG-UI server integration
    logger.info("🌐 Starting crew with AG-UI server...")
    logger.warning("AG-UI server integration not yet implemented")
    run()

if __name__ == "__main__":
    # Allow running with different modes
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "server":
            run_with_server()
        else:
            result = run()
            # Ensure we exit with 0 for success
            sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)