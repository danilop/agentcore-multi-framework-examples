# Test Suite for AgentCore Strands Agents

This directory contains comprehensive tests for the AgentCore Strands Agents project.

## Test Structure

### Test Files

- **`conftest.py`** - Pytest configuration and shared fixtures
- **`test_agent.py`** - Unit tests for the core agent functionality
- **`test_agentcore_integration.py`** - Integration tests for agentcore launch/invoke
- **`test_agent_memory.py`** - Tests for agent memory functionality
- **`test_agentcore_commands.py`** - Tests for agentcore command execution

### Test Categories

#### Unit Tests
- Agent creation and configuration
- Memory hook integration
- Basic functionality testing
- Error handling

#### Integration Tests
- Full agentcore launch/invoke workflow
- Memory persistence across invocations
- Command-line interface testing
- Response parsing and validation

## Running Tests

### Basic Test Execution

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_agent.py

# Run specific test class
pytest tests/test_agentcore_integration.py::TestAgentCoreIntegration
```

### Test Categories

```bash
# Run only unit tests (exclude slow integration tests)
pytest -m "not slow"

# Run only integration tests
pytest -m integration

# Run memory-related tests
pytest -m memory

# Run agentcore-related tests
pytest -m agentcore
```

### Slow Integration Tests

Some tests require actual agentcore execution and are marked as "slow":

```bash
# Run all tests including slow ones
pytest -m slow

# Run only slow tests
pytest -m slow

# Skip slow tests (default for CI)
pytest -m "not slow"
```

## Test Fixtures

### Available Fixtures

- **`agentcore_config`** - Loaded agentcore configuration
- **`test_payload`** - Standard test payload for invocations
- **`expected_response_structure`** - Expected response format
- **`mock_agentcore_process`** - Mocked agentcore process
- **`agentcore_helper`** - Helper class for integration testing

### Using Fixtures

```python
def test_example(agentcore_helper, test_payload):
    """Example test using fixtures."""
    response = agentcore_helper.invoke_agent(test_payload)
    assert "error" not in response
```

## Integration Testing

### Prerequisites

For full integration tests, ensure:

1. **agentcore CLI** is installed and available in PATH
2. **Docker** is running (for containerized agent execution)
3. **Virtual environment** is activated with all dependencies

### Manual Testing

The integration tests replicate the manual testing workflow:

```bash
# Terminal 1: Launch agent
agentcore launch --local

# Terminal 2: Invoke agent
agentcore invoke --local '{"prompt": "What did I just ask?"}'
```

### Automated Integration Testing

The test suite includes automated versions of this workflow:

```python
def test_agentcore_full_integration(agentcore_helper, test_payload):
    """Full integration test with actual agentcore launch and invoke."""
    # Launch the agent
    launch_success = agentcore_helper.launch_agent(timeout=60)
    
    # Invoke the agent
    response = agentcore_helper.invoke_agent(test_payload)
    
    # Verify response
    assert "error" not in response
```

## Memory Testing

### Memory Hook Testing

Tests verify that the short-term memory hook:

1. Is properly initialized with the agent
2. Maintains conversation context
3. Persists memory across invocations
4. Uses the correct memory ID

### Memory Scenarios

- **Conversation Memory**: Agent remembers previous messages
- **Cross-Session Memory**: Memory behavior across different sessions
- **Memory Hook Integration**: Proper integration with agent lifecycle

## Mock Testing

### Subprocess Mocking

Many tests use mocked subprocess calls to avoid requiring actual agentcore execution:

```python
with patch('subprocess.run') as mock_run:
    mock_result = Mock()
    mock_result.returncode = 0
    mock_result.stdout = '{"response": {"result": "success"}}'
    mock_run.return_value = mock_result
    
    # Test execution
    response = helper.invoke_agent(payload)
```

### Agent Mocking

Agent behavior is mocked for unit tests:

```python
with patch('agentcore_strands_agents.agent.agent') as mock_agent:
    mock_result = Mock()
    mock_result.message = "Test response"
    mock_agent.return_value = mock_result
    
    # Test agent invocation
    result = invoke(payload)
```

## Continuous Integration

### CI Configuration

For CI environments, use:

```bash
# Run tests excluding slow integration tests
pytest -m "not slow" --tb=short

# With coverage reporting
pytest -m "not slow" --cov=src/agentcore_strands_agents --cov-report=xml
```

### Test Environment

Tests are designed to work in various environments:

- **Local Development**: Full test suite including slow tests
- **CI/CD**: Fast tests excluding slow integration tests
- **Docker**: Containerized test execution

## Troubleshooting

### Common Issues

1. **agentcore command not found**
   - Ensure agentcore is installed: `pip install bedrock-agentcore`
   - Check PATH configuration

2. **Docker not available**
   - Install Docker Desktop
   - Ensure Docker daemon is running

3. **Memory tests failing**
   - Check that memory hook is properly configured
   - Verify memory ID is correct

4. **Integration tests timing out**
   - Increase timeout values in test configuration
   - Check system resources

### Debug Mode

Run tests with debug output:

```bash
pytest -v -s --tb=long
```

## Contributing

When adding new tests:

1. **Follow naming conventions**: `test_*.py` files, `test_*` functions
2. **Use appropriate markers**: `@pytest.mark.slow`, `@pytest.mark.integration`
3. **Add fixtures**: For reusable test components
4. **Mock external dependencies**: Avoid requiring external services
5. **Document test purpose**: Clear docstrings explaining test goals
