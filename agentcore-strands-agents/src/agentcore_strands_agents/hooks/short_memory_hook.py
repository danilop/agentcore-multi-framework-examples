import json
import logging
from bedrock_agentcore.memory import MemoryClient
from strands.hooks import HookProvider, HookRegistry, AgentInitializedEvent, MessageAddedEvent

# Configure logger for this module
logger = logging.getLogger(__name__)


class ShortMemoryHook(HookProvider):
    """Hook to store and retrieve conversation history from memory."""

    def __init__(self, memory_id: str):
        """Initialize the ShortMemoryHook with the memory ID."""
        self.memory_client = MemoryClient()
        self.memory_id = memory_id

    def register_hooks(self, registry: HookRegistry) -> None:
        registry.add_callback(AgentInitializedEvent, self.on_agent_initialized)
        registry.add_callback(MessageAddedEvent, self.on_message_added)

    def on_agent_initialized(self, event: AgentInitializedEvent) -> None:
        logger.info("Agent initialized: %s", event.agent.name)
        logger.debug("Agent messages: %s", event.agent.messages)

        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")

        logger.debug("Retrieving conversation history for actor_id=%s, session_id=%s", actor_id, session_id)
        
        try:
            conversations = self.memory_client.get_last_k_turns(
                memory_id=self.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=100,
            )
            logger.debug("Retrieved %d conversation turns from memory", len(conversations) if conversations else 0)
        except Exception as e:
            logger.warning("Failed to retrieve conversation history from memory: %s", e)
            conversations = None

        if conversations:
            # Format conversation history for context
            context_messages = []
            for turn in reversed(conversations):
                for message in turn:
                    role = message['role']
                    content = message['content']
                    context_messages.append(f"{role}: {content}")
            
            context = "\n".join(context_messages)
            
            # Add context to agent's system prompt.
            if event.agent.system_prompt is None:
                event.agent.system_prompt = ""
            event.agent.system_prompt += f"\n\nRecent conversation:\n{context}"
            
            logger.info(f"Added conversation context to agent system prompt ({len(context_messages)} messages: \n{context}")
        else:
            logger.info("No previous conversation history found")
            

    def on_message_added(self, event: MessageAddedEvent) -> None:
        logger.info("Message added to agent: %s", event.agent.name)
        logger.debug("Agent messages: %s", event.agent.messages)

        last_message = event.agent.messages[-1]
        last_message_tuple = (json.dumps(last_message["content"]), last_message["role"])


        actor_id = event.agent.state.get("actor_id")
        session_id = event.agent.state.get("session_id")

        logger.debug("Storing message in memory for actor_id=%s, session_id=%s", actor_id, session_id)

        try:
            self.memory_client.create_event(
                memory_id=self.memory_id, # This is the id from create_memory or list_memories
                actor_id=actor_id,  # This is the identifier of the actor, could be an agent or end-user.
                session_id=session_id, #Unique id for a particular request/conversation.
                messages=[last_message_tuple]
            )
            logger.info("Successfully stored message in memory")
        except Exception as e:
            logger.error("Failed to store message in memory: %s", e, exc_info=True)
