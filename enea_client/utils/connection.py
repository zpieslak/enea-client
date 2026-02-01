from __future__ import annotations

import http.client as http_client
import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING
from urllib.parse import urlparse

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger(__name__)

@contextmanager
def open_connection(url: str, timeout: int) -> Generator[http_client.HTTPConnection, None, None]:
    parsed_url = urlparse(url)

    connection_class = (
        http_client.HTTPSConnection if parsed_url.scheme == "https" else http_client.HTTPConnection
    )

    connection = connection_class(
        host=str(parsed_url.hostname),
        port=parsed_url.port,
        timeout=timeout,
    )

    connection.set_debuglevel(
        1 if logger.getEffectiveLevel() < logging.INFO else 0,
    )

    try:
        yield connection
    finally:
        connection.close()
