"""Pytest configuration and shared fixtures for agent tests."""

import json
import os
import subprocess
import time
import pytest
import requests
from typing import Dict, Any


@pytest.fixture(scope="session")
def agentcore_config() -> Dict[str, Any]:
    """Load agentcore configuration for testing."""
    # config_path = os.path.join(os.path.dirname(__file__), "..", ".bedrock_agentcore.yaml")
    # For testing, we'll use a simplified config
    return {
        "default_agent": "agent",
        "agents": {
            "agent": {
                "name": "agent",
                "entrypoint": "src/agentcore_strands_agents/agent.py",
                "platform": "linux/arm64",
                "container_runtime": "docker"
            }
        }
    }


@pytest.fixture(scope="session")
def test_payload() -> Dict[str, str]:
    """Standard test payload for agent invocations."""
    return {"prompt": "What did I just ask?"}


@pytest.fixture(scope="session")
def expected_response_structure() -> Dict[str, Any]:
    """Expected structure of agent responses."""
    return {
        "response": {
            "result": {
                "role": "assistant",
                "content": [{"text": str}]
            }
        }
    }


@pytest.fixture
def mock_agentcore_process():
    """Mock agentcore process for unit testing."""
    class MockProcess:
        def __init__(self):
            self.returncode = 0
            self.stdout = b'{"response": {"result": {"role": "assistant", "content": [{"text": "Test response"}]}}}'
            self.stderr = b''
        
        def communicate(self, input=None, timeout=None):  # noqa: A002  # vulture: ignore
            return self.stdout, self.stderr
        
        def poll(self):
            return self.returncode
        
        def terminate(self):
            pass
        
        def wait(self, timeout=None):
            return self.returncode
    
    return MockProcess()


@pytest.fixture
def agentcore_launch_command() -> str:
    """Command to launch agentcore locally."""
    return "agentcore launch --local"


@pytest.fixture
def agentcore_invoke_command() -> str:
    """Command template to invoke agentcore locally."""
    return "agentcore invoke --local '{}'"


class AgentCoreTestHelper:
    """Helper class for agentcore integration testing."""
    
    def __init__(self, base_dir: str):
        self.base_dir = base_dir
        self.process = None
        self.agent_url = "http://localhost:8080"
    
    def launch_agent(self, timeout: int = 30) -> bool:
        """Launch the agent and wait for it to be ready."""
        try:
            # Start the agent process
            self.process = subprocess.Popen(
                ["agentcore", "launch", "--local"],
                cwd=self.base_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Wait for the agent to be ready
            start_time = time.time()
            while time.time() - start_time < timeout:
                try:
                    response = requests.get(f"{self.agent_url}/health", timeout=1)
                    if response.status_code == 200:
                        return True
                except requests.exceptions.RequestException:
                    pass
                time.sleep(1)
            
            return False
        except Exception as e:
            print(f"Error launching agent: {e}")
            return False
    
    def invoke_agent(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Invoke the agent with a payload."""
        try:
            # Use subprocess to call agentcore invoke
            cmd = ["agentcore", "invoke", "--local", json.dumps(payload)]
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse the response from stdout
                response_text = result.stdout.strip()
                # Extract JSON from the response
                if "Response:" in response_text:
                    json_start = response_text.find("{", response_text.find("Response:"))
                    if json_start != -1:
                        json_text = response_text[json_start:]
                        return json.loads(json_text)
                # If no "Response:" found, try to parse the entire stdout as JSON
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    return {"error": "Could not parse response", "raw_output": response_text}
            else:
                return {
                    "error": "Invocation failed",
                    "stderr": result.stderr,
                    "stdout": result.stdout
                }
        except subprocess.TimeoutExpired:
            return {"error": "Invocation timed out"}
        except Exception as e:
            return {"error": f"Invocation error: {str(e)}"}
    
    def cleanup(self):
        """Clean up the agent process."""
        if self.process:
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None


@pytest.fixture
def agentcore_helper():
    """Fixture providing AgentCoreTestHelper instance."""
    base_dir = os.path.dirname(os.path.dirname(__file__))
    helper = AgentCoreTestHelper(base_dir)
    yield helper
    helper.cleanup()
