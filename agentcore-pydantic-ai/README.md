# Building and Deploying AI agents using Pydantic AI and Amazon Bedrock AgentCore

This is a sample project showing how to build an AI agent with Pydantic AI and deploy in production using AgentCore.

## About PydanticAI

PydanticAI is a Python framework for building AI agents that leverages Pydantic's type validation and serialization capabilities. It provides a structured approach to creating AI agents with strong typing, automatic validation, and seamless integration with various LLM providers. PydanticAI enables developers to build reliable, type-safe AI applications with clear data contracts and robust error handling, making it ideal for production-ready AI agent development.

## Installing Dependencies

This project uses [uv](https://github.com/astral-sh/uv), a fast Python package installer and resolver. If you don't have uv installed, follow the [installation instructions](https://github.com/astral-sh/uv#installation) on the project's GitHub repository.

Install all project dependencies:

```sh
uv sync
```

I add code in `main.py` to import the AgentCore SDK and include an entrypoint function.

## Memory Configuration

Set up AgentCore memory (do this only once for all projects):

```sh
cd ../scripts
uv sync
uv run create-memory
uv run add-sample-memory
cd ../agentcore-pydantic-ai
```

The `create-memory` script creates a new AgentCore memory instance with all three strategies (User Preferences, Semantic Facts, Session Summaries) and saves the configuration to `../config/memory-config.json`. The `add-sample-memory` script adds a sample memory event ("I like apples but not bananas") to demonstrate the memory system.

**Note**: You only need to run these memory setup steps once. The memory configuration will be shared across all AgentCore framework projects.

After creating the memory, copy the memory configuration files to your project directory:

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

Now I follow the usual process to configure and launch (locally first, then deploying to the cloud) the agent in the AgentCore Runtime.

```sh
agentcore configure -n pydanticaiagent -e main.py # All default values when asked
agentcore launch --local
agentcore invoke --local '{ "prompt": "What did I say about fruit?" }'
```

When I am satisfied with the local tests, I deploy to the cloud:

```sh
agentcore launch
```

If you modify the code, you can update a cloud deployment by running `agentcore launch` again. It'll create a new version for the same endpoint.

```sh
agentcore status
agentcore invoke '{ "prompt": "What did I say about fruit?" }'
```

Before invoking the agent, I use in another terminal the AWS CLI command shown by `agentcore launch` to follow the logs on Amazon CloudWatch Logs:

```sh
aws logs tail /aws/bedrock-agentcore/runtimes/<AGENT_ID-ENDPOINT_ID> --follow
```
