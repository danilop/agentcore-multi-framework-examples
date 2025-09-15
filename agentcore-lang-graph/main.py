from typing import Annotated, Dict, Any, Optional
import logging

from typing_extensions import TypedDict

from langchain.chat_models import init_chat_model
from langchain_tavily import TavilySearch

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition

from bedrock_agentcore import BedrockAgentCoreApp
from bedrock_agentcore.runtime.context import RequestContext

from memory import MemoryManager as AgentMemoryManager

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Configuration constants
DEFAULT_ACTOR_ID = "my-user-id"
DEFAULT_SESSION_ID = "DEFAULT"

tool = TavilySearch(max_results=2)
tools = [tool]
tool.invoke("What's a 'node' in LangGraph?")

class State(TypedDict):
    messages: Annotated[list, add_messages]

graph_builder = StateGraph(State)

llm = init_chat_model(
    "us.anthropic.claude-3-7-sonnet-20250219-v1:0",
    model_provider="bedrock_converse",
)

llm_with_tools = llm.bind_tools(tools)


def chatbot(state: State):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=[tool])
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
    {"tools": "tools", END: END},
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")
graph = graph_builder.compile()

#image = graph.get_graph().draw_mermaid_png()
#with open("graph_diagram.png", "wb") as f:
#    f.write(image)

# Initialize memory manager
memory_manager = AgentMemoryManager(
    default_actor_id=DEFAULT_ACTOR_ID,
    default_session_id=DEFAULT_SESSION_ID,
    logger=logger
)

app = BedrockAgentCoreApp()


@app.entrypoint
def invoke(payload: Dict[str, Any], context: Optional[RequestContext] = None) -> Dict[str, Any]:
    """Main entrypoint with AgentCore memory integration."""
    
    logger.info("LangGraph invocation started")
    logger.debug(f"Payload: {payload}")
    logger.debug(f"Context: {context}")
    
    # Extract parameters with context priority for session_id
    actor_id = payload.get("actor_id", DEFAULT_ACTOR_ID)
    session_id = context.session_id if context and context.session_id else payload.get("session_id", DEFAULT_SESSION_ID)
    
    logger.info(f"Processing request for actor_id: {actor_id}, session_id: {session_id}")
    
    prompt = payload.get("prompt", "No prompt found in input, please guide customer as to what tools can be used")
    logger.debug(f"Original prompt: {prompt}")

    # Enhance prompt with AgentCore memory context
    memory_context = memory_manager.get_memory_context(
        user_input=prompt,
        actor_id=actor_id,
        session_id=session_id
    )
    enhanced_prompt = f"{memory_context}\n\nCurrent user message: {prompt}" if memory_context else prompt
    
    logger.info(f"Enhanced prompt with memory context:\n\n{enhanced_prompt}")

    # Create messages for LangGraph
    messages = {"messages": [{"role": "user", "content": enhanced_prompt}]}
    
    try:
        # Invoke the LangGraph
        response = graph.invoke(messages)
        logger.info("LangGraph execution completed successfully")
        
        response_message = response['messages'][-1].content
        logger.debug(f"Response message: {response_message}")

        # Store conversation in AgentCore memory
        memory_manager.store_conversation(
            user_input=prompt,
            response=response_message,
            actor_id=actor_id,
            session_id=session_id
        )
        
        logger.info("Stored conversation in AgentCore memory")

        return {"result": response_message}
        
    except Exception as e:
        logger.error(f"Error during LangGraph execution: {e}", exc_info=True)
        return {"error": f"An error occurred while processing your request: {str(e)}"}


if __name__ == "__main__":
    app.run()
