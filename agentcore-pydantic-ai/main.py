import json
import logging
from typing import Dict, Any, Optional, List

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


def convert_pydantic_messages_for_storage(messages: List[Any]) -> List[tuple]:
    """Convert Pydantic AI message objects to memory storage format."""
    messages_to_store = []
    
    for msg in messages:
        try:
            # Handle Pydantic AI ModelMessage objects
            if hasattr(msg, 'parts') and msg.parts:
                for part in msg.parts:
                    if hasattr(part, 'content'):
                        content = part.content
                        
                        if hasattr(msg, 'kind'):
                            if msg.kind == 'request':
                                if hasattr(part, 'part_kind') and part.part_kind == 'user-prompt':
                                    role = 'USER'
                                elif hasattr(part, 'part_kind') and part.part_kind == 'system-prompt':
                                    role = 'SYSTEM'
                                else:
                                    role = 'USER'
                            elif msg.kind == 'response':
                                role = 'ASSISTANT'
                            else:
                                role = 'ASSISTANT'
                        else:
                            role = 'ASSISTANT' if 'Response' in type(msg).__name__ else 'USER'
                        
                        message_tuple = (
                            json.dumps(content) if not isinstance(content, str) else content, 
                            role
                        )
                        messages_to_store.append(message_tuple)
            
            # Handle simple string messages
            elif isinstance(msg, str):
                messages_to_store.append((msg, 'USER'))
            
            # Handle dict messages
            elif isinstance(msg, dict):
                content = msg.get('content', str(msg))
                role = msg.get('role', 'USER')
                messages_to_store.append((content, role))
                        
        except Exception as e:
            logger.warning(f"Failed to convert message for storage: {e}")
            continue
    
    return messages_to_store


def store_pydantic_messages_in_memory(
    new_messages: List[Any],
    memory_manager: AgentMemoryManager,
    actor_id: str,
    session_id: str
) -> bool:
    """
    Store new Pydantic AI messages in memory using store_conversation.
    
    Args:
        new_messages: List of new Pydantic AI message objects to store
        memory_manager: The memory manager instance
        actor_id: Actor identifier
        session_id: Session identifier
        
    Returns:
        True if messages were stored successfully, False otherwise
    """
    if not new_messages:
        return True
    
    logger.debug(f"Storing {len(new_messages)} new messages for {actor_id}:{session_id}")
    
    try:
        messages_to_store = convert_pydantic_messages_for_storage(new_messages)
        
        if messages_to_store:
            # Store each message pair using store_conversation
            for i in range(0, len(messages_to_store), 2):
                if i + 1 < len(messages_to_store):
                    # We have a pair of messages
                    user_msg = messages_to_store[i]
                    assistant_msg = messages_to_store[i + 1]
                    
                    # Extract content from tuples
                    user_content = user_msg[0] if isinstance(user_msg, tuple) else str(user_msg)
                    assistant_content = assistant_msg[0] if isinstance(assistant_msg, tuple) else str(assistant_msg)
                    
                    # Store the conversation pair
                    memory_manager.store_conversation(
                        user_input=user_content,
                        response=assistant_content,
                        actor_id=actor_id,
                        session_id=session_id
                    )
                else:
                    # Single message (likely a user message)
                    single_msg = messages_to_store[i]
                    content = single_msg[0] if isinstance(single_msg, tuple) else str(single_msg)
                    
                    # Store as a user message with empty response
                    memory_manager.store_conversation(
                        user_input=content,
                        response="",
                        actor_id=actor_id,
                        session_id=session_id
                    )
            
            logger.info(f"Successfully stored {len(messages_to_store)} messages in memory")
            return True
        else:
            logger.warning("No messages were converted for storage")
            return False
            
    except Exception as e:
        logger.error(f"Failed to store messages in memory: {e}", exc_info=True)
        return False


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> str:
    """Main entrypoint with refactored memory functionality using AgentMemoryManager."""
    

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
        store_pydantic_messages_in_memory(new_messages, memory_manager, actor_id, session_id)
    
    # Update session message history (keep last NUM_MESSAGES)
    session_message_history[session_id] = all_messages_after[-NUM_MESSAGES:]

    return result.output


if __name__ == "__main__":
    app.run()