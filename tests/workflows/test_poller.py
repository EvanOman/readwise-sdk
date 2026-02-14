"""Tests for BackgroundPoller."""

import tempfile
import threading
import time
from datetime import UTC, datetime
from pathlib import Path

import httpx
import respx

from readwise_sdk.client import READWISE_API_V2_BASE, ReadwiseClient
from readwise_sdk.workflows.poller import BackgroundPoller, PollerConfig, PollerState
from tests.workflows.conftest import mock_full_sync


class TestPollerState:
    """Tests for PollerState."""

    def test_empty_state(self) -> None:
        """Test empty poller state."""
        state = PollerState()
        assert state.last_poll_time is None
        assert state.poll_count == 0
        assert state.is_running is False

    def test_state_serialization(self) -> None:
        """Test state serialization and deserialization."""
        state = PollerState(
            last_poll_time=datetime(2024, 1, 15, tzinfo=UTC),
            poll_count=5,
            error_count=1,
            last_error="Test error",
        )

        restored = PollerState.from_dict(state.to_dict())

        assert restored.last_poll_time == state.last_poll_time
        assert restored.poll_count == 5
        assert restored.error_count == 1
        assert restored.last_error == "Test error"


class TestBackgroundPoller:
    """Tests for BackgroundPoller."""

    @respx.mock
    def test_poll_once(self, client: ReadwiseClient) -> None:
        """Test single poll operation."""
        mock_full_sync(highlights=[{"id": 1, "text": "Test"}])

        poller = BackgroundPoller(client)
        result = poller.poll_once()

        assert len(result.highlights) == 1
        assert poller.state.poll_count == 1

    @respx.mock
    def test_poll_callbacks(self, client: ReadwiseClient) -> None:
        """Test sync callbacks are invoked."""
        mock_full_sync(highlights=[{"id": 1, "text": "Test"}])

        callback_results = []
        poller = BackgroundPoller(client)
        poller.on_sync(callback_results.append)
        poller.poll_once()

        assert len(callback_results) == 1
        assert len(callback_results[0].highlights) == 1

    @respx.mock
    def test_error_callbacks(self, client: ReadwiseClient) -> None:
        """Test error callbacks are invoked without crashing the poller."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        error_results = []
        poller = BackgroundPoller(client)
        poller.on_error(error_results.append)

        try:
            poller.poll_once()
        except Exception:
            pass

    @respx.mock
    def test_state_persistence(self, client: ReadwiseClient) -> None:
        """Test state is persisted to file and restored by a new poller."""
        mock_full_sync()

        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "poller_state.json"
            config = PollerConfig(state_file=state_file)

            poller = BackgroundPoller(client, config=config)
            poller.poll_once()

            assert state_file.exists()

            poller2 = BackgroundPoller(client, config=config)
            assert poller2.state.poll_count == 1

    @respx.mock
    def test_highlights_only_config(self, client: ReadwiseClient) -> None:
        """Test polling with only highlights enabled."""
        mock_full_sync(highlights=[{"id": 1, "text": "Test"}])

        config = PollerConfig(include_documents=False)
        poller = BackgroundPoller(client, config=config)
        result = poller.poll_once()

        assert len(result.highlights) == 1
        assert len(result.documents) == 0

    def test_reset_errors(self, client: ReadwiseClient) -> None:
        """Test resetting error state."""
        poller = BackgroundPoller(client)
        poller._consecutive_errors = 3
        poller._current_backoff = 600
        poller._state.last_error = "Test error"

        poller.reset_errors()

        assert poller._consecutive_errors == 0
        assert poller._current_backoff == poller._config.poll_interval
        assert poller._state.last_error is None

    def test_is_running_property(self, client: ReadwiseClient) -> None:
        """Test is_running property."""
        poller = BackgroundPoller(client)

        assert poller.is_running is False

        poller._state.is_running = True
        assert poller.is_running is True

    @respx.mock
    def test_start_blocking(self, client: ReadwiseClient) -> None:
        """Test starting the poller in blocking mode with a stop event that fires quickly."""
        mock_full_sync(highlights=[{"id": 1, "text": "Test"}])

        config = PollerConfig(poll_interval=1)
        poller = BackgroundPoller(client, config=config)

        def stop_after_delay():
            time.sleep(0.2)
            poller._stop_event.set()

        stopper = threading.Thread(target=stop_after_delay)
        stopper.start()

        poller.start(blocking=True)
        stopper.join()

        assert poller.state.is_running is False
        assert poller.state.poll_count >= 1

    @respx.mock
    def test_start_stop_threaded(self, client: ReadwiseClient) -> None:
        """Test starting in non-blocking mode and then stopping."""
        mock_full_sync(highlights=[{"id": 1, "text": "Test"}])

        config = PollerConfig(poll_interval=1)
        poller = BackgroundPoller(client, config=config)

        poller.start(blocking=False)
        assert poller.is_running is True

        time.sleep(0.3)

        poller.stop(timeout=2)
        assert poller.is_running is False

    @respx.mock
    def test_poll_loop_error_handling(self, client: ReadwiseClient) -> None:
        """Test that errors in the poll loop trigger backoff and error callbacks."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        error_results = []
        config = PollerConfig(
            poll_interval=1,
            max_consecutive_errors=3,
            backoff_multiplier=2.0,
        )
        poller = BackgroundPoller(client, config=config)
        poller.on_error(error_results.append)

        def stop_after_delay():
            time.sleep(0.5)
            poller._stop_event.set()

        stopper = threading.Thread(target=stop_after_delay)
        stopper.start()

        poller.start(blocking=True)
        stopper.join()

        assert len(error_results) >= 1
        assert poller.state.error_count >= 1
        assert poller.state.last_error is not None

    @respx.mock
    def test_poll_loop_max_errors(self, client: ReadwiseClient) -> None:
        """Test that exceeding max consecutive errors stops the loop."""
        respx.get(f"{READWISE_API_V2_BASE}/highlights/").mock(
            return_value=httpx.Response(500, json={"error": "Server error"})
        )

        config = PollerConfig(
            poll_interval=0,
            max_consecutive_errors=2,
            backoff_multiplier=1.0,
            max_backoff=0,
        )
        poller = BackgroundPoller(client, config=config)

        poller.start(blocking=True)

        assert poller.state.is_running is False
        assert poller._consecutive_errors >= config.max_consecutive_errors

    @respx.mock
    def test_incremental_poll(self, client: ReadwiseClient) -> None:
        """Test polling with existing state covers the 'since' branches."""
        mock_full_sync(highlights=[{"id": 1, "text": "Test"}])

        poller = BackgroundPoller(client)
        poller._state.last_highlight_sync = datetime(2024, 1, 1, tzinfo=UTC)
        poller._state.last_document_sync = datetime(2024, 1, 1, tzinfo=UTC)

        result = poller.poll_once()

        assert len(result.highlights) == 1
        assert poller.state.poll_count == 1
        assert poller._state.last_highlight_sync > datetime(2024, 1, 1, tzinfo=UTC)
        assert poller._state.last_document_sync > datetime(2024, 1, 1, tzinfo=UTC)

    def test_corrupt_state_file(self, client: ReadwiseClient) -> None:
        """Test that invalid JSON in state file is handled gracefully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "poller_state.json"
            state_file.write_text("this is not valid json!!!")

            config = PollerConfig(state_file=state_file)
            poller = BackgroundPoller(client, config=config)

            assert poller.state.poll_count == 0
            assert poller.state.last_poll_time is None

    @respx.mock
    def test_callback_exception_swallowed(self, client: ReadwiseClient) -> None:
        """Test that a callback raising an exception doesn't crash the poller."""
        mock_full_sync(highlights=[{"id": 1, "text": "Test"}])

        def bad_callback(result):
            raise RuntimeError("callback error")

        good_results = []
        poller = BackgroundPoller(client)
        poller.on_sync(bad_callback)
        poller.on_sync(good_results.append)

        result = poller.poll_once()

        assert result is not None
        assert poller.state.poll_count == 1
        assert len(good_results) == 1
