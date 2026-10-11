import logging
from pathlib import Path

from pytest import LogCaptureFixture

from enea_client.config import Config
from enea_client.utils.file_store import FileStore


def test_file_store_successful_write(config: Config, caplog: LogCaptureFixture) -> None:
    test_data = (
        'Data;import;export;net_import;net_export\n'
        '\x00"=""2025-09-01 00:59"""\x00;"0,507";"0";"0,507";"0"\n'
        '"2025-09-01 01:59";"---";"0";"---";"0"\n'
    )

    with caplog.at_level(logging.INFO):
        result = FileStore.call(config, "09.2025", test_data)

    # Check that file was created and returned
    assert result is not None
    assert isinstance(result, Path)
    assert result.exists()
    assert result.name == "09.2025.csv"

    # Check file contents
    assert result.read_text(encoding="utf-8") == test_data
    assert result.read_bytes() == test_data.encode("utf-8")

    # Check logging
    assert f"Saving file to: {result}" in caplog.text

