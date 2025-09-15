"""
AgentCore Memory Manager

This module provides unified memory functionality for all AgentCore frameworks, including:
1. Loading previous conversation context during initialization
2. Retrieving relevant memories before message processing
3. Storing new messages after each response
4. Storing semantic facts (for LlamaIndex)

Usage:
    memory_manager = MemoryManager()
    
    # Get memory context for any framework
    memory_context = memory_manager.get_memory_context(
        user_input="User's current message",
        actor_id="user-123",
        session_id="session-456"
    )
    
    # Store conversation after response
    memory_manager.store_conversation(
        user_input="User's message",
        response="Agent's response",
        actor_id="user-123", 
        session_id="session-456"
    )
    
    # Store facts (LlamaIndex specific)
    memory_manager.store_facts(
        facts=["fact1", "fact2"],
        actor_id="user-123",
        session_id="session-456"
    )
"""

import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

from bedrock_agentcore.memory import MemoryClient


class MemoryConfig:
    """Manages memory configuration from JSON file with caching."""
    
    _cached_config: Optional[Dict[str, Any]] = None
    _cached_path: Optional[str] = None
    
    def __init__(self, config_path: str = "memory-config.json"):
        """Initialize memory configuration.
        
        Args:
            config_path: Path to the memory configuration JSON file
        """
        self.config_path = config_path
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from JSON file with caching."""
        if (MemoryConfig._cached_config is not None and 
            MemoryConfig._cached_path == self.config_path):
            return
        
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Memory config file not found: {self.config_path}")
            
            with open(config_file, 'r') as f:
                config = json.load(f)
            
            MemoryConfig._cached_config = config
            MemoryConfig._cached_path = self.config_path
            
            logger = logging.getLogger(__name__)
            logger.debug(f"Loaded memory configuration from {self.config_path}")
            
        except Exception as e:
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load memory configuration: {e}")
            raise
    
    @property
    def memory_id(self) -> str:
        """Get the memory ID."""
        return MemoryConfig._cached_config["memory_id"]


def retrieve_memories_for_actor(
    memory_id: str,
    actor_id: str,
    search_query: str,
    memory_client: MemoryClient
) -> List[Dict[str, Any]]:
    """Retrieve memories for a specific actor from the memory store.
    
    Args:
        memory_id: The memory ID to search in.
        actor_id: The actor ID to build namespace from.
        search_query: The search query to find relevant memories.
        memory_client: The memory client instance.
    
    Returns:
        A list of memories retrieved from the memory client.
    """
    namespace = f"/actor/{actor_id}/"
    
    try:
        memories = memory_client.retrieve_memories(
            memory_id=memory_id,
            namespace=namespace,
            query=search_query
        )
        logger = logging.getLogger(__name__)
        logger.debug(f"Retrieved {len(memories)} memories from namespace {namespace} with query '{search_query}'")
        return memories
    except Exception as e:
        logger = logging.getLogger(__name__)
        logger.error(f"Failed to retrieve memories: {e}")
        return []


def format_memory_context(memories: List[Dict[str, Any]]) -> str:
    """Format retrieved memories into a readable context string.
    
    Args:
        memories: List of memory objects from the memory client
        
    Returns:
        Formatted string containing the memory context
    """
    if not memories:
        return "No relevant memories found."
    
    context_parts = []
    for i, memory in enumerate(memories, 1):
        # Extract relevant information from memory object
        content = memory.get("content", "")
        metadata = memory.get("metadata", {})
        
        # Format the memory entry
        memory_entry = f"{i}. {content}"
        
        # Add metadata if available
        if metadata:
            metadata_str = ", ".join([f"{k}: {v}" for k, v in metadata.items()])
            memory_entry += f" (Metadata: {metadata_str})"
        
        context_parts.append(memory_entry)
    
    return "\n".join(context_parts)


class MemoryManager:
    """
    Unified memory manager for all AgentCore frameworks.
    
    Provides comprehensive memory functionality:
    1. Load previous conversation context during initialization
    2. Retrieve relevant memories before message processing  
    3. Store new messages after each response
    4. Store semantic facts (LlamaIndex specific)
    """
    
    def __init__(
        self,
        default_actor_id: str = "default-user",
        default_session_id: str = "default-session",
        max_conversation_turns: int = 100,
        logger: Optional[logging.Logger] = None
    ):
        """
        Initialize the MemoryManager.
        
        Args:
            default_actor_id: Default actor ID if none provided
            default_session_id: Default session ID if none provided
            max_conversation_turns: Maximum number of conversation turns to load
            logger: Optional logger instance
        """
        # Load memory configuration
        self.memory_config = MemoryConfig()
        self.default_actor_id = default_actor_id
        self.default_session_id = default_session_id
        self.max_conversation_turns = max_conversation_turns
        self.logger = logger or logging.getLogger(__name__)
        
        # Memory client
        self.memory_client = MemoryClient()
        
        # Session tracking for conversation context loading
        self._initialized_sessions: Dict[str, bool] = {}
        
        self.logger.info(f"MemoryManager initialized with memory_id: {self.memory_config.memory_id}")

    def get_memory_context(
        self,
        user_input: str,
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        load_conversation_context: bool = True,
        retrieve_relevant_memories: bool = True
    ) -> str:
        """
        Get memory context as a string to be added to user input.
        
        This method retrieves conversation context and relevant memories
        and returns them as a formatted string that can be prepended to the user input.
        
        Args:
            user_input: Current user input/message
            actor_id: Actor identifier (uses default if None)
            session_id: Session identifier (uses default if None)
            load_conversation_context: Whether to load previous conversation context
            retrieve_relevant_memories: Whether to retrieve relevant memories
            
        Returns:
            Formatted memory context string
        """
        actor_id = actor_id or self.default_actor_id
        session_id = session_id or self.default_session_id
        session_key = f"{actor_id}:{session_id}"
        
        context_parts = []
        
        if load_conversation_context and not self._initialized_sessions.get(session_key, False):
            self.logger.info(f"Loading conversation context for session: {session_key}")
            conversation_context = self._load_conversation_context(actor_id, session_id)
            if conversation_context:
                context_parts.append(f"Recent conversation:\n{conversation_context}")
                self.logger.info("Added conversation context to memory context")
            
            self._initialized_sessions[session_key] = True
            
        if retrieve_relevant_memories and user_input:
            self.logger.info("Retrieving relevant memories for user input")
            relevant_memories = retrieve_memories_for_actor(
                memory_id=self.memory_config.memory_id,
                actor_id=actor_id,
                search_query=user_input,
                memory_client=self.memory_client
            )
            if relevant_memories:
                memory_context = format_memory_context(relevant_memories)
                context_parts.append(f"Relevant long-term memory context:\n{memory_context}")
                self.logger.info(f"Added {len(relevant_memories)} relevant memories to memory context")
            else:
                self.logger.info("No relevant memories found")
        
        return "\n\n".join(context_parts) if context_parts else ""

    def store_conversation(
        self,
        user_input: str,
        response: str,
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store conversation in memory after agent response.
        
        Args:
            user_input: User's input/message
            response: Agent's response
            actor_id: Actor identifier (uses default if None)
            session_id: Session identifier (uses default if None)
            metadata: Optional metadata to store with the conversation
            
        Returns:
            True if conversation was stored successfully, False otherwise
        """
        if not user_input or not response:
            self.logger.warning("Cannot store conversation: missing user_input or response")
            return False
        
        actor_id = actor_id or self.default_actor_id
        session_id = session_id or self.default_session_id
        
        self.logger.debug(f"Storing conversation for {actor_id}:{session_id}")
        
        try:
            # Create messages in the format expected by AgentCore memory
            messages_to_store = [
                (user_input, 'USER'),
                (response, 'ASSISTANT')
            ]
            
            self.memory_client.create_event(
                memory_id=self.memory_config.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                messages=messages_to_store
            )
            self.logger.info("Successfully stored conversation in memory")
            return True
                
        except Exception as e:
            self.logger.error(f"Failed to store conversation in memory: {e}", exc_info=True)
            return False

    def store_facts(
        self,
        facts: List[str],
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Store semantic facts in memory (LlamaIndex specific functionality).
        
        Args:
            facts: List of facts to store
            actor_id: Actor identifier (uses default if None)
            session_id: Session identifier (uses default if None)
            metadata: Optional metadata for the facts
            
        Returns:
            True if facts were stored successfully, False otherwise
        """
        if not facts:
            return True
        
        actor_id = actor_id or self.default_actor_id
        session_id = session_id or self.default_session_id
        
        self.logger.info(f"Storing {len(facts)} facts (actor: {actor_id}, session: {session_id})")
        
        try:
            namespace = f"/actor/{actor_id}/"
            
            memories = []
            for fact in facts:
                memories.append({
                    "content": fact,
                    "metadata": {
                        "type": "semantic_fact",
                        **(metadata or {})
                    }
                })
            
            self.memory_client.store_memories(
                memory_id=self.memory_config.memory_id,
                namespace=namespace,
                memories=memories
            )
            
            self.logger.debug(f"Successfully stored {len(facts)} facts")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to store facts: {e}")
            return False

    def store_new_messages(
        self,
        new_messages: List[Any],
        actor_id: Optional[str] = None,
        session_id: Optional[str] = None
    ) -> bool:
        """
        Store new messages in memory after agent response (Pydantic AI specific).
        
        Args:
            new_messages: List of new message objects to store
            actor_id: Actor identifier (uses default if None)
            session_id: Session identifier (uses default if None)
            
        Returns:
            True if messages were stored successfully, False otherwise
        """
        if not new_messages:
            return True
        
        actor_id = actor_id or self.default_actor_id
        session_id = session_id or self.default_session_id
        
        self.logger.debug(f"Storing {len(new_messages)} new messages for {actor_id}:{session_id}")
        
        try:
            messages_to_store = self._convert_messages_for_storage(new_messages)
            
            if messages_to_store:
                self.memory_client.create_event(
                    memory_id=self.memory_config.memory_id,
                    actor_id=actor_id,
                    session_id=session_id,
                    messages=messages_to_store
                )
                self.logger.info(f"Successfully stored {len(messages_to_store)} messages in memory")
                return True
            else:
                self.logger.warning("No messages were converted for storage")
                return False
                
        except Exception as e:
            self.logger.error(f"Failed to store messages in memory: {e}", exc_info=True)
            return False

    def _load_conversation_context(self, actor_id: str, session_id: str) -> str:
        """Load previous conversation history from memory and return as context string."""
        self.logger.debug(f"Loading conversation history for {actor_id}:{session_id}")
        
        try:
            conversations = self.memory_client.get_last_k_turns(
                memory_id=self.memory_config.memory_id,
                actor_id=actor_id,
                session_id=session_id,
                k=self.max_conversation_turns,
            )
            self.logger.debug(f"Retrieved {len(conversations) if conversations else 0} conversation turns")
        except Exception as e:
            self.logger.warning(f"Failed to retrieve conversation history: {e}")
            return ""

        if not conversations:
            return ""

        context_messages = []
        for turn in reversed(conversations):
            for message in turn:
                try:
                    role = message['role']
                    content = message['content']
                    
                    if isinstance(content, str) and content.startswith('{'):
                        try:
                            parsed_content = json.loads(content)
                            content = str(parsed_content)
                        except json.JSONDecodeError:
                            pass
                    
                    context_messages.append(f"{role}: {content}")
                except Exception as e:
                    self.logger.warning(f"Failed to process message from memory: {e}")
                    continue
        
        conversation_context = "\n".join(context_messages)
        self.logger.debug(f"Loaded conversation context from {len(context_messages)} messages")
        return conversation_context

    def _convert_messages_for_storage(self, messages: List[Any]) -> List[tuple]:
        """Convert various message types to memory storage format."""
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
                self.logger.warning(f"Failed to convert message for storage: {e}")
                continue
        
        return messages_to_store

    def get_memory_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about memory usage (useful for debugging/monitoring).
        
        Returns:
            Dictionary with memory statistics
        """
        return {
            "memory_id": self.memory_config.memory_id,
            "default_actor_id": self.default_actor_id,
            "default_session_id": self.default_session_id,
            "max_conversation_turns": self.max_conversation_turns,
            "initialized_sessions": len(self._initialized_sessions)
        }


# Backward compatibility aliases for different frameworks
CrewMemoryManager = MemoryManager
AgentMemoryManager = MemoryManager
LlamaIndexMemoryManager = MemoryManager