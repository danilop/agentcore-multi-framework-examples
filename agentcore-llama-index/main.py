#!/usr/bin/env python
"""
LlamaIndex Agent with AgentCore integration.

This module provides both interactive conversational capabilities and single invocation
support using LlamaIndex agents with AgentCore memory management.
"""

import json
import logging
from typing import Dict, Any, Optional

from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from llama_index.core.agent.workflow import FunctionAgent
from llama_index.llms.bedrock_converse import BedrockConverse
from llama_index.embeddings.bedrock import BedrockEmbedding
from llama_index.core import Settings

from memory import MemoryManager as LlamaIndexMemoryManager
from tools import create_llamaindex_tools, get_system_prompt

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration constants
DEFAULT_ACTOR_ID = "my-user-id"
DEFAULT_SESSION_ID = "DEFAULT"
MODEL_ID = "us.amazon.nova-pro-v1:0"
EMBEDDING_MODEL_ID = "amazon.titan-embed-text-v2:0"

# Initialize components
app = BedrockAgentCoreApp()

# Global agent instance (will be initialized lazily)
agent_instance = None
memory_manager = None


def initialize_llamaindex_settings():
    """Initialize LlamaIndex global settings."""
    try:
        # Configure LLM
        llm = BedrockConverse(
            model=MODEL_ID,
        )
        
        # Configure embeddings
        embed_model = BedrockEmbedding(
            model_name=EMBEDDING_MODEL_ID,
            region_name="us-east-1"
        )
        
        # Set global settings
        Settings.llm = llm
        Settings.embed_model = embed_model
        Settings.chunk_size = 512
        Settings.chunk_overlap = 50
        
        logger.info("LlamaIndex settings initialized successfully")
        return llm
        
    except Exception as e:
        logger.error(f"Failed to initialize LlamaIndex settings: {e}")
        raise


def create_agent(actor_id: str = DEFAULT_ACTOR_ID, session_id: str = DEFAULT_SESSION_ID) -> FunctionAgent:
    """Create and configure the LlamaIndex FunctionAgent.
    
    Args:
        actor_id: Actor ID for memory management
        session_id: Session ID for memory management
        
    Returns:
        Configured FunctionAgent instance
    """
    global memory_manager
    
    logger.info(f"Creating LlamaIndex agent (actor: {actor_id}, session: {session_id})")
    
    # Initialize LlamaIndex settings
    llm = initialize_llamaindex_settings()
    
    # Initialize memory manager
    memory_manager = LlamaIndexMemoryManager(
        default_actor_id=actor_id,
        default_session_id=session_id,
        logger=logger
    )
    
    # Create tools
    tools = create_llamaindex_tools(memory_manager=memory_manager)
    
    # Get system prompt
    system_prompt = get_system_prompt()
    
    # Create FunctionAgent
    agent = FunctionAgent(
        tools=tools,
        llm=llm,
        system_prompt=system_prompt
    )
    
    logger.info("LlamaIndex FunctionAgent created successfully")
    return agent


@app.entrypoint
async def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> str:
    """
    AgentCore entrypoint for LlamaIndex agent invocation.
    
    Supports both single invocation and conversational interactions.
    """
    global agent_instance
    
    logger.info("LlamaIndex agent invocation started")
    
    # Debug logging
    logger.debug(f"Payload: {json.dumps(payload, indent=2, default=str)}")
    logger.debug(f"Context: {json.dumps(context or {}, indent=2, default=str)}")
    
    # Extract parameters
    user_input = payload.get("prompt", "Hello! What can you help me with?")
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = context.session_id if context and context.session_id else payload.get("session_id", DEFAULT_SESSION_ID)
    
    logger.info(f"Processing request for actor_id: {actor_id}, session_id: {session_id}")
    
    try:
        # Initialize agent if not already done
        if agent_instance is None:
            agent_instance = create_agent(actor_id, session_id)
        
        # Enhance the user input with memory context if available
        if memory_manager:
            memory_context = memory_manager.get_memory_context(
                user_input=user_input,
                actor_id=actor_id,
                session_id=session_id
            )
            
            # Update agent's system prompt if enhanced
            if memory_context:
                enhanced_prompt = f"{get_system_prompt()}\n\nRelevant context from previous interactions:\n{memory_context}\nPlease use this context to provide more personalized and informed responses."
                logger.info("Using enhanced prompt with memory context")
                agent_instance.update_prompts({"system_prompt": enhanced_prompt})
        
        # Run the agent
        logger.info("Running LlamaIndex agent")
        response = await agent_instance.run(user_input)
        response_text = str(response)
        
        logger.info("Agent execution completed successfully")
        
        # Store conversation in memory
        if memory_manager:
            memory_manager.store_conversation(
                user_input=user_input,
                response=response_text,
                actor_id=actor_id,
                session_id=session_id
            )
        
        return response_text
        
    except Exception as e:
        logger.error(f"Error during agent execution: {e}", exc_info=True)
        return f"Error: An error occurred while processing your request: {str(e)}"


if __name__ == "__main__":
    app.run()
