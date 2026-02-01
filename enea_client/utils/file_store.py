from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from enea_client.config import Config

logger = logging.getLogger(__name__)

class FileStore:
    @staticmethod
    def call(config: Config, date: str, data: str) -> None | Path:
        output_file_path = Path(f"{config.output_dir}/{date}.csv")

        logger.info("Saving file to: %s", output_file_path)
        output_file_path.write_text(data, encoding="utf-8")

        return output_file_path
