import logging
from strands.hooks import HookProvider, HookRegistry, BeforeInvocationEvent
from bedrock_agentcore.memory import MemoryClient

# Import local memory modules
from .memory import MemoryConfig, retrieve_memories_for_actor, format_memory_context
            
# Configure logger for this module
logger = logging.getLogger(__name__)


class LongTermMemoryHook(HookProvider):
    """Hook to retrieve and inject long-term memory context before model invocation."""

    def __init__(self, memory_id: str):
        """Initialize the LongTermMemoryHook with the memory ID."""
        self.memory_id = memory_id
        self.memory_client = MemoryClient()
        self.memory_config = MemoryConfig()

    def register_hooks(self, registry: HookRegistry) -> None:
        """Register the hook to listen for BeforeInvocationEvent."""
        registry.add_callback(BeforeInvocationEvent, self.on_before_invocation)

    def on_before_invocation(self, event: BeforeInvocationEvent) -> None:
        """Retrieve long-term memory and add context before model invocation."""
        logger.info(f"Before invocation: {event.agent.name}")
        
        # Get the current user message (last message in the conversation)
        if not event.agent.messages:
            logger.debug("No messages found, skipping long-term memory retrieval")
            return
            
        # Get the last user message as the query
        last_message = event.agent.messages[-1]
        if last_message.get("role") != "USER":
            logger.debug("Last message is not from user, skipping long-term memory retrieval")
            return
            
        user_query = last_message.get("content", "")
        if not user_query:
            logger.debug("No user query content found, skipping long-term memory retrieval")
            return

        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")

        logger.debug(f"Retrieving long-term memory for query: {user_query}, actor_id={actor_id}, session_id={session_id}")
        
        try:
            # Retrieve memories using AWS CLI-like syntax
            retrieved_memories = retrieve_memories_for_actor(
                memory_id=self.memory_config.memory_id,
                actor_id=actor_id,
                search_query=user_query,
                memory_client=self.memory_client
            )
            
            logger.debug("Retrieved %d memories from long-term memory", len(retrieved_memories))
            
            if retrieved_memories:
                # Format the retrieved memories as context
                memory_context = format_memory_context(retrieved_memories)
                
                # Add the memory context to the agent's system prompt
                if event.agent.system_prompt is None:
                    event.agent.system_prompt = ""
                
                # Add memory context to system prompt
                event.agent.system_prompt += f"\n\nRelevant long-term memory context:\n{memory_context}"
                
                logger.info(f"Added long-term memory context to agent system prompt ({len(retrieved_memories)} memories)")
            else:
                logger.info("No relevant long-term memories found for query")
                
        except Exception as e:
            logger.error(f"Failed to retrieve long-term memory: {e}", exc_info=True)

