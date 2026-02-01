import logging
from pathlib import Path

from pytest import LogCaptureFixture

from enea_client.config import Config
from enea_client.utils.file_store import FileStore


def test_file_store_successful_write(config: Config, caplog: LogCaptureFixture) -> None:
    test_data = "test,data,content\n1,2,3\n4,5,6"

    with caplog.at_level(logging.INFO):
        result = FileStore.call(config, "09.2025", test_data)

    # Check that file was created and returned
    assert result is not None
    assert isinstance(result, Path)
    assert result.exists()
    assert result.name == "09.2025.csv"

    # Check file contents
    assert result.read_text(encoding="utf-8") == test_data

    # Check logging
    assert f"Saving file to: {result}" in caplog.text

