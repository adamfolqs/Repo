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


_BOUNCE_RE = re.compile(
    r"(?:wasn't delivered to|not delivered to|failed permanently to)\s+"
    r"([\w.+-]+@[\w.-]+\.\w+)", re.I
)


def attribute(item: dict, roster_emails: set[str]) -> str:
    """Which recipient a reply belongs to — often not who sent it.

    Three cases seen in the first hour of the real campaign, all of which a
    plain sender-address match gets wrong:

    * a bounce arrives from mailer-daemon and names the dead address in its
      body, so the address is parsed out of the text;
    * an explicit `for` field, when the reply itself says who it is about
      (an agency answering on behalf of a creator it represents);
    * a colleague replies from their own address on the same domain
      (philip@mightyjoy.com for julie@, emma@ for lottie@), so a unique
      same-domain recipient is the match. Only when it is unique -- two
      creators at one agency would make the guess a coin flip.
    """
    sender = normalize_address(item.get("from"))
    if sender in roster_emails:
        return sender

    if "mailer-daemon" in sender or "postmaster" in sender:
        found = _BOUNCE_RE.search(item.get("snippet") or "")
        if found and found.group(1).lower() in roster_emails:
            return found.group(1).lower()
        return ""

    stated = normalize_address(item.get("for"))
    if stated in roster_emails:
        return stated

    domain = sender.rsplit("@", 1)[-1] if "@" in sender else ""
    if domain:
        same = [e for e in roster_emails if e.endswith("@" + domain)]
        if len(same) == 1:
            return same[0]
    return ""


def load_replies(path: Path = REPLIES, roster_emails: set[str] | None = None) -> dict[str, dict]:
    """Newest reply per *recipient*, attributed via `attribute()`."""
    if not path.exists():
        return {}
    roster_emails = roster_emails or set()
    by_recipient: dict[str, dict] = {}
    for item in json.loads(path.read_text(encoding="utf-8")):
        address = attribute(item, roster_emails)
        if not address:
            continue
        current = by_recipient.get(address)
        if not current or (item.get("date") or "") > (current.get("date") or ""):
            by_recipient[address] = item
    return by_recipient


# An autoresponder that says "thanks for your interest" reads as a hot lead to
# any keyword matcher. Since "interested" is the number that decides who gets
# chased first, auto-replies have to be ruled out before enthusiasm is scored,
# and the subject line is where they announce themselves most reliably.
_AUTO_SUBJECT = ("automatic reply", "auto reply", "auto-reply", "autoreply",
                 "out of office", "away from my", "thank you for your interest",
                 "thanks for reaching out! re:")
# A quoted price is the most reliable "yes, let's talk terms" signal there is,
# and it survives phrasing the keyword list will never anticipate -- "$200 per
# video", "1 video: $1,500", "my rate is 500 USD". Declines and autoresponders
# are ruled out before this is consulted, so a price inside a "no thanks" or an
# out-of-office cannot be misread as interest.
_PRICE_RE = re.compile(r"(?:[$£€]\s?\d|\b\d[\d,.]*\s?(?:usd|eur|gbp)\b)", re.I)

# ...but a figure quoted as past performance is a boast, not a price. Agencies
# open with "has driven $162k in GMV", which is a different claim from "$250 per
# video" and must not be read as one.
# The figure and the word can sit a clause apart -- "$162k in recent 30-day
# TikTok Shop GMV" -- so allow some distance, but not across a sentence break.
_BOAST_RE = re.compile(
    r"(?:[$£€]\s?[\d,.]+\s?[kmb]?\b[^.!?\n]{0,40}?"
    r"\b(?:gmv|sales|revenue|earnings|views)\b"
    r"|\b(?:gmv|sales|revenue|earnings)\b[^.!?\n]{0,20}?[$£€]\s?[\d,.]+)", re.I)

_AUTO_BODY = ("this is an automated", "automated response", "automatic reply",
              "out of office", "annual leave", "on leave", "i am away",
              "i'm away", "received your message and", "manage my own inbox",
              "review all collaboration requests")


