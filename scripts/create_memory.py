import json
import logging
import sys
from datetime import datetime
from pathlib import Path

from bedrock_agentcore.memory import MemoryClient
from bedrock_agentcore.memory.constants import StrategyType

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

MEMORY_NAME = f"MyAgentMemory{datetime.now().strftime('%Y%m%d%H%M%S')}"
CONFIG_FILE_PATH = Path("../config/memory-config.json")

# Memory strategies configuration with corrected namespaces (fixing SDK bug: {strategyId} -> {memoryStrategyId})
MEMORY_STRATEGIES = [
    {
        StrategyType.USER_PREFERENCE.value: {
            "name": "UserPreferences",
            "namespaces": ["/actor/{actorId}/strategy/{memoryStrategyId}"]
        }
    },
    {
        StrategyType.SEMANTIC.value: {
            "name": "SemanticFacts",
            "namespaces": ["/actor/{actorId}/strategy/{memoryStrategyId}/{sessionId}"]
        }
    },
    {
        StrategyType.SUMMARY.value: {
            "name": "SessionSummaries", 
            "namespaces": ["/actor/{actorId}/strategy/{memoryStrategyId}/{sessionId}"]
        }
    }
]


def create_memory():
    """Create a new memory instance for the agent with all three strategies."""
    logger.info("Creating memory with name: %s", MEMORY_NAME)

    try:
        memory_client = MemoryClient()

        memory = memory_client.create_memory_and_wait(
            name=MEMORY_NAME,
            description="Memory for my agent with all three strategies",
            strategies=MEMORY_STRATEGIES
        )

        memory_id = memory.get("id")
        print(f"Created memory: {memory_id}")
        print("Memory strategies created:")
        print("  - User Preferences: /actor/{actorId}/strategy/{memoryStrategyId}")
        print("  - Semantic Facts: /actor/{actorId}/strategy/{memoryStrategyId}/{sessionId}")
        print("  - Session Summaries: /actor/{actorId}/strategy/{memoryStrategyId}/{sessionId}")
        logger.info("Successfully created memory with ID: %s", memory_id)
        logger.info("Created memory with all three strategies: UserPreferences, SemanticFacts, SessionSummaries")
        logger.debug("Full memory object: %s", memory)

        return memory_id

    except Exception as e:
        logger.error("Failed to create memory: %s", e, exc_info=True)
        raise


def save_memory_config(memory_id: str):
    """Save memory configuration to JSON file."""
    config_path = CONFIG_FILE_PATH
    
    config = {
        "memory_id": memory_id
    }
    
    config_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(config_path, 'w') as f:
        json.dump(config, f, indent=2)
    
    logger.info(f"Memory configuration saved to {config_path}")


def main():
    """Main function to create the memory."""
    try:
        memory_id = create_memory()
        save_memory_config(memory_id)
        
        print(f"Memory created successfully! ID: {memory_id}")
        print(f"Configuration saved to {CONFIG_FILE_PATH}")

    except Exception as e:
        logger.error("Script failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
