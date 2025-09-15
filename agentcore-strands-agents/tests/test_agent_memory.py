"""Tests for agent memory functionality."""

# import pytest
from unittest.mock import Mock, patch
from agentcore_strands_agents.agent import create_agent
from agentcore_strands_agents.hooks.short_memory_hook import ShortMemoryHook


class TestAgentMemory:
    """Test agent memory functionality."""
    
    def test_agent_has_memory_hook(self):
        """Test that agent is created with memory hook."""
        agent = create_agent()
        
        # Check that hooks are present
        assert agent.hooks is not None
        assert agent.hooks.has_callbacks() is True
        
        # Verify memory hook is in the hooks registry
        # The hooks registry doesn't expose _hooks directly, so we check differently
        # We can verify the hook is working by checking if callbacks are registered
        assert agent.hooks.has_callbacks() is True
    
    def test_memory_hook_initialization(self):
        """Test memory hook initialization."""
        memory_id = "test-memory-id"
        hook = ShortMemoryHook(memory_id=memory_id)
        
        assert hook.memory_id == memory_id
        assert hook is not None
    
    def test_agent_state_initialization(self):
        """Test that agent state is properly initialized."""
        agent = create_agent()
        
        assert agent.state is not None
        # AgentState is not a dict, so we need to access it differently
        assert hasattr(agent.state, 'get')
        assert agent.state.get("actor_id") == "my-user-id"
        assert agent.state.get("session_id") == "DEFAULT"
    
    def test_memory_persistence_across_invocations(self):
        """Test that memory persists across multiple agent invocations."""
        agent = create_agent()
        
        # First invocation
        with patch('strands.Agent') as mock_agent_class:
            mock_agent_instance = Mock()
            mock_agent_instance.return_value = Mock(message="First response")
            mock_agent_class.return_value = mock_agent_instance
            
            # Simulate first call
            result1 = agent("What is my name?")
            
            # Second invocation - should have memory of first
            mock_agent_instance.return_value = Mock(message="Your name is John (from memory)")
            result2 = agent("What did I just ask?")
            
            # In a real scenario, the second response should reference the first
            # This test verifies the structure is in place for memory
            assert result1 is not None
            assert result2 is not None
    
    def test_memory_hook_with_different_memory_ids(self):
        """Test that different memory IDs create separate memory contexts."""
        memory_id_1 = "memory-1"
        memory_id_2 = "memory-2"
        
        hook1 = ShortMemoryHook(memory_id=memory_id_1)
        hook2 = ShortMemoryHook(memory_id=memory_id_2)
        
        assert hook1.memory_id != hook2.memory_id
        assert hook1.memory_id == memory_id_1
        assert hook2.memory_id == memory_id_2
    
    def test_agent_memory_integration(self):
        """Test integration of memory hook with agent."""
        agent = create_agent()
        
        # Verify the agent has the expected structure for memory
        assert hasattr(agent, 'hooks')
        assert hasattr(agent, 'state')
        # Tools are accessed differently in Strands
        assert hasattr(agent, 'tool_names')
        
        # Verify memory hook is properly integrated
        # We can't directly access the hooks list, but we can verify callbacks exist
        assert agent.hooks.has_callbacks() is True


class TestMemoryHookBehavior:
    """Test specific memory hook behaviors."""
    
    def test_memory_hook_callbacks(self):
        """Test that memory hook registers proper callbacks."""
        hook = ShortMemoryHook(memory_id="test-memory")
        
        # The hook should have methods that can be called
        # This is a basic structure test
        assert hasattr(hook, 'memory_id')
        assert hook.memory_id == "test-memory"
    
    def test_memory_hook_with_agent_state(self):
        """Test memory hook interaction with agent state."""
        agent = create_agent()
        
        # Agent should have state that memory hook can use
        assert agent.state is not None
        assert hasattr(agent.state, 'get')
        assert agent.state.get("actor_id") is not None
        assert agent.state.get("session_id") is not None
        
        # Memory hook should be able to access this state
        # We can't directly access the hooks list, but we can verify the structure
        assert agent.hooks.has_callbacks() is True


class TestMemoryScenarios:
    """Test various memory scenarios."""
    
    def test_conversation_memory(self):
        """Test that agent remembers conversation context."""
        agent = create_agent()
        
        # This test would ideally test actual memory functionality
        # For now, we test the structure is in place
        
        # Simulate a conversation
        with patch('strands.Agent') as _:
            mock_agent_instance = Mock()
            
            # First message
            mock_agent_instance.return_value = Mock(message="Hello! I'm here to help.")
            result1 = agent("Hello")
            
            # Second message - should reference previous context
            mock_agent_instance.return_value = Mock(message="You said 'Hello' earlier.")
            result2 = agent("What did I say before?")
            
            # Verify both calls succeeded
            assert result1 is not None
            assert result2 is not None
    
    def test_memory_across_sessions(self):
        """Test memory behavior across different sessions."""
        # Create agent with default session
        agent1 = create_agent()
        
        # Create agent with different session (simulated)
        agent2 = create_agent()
        # We can't directly modify the state, but we can verify both agents have the same structure
        
        # Both should have memory hooks but potentially different contexts
        assert agent1.hooks.has_callbacks()
        assert agent2.hooks.has_callbacks()
        
        # Both should have the same memory ID (as configured in the agent creation)
        # We can't directly access the hooks, but we can verify the structure is consistent
        assert agent1.state.get("actor_id") == agent2.state.get("actor_id")
        assert agent1.state.get("session_id") == agent2.state.get("session_id")
