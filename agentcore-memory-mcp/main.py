import logging

from mcp.server.fastmcp import FastMCP
from bedrock_agentcore.memory import MemoryClient
from memory import MemoryConfig, retrieve_memories_for_actor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global constants
ACTOR_ID = "my-user-id"

mcp = FastMCP("AgentCore Memory MCP")

# Initialize memory components
memory_config = MemoryConfig()
memory_client = MemoryClient()

@mcp.tool()
def retrieve_memory(
    query: str,
    max_results: int = 10
) -> str:
    """
    Retrieve memories from AgentCore memory store based on a search query.
    
    Args:
        query: The search query to find relevant memories
        max_results: Maximum number of memories to return (default: 10)
    
    Returns:
        The retrieved memories
    """
    try:
        logger.info(f"Retrieving memories for actor '{ACTOR_ID}' with query: '{query}'")
        
        # Retrieve memories using the direct function
        memories = retrieve_memories_for_actor(
            memory_id=memory_config.memory_id,
            actor_id=ACTOR_ID,
            search_query=query,
            memory_client=memory_client
        )
        
        # Limit results if requested
        if max_results > 0 and len(memories) > max_results:
            memories = memories[:max_results]
        
        # Create a nicely formatted response
        if not memories:
            result = "❌ No relevant memories found."
        else:
            result = f"Found {len(memories)} relevant memories:\n\n"
            
            # Add each memory with nice formatting
            for i, memory in enumerate(memories, 1):
                content = memory.get("content", "")
                metadata = memory.get("metadata", {})
                
                result += f"**{i}.** {content}\n"
                
                # Add metadata if available
                if metadata:
                    metadata_items = [f"{k}: {v}" for k, v in metadata.items()]
                    result += f"   📝 *Metadata: {', '.join(metadata_items)}*\n"
                
                result += "\n"
        
        logger.info(f"Successfully retrieved {len(memories)} memories for query: '{query}'")
        return result
        
    except Exception as e:
        error_msg = f"Failed to retrieve memories: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        return f"❌ Error retrieving memories: {str(e)}"


mcp.run()