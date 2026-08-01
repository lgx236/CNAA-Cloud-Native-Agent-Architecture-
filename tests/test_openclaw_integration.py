"""Tests for OpenClaw integration example."""

import unittest
from unittest.mock import Mock, patch

from examples.openclaw_integration import OpenClawCNAAIntegration


class TestOpenClawIntegration(unittest.TestCase):
    """Test OpenClaw integration example."""

    def setUp(self):
        """Set up test fixtures."""
        self.cnaa = OpenClawCNAAIntegration("http://localhost:8080")

    @patch("examples.openclaw_integration.requests.post")
    def test_store_memory(self, mock_post):
        """IMPLEMENTED: Verify store_memory calls CNAA correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok", "memory_id": "mem-001"}
        mock_post.return_value = mock_response

        result = self.cnaa.store_memory(
            agent_id="agent-001",
            memory_id="mem-001",
            memory_type="long_term",
            content={"task": "test"},
            tags=["test"],
            completion_score=0.9,
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["memory_id"], "mem-001")
        mock_post.assert_called_once()

    @patch("examples.openclaw_integration.requests.post")
    def test_get_memory(self, mock_post):
        """IMPLEMENTED: Verify get_memory calls CNAA correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "memory": {"memory_id": "mem-001", "content": {"task": "test"}},
        }
        mock_post.return_value = mock_response

        result = self.cnaa.get_memory("agent-001", "mem-001")

        self.assertEqual(result["status"], "ok")
        self.assertIn("memory", result)

    @patch("examples.openclaw_integration.requests.post")
    def test_list_memories(self, mock_post):
        """IMPLEMENTED: Verify list_memories calls CNAA correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "status": "ok",
            "memories": [{"memory_id": "mem-001"}, {"memory_id": "mem-002"}],
        }
        mock_post.return_value = mock_response

        result = self.cnaa.list_memories("agent-001")

        self.assertEqual(result["status"], "ok")
        self.assertEqual(len(result["memories"]), 2)

    @patch("examples.openclaw_integration.requests.post")
    def test_update_state(self, mock_post):
        """IMPLEMENTED: Verify update_state calls CNAA correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = self.cnaa.update_state(
            agent_id="agent-001",
            state_id="state-001",
            category="knowledge",
            content={"key": "value"},
        )

        self.assertEqual(result["status"], "ok")

    @patch("examples.openclaw_integration.requests.post")
    def test_update_preference(self, mock_post):
        """IMPLEMENTED: Verify update_preference calls CNAA correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = self.cnaa.update_preference(
            agent_id="agent-001",
            preference_id="pref-001",
            key="language",
            value={"preferred": "python"},
            importance=0.8,
        )

        self.assertEqual(result["status"], "ok")

    @patch("examples.openclaw_integration.requests.post")
    def test_update_environment(self, mock_post):
        """IMPLEMENTED: Verify update_environment calls CNAA correctly."""
        mock_response = Mock()
        mock_response.json.return_value = {"status": "ok"}
        mock_post.return_value = mock_response

        result = self.cnaa.update_environment(
            agent_id="agent-001",
            env_id="env-001",
            context={"os": "linux"},
        )

        self.assertEqual(result["status"], "ok")


if __name__ == "__main__":
    unittest.main()
