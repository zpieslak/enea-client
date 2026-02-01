from __future__ import annotations

import logging
import subprocess
from typing import TYPE_CHECKING

from enea_client.client import Client
from enea_client.utils.file_store import FileStore
from enea_client.utils.sanitizer import Sanitizer

if TYPE_CHECKING:
    from enea_client.config import Config

logger = logging.getLogger(__name__)

class App:
    def __init__(self, config: Config) -> None:
        self.config = config

    def call(self) -> None:
        client = Client(self.config)

        if not client.authenticate():
            logger.error("Authentication failed")
            return

        file_paths = []

        for date in self.config.dates:
            data = client.get_data(date)

            if data is None:
                logger.error("Failed to retrieve data")
                return

            sanitized_data = Sanitizer.call(data)

            file_path = FileStore.call(self.config, date, sanitized_data)

            file_paths.append(file_path)

        # Run post-processing script if configured and data was processed
        if self.config.post_process_script:
            logger.info(
                "Running post-processing script: %s, with %s files", self.config.post_process_script, file_paths,
            )

            subprocess.run([self.config.post_process_script, *map(str, file_paths)], check=True) # noqa: S603
