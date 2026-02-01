from __future__ import annotations

from dataclasses import dataclass, field
from zoneinfo import ZoneInfo


@dataclass
class Config:
    dates: list[str]
    enea_login: str
    enea_password: str
    enea_pod_guid: str
    output_dir: str
    post_process_script: str | None = None

    connection_timeout: int = 60
    enea_url: str = "https://ebok.enea.pl"
    enea_timezone: ZoneInfo = field(default_factory=lambda: ZoneInfo("Europe/Warsaw"))
