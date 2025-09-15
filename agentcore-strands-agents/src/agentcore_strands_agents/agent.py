"""Agent configuration and creation logic with main application entry point."""

import json
import logging
from typing import List, Dict, Any, Optional

from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from bedrock_agentcore.memory import MemoryClient
# from bedrock_agentcore.memory.constants import StrategyType, DEFAULT_NAMESPACES

from strands import Agent, tool
from strands_tools import calculator

from .hooks.short_memory_hook import ShortMemoryHook
from .hooks.long_term_memory_hook import LongTermMemoryHook
# Import shared memory modules
from .hooks.memory import MemoryConfig, retrieve_memories_for_actor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

DEFAULT_ACTOR_ID = "my-user-id"
DEFAULT_SESSION_ID = "DEFAULT"

# Initialize memory configuration and client
memory_config = MemoryConfig()
memory_client = MemoryClient()

# Initialize the Bedrock AgentCore app
app = BedrockAgentCoreApp()



# Agent instance will be created lazily when needed
agent = None


@tool
def retrieve_memories(query: str) -> List[Dict[str, Any]]:
    """Retrieve memories from the memory client using AWS CLI-like syntax.
    Args:
        query: The search query to find relevant memories.
    Returns:
        A list of memories retrieved from the memory client.
    """
    actor_id = agent.state.get("actor_id")
    return retrieve_memories_for_actor(
        memory_id=memory_config.memory_id,
        actor_id=actor_id,
        search_query=query,
        memory_client=memory_client
    )


def create_agent(actor_id: str, session_id: str) -> Agent:
    """Create and configure the agent with hooks and tools."""
    logger.info("Creating agent with memory hook and calculator tool")
    logger.debug("Agent state - actor_id: %s, session_id: %s", actor_id, session_id)
    
    agent = Agent(
        hooks=[
            ShortMemoryHook(memory_id=memory_config.memory_id),
            LongTermMemoryHook(memory_id=memory_config.memory_id)
        ],
        tools=[calculator, retrieve_memories], 
        state={"actor_id": actor_id, "session_id": session_id}
    )
    
    logger.info("Agent created successfully")
    return agent


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> Dict[str, Any]:
    """AI agent entrypoint"""   
    global agent
    
    # Extract parameters with context priority for session_id
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = context.session_id if context and context.session_id else payload.get("session_id", DEFAULT_SESSION_ID)
    
    if agent is None:
        agent = create_agent(actor_id, session_id)
    
    logger.info("Received invocation request")
    logger.debug("Payload: %s", json.dumps(payload, indent=2))
    logger.debug("Context: %s", json.dumps(context, indent=2, default=str) if context else "No context")
    logger.info(f"Processing request for actor_id: {actor_id}, session_id: {session_id}")
    
    user_message = payload.get("prompt", "Explain what you can do for me.")
    logger.debug("User message: %s", user_message)
    
    try:
        result = agent(user_message)
        logger.info("Agent response generated successfully")
        return {"result": result.message}
    except Exception as e:
        logger.error("Error during agent invocation: %s", e, exc_info=True)
        return {"error": "An error occurred while processing your request"}


def main():
    """Main entry point for the application."""
    app.run()


if __name__ == "__main__":
    main()
