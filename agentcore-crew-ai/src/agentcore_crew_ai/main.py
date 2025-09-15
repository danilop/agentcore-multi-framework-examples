#!/usr/bin/env python
import sys
import warnings
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

from agentcore_crew_ai.crew import AgentcoreCrewAi
from .memory import MemoryManager as CrewMemoryManager

from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext

# Import shared memory utilities
from .memory import retrieve_memories_for_actor

warnings.filterwarnings("ignore", category=SyntaxWarning, module="pysbd")

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuration constants
DEFAULT_ACTOR_ID = "my-user-id"
DEFAULT_SESSION_ID = "DEFAULT"

# Initialize components
app = BedrockAgentCoreApp()

memory_manager = CrewMemoryManager(
    default_actor_id=DEFAULT_ACTOR_ID,
    default_session_id=DEFAULT_SESSION_ID,
    logger=logger
)


# Legacy function for backward compatibility (if needed by crew.py)
def retrieve_memories(query: str) -> List[Dict[str, Any]]:
    """Retrieve memories from the memory client using shared function.
    Args:
        query: The query to retrieve memories from the memory client.
    Returns:
        A list of memories retrieved from the memory client.
    """
    return retrieve_memories_for_actor(
        memory_id=memory_manager.memory_config.memory_id,
        actor_id=memory_manager.default_actor_id,
        search_query=query,
        memory_client=memory_manager.memory_client
    )


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> str:
    """
    Invoke the crew with enhanced memory functionality.
    """
    logger.info("CrewAI invocation started")
    
    user_input = payload.get("prompt")
    if not user_input:
        logger.warning("No prompt provided in payload")
        return "Error: No prompt provided"
    
    # Get actor_id and session_id from payload or context
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = context.session_id if context and context.session_id else payload.get("session_id", DEFAULT_SESSION_ID)
    
    logger.info(f"Processing request for actor_id: {actor_id}, session_id: {session_id}")
    
    # Enhance input with relevant memories using memory manager
    memory_context = memory_manager.get_memory_context(
        user_input=user_input,
        actor_id=actor_id,
        session_id=session_id
    )
    enhanced_input = f"{memory_context}\n\n{user_input}" if memory_context else user_input
    
    # Prepare inputs for crew
    inputs = {
        'topic': enhanced_input,
        'current_year': str(datetime.now().year)
    }

    try:
        # Run the crew
        logger.info("Starting crew execution")
        result = AgentcoreCrewAi().crew().kickoff(inputs=inputs)
        logger.info("Crew execution completed successfully")
        
        # Store the conversation in memory using memory manager
        memory_manager.store_conversation(
            user_input=user_input,
            response=result.raw,
            actor_id=actor_id,
            session_id=session_id
        )
        
        # Return the result
        return result.raw
        
    except Exception as e:
        logger.error(f"Error during crew execution: {e}", exc_info=True)
        return f"Error: An error occurred while processing your request: {str(e)}"


def run():
    """
    Run the crew.
    """
    inputs = {
        'topic': 'AI LLMs',
        'current_year': str(datetime.now().year)
    }
    
    try:
        AgentcoreCrewAi().crew().kickoff(inputs=inputs)
    except Exception as e:
        raise Exception(f"An error occurred while running the crew: {e}")


def train():
    """
    Train the crew for a given number of iterations.
    """
    inputs = {
        "topic": "AI LLMs",
        'current_year': str(datetime.now().year)
    }
    try:
        AgentcoreCrewAi().crew().train(n_iterations=int(sys.argv[1]), filename=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while training the crew: {e}")


def replay():
    """
    Replay the crew execution from a specific task.
    """
    try:
        AgentcoreCrewAi().crew().replay(task_id=sys.argv[1])

    except Exception as e:
        raise Exception(f"An error occurred while replaying the crew: {e}")


def test():
    """
    Test the crew execution and returns the results.
    """
    inputs = {
        "topic": "AI LLMs",
        "current_year": str(datetime.now().year)
    }
    
    try:
        AgentcoreCrewAi().crew().test(n_iterations=int(sys.argv[1]), eval_llm=sys.argv[2], inputs=inputs)

    except Exception as e:
        raise Exception(f"An error occurred while testing the crew: {e}")


if __name__ == "__main__":
    app.run()