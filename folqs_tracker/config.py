"""Settings for the weekly tracker, loaded from .env."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

# The Folqs TikTok Shop Wiki and the retainer sample tracker linked from its
# Homepage tab. Defaults so a fresh checkout points at the right books.
DEFAULT_WIKI_SHEET_ID = "1exP-EUYUuTmQZevSn-jeg02sBJF9KHZUA4YU1abFJkE"
DEFAULT_SAMPLES_SHEET_ID = "1e8OsOnI9smEnoDsnHARr8nB-qA7jDARoOtmQiiOao7Q"


def _load_dotenv() -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass


@dataclass
class TrackerSettings:
    # --- Google Sheets ---
    service_account_json: str = "./service_account.json"
    wiki_sheet_id: str = DEFAULT_WIKI_SHEET_ID
    weekly_tab: str = "Weekly Performance (1)"
    samples_sheet_id: str = DEFAULT_SAMPLES_SHEET_ID
    samples_tab: str = "Tracker"

    # --- Claude ---
    anthropic_api_key: str = ""
    model: str = "claude-opus-5"

    # --- Inputs / outputs ---
    screenshot_dir: Path = field(default_factory=lambda: Path("data/tracking/inbox"))
    archive_dir: Path = field(default_factory=lambda: Path("data/tracking/archive"))
    snapshot_dir: Path = field(default_factory=lambda: Path("data/tracking/snapshots"))

    # --- Browser capture ---
    session_file: Path = field(default_factory=lambda: Path(".tiktok_session.json"))
    capture_plan: Path = field(default_factory=lambda: Path("capture_plan.json"))
    capture_headless: bool = True

    # --- Email digest ---
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_user: str = ""
    smtp_password: str = ""
    email_from: str = ""
    email_to: str = "adam@folqs.co"

    # --- Telegram ---
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    @classmethod
    def load(cls) -> "TrackerSettings":
        _load_dotenv()
        env = os.getenv
        return cls(
            service_account_json=env("GOOGLE_SERVICE_ACCOUNT_JSON", "./service_account.json"),
            wiki_sheet_id=env("FOLQS_WIKI_SHEET_ID", DEFAULT_WIKI_SHEET_ID),
            weekly_tab=env("FOLQS_WEEKLY_TAB", "Weekly Performance (1)"),
            samples_sheet_id=env("SAMPLES_TRACKER_SHEET_ID", DEFAULT_SAMPLES_SHEET_ID),
            samples_tab=env("SAMPLES_TRACKER_TAB", "Tracker"),
            anthropic_api_key=env("ANTHROPIC_API_KEY", ""),
            model=env("TRACKER_MODEL", "claude-opus-5"),
            screenshot_dir=Path(env("TRACKER_SCREENSHOT_DIR", "data/tracking/inbox")),
            archive_dir=Path(env("TRACKER_ARCHIVE_DIR", "data/tracking/archive")),
            snapshot_dir=Path(env("TRACKER_SNAPSHOT_DIR", "data/tracking/snapshots")),
            session_file=Path(env("TIKTOK_SESSION_FILE", ".tiktok_session.json")),
            capture_plan=Path(env("TRACKER_CAPTURE_PLAN", "capture_plan.json")),
            capture_headless=env("TRACKER_CAPTURE_HEADLESS", "1") not in ("0", "false", "False"),
            smtp_host=env("SMTP_HOST", ""),
            smtp_port=int(env("SMTP_PORT", "587")),
            smtp_user=env("SMTP_USER", ""),
            smtp_password=env("SMTP_PASSWORD", ""),
            email_from=env("REPORT_EMAIL_FROM", env("SMTP_USER", "")),
            email_to=env("REPORT_EMAIL_TO", "adam@folqs.co"),
            telegram_bot_token=env("TELEGRAM_BOT_TOKEN", ""),
            telegram_chat_id=env("TELEGRAM_CHAT_ID", ""),
        )

    @property
    def email_configured(self) -> bool:
        return bool(self.smtp_host and self.email_from and self.email_to)

    @property
    def telegram_configured(self) -> bool:
        return bool(self.telegram_bot_token and self.telegram_chat_id)
