#!/usr/bin/env python3
"""
Script to add sample memory to the AgentCore memory system.

This script adds a single sample memory event to demonstrate the memory system.
"""

import json
import logging
from pathlib import Path

from bedrock_agentcore.memory import MemoryClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Sample memory content
SAMPLE_MEMORY_CONTENT = "I like apples but not bananas"

# Default actor and session IDs (consistent with other frameworks)
DEFAULT_ACTOR_ID = "my-user-id"
DEFAULT_SESSION_ID = "DEFAULT"


class MemoryConfig:
    """Manages memory configuration from JSON file."""
    
    def __init__(self, config_path: str = "../config/memory-config.json"):
        """Initialize memory configuration.
        
        Args:
            config_path: Path to the memory configuration JSON file
        """
        self.config_path = config_path
        self._load_config()
    
    def _load_config(self) -> None:
        """Load configuration from JSON file."""
        try:
            config_file = Path(self.config_path)
            if not config_file.exists():
                raise FileNotFoundError(f"Memory config file not found: {self.config_path}")
            
            with open(config_file, 'r') as f:
                self.config = json.load(f)
            
            logger.debug(f"Loaded memory configuration from {self.config_path}")
            
        except Exception as e:
            logger.error(f"Failed to load memory configuration: {e}")
            raise
    
    @property
    def memory_id(self) -> str:
        """Get the memory ID."""
        return self.config["memory_id"]


def add_sample_event(
    actor_id: str = DEFAULT_ACTOR_ID,
    session_id: str = DEFAULT_SESSION_ID
) -> bool:
    """
    Add a sample memory event to the AgentCore memory system.
    
    Args:
        actor_id: The actor ID to associate with the memory
        session_id: The session ID to associate with the memory
        
    Returns:
        True if the memory was stored successfully, False otherwise
    """
    try:
        # Load memory configuration
        memory_config = MemoryConfig()
        memory_id = memory_config.memory_id
        
        logger.info(f"Using memory ID: {memory_id}")
        logger.info(f"Adding sample memory for actor: {actor_id}, session: {session_id}")
        
        # Initialize memory client
        memory_client = MemoryClient()
        
        # Create a memory event with the sample content
        messages_to_store = [
            (SAMPLE_MEMORY_CONTENT, 'USER')
        ]
        
        # Store the memory event
        memory_client.create_event(
            memory_id=memory_id,
            actor_id=actor_id,
            session_id=session_id,
            messages=messages_to_store
        )
        
        logger.info(f"Successfully stored sample memory event: '{SAMPLE_MEMORY_CONTENT}'")
        logger.info(f"Memory stored for actor_id: {actor_id}, session_id: {session_id}")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to add sample memory: {e}", exc_info=True)
        return False


def main():
    """Main function to add sample memory."""
    print("AgentCore Sample Memory Adder")
    print("=" * 40)
    
    # Add the sample memory event
    print(f"Adding sample memory event: '{SAMPLE_MEMORY_CONTENT}'")
    success = add_sample_event()
    
    if success:
        print("✓ Sample memory event added successfully!")
        print(f"\nMemory event added:")
        print(f"  - Content: '{SAMPLE_MEMORY_CONTENT}'")
        print(f"  - Role: USER")
        print(f"  - Actor ID: {DEFAULT_ACTOR_ID}")
        print(f"  - Session ID: {DEFAULT_SESSION_ID}")
    else:
        print("✗ Failed to add sample memory event")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())