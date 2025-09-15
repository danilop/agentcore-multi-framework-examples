"""Custom tools for LlamaIndex agents."""

import logging
from typing import List
from llama_index.core.tools import FunctionTool
from llama_index.tools.requests import RequestsToolSpec
from llama_index.tools.wikipedia import WikipediaToolSpec

# Import shared memory utilities
from memory import retrieve_memories_for_actor


logger = logging.getLogger(__name__)


def calculator(expression: str) -> str:
    """Perform basic mathematical calculations.
    
    Args:
        expression: A mathematical expression to evaluate (e.g., "2 + 3 * 4")
        
    Returns:
        The result of the calculation as a string
    """
    try:
        # Basic safety check - only allow numbers, operators, and parentheses
        allowed_chars = set('0123456789+-*/().,e ')
        if not all(c in allowed_chars for c in expression):
            return "Error: Invalid characters in expression. Only numbers, +, -, *, /, (, ) are allowed."
        
        # Evaluate the expression
        result = eval(expression)
        return f"The result of '{expression}' is {result}"
        
    except ZeroDivisionError:
        return "Error: Division by zero"
    except Exception as e:
        return f"Error calculating '{expression}': {str(e)}"


def text_analyzer(text: str) -> str:
    """Analyze text and provide basic statistics.
    
    Args:
        text: The text to analyze
        
    Returns:
        Analysis results including word count, character count, etc.
    """
    if not text:
        return "No text provided for analysis."
    
    try:
        words = text.split()
        sentences = text.count('.') + text.count('!') + text.count('?')
        paragraphs = text.count('\n\n') + 1
        
        analysis = f"""Text Analysis Results:
- Characters: {len(text)}
- Characters (no spaces): {len(text.replace(' ', ''))}
- Words: {len(words)}
- Sentences: {sentences}
- Paragraphs: {paragraphs}
- Average words per sentence: {len(words) / max(sentences, 1):.1f}
"""
        return analysis
        
    except Exception as e:
        return f"Error analyzing text: {str(e)}"


def create_llamaindex_tools(memory_manager=None) -> List[FunctionTool]:
    """Create a list of tools for the LlamaIndex agent.
    
    Args:
        memory_manager: Optional memory manager for memory-related tools
        
    Returns:
        List of FunctionTool instances
    """
    tools = []
    
    # Basic function tools
    tools.extend([
        FunctionTool.from_defaults(
            fn=calculator,
            name="calculator",
            description="Perform basic mathematical calculations with expressions like '2 + 3 * 4'"
        ),
        FunctionTool.from_defaults(
            fn=text_analyzer,
            name="text_analyzer", 
            description="Analyze text and provide statistics like word count, character count, etc."
        )
    ])
    
    # Add memory retrieval tool if memory manager is provided
    if memory_manager:
        def retrieve_memories(query: str, max_results: int = 5) -> str:
            """Retrieve relevant memories based on a query using shared function.
            
            Args:
                query: The query to search for in memories
                max_results: Maximum number of results to return
                
            Returns:
                Formatted string of retrieved memories
            """
            try:
                
                memories = retrieve_memories_for_actor(
                    memory_id=memory_manager.memory_config.memory_id,
                    actor_id=memory_manager.default_actor_id,
                    search_query=query,
                    memory_client=memory_manager.memory_client
                )
                # Limit results if needed
                if max_results and len(memories) > max_results:
                    memories = memories[:max_results]
                
                if not memories:
                    return f"No relevant memories found for query: '{query}'"
                
                result = f"Retrieved {len(memories)} memories for '{query}':\n\n"
                for i, memory in enumerate(memories, 1):
                    content = memory.get('content', 'No content')
                    score = memory.get('score', 'N/A')
                    result += f"{i}. (Score: {score}) {content}\n"
                
                return result
                
            except Exception as e:
                return f"Error retrieving memories: {str(e)}"
        
        tools.append(
            FunctionTool.from_defaults(
                fn=retrieve_memories,
                name="retrieve_memories",
                description="Retrieve relevant memories from previous conversations and interactions"
            )
        )
    
    # Add external tools
    try:
        # Wikipedia tool
        wikipedia_spec = WikipediaToolSpec()
        wikipedia_tools = wikipedia_spec.to_tool_list()
        tools.extend(wikipedia_tools)
        logger.info("Added Wikipedia tools")
        
    except Exception as e:
        logger.warning(f"Could not add Wikipedia tools: {e}")
    
    try:
        # Requests tool for web requests
        requests_spec = RequestsToolSpec()
        requests_tools = requests_spec.to_tool_list()
        tools.extend(requests_tools)
        logger.info("Added Requests tools")
        
    except Exception as e:
        logger.warning(f"Could not add Requests tools: {e}")
    
    logger.info(f"Created {len(tools)} tools for LlamaIndex agent")
    return tools


def get_system_prompt() -> str:
    """Get the system prompt for the LlamaIndex agent.
    
    Returns:
        System prompt string
    """
    return """You are a helpful AI assistant powered by LlamaIndex and AgentCore. You have access to various tools including:

1. Calculator - for mathematical computations
2. Text Analyzer - for analyzing text content
3. Memory Retrieval - for accessing previous conversation context
4. Wikipedia - for factual information lookup
5. Web Requests - for accessing web content

Key capabilities:
- Provide accurate, helpful responses
- Use tools when appropriate to enhance your responses
- Remember context from previous interactions
- Perform calculations and analysis
- Look up factual information
- Access web content when needed

Always be concise but thorough, and explain your reasoning when using tools. If you're unsure about something, say so rather than guessing."""
