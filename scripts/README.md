# AgentCore Scripts

This directory contains utility scripts for managing AgentCore memory. It's now a standalone Python project that can be run using `uv run`.

## Project Structure

```
scripts/
├── __init__.py                 # Package initialization
├── pyproject.toml             # Project configuration and dependencies
├── create_memory.py           # Script to create new memory instances
├── add_sample_memory.py       # Script to add sample memory events
└── README.md                  # This file
```

## Installation

The project uses `uv` for dependency management. No manual installation is required - `uv run` will automatically handle dependencies.

## Available Scripts

### 1. Create Memory (`create-memory`)

Creates a new AgentCore memory instance with all three strategies:
- User Preferences
- Semantic Facts  
- Session Summaries

**Usage:**
```bash
uv run create-memory
```

**What it does:**
- Creates a new memory instance with a timestamped name
- Configures all three memory strategies
- Saves the memory configuration to `../config/memory-config.json`
- Waits for the memory to be in ACTIVE status

### 2. Add Sample Memory (`add-sample-memory`)

Adds a single sample memory event to demonstrate the memory system:
- User message: "I like apples but not bananas"

**Usage:**
```bash
uv run add-sample-memory
```

**What it does:**
- Uses the memory configuration from `../config/memory-config.json`
- Adds a single memory event with the sample content
- Uses actor_id: "my-user-id" and session_id: "DEFAULT" (consistent with other frameworks)

## Memory Event

The script adds a single memory event that stores the user's message as a conversation event that can be retrieved later for context. It uses the `memory_client.create_event()` method.

## Dependencies

The project automatically installs these dependencies when using `uv run`:

- `bedrock-agentcore>=0.1.3` - Core AgentCore functionality
- `boto3>=1.40.25` - AWS SDK for Python

## Configuration

The scripts use a simplified configuration approach:
- **Default config file**: `../config/memory-config.json`
- **No complex path searching**: Direct path resolution for faster execution
- **Predictable behavior**: Always uses the same config file location

## Examples

### Create a new memory instance
```bash
cd /Users/danilop/Tests/AgentCore/BlogSeries/scripts
uv run create-memory
```

### Add sample memory data
```bash
cd /Users/danilop/Tests/AgentCore/BlogSeries/scripts
uv run add-sample-memory
```

### Run both scripts in sequence
```bash
cd /Users/danilop/Tests/AgentCore/BlogSeries/scripts
uv run create-memory && uv run add-sample-memory
```

### Run from parent directory
```bash
cd /Users/danilop/Tests/AgentCore/BlogSeries
uv run --project scripts create-memory
uv run --project scripts add-sample-memory
```

## Example Output

```
AgentCore Sample Memory Adder
========================================
Adding sample memory event: 'I like apples but not bananas'
✓ Sample memory event added successfully!

Memory event added:
  - Content: 'I like apples but not bananas'
  - Role: USER
  - Actor ID: my-user-id
  - Session ID: DEFAULT
```

## Development

### Adding New Scripts

1. Create a new Python file (e.g., `my_script.py`)
2. Add a `main()` function
3. Add an entry to `[project.scripts]` in `pyproject.toml`:
   ```toml
   my-script = "my_script:main"
   ```
4. Run with: `uv run my-script`

### Project Configuration

The `pyproject.toml` file contains:
- Project metadata
- Dependencies
- Script entry points
- Build configuration for hatchling

### Customization

You can modify the scripts to:
- Change the user preference message
- Use different actor_id and session_id values
- Add additional memory types
- Specify custom memory configuration file paths

## Troubleshooting

### Memory Creation Takes Time
The `create-memory` script waits for the memory to reach ACTIVE status, which can take 30-60 seconds. This is normal behavior.

### Configuration File Not Found
If you get "Memory config file not found", ensure you have a valid `memory-config.json` file at `../config/memory-config.json`.

### AWS Credentials
Make sure your AWS credentials are configured (via AWS CLI, environment variables, or IAM roles).

## Integration with AgentCore Projects

These scripts are designed to work with the AgentCore framework projects in the parent directory. They can:

- Create shared memory instances used by all projects
- Add sample data for testing memory functionality
- Manage memory configuration across multiple agent frameworks

The memory created by these scripts can be used by any of the AgentCore projects (CrewAI, LangGraph, LlamaIndex, Pydantic AI, Strands Agents).

## Technical Details

### Memory System Architecture
- **Unified Memory Manager**: All frameworks use the same `MemoryManager` class
- **Memory Configuration**: Each project has a `memory-config.json` file containing a `memory_id`
- **Memory Operations**: Supports conversation events and semantic facts
- **Namespace Structure**: Memory is organized by actor ID and session ID using the pattern `/actor/{actorId}/`

### Script Features
- **Simplified Path Resolution**: Direct path to config file for faster execution
- **Error Handling**: Comprehensive error handling and logging
- **Standalone Operation**: No external dependencies on other project files
- **Clean Interface**: Simple command-line interface with `uv run`