"""Tests for agent sender (send_batch with retries)."""
import pytest
from unittest.mock import patch, MagicMock

import httpx

from agent.sender import send_batch, DEFAULT_BACKOFF


def test_send_batch_success():
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        ok, code = send_batch("http://localhost:8000/api/v1/events", [{"a": 1}])
        assert ok is True
        assert code == 200
        mock_post.assert_called_once()
        call_kw = mock_post.call_args[1]
        assert call_kw["json"] == [{"a": 1}]
        assert "Content-Type" in call_kw["headers"]


def test_send_batch_with_api_key():
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=200)
        send_batch("http://localhost/api/v1/events", [], api_key="secret")
        call_kw = mock_post.call_args[1]
        assert call_kw["headers"]["Authorization"] == "Bearer secret"


def test_send_batch_client_error_no_retry():
    with patch("httpx.post") as mock_post:
        mock_post.return_value = MagicMock(status_code=400)
        ok, code = send_batch("http://localhost/api/v1/events", [])
        assert ok is False
        assert code == 400
        mock_post.assert_called_once()


def test_send_batch_server_error_retries():
    with patch("httpx.post") as mock_post:
        with patch("time.sleep"):
            mock_post.return_value = MagicMock(status_code=503)
            ok, code = send_batch("http://localhost/api/v1/events", [])
            assert ok is False
            # After all retries exhausted, sender returns (False, 0)
            assert code == 0
            assert mock_post.call_count == len(DEFAULT_BACKOFF)
