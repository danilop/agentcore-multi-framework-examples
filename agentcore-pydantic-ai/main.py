import json
import logging
from typing import Dict, Any, Optional

from pydantic_ai import Agent
from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext
from memory import MemoryManager as AgentMemoryManager

# Configure logger for this module
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuration constants
MODEL = 'bedrock:us.amazon.nova-premier-v1:0'
NUM_MESSAGES = 30
DEFAULT_ACTOR_ID = "my-user-id"
DEFAULT_SESSION_ID = "DEFAULT"

# Initialize components
memory_manager = AgentMemoryManager(
    default_actor_id=DEFAULT_ACTOR_ID,
    default_session_id=DEFAULT_SESSION_ID,
    logger=logger
)

app = BedrockAgentCoreApp()

# Session state tracking (minimal global state)  
session_message_history = {}  # Dict[session_id, List[ModelMessage]]


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> str:
    """Main entrypoint with refactored memory functionality using AgentMemoryManager."""
    
    print("Payload:")
    print(json.dumps(payload, indent=2, default=str))
    print("Context:")
    print(json.dumps(context, indent=2, default=str))

    prompt = payload.get('prompt')
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    
    # Get session_id from context (AgentCore automatically provides this)
    session_id = context.session_id if context and context.session_id else payload.get("session_id", DEFAULT_SESSION_ID)
    logger.info(f"Using session_id from context: {session_id} (type: {type(session_id)})")
    logger.info(f"Context session_id: {context.session_id if context else 'No context'}")

    # Get or initialize message history for this session
    if session_id not in session_message_history:
        session_message_history[session_id] = []
    
    current_message_history = session_message_history[session_id]
    previous_message_count = len(current_message_history)

    # Get memory context to add to user prompt
    memory_context = memory_manager.get_memory_context(
        user_input=prompt or "",
        actor_id=actor_id,
        session_id=session_id
    )
    
    # Create enhanced user prompt with memory context
    enhanced_prompt = prompt or "Hello"
    if memory_context:
        enhanced_prompt = f"{memory_context}\n\nUser: {enhanced_prompt}"
        logger.info("Added memory context to user prompt")
    
    # Create agent with base instructions
    agent = Agent(MODEL, instructions='Be concise, reply with one sentence.')
    
    # Run the agent with enhanced prompt
    result = agent.run_sync(enhanced_prompt, message_history=current_message_history)

    # Get all messages after the run
    all_messages_after = result.all_messages()
    
    # Detect and store new messages
    new_messages = all_messages_after[previous_message_count:]
    if new_messages:
        logger.info(f"Storing {len(new_messages)} new messages in memory")
        memory_manager.store_new_messages(new_messages, actor_id, session_id)
    
    # Update session message history (keep last NUM_MESSAGES)
    session_message_history[session_id] = all_messages_after[-NUM_MESSAGES:]

    return result.output


if __name__ == "__main__":
    app.run()