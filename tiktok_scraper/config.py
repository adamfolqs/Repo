"""Settings, loaded from .env with sane defaults."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


@dataclass
class Settings:
    provider: str = "playwright"
    brightdata_token: str = ""
    google_service_account_json: str = "./service_account.json"
    google_sheet_id: str = ""
    request_delay_seconds: float = 2.5
    max_retries: int = 3
    output_dir: Path = field(default_factory=lambda: Path("data/output"))

    @classmethod
    def load(cls) -> "Settings":
        _load_dotenv()
        return cls(
            provider=os.getenv("TIKTOK_PROVIDER", "playwright"),
            brightdata_token=os.getenv("BRIGHTDATA_API_TOKEN", ""),
            google_service_account_json=os.getenv(
                "GOOGLE_SERVICE_ACCOUNT_JSON", "./service_account.json"
            ),
            google_sheet_id=os.getenv("GOOGLE_SHEET_ID", ""),
            request_delay_seconds=float(os.getenv("REQUEST_DELAY_SECONDS", "2.5")),
            max_retries=int(os.getenv("MAX_RETRIES", "3")),
        )
