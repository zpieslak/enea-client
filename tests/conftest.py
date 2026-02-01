from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from enea_client.config import Config

if TYPE_CHECKING:
    from pathlib import Path

    from pytest_httpserver import HTTPServer


@pytest.fixture
def config(tmp_path: Path, httpserver: HTTPServer) -> Config:
    return Config(
        dates=["09.2025"],
        enea_login="test@example.com",
        enea_password="test_password", # noqa: S106
        enea_pod_guid="test-pod-guid-123",
        enea_url=httpserver.url_for(""),
        output_dir=str(tmp_path),
    )
