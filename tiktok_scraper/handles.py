"""Turn a creator's display name into a *verified* @handle, or nothing.

The sourcing sheet lists creators by the label read off a screen recording,
not by handle. Those labels cannot be turned into handles by transformation:
TikTok display names are not unique, and a handle often looks nothing like the
name it shows (Creakzzz -> @creakzshop, JESSYKARINA -> @mrsplaytoomuch).

So this never *derives* a handle. It proposes candidates, opens each one's
profile, and keeps it only if the account that actually loaded says it is that
person -- its display name or its handle matches the label. Anything else is
reported unresolved, with the candidates listed, because a wrong handle sends
outreach to a stranger who never mentioned the product.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from typing import Iterable, Optional

from .providers.base import BlockedError, ProviderError

# Labels that are not names at all, or are too common to ever resolve to one
# account. Searching these burns requests and can only produce a wrong answer.
_UNRESOLVABLE = {
    "unreadable creator", "unknown", "n/a", "", "-",
}
_GENERIC_SINGLE_NAMES = {
    "jacquie", "taylor", "nikki", "shawna", "julissa", "sarah", "ashley",
    "jessica", "maria", "ana", "laura", "karen", "michelle", "amanda",
    "brittany", "megan", "rachel", "lauren", "kelsey", "chloe", "sofia",
}


def normalize(value: str | None) -> str:
    """Comparison key: accent-folded, lowercased, alphanumerics only."""
    if not value:
        return ""
    text = unicodedata.normalize("NFKD", str(value))
    text = "".join(c for c in text if not unicodedata.combining(c))
    return "".join(c for c in text.lower() if c.isalnum())


def is_worth_resolving(name: str | None) -> bool:
    """Whether a label could identify one account at all."""
    if not name:
        return False
    cleaned = name.strip().lower()
    if cleaned in _UNRESOLVABLE:
        return False
    if cleaned in _GENERIC_SINGLE_NAMES:
        return False
    # A bare first name shorter than this matches too many accounts to verify.
    if len(cleaned.split()) == 1 and len(normalize(cleaned)) < 5:
        return False
    return True


def candidate_handles(name: str) -> list[str]:
    """Handles worth *checking* for a label — never returned as answers.

    Ordered cheapest-first: labels that are already a handle, then the usual
    spacing conventions.
    """
    raw = name.strip().lstrip("@")
    words = [w for w in re.split(r"[^A-Za-z0-9]+", raw) if w]
    if not words:
        return []

    lowered = [w.lower() for w in words]
    joined = "".join(lowered)
    out = [
        raw.lower() if re.fullmatch(r"[A-Za-z0-9_.]+", raw) else "",
        joined,
        ".".join(lowered),
        "_".join(lowered),
        joined + "official",
    ]
    if len(lowered) > 2:
        # "Giselle De Garcia" is usually @gisellegarcia, not @gisellidegarcia.
        particles = {"de", "la", "del", "el", "van", "der", "di", "da"}
        trimmed = [w for w in lowered if w not in particles]
        if trimmed and trimmed != lowered:
            out.append("".join(trimmed))
            out.append(".".join(trimmed))
    seen, ordered = set(), []
    for candidate in out:
        if candidate and candidate not in seen and len(candidate) >= 2:
            seen.add(candidate)
            ordered.append(candidate)
    return ordered


@dataclass
class Resolution:
    name: str
    handle: str = ""
    profile_url: str = ""
    confidence: str = "not found"
    evidence: str = ""
    followers: Optional[int] = None
    checked: list[str] = field(default_factory=list)


def resolve_name(
    name: str,
    provider,
    known_creators: dict[str, object] | None = None,
    extra_candidates: Iterable[str] = (),
) -> Resolution:
    """Verify a label against real profiles. Returns a Resolution, never a guess."""
    result = Resolution(name=name)
    key = normalize(name)

    # Cheapest evidence first: someone already scraped in this run whose
    # display name or handle matches, and who we therefore know posts here.
    for creator in (known_creators or {}).values():
        if key and key in {normalize(getattr(creator, "handle", "")),
                           normalize(getattr(creator, "nickname", ""))}:
            result.handle = creator.handle
            result.profile_url = f"https://www.tiktok.com/@{creator.handle}"
            result.confidence = "confirmed (matched a scraped creator)"
            result.evidence = f"display name '{creator.nickname}' matches the label"
            result.followers = getattr(creator, "followers", None)
            return result

    if not is_worth_resolving(name):
        result.confidence = "unresolvable label"
        result.evidence = (
            "too generic to identify one account — several real accounts share it"
        )
        return result

    for candidate in list(candidate_handles(name)) + list(extra_candidates):
        result.checked.append(candidate)
        try:
            creator = provider.fetch_creator(candidate)
        except BlockedError:
            raise
        except ProviderError:
            continue

        landed, nickname = normalize(creator.handle), normalize(creator.nickname)

        # The labels came off a screen recording of TikTok Shop, which shows
        # each creator's *display name*. So a display-name match is the
        # confirmation; a handle-only match is not.
        if key and key == nickname:
            result.handle = creator.handle
            result.profile_url = f"https://www.tiktok.com/@{creator.handle}"
            result.confidence = "confirmed (profile verified)"
            result.evidence = (
                f"landed on @{creator.handle}, display name "
                f"'{creator.nickname}' — matches the label"
            )
            result.followers = creator.followers
            return result

        if key and key == landed:
            # The label spells a real handle, but that account displays a
            # different name -- which is exactly how the known misses look
            # (Creakzzz is @creakzshop, and @creakzzz is somebody else).
            # Record it, clearly marked, and keep checking.
            if not result.handle:
                result.handle = creator.handle
                result.profile_url = f"https://www.tiktok.com/@{creator.handle}"
                result.confidence = "unconfirmed — handle matches, display name differs"
                result.evidence = (
                    f"@{creator.handle} exists but displays '{creator.nickname}'; "
                    "verify before contacting"
                )
                result.followers = creator.followers
            continue

        # The account exists but is someone else. Worth recording: it is
        # exactly the handle a name-to-handle guess would have produced.
        if not result.evidence:
            result.evidence = (
                f"@{candidate} exists but is '{creator.nickname}', not this creator"
            )

    # Keep an unconfirmed handle found along the way rather than discarding it;
    # only a search that turned up nothing at all is "not found".
    if not result.handle:
        result.confidence = "not found"
        if not result.evidence:
            result.evidence = "checked: " + ", ".join(f"@{c}" for c in result.checked)
    return result
