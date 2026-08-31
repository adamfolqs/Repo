"""Reconcile the outreach roster against what actually landed in Gmail.

Run this any time to refresh who has replied. It reads
`data/outreach/campaign_roster.csv`, matches each recipient against a Gmail
export of the campaign's replies, and writes the statuses back.

Deliberately split in two: this script does the matching and the file writing,
and a separate step fetches from Gmail. That way the reply data can be
refreshed from a real inbox without this script needing mail credentials, and
the matching logic stays testable offline.

Usage:
    # 1. dump replies (done by the assistant via the Gmail tools) into
    #    data/outreach/replies.json  -- a list of {from, date, snippet}
    # 2. python track_replies.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from pathlib import Path

ROSTER = Path("data/outreach/campaign_roster.csv")
REPLIES = Path("data/outreach/replies.json")

_ADDR_RE = re.compile(r"[\w.+-]+@[\w.-]+\.\w+")


def normalize_address(value: str | None) -> str:
    """Bare lowercase address out of a 'Name <addr@x.com>' header."""
    match = _ADDR_RE.search(value or "")
    return match.group(0).lower() if match else ""


def load_replies(path: Path = REPLIES) -> dict[str, dict]:
    """Newest reply per sender address."""
    if not path.exists():
        return {}
    by_sender: dict[str, dict] = {}
    for item in json.loads(path.read_text(encoding="utf-8")):
        address = normalize_address(item.get("from"))
        if not address:
            continue
        current = by_sender.get(address)
        if not current or (item.get("date") or "") > (current.get("date") or ""):
            by_sender[address] = item
    return by_sender


def classify(snippet: str) -> str:
    """Rough triage so the interesting replies surface first.

    Keyword-based and therefore fallible -- it decides sort order and a label,
    never whether someone is contacted again, so a misread costs a glance
    rather than a mistake. 'interested' is checked last so a message that both
    shares a number and declines is not read as a win.
    """
    text = (snippet or "").lower()
    if any(w in text for w in ("unsubscribe", "not interested", "no thanks",
                               "stop emailing", "remove me", "no gracias")):
        return "declined"
    if any(w in text for w in ("out of office", "away from", "on leave",
                               "automatic reply", "autoreply")):
        return "auto-reply"
    if any(w in text for w in ("undeliverable", "delivery has failed",
                               "address not found", "mailer-daemon")):
        return "bounced"
    if any(w in text for w in ("whatsapp", "+1", "+52", "my number", "rate",
                               "interested", "sounds good", "yes", "me interesa")):
        return "interested"
    return "replied"


def main() -> int:
    if not ROSTER.exists():
        print(f"no roster at {ROSTER}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(ROSTER.open(encoding="utf-8")))
    replies = load_replies()

    counts = {"interested": 0, "replied": 0, "declined": 0,
              "auto-reply": 0, "bounced": 0}
    for row in rows:
        if row["segment"] == "EXCLUDED":
            continue
        hit = replies.get((row["email"] or "").lower())
        if not hit:
            # Leave 'sent'/'not sent' alone: absence of a reply is not a status
            # change, and overwriting it would erase the send record.
            continue
        status = classify(hit.get("snippet", ""))
        row["reply_status"] = status
        row["replied_at"] = (hit.get("date") or "")[:19]
        row["reply_snippet"] = (hit.get("snippet") or "").replace("\n", " ")[:180]
        counts[status] = counts.get(status, 0) + 1

    with ROSTER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    sent = sum(1 for r in rows if r["sent_at"])
    replied = sum(counts[k] for k in ("interested", "replied", "declined"))
    print(f"roster: {len(rows)} rows, {sent} marked sent")
    for key, value in counts.items():
        if value:
            print(f"  {key:12} {value}")
    if sent:
        print(f"  reply rate  {replied / sent:.0%} ({replied}/{sent})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
