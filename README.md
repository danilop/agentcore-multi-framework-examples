# Amazon Bedrock AgentCore – Multi Framework Examples

This repository contains sample implementations of AI agents using different frameworks, all integrated with Amazon Bedrock AgentCore for production deployment and centralized memory management.

For more information on these implementaitons, see this blog post series:

[Building Production-Ready AI Agents: A Multi-Framework Journey with Amazon Bedrock AgentCore](https://dev.to/aws/building-production-ready-ai-agents-a-multi-framework-journey-with-amazon-bedrock-agentcore-p32)

## Installing Dependencies

Each project uses [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver, for dependency management. If you don't have uv installed, follow the [installation instructions](https://github.com/astral-sh/uv#installation) on the project's GitHub repository.

Navigate to any project directory and install dependencies:

```sh
uv sync
```

## Repository Structure

```
agentcore-multi-framework-examples/
├── agentcore-strands-agents/        # Strands Agents implementation
├── agentcore-crew-ai/               # CrewAI implementation  
├── agentcore-pydantic-ai/           # Pydantic AI implementation
├── agentcore-llama-index/           # LlamaIndex implementation
├── agentcore-lang-graph/            # LangGraph implementation
├── agentcore-memory-mcp/            # Memory MCP server implementation
├── scripts/                         # Shared memory management scripts  
│   ├── create_memory.py             # Create memory instance
│   ├── add_sample_memory.py         # Add sample memory events
└── config/                          # Centralized memory configuration
```

## Projects Overview

### 🔗 [Strands Agents](./agentcore-strands-agents/)
Modern, hook-based agent framework with clean architecture and built-in memory management.

### 👥 [CrewAI](./agentcore-crew-ai/) 
Multi-agent collaboration framework for complex tasks requiring specialized roles.

### 🔍 [Pydantic AI](./agentcore-pydantic-ai/)
Type-safe agent framework with Pydantic integration for structured data handling.

### 📚 [LlamaIndex](./agentcore-llama-index/)
RAG-focused framework with advanced document processing and retrieval capabilities.

### 🌐 [LangGraph](./agentcore-lang-graph/)
Graph-based agent framework for complex, stateful workflows with AgentCore memory integration.

### 🔌 [Memory MCP](./agentcore-memory-mcp/)
Model Context Protocol (MCP) server providing memory retrieval capabilities for AgentCore memory.

## Memory Management

All projects use **centralized memory configuration** managed through:

- **Scripts**: `./scripts/` - Shared scripts for creating and managing memory instances
- **Configuration**: `./config/memory-config.json` - Single source of truth for memory settings, created by the shared scripts

### Memory Features

- **Unified Memory**: Single memory instance with simplified namespace structure
- **Actor-based Organization**: Memories organized by actor ID using `/actor/{actorId}/` namespace
- **Centralized Configuration**: Single JSON file manages all memory settings
- **Automatic Loading**: Projects automatically load configuration without hardcoded values

### Creating Memory

Set up AgentCore memory (do this only once for all projects):

```bash
cd scripts
uv sync
uv run create-memory
uv run add-sample-memory
cd ..
```

The `create-memory` script creates a new AgentCore memory instance with all three strategies (User Preferences, Semantic Facts, Session Summaries) and saves the configuration to `./config/memory-config.json`. The `add-sample-memory` script adds a sample memory event to demonstrate the memory system:

- **Sample Event**: "I like apples but not bananas" (stored as a conversation event)

This sample memory can be retrieved by any of the agent frameworks when asked about fruit preferences.

**Note**: You only need to run these memory setup steps once. The memory configuration will be shared across all AgentCore framework projects.

## Memory Management Scripts

The `./scripts/` directory contains utility scripts for managing AgentCore memory. These scripts are designed as a standalone Python project that can be run using `uv run`.

### Available Scripts

#### 1. Create Memory (`create-memory`)
Creates a new AgentCore memory instance with all three strategies:
- **User Preferences**: Stores user-specific preferences and settings
- **Semantic Facts**: Stores factual information and knowledge
- **Session Summaries**: Maintains conversation context and summaries

**Usage:**
```bash
cd scripts
uv run create-memory
```

#### 2. Add Sample Memory (`add-sample-memory`)
Adds a sample memory event to demonstrate the memory system:
- **Content**: "I like apples but not bananas"
- **Actor ID**: "my-user-id"
- **Session ID**: "DEFAULT"

**Usage:**
```bash
cd scripts
uv run add-sample-memory
```

### Script Features
- **Standalone Operation**: No external dependencies on other project files
- **Simplified Configuration**: Direct path resolution for faster execution
- **Error Handling**: Comprehensive error handling and logging
- **Clean Interface**: Simple command-line interface with `uv run`

For detailed information about the scripts, see the [Scripts README](./scripts/README.md).

## Getting Started

1. **Choose a framework** from the project directories
2. **Create memory** using the scripts (if needed)
3. **Follow the README** in the specific project directory
4. **Deploy** using AgentCore toolkit

The `agentcore` command is in the Python virtual environment. You can either run it with `uv run agentcore` or activate the virtual environment to just use `agentcore`:

```sh
# Option 1: Use uv run
uv run agentcore launch

# Option 2: Activate virtual environment first
source .venv/bin/activate
agentcore launch
```

## Key Benefits

- **Production Ready**: All projects deployable via AgentCore
- **Memory Persistence**: Consistent memory management across frameworks
- **Clean Architecture**: DRY principles with shared configuration
- **Educational**: Compare different agent framework approaches
- **Scalable**: Centralized configuration management

## Memory Configuration Structure

```json
{
  "memory_id": "..."
}
```

The simplified configuration only stores the memory ID. All memories are organized using the `/actor/{actorId}/` namespace pattern.

## Architecture Highlights

- **Centralized Config**: Single `memory-config.json` for all projects
- **Framework Agnostic**: Memory integration works across all agent frameworks
- **Production Focus**: Built for real-world deployment scenarios
- **Educational Value**: Compare frameworks while maintaining consistency

Each project demonstrates different agent framework capabilities while maintaining consistent memory management and deployment patterns.

## Cleaning Up Resources

To delete the resources created by `agentcore launch`, use the `agentcore` command in the Python virtual event:

```bash
agentcore destroy
```

This command deletes the AgentCore agent, the ECR images, the CodeBuild project, and the IAM roles used by the agent and by CodeBuild.

To delete the memory, including all stored events, the strategies, and the memories extracted form the events, lookup the memory ID in the `../config/memory-config.json` file and use the AWS CLI:

```bash
aws bedrock-agentcore-control delete-memory --memory-id <MEMORY_ID>
```
