# Building and Deploying AI Agents using LlamaIndex and Amazon Bedrock AgentCore

This is a sample project showing how to build an AI agent with LlamaIndex and deploy in production using AgentCore.

## About LlamaIndex

LlamaIndex is a data framework for LLM applications that provides tools for ingesting, structuring, and accessing private or domain-specific data. It enables developers to build RAG (Retrieval-Augmented Generation) applications by creating indexes from various data sources and providing query interfaces for LLMs. LlamaIndex simplifies the process of connecting LLMs to external data, making it easy to build intelligent applications that can reason over private documents, databases, and APIs.

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
cd ../agentcore-llama-index
```

The `create-memory` script creates a new AgentCore memory instance with all three strategies (User Preferences, Semantic Facts, Session Summaries) and saves the configuration to `../config/memory-config.json`. The `add-sample-memory` script adds a sample memory event ("I like apples but not bananas") to demonstrate the memory system.

**Note**: You only need to run these memory setup steps once. The memory configuration will be shared across all AgentCore framework projects.

After creating the memory, copy the memory configuration files to your project directory:

```sh
cp ../config/memory-config.json .
```

This ensures the memory configuration is available in the container when deployed with AgentCore.

I add code in `main.py` to import the AgentCore SDK and include an entrypoint function. To simplify testing locally, I also add at the end a couple of lines to run the `app`. In fact, I can now run it with:

```sh
uv run main.py
```

## Deploy using the Amazon Bedrock AgentCore starter toolkit

The `agentcore` command is in the Python virtual environment. I either run it with `uv run agentcore` or activate the virtual environment to just use `agentcore`. I use the latter.

```sh
source .venv/bin/activate
agentcore --help
```

Now I follow the usual process to configure and launch (locally first, then deploying to the cloud) the agent in the AgentCore Runtime.

### Local Development

1. Configure AgentCore:

```sh
agentcore configure -n llamaindexagent -e main.py
```

2. Launch locally:

```sh
agentcore launch --local
```

3. Test the agent:

```sh
agentcore invoke --local '{"prompt": "What did I say about fruit?"}'
```

### Cloud Deployment

1. Deploy to AWS:

```sh
agentcore launch
```

If you modify the code, you can update a cloud deployment by running `agentcore launch` again. It'll create a new version for the same endpoint.

2. Check status:

```sh
agentcore status
```

3. Invoke the deployed agent:

```sh
agentcore invoke '{"prompt": "What did I say about fruit?"}'
```

4. Monitor logs:

```sh
aws logs tail /aws/bedrock-agentcore/runtimes/<AGENT_ID-ENDPOINT_ID> --follow
```

