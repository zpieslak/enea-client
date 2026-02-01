from __future__ import annotations

import logging
import re

logger = logging.getLogger(__name__)

class Sanitizer:
    @staticmethod
    def call(data: str) -> str:
        # Drop lines containing "---"
        data = re.sub(r'^.*"---".*\n?', "", data, flags=re.MULTILINE)

        # Remove unwanted characters: null bytes and specific patterns
        data = re.sub(r'(\u0000|"="|""\u0000)', "", data)

        # Replace commas in numbers with dots (e.g., 1,23 -> 1.23)
        return re.sub(r"(?<=\d),(?=\d)", ".", data)
