from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING
from unittest.mock import Mock, patch

from enea_client.app import App

if TYPE_CHECKING:
    from pytest import LogCaptureFixture

    from enea_client.config import Config


@patch("enea_client.app.subprocess")
@patch("enea_client.app.FileStore")
@patch("enea_client.app.Client")
def test_app_call_success_with_post_process(
    mock_client_class: Mock,
    mock_file_store: Mock,
    mock_subprocess: Mock,
    config: Config,
    caplog: LogCaptureFixture,
) -> None:
    # Setup authenticated client with data
    mock_client = Mock()
    mock_client.authenticate.return_value = True
    raw_data = '\x00"=""2025-09-01 00:59"""\x00;"0,507";"0";"0,507";"0"\n'
    mock_client.get_data.return_value = raw_data
    mock_client_class.return_value = mock_client

    # Mock file store to return file path
    mock_file_store.call.return_value = "/path/to/file.csv"

    # Set up config with post-process script
    config.post_process_script = "/path/to/script.sh"

    # Execute the main app functionality
    with caplog.at_level(logging.INFO):
        app = App(config)
        app.call()

    # Verify key behaviors
    mock_client.authenticate.assert_called_once()
    mock_client.get_data.assert_called_once()
    mock_file_store.call.assert_called_once_with(config, config.dates[0], raw_data)

    # Verify post-processing script execution
    mock_subprocess.run.assert_called_once_with(["/path/to/script.sh", "/path/to/file.csv"], check=True)

    # Verify logging
    assert "Running post-processing script: /path/to/script.sh, with ['/path/to/file.csv'] files" in caplog.text

@patch("enea_client.app.subprocess")
@patch("enea_client.app.Client")
def test_app_saves_raw_csv_without_post_process(
    mock_client_class: Mock,
    mock_subprocess: Mock,
    config: Config,
) -> None:
    config.dates = ["09.2025", "10.2025"]
    raw_data = (
        'Data;import;export;net_import;net_export\n'
        '\x00"=""2025-09-01 00:59"""\x00;"0,507";"0";"0,507";"0"\n'
        '"2025-09-01 01:59";"---";"0";"---";"0"\n'
    )
    mock_client = mock_client_class.return_value
    mock_client.authenticate.return_value = True
    mock_client.get_data.return_value = raw_data

    App(config).call()

    for date in config.dates:
        assert (Path(config.output_dir) / f"{date}.csv").read_bytes() == raw_data.encode("utf-8")
    assert mock_client.get_data.call_count == len(config.dates)
    mock_subprocess.run.assert_not_called()


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
