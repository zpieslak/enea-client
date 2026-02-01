from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from enea_client.app import App

if TYPE_CHECKING:
    from pytest import LogCaptureFixture

    from enea_client.config import Config


@patch("enea_client.app.subprocess")
@patch("enea_client.app.FileStore")
@patch("enea_client.app.Sanitizer")
@patch("enea_client.app.Client")
def test_app_call_success_with_post_process(
    mock_client_class: Mock,
    mock_sanitizer: Mock,
    mock_file_store: Mock,
    mock_subprocess: Mock,
    config: Config,
    caplog: LogCaptureFixture,
) -> None:
    # Setup authenticated client with data
    mock_client = Mock()
    mock_client.authenticate.return_value = True
    mock_client.get_data.return_value = {"test": "data"}
    mock_client_class.return_value = mock_client

    # Mock sanitizer to return processed data
    mock_sanitizer.call.return_value = {"sanitized": "data"}

    # Mock file store to return file path
    mock_file_store.call.return_value = "/path/to/file.json"

    # Set up config with post-process script
    config.post_process_script = "/path/to/script.sh"

    # Execute the main app functionality
    with caplog.at_level(logging.INFO):
        app = App(config)
        app.call()

    # Verify key behaviors
    mock_client.authenticate.assert_called_once()
    mock_client.get_data.assert_called_once()
    mock_sanitizer.call.assert_called_once_with({"test": "data"})
    mock_file_store.call.assert_called_once_with(config, config.dates[0], {"sanitized": "data"})

    # Verify post-processing script execution
    mock_subprocess.run.assert_called_once_with(["/path/to/script.sh", "/path/to/file.json"], check=True)

    # Verify logging
    assert "Running post-processing script: /path/to/script.sh, with ['/path/to/file.json'] files" in caplog.text

@patch("enea_client.app.Client")
def test_app_call_authentication_failure(mock_client_class: Mock, config: Config) -> None:
    # Setup unauthenticated client
    mock_client = Mock()
    mock_client.authenticate.return_value = False
    mock_client_class.return_value = mock_client

    # Execute app with failed authentication
    app = App(config)
    app.call()

    # Verify early return on auth failure
    mock_client.authenticate.assert_called_once()
    mock_client.get_data.assert_not_called()

@patch("enea_client.app.Client")
def test_app_call_data_retrieval_failure(mock_client_class: Mock, config: Config, caplog: LogCaptureFixture) -> None:
    # Setup authenticated client that returns None data
    mock_client = Mock()
    mock_client.authenticate.return_value = True
    mock_client.get_data.return_value = None
    mock_client_class.return_value = mock_client

    # Execute app with data retrieval failure
    with caplog.at_level(logging.ERROR):
        app = App(config)
        app.call()

    # Verify authentication and data retrieval were attempted
    mock_client.authenticate.assert_called_once()
    mock_client.get_data.assert_called_once()

    # Verify error was logged
    assert "Failed to retrieve data" in caplog.text
