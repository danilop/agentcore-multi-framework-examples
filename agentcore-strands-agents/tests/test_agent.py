"""Tests for the agent module."""

import pytest
from unittest.mock import Mock, patch
from agentcore_strands_agents.agent import create_agent, invoke, main, DEFAULT_ACTOR_ID, DEFAULT_SESSION_ID


@pytest.mark.unit
def test_create_agent():
    """Test that agent can be created successfully."""
    agent = create_agent()
    assert agent is not None
    assert agent.state.get("actor_id") == DEFAULT_ACTOR_ID
    assert agent.state.get("session_id") == DEFAULT_SESSION_ID
    assert len(agent.tool_names) == 2
    assert "calculator" in agent.tool_names
    assert "retrieve_memories" in agent.tool_names


@pytest.mark.unit
@pytest.mark.memory
def test_create_agent_with_memory_hook():
    """Test that agent is created with memory hook."""
    agent = create_agent()
    # Check that hooks registry has callbacks (indicating memory hook was added)
    assert agent.hooks.has_callbacks() is True


@pytest.mark.unit
def test_invoke_function():
    """Test the invoke function with mock agent."""
    # Mock the agent to avoid actual execution
    with patch('agentcore_strands_agents.agent.agent') as mock_agent:
        mock_result = Mock()
        mock_result.message = "Test response"
        mock_agent.return_value = mock_result
        
        payload = {"prompt": "Test message"}
        result = invoke(payload)
        
        assert result == {"result": "Test response"}
        mock_agent.assert_called_once_with("Test message")


@pytest.mark.unit
def test_invoke_function_default_prompt():
    """Test the invoke function with default prompt."""
    with patch('agentcore_strands_agents.agent.agent') as mock_agent:
        mock_result = Mock()
        mock_result.message = "Default response"
        mock_agent.return_value = mock_result
        
        payload = {}
        result = invoke(payload)
        
        assert result == {"result": "Default response"}
        mock_agent.assert_called_once_with("Explain what you can do for me.")


@pytest.mark.unit
def test_invoke_function_error_handling():
    """Test the invoke function error handling."""
    with patch('agentcore_strands_agents.agent.agent') as mock_agent:
        mock_agent.side_effect = Exception("Test error")
        
        payload = {"prompt": "Test message"}
        result = invoke(payload)
        
        assert result == {"error": "An error occurred while processing your request"}


@pytest.mark.unit
@patch('agentcore_strands_agents.agent.app')
def test_main_function(mock_app):
    """Test the main function."""
    main()
    mock_app.run.assert_called_once()