def classify(snippet: str, subject: str = "") -> str:
    """Rough triage so the interesting replies surface first.

    Keyword-based and therefore fallible -- it decides sort order and a label,
    never whether someone is contacted again, so a misread costs a glance
    rather than a mistake. Order matters more than the keywords: a decline that
    also shares a number is a decline, and an autoresponder that thanks you for
    your interest is not a lead.
    """
    text = (snippet or "").lower()
    head = (subject or "").lower()
    if any(w in text for w in ("unsubscribe", "not interested", "no thanks",
                               "stop emailing", "remove me", "no gracias",
                               # Polite mismatch declines, which is how a
                               # wrongly-targeted creator actually answers.
                               "going to pass", "gonna pass", "pass on this",
                               "not a natural fit", "not a fit",
                               "not a good fit", "wouldn't be a fit",
                               "don't promote", "do not promote",
                               "have to decline", "will decline")):
        return "declined"
    if any(w in text for w in ("undeliverable", "delivery has failed",
                               "address not found", "mailer-daemon")):
        return "bounced"
    if any(w in head for w in _AUTO_SUBJECT) or any(w in text for w in _AUTO_BODY):
        return "auto-reply"
    # Someone who has said yes to terms is not the same as a warm lead, and
    # burying the two together loses the one row that needs invoicing rather
    # than chasing. Phrasing here has to imply commitment, not enthusiasm:
    # "sounds great, tell me more" is still only interest.
    if any(w in text for w in ("looking forward to getting started",
                               "let's get started", "lets get started",
                               "let's do it", "lets do it", "happy to proceed",
                               "count me in", "sign me up", "i'm in!", "im in!",
                               "we have a deal", "i accept", "acepto",
                               "vamos a hacerlo")):
        return "accepted"
    if any(w in text for w in ("whatsapp", "+1", "+52", "my number", "i charge",
                               "flat rate", "my rate", "interested", "sounds good",
                               "me interesa", "open to", "would love", "send me",
                               "more details", "learn more",
                               # A creator who answers with a price is a lead,
                               # even when the mail never says "interested" --
                               # a rate card IS the yes.
                               "per video", "my rates", "rate card",
                               "paid collaborations", "packages available",
                               # How a manager says yes on a creator's behalf.
                               "strong fit", "could be a fit", "good fit for")):
        return "interested"
    if _PRICE_RE.search(_BOAST_RE.sub(" ", text)):
        return "interested"
    return "replied"


def main() -> int:
    if not ROSTER.exists():
        print(f"no roster at {ROSTER}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(ROSTER.open(encoding="utf-8")))
    roster_emails = {
        (r["email"] or "").lower() for r in rows
        if r["segment"] != "EXCLUDED" and r["email"]
    }
    replies = load_replies(roster_emails=roster_emails)

    counts = {"accepted": 0, "interested": 0, "replied": 0, "declined": 0,
              "auto-reply": 0, "bounced": 0}
    for row in rows:
        if row["segment"] == "EXCLUDED":
            continue
        hit = replies.get((row["email"] or "").lower())
        if not hit:
            # Leave 'sent'/'not sent' alone: absence of a reply is not a status
            # change, and overwriting it would erase the send record.
            continue
        status = classify(hit.get("snippet", ""), hit.get("subject", ""))
        row["reply_status"] = status
        row["replied_at"] = (hit.get("date") or "")[:19]
        row["reply_snippet"] = (hit.get("snippet") or "").replace("\n", " ")[:180]
        counts[status] = counts.get(status, 0) + 1

    with ROSTER.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    sent = sum(1 for r in rows if r["sent_at"])
    replied = sum(counts[k] for k in ("accepted", "interested", "replied",
                                      "declined"))
    print(f"roster: {len(rows)} rows, {sent} marked sent")
    for key, value in counts.items():
        if value:
            print(f"  {key:12} {value}")
    if sent:
        print(f"  reply rate  {replied / sent:.0%} ({replied}/{sent})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
