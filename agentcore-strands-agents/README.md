# Building and Deploying AI Agents with Amazon Bedrock AgentCore and Strands Agents

This is a sample project showing how to build an AI agent with Strands Agents and deploy in production using AgentCore.

## About Strands Agents

Strands Agents is a Python SDK for building AI agents with a focus on simplicity and production readiness. It provides a clean, intuitive API for creating agents with built-in support for tools and various LLM providers. Strands Agents emphasizes developer experience with minimal boilerplate code, making it easy to build and deploy sophisticated AI agents that can handle complex tasks while maintaining clean, maintainable code.

## Installing Dependencies

This project uses [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver. If you don't have uv installed, follow the [installation instructions](https://github.com/astral-sh/uv#installation) on the project's GitHub repository.

Install all project dependencies:

```sh
uv sync
```

## Memory Configuration

Set up AgentCore memory (do this only once for all projects):

```sh
cd ../scripts
uv sync
uv run create-memory
uv run add-sample-memory
cd ../agentcore-strands-agents
```

The `create-memory` script creates a new AgentCore memory instance with all three strategies (User Preferences, Semantic Facts, Session Summaries) and saves the configuration to `../config/memory-config.json`. The `add-sample-memory` script adds a sample memory event ("I like apples but not bananas") to demonstrate the memory system.

**Note**: You only need to run these memory setup steps once. The memory configuration will be shared across all AgentCore framework projects.

After creating the memory, copy the memory configuration file to your project directory:

```sh
cp ../config/memory-config.json .
```

This ensures the memory configuration is available in the container when deployed with AgentCore.

## Deploy using the Amazon Bedrock AgentCore starter toolkit

The `agentcore` command is in the Python virtual environment. I either run it with `uv run agentcore` or activate the virtual environment to just use `agentcore`. I use the latter.

```sh
source .venv/bin/activate
agentcore --help
```

A container engine is required for local deployment (Docker/Finch/Podman). Default cloud deployment uses AWS CodeBuild (no container engine needed).

To configure the agent for AgentCore Runtime, I use the default for all questions:

```sh
agentcore configure -n strandsagent -e src/agentcore_strands_agents/agent.py 
```

To deploy locally using the AgentCore starter toolkit, I run:

```sh
agentcore launch --local
```

In another terminal, I invoke the local agent using the AgentCore starter toolkit:

```sh
agentcore invoke --local '{ "prompt": "What did I say about fruit?" }'
```

Now I deploy to the cloud using AgentCore Runtime:

```sh
agentcore launch
```

If you modify the code, you can update a cloud deployment by running `agentcore launch` again. It'll create a new version for the same endpoint.

I check the status of my Bedrock AgentCore endpoint with:

```sh
agentcore status
```

The status command tells where I find the Amazon CloudWatch Logs and the AWS CLI command to use to follow the logs. I run that command in a separate terminal.

I invoke the deployed agent using the AgentCore starter toolkit:

```sh
agentcore invoke '{ "prompt": "What did I say about fruit?" }'
```

The AgentCore starter toolkit automatically preserves the session, so further invocations continue the previous conversation:

```sh
agentcore invoke '{ "prompt": "Thanks for bringing that back." }'
```

Similarly, I invoke the deployed agent using the AWS CLI. Note that the payload needs to be base64-encoded. The output is in the specified file.

```sh
aws bedrock-agentcore invoke-agent-runtime --agent-runtime-arn <ARN from agentcore status> --runtime-session-id $(python -c 'import uuid; print(uuid.uuid4())') --payload $(echo -n '{"prompt": "What did I say about fruit?"}' | base64) output.txt
```

When using the CLI or the API, to send multiple invocations in the same session, I need to pass the same `--runtime-session-id`.
