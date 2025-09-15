# AgentCore Memory MCP Server

A Model Context Protocol (MCP) server that provides memory retrieval capabilities for AgentCore memory stores. This server exposes memory functionality as MCP tools that can be used by AI assistants and other MCP clients.

## Overview

The AgentCore Memory MCP Server bridges the gap between AgentCore's centralized memory system and MCP-compatible clients. It provides a standardized interface for retrieving memories from AgentCore memory stores, making it easy to integrate memory capabilities into any MCP-enabled application.

## Features

- **Memory Retrieval**: Search and retrieve memories from AgentCore memory stores
- **Actor-based Organization**: Memories organized by actor ID using `/actor/{actorId}/` namespace
- **Configurable Results**: Control the number of results returned
- **Formatted Output**: Formatted memory results with metadata
- **Error Handling**: Robust error handling with detailed logging
- **MCP Standard**: Full compliance with Model Context Protocol specifications

## Installation

This project uses [uv](https://github.com/astral-sh/uv) for dependency management. If you don't have uv installed, follow the [installation instructions](https://github.com/astral-sh/uv#installation).

```bash
# Install dependencies
uv sync
```

## Configuration

The server uses the `../config/memory-config.json` file to configure the AgentCore memory instance.

The memory ID there should point to an existing AgentCore memory instance. You can create one using the shared scripts in the parent directory:

```bash
cd ../scripts
uv sync
uv run create-memory
uv run add-sample-memory
```

## Usage

### Running the MCP Server

```bash
# Run the MCP server
uv run python main.py
```

The server will start and listen for MCP connections. You can connect to it using any MCP-compatible client.

### Available Tools

#### `retrieve_memory`

Retrieves memories from the AgentCore memory store based on a search query.

**Parameters:**
- `query` (string): The search query to find relevant memories
- `max_results` (integer, optional): Maximum number of memories to return (default: 10)

**Returns:**
- Formatted string containing the retrieved memories with metadata

**Example Usage:**
```python
# Retrieve memories about user preferences
result = retrieve_memory(
    query="user preferences about food",
    max_results=5
)
```

## Architecture

### Components

1. **FastMCP Server**: Uses the FastMCP framework for MCP server implementation
2. **Memory Client**: AgentCore MemoryClient for interacting with memory stores
3. **Memory Config**: Configuration management for memory instance settings
4. **Memory Manager**: Shared memory module

### Memory Organization

Memories are organized using the AgentCore namespace pattern:
- **Namespace**: `/actor/{actorId}/`
- **Actor ID**: Currently hardcoded in the `ACTOR_ID` constant in `main.py`
- **Search**: Semantic search across all memories in the actor's namespace

### Data Flow

1. MCP client sends `retrieve_memory` request
2. Server extracts query and max_results parameters
3. Memory client searches the configured memory store
4. Results are formatted with metadata and returned
5. Client receives formatted memory context

## Integration with AgentCore

This MCP server is part of the larger AgentCore ecosystem:

- **Shared Memory**: Uses the same memory configuration as other AgentCore projects
- **Unified Namespace**: Follows the `/actor/{actorId}/` pattern used across all projects
- **Consistent API**: Provides the same memory retrieval capabilities as other frameworks

## Development

### Project Structure

```
agentcore-memory-mcp/
├── main.py                 # MCP server implementation
├── memory.py              # Shared memory functionality
├── memory-config.json     # Memory configuration
├── pyproject.toml         # Project dependencies
└── README.md             # This file
```

### Dependencies

- `bedrock-agentcore`: AgentCore memory client
- `mcp[cli]`: Model Context Protocol framework

### Logging

The server includes comprehensive logging:
- Info level: Memory retrieval operations and results
- Error level: Detailed error information with stack traces
- Debug level: Detailed operation flow (when enabled)

## Example Output

When retrieving memories, the server returns formatted results like:

```
Found 3 relevant memories:

**1.** I like apples but not bananas
   📝 *Metadata: type: user_preference, timestamp: 2025-01-10T15:14:48Z*

**2.** My favorite programming language is Python
   📝 *Metadata: type: semantic_fact, confidence: 0.95*

**3.** I prefer working in the morning
   📝 *Metadata: type: user_preference, category: schedule*
```
