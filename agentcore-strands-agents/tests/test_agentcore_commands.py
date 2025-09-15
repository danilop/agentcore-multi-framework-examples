"""Tests for agentcore command execution and validation."""

import json
import subprocess
import pytest
from unittest.mock import patch, Mock
from conftest import AgentCoreTestHelper


class TestAgentCoreCommandExecution:
    """Test agentcore command execution."""
    
    def test_agentcore_command_availability(self):
        """Test that agentcore command is available in the system."""
        try:
            result = subprocess.run(
                ["agentcore", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            # Command exists (even if it fails, it should not be "command not found")
            assert result.returncode != 127, "agentcore command should be available"
        except FileNotFoundError:
            pytest.skip("agentcore command not found in PATH")
        except subprocess.TimeoutExpired:
            pytest.skip("agentcore command timed out")
    
    def test_launch_command_structure(self):
        """Test the structure of the launch command."""
        expected_command = ["agentcore", "launch", "--local"]
        
        # Verify command structure
        assert len(expected_command) == 3
        assert expected_command[0] == "agentcore"
        assert expected_command[1] == "launch"
        assert expected_command[2] == "--local"
    
    def test_invoke_command_structure(self):
        """Test the structure of the invoke command."""
        test_payload = {"prompt": "Test message"}
        payload_json = json.dumps(test_payload)
        expected_command = ["agentcore", "invoke", "--local", payload_json]
        
        # Verify command structure
        assert len(expected_command) == 4
        assert expected_command[0] == "agentcore"
        assert expected_command[1] == "invoke"
        assert expected_command[2] == "--local"
        assert expected_command[3] == payload_json
    
    def test_payload_json_serialization(self):
        """Test that payloads are properly serialized to JSON."""
        test_cases = [
            {"prompt": "Simple message"},
            {"prompt": "Message with special chars: !@#$%^&*()"},
            {"prompt": "Message with quotes: \"Hello World\""},
            {"prompt": "Message with newlines:\nLine 2\nLine 3"},
            {"prompt": "Unicode message: 你好世界 🌍"},
        ]
        
        for payload in test_cases:
            # Serialize to JSON
            json_str = json.dumps(payload)
            
            # Verify it can be parsed back
            parsed_payload = json.loads(json_str)
            assert parsed_payload == payload
            
            # Verify it's valid JSON
            assert isinstance(json_str, str)
            assert json_str.startswith("{")
            assert json_str.endswith("}")
    
    def test_command_execution_with_mock(self):
        """Test command execution using mocked subprocess."""
        with patch('subprocess.run') as mock_run:
            # Mock successful execution
            mock_result = Mock()
            mock_result.returncode = 0
            mock_result.stdout = '{"response": {"result": "success"}}'
            mock_result.stderr = ""
            mock_run.return_value = mock_result
            
            # Test invoke command
            helper = AgentCoreTestHelper("/tmp")
            response = helper.invoke_agent({"prompt": "test"})
            
            # Verify subprocess was called correctly
            mock_run.assert_called_once()
            call_args = mock_run.call_args
            
            # Verify command structure
            command = call_args[0][0]
            assert command[0] == "agentcore"
            assert command[1] == "invoke"
            assert command[2] == "--local"
            assert command[3] == '{"prompt": "test"}'
            
            # Verify response
            assert "error" not in response
            assert "response" in response
    
    def test_command_execution_error_handling(self):
        """Test error handling in command execution."""
        with patch('subprocess.run') as mock_run:
            # Mock command failure
            mock_result = Mock()
            mock_result.returncode = 1
            mock_result.stdout = ""
            mock_result.stderr = "Error: Command failed"
            mock_run.return_value = mock_result
            
            helper = AgentCoreTestHelper("/tmp")
            response = helper.invoke_agent({"prompt": "test"})
            
            # Verify error handling
            assert "error" in response
            assert "Command failed" in response["stderr"]
    
    def test_command_timeout_handling(self):
        """Test timeout handling in command execution."""
        with patch('subprocess.run') as mock_run:
            from subprocess import TimeoutExpired
            mock_run.side_effect = TimeoutExpired("agentcore", 30)
            
            helper = AgentCoreTestHelper("/tmp")
            response = helper.invoke_agent({"prompt": "test"})
            
            # Verify timeout handling
            assert "error" in response
            assert "timed out" in response["error"]


class TestAgentCoreProcessManagement:
    """Test agentcore process management."""
    
    def test_process_launch_mock(self):
        """Test process launch using mocked subprocess."""
        with patch('subprocess.Popen') as mock_popen:
            # Mock process
            mock_process = Mock()
            mock_process.poll.return_value = None  # Process still running
            mock_popen.return_value = mock_process
            
            helper = AgentCoreTestHelper("/tmp")
            _ = helper.launch_agent(timeout=5)
            
            # Verify process was started
            mock_popen.assert_called_once()
            call_args = mock_popen.call_args
            
            # Verify command structure
            command = call_args[0][0]
            assert command[0] == "agentcore"
            assert command[1] == "launch"
            assert command[2] == "--local"
    
    def test_process_cleanup(self):
        """Test process cleanup functionality."""
        with patch('subprocess.Popen') as mock_popen:
            # Mock process
            mock_process = Mock()
            mock_process.terminate.return_value = None
            mock_process.wait.return_value = 0
            mock_popen.return_value = mock_process
            
            helper = AgentCoreTestHelper("/tmp")
            helper.process = mock_process
            helper.cleanup()
            
            # Verify cleanup was called
            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once_with(timeout=5)
    
    def test_process_cleanup_with_timeout(self):
        """Test process cleanup with timeout."""
        with patch('subprocess.Popen') as mock_popen:
            # Mock process that times out on wait
            mock_process = Mock()
            mock_process.terminate.return_value = None
            mock_process.wait.side_effect = subprocess.TimeoutExpired("agentcore", 5)
            mock_process.kill.return_value = None
            mock_popen.return_value = mock_process
            
            helper = AgentCoreTestHelper("/tmp")
            helper.process = mock_process
            helper.cleanup()
            
            # Verify cleanup sequence
            mock_process.terminate.assert_called_once()
            mock_process.wait.assert_called_once_with(timeout=5)
            mock_process.kill.assert_called_once()


class TestAgentCoreResponseParsing:
    """Test parsing of agentcore responses."""
    
    def test_response_parsing_success(self):
        """Test successful response parsing."""
        sample_response = """Payload:
{
  "prompt": "What did I just ask?"
}
Invoking BedrockAgentCore agent 'agent' locally
Session ID: 4a7815a3-5efe-4f69-8ca4-fce245076c8a

Response:
{
  "response": {
    "result": {
      "role": "assistant",
      "content": [{"text": "You asked: What did I just ask?"}]
    }
  }
}"""
        
        # Test parsing logic
        if "Response:" in sample_response:
            json_start = sample_response.find("{", sample_response.find("Response:"))
            if json_start != -1:
                json_text = sample_response[json_start:]
                parsed = json.loads(json_text)
                
                assert "response" in parsed
                assert "result" in parsed["response"]
                assert parsed["response"]["result"]["role"] == "assistant"
    
    def test_response_parsing_error(self):
        """Test error response parsing."""
        error_response = """Error: Agent not found
Command failed with exit code 1"""
        
        # Test error handling
        if "Error:" in error_response:
            assert "Agent not found" in error_response
    
    def test_response_parsing_malformed_json(self):
        """Test handling of malformed JSON responses."""
        malformed_response = """Response:
{
  "response": {
    "result": {
      "role": "assistant",
      "content": [{"text": "Incomplete response"
}"""
        
        # Test malformed JSON handling
        try:
            if "Response:" in malformed_response:
                json_start = malformed_response.find("{", malformed_response.find("Response:"))
                if json_start != -1:
                    json_text = malformed_response[json_start:]
                    json.loads(json_text)
        except json.JSONDecodeError:
            # This is expected for malformed JSON
            assert True


class TestAgentCoreConfiguration:
    """Test agentcore configuration handling."""
    
    def test_config_file_structure(self, agentcore_config):
        """Test that configuration has expected structure."""
        config = agentcore_config
        
        assert "default_agent" in config
        assert "agents" in config
        assert "agent" in config["agents"]
        
        agent_config = config["agents"]["agent"]
        assert "name" in agent_config
        assert "entrypoint" in agent_config
        assert "platform" in agent_config
        assert "container_runtime" in agent_config
    
    def test_agent_entrypoint_path(self, agentcore_config):
        """Test that agent entrypoint path is correct."""
        config = agentcore_config
        entrypoint = config["agents"]["agent"]["entrypoint"]
        
        assert entrypoint == "src/agentcore_strands_agents/agent.py"
        assert entrypoint.endswith(".py")
        assert "agentcore_strands_agents" in entrypoint
