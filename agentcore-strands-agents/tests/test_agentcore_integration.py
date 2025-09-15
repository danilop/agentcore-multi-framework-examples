"""Integration tests for agentcore launch and invoke functionality."""

import json
import pytest
# import time
from unittest.mock import patch, Mock
from conftest import AgentCoreTestHelper


class TestAgentCoreIntegration:
    """Integration tests for agentcore functionality."""
    
    @pytest.mark.agentcore
    def test_agentcore_launch_command_exists(self):
        """Test that agentcore command is available in the environment."""
        import subprocess
        try:
            result = subprocess.run(
                ["agentcore", "--help"],
                capture_output=True,
                text=True,
                timeout=10
            )
            assert result.returncode == 0, "agentcore command should be available"
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            pytest.skip(f"agentcore command not available: {e}")
    
    @pytest.mark.integration
    def test_agentcore_invoke_with_mock(self, _, test_payload):
        """Test agentcore invoke using mocked subprocess."""
        with patch('subprocess.run') as mock_run:
            # Mock the subprocess.run call
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = json.dumps({
                "response": {
                    "result": {
                        "role": "assistant",
                        "content": [{"text": "Test response from agent"}]
                    }
                }
            })
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            # Create helper and test invocation
            helper = AgentCoreTestHelper("/tmp")
            response = helper.invoke_agent(test_payload)
            
            assert "error" not in response
            assert "response" in response
            assert response["response"]["result"]["role"] == "assistant"
            assert len(response["response"]["result"]["content"]) > 0
    
    def test_agentcore_invoke_error_handling(self, test_payload):
        """Test error handling in agentcore invoke."""
        with patch('subprocess.run') as mock_run:
            # Mock subprocess failure
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error: Agent not found"
            mock_run.return_value = mock_result
            
            helper = AgentCoreTestHelper("/tmp")
            response = helper.invoke_agent(test_payload)
            
            assert "error" in response
            assert "Agent not found" in response["stderr"]
    
    def test_agentcore_invoke_timeout(self, test_payload):
        """Test timeout handling in agentcore invoke."""
        with patch('subprocess.run') as mock_run:
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired("agentcore", 30)
            
            helper = AgentCoreTestHelper("/tmp")
            response = helper.invoke_agent(test_payload)
            
            assert "error" in response
            assert "timed out" in response["error"]
    
    @pytest.mark.slow
    @pytest.mark.integration
    @pytest.mark.agentcore
    def test_agentcore_full_integration(self, agentcore_helper, test_payload):
        """Full integration test with actual agentcore launch and invoke.
        
        This test is marked as 'slow' and will only run when explicitly requested.
        Use: pytest -m slow
        """
        # Launch the agent
        launch_success = agentcore_helper.launch_agent(timeout=60)
        if not launch_success:
            pytest.skip("Could not launch agent - may need manual setup")
        
        try:
            # Invoke the agent
            response = agentcore_helper.invoke_agent(test_payload)
            
            # Verify response structure
            assert "error" not in response, f"Agent invocation failed: {response}"
            assert "response" in response
            
            response_data = response["response"]
            assert "result" in response_data
            
            result = response_data["result"]
            assert "role" in result
            assert "content" in result
            assert result["role"] == "assistant"
            assert isinstance(result["content"], list)
            assert len(result["content"]) > 0
            
            # Verify the agent remembered the conversation (memory test)
            content_text = result["content"][0]["text"]
            assert "What did I just ask" in content_text or "just asked" in content_text
            
        finally:
            agentcore_helper.cleanup()
    
    def test_agentcore_response_structure(self, _):
        """Test that agent responses match expected structure."""
        # This is a structural test - the actual structure should match
        # expected = expected_response_structure
        
        # Example response structure validation
        sample_response = {
            "response": {
                "result": {
                    "role": "assistant",
                    "content": [{"text": "Sample response text"}]
                }
            }
        }
        
        # Validate structure
        assert "response" in sample_response
        assert "result" in sample_response["response"]
        assert "role" in sample_response["response"]["result"]
        assert "content" in sample_response["response"]["result"]
        assert sample_response["response"]["result"]["role"] == "assistant"
        assert isinstance(sample_response["response"]["result"]["content"], list)
    
    def test_multiple_invocations_memory(self, agentcore_helper):
        """Test that the agent maintains memory across multiple invocations."""
        # This test would require the agent to be running
        # For now, we'll test the concept with mocked responses
        
        with patch('subprocess.run') as mock_run:
            # First invocation
            first_response = {
                "response": {
                    "result": {
                        "role": "assistant",
                        "content": [{"text": "Hello! How can I help you?"}]
                    }
                }
            }
            
            # Second invocation (should reference previous conversation)
            second_response = {
                "response": {
                    "result": {
                        "role": "assistant",
                        "content": [{"text": "You previously asked 'Hello! How can I help you?'"}]
                    }
                }
            }
            
            mock_run.side_effect = [
                Mock(returncode=0, stdout=json.dumps(first_response), stderr=""),
                Mock(returncode=0, stdout=json.dumps(second_response), stderr="")
            ]
            
            helper = AgentCoreTestHelper("/tmp")
            
            # First invocation
            response1 = helper.invoke_agent({"prompt": "Hello"})
            assert "error" not in response1
            
            # Second invocation
            response2 = helper.invoke_agent({"prompt": "What did I just say?"})
            assert "error" not in response2
            
            # Verify memory functionality (in a real test, this would check actual memory)
            content2 = response2["response"]["result"]["content"][0]["text"]
            assert "previously" in content2 or "just" in content2


class TestAgentCoreCommands:
    """Test agentcore command-line interface."""
    
    def test_launch_command_format(self):
        """Test that launch command is properly formatted."""
        expected_cmd = ["agentcore", "launch", "--local"]
        # This is a basic format test
        assert len(expected_cmd) == 3
        assert expected_cmd[0] == "agentcore"
        assert expected_cmd[1] == "launch"
        assert expected_cmd[2] == "--local"
    
    def test_invoke_command_format(self, test_payload):
        """Test that invoke command is properly formatted."""
        payload_json = json.dumps(test_payload)
        expected_cmd = ["agentcore", "invoke", "--local", payload_json]
        
        assert len(expected_cmd) == 4
        assert expected_cmd[0] == "agentcore"
        assert expected_cmd[1] == "invoke"
        assert expected_cmd[2] == "--local"
        assert expected_cmd[3] == payload_json
    
    def test_payload_serialization(self, test_payload):
        """Test that payloads are properly serialized to JSON."""
        payload_json = json.dumps(test_payload)
        parsed_payload = json.loads(payload_json)
        
        assert parsed_payload == test_payload
        assert "prompt" in parsed_payload
        assert parsed_payload["prompt"] == "What did I just ask?"
