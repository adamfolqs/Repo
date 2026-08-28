"""Append rows straight into a Google Sheet.

Requires a Google Cloud service account:
  1. console.cloud.google.com -> create project -> enable "Google Sheets API"
  2. Create a service account -> Keys -> Add key -> JSON -> save as service_account.json
  3. Open your Sheet -> Share -> paste the service account's client_email -> Editor

Without step 3 you get a 403; it is the step everyone misses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Sequence

from pydantic import BaseModel

from .files import to_rows

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]


class SheetsSink:
    def __init__(self, service_account_json: str | Path, sheet_id: str):
        try:
            import gspread
            from google.oauth2.service_account import Credentials
        except ImportError as exc:  # pragma: no cover - depends on optional extra
            raise RuntimeError(
                "Google Sheets output needs extra packages:\n"
                "    pip install gspread google-auth"
            ) from exc

        key_path = Path(service_account_json)
        if not key_path.exists():
            raise FileNotFoundError(
                f"Service account key not found at {key_path}.\n"
                "See the setup steps at the top of tiktok_scraper/sinks/sheets.py"
            )

        creds = Credentials.from_service_account_file(str(key_path), scopes=SCOPES)
        self._client = gspread.authorize(creds)
        self._sheet_id = sheet_id
        self.service_account_email = creds.service_account_email

    def write(
        self,
        records: Sequence[BaseModel],
        columns: Sequence[str],
        worksheet_name: str,
        mode: str = "append",
    ) -> int:
        """Write records to a tab. mode='append' adds rows, 'replace' clears first.

        Returns the number of data rows written.
        """
        import gspread

        book = self._client.open_by_key(self._sheet_id)

        try:
            ws = book.worksheet(worksheet_name)
        except gspread.WorksheetNotFound:
            ws = book.add_worksheet(
                title=worksheet_name, rows=max(len(records) + 10, 100), cols=len(columns)
            )
            ws.append_row(list(columns), value_input_option="RAW")

        if mode == "replace":
            ws.clear()
            ws.append_row(list(columns), value_input_option="RAW")
        elif not ws.get_all_values():
            # Tab existed but was empty — still needs a header.
            ws.append_row(list(columns), value_input_option="RAW")

        rows = to_rows(records, columns)
        if rows:
            # USER_ENTERED so numbers land as numbers and URLs stay clickable.
            ws.append_rows(rows, value_input_option="USER_ENTERED")
        return len(rows)
