"""Source video URLs from TikTok's keyword landing pages.

`/search?q=` is login-walled for logged-out users -- the grid renders as
skeleton placeholders and the results XHR is never issued. `/tag/<hashtag>`
gives nothing either. But `/discover/<keyword>` still renders a real video
grid, and it is the one keyword-driven surface that does.

So discovery is: ask a discover page for its grid, scroll it, and read the
`<a href=".../@handle/video/id">` anchors. That yields URLs and handles only --
the grid carries no engagement numbers. Those come from HttpSSRProvider,
which reads each video's own page. Splitting it that way is deliberate:
nothing here has to estimate a like count, and a video we cannot resolve ends
up with empty cells rather than invented ones.
"""

from __future__ import annotations

import re
import time

from .base import BlockedError, ProviderError
from .playwright_provider import _CAPTCHA_MARKERS, PlaywrightProvider

_VIDEO_HREF_RE = re.compile(r"/@([A-Za-z0-9_.-]+)/video/(\d{15,})")
_DISCOVER_HREF_RE = re.compile(r"/discover/([a-z0-9\-]+)")

# TikTok slugifies discover keywords: spaces and '#' become hyphens.
_SLUG_RE = re.compile(r"[^a-z0-9]+")

# Discover pages link to related keyword pages, which is a crawlable graph --
# but it drifts fast. Two hops off "bovine colostrum" is cattle husbandry in
# Portuguese. A related slug is only followed if it still looks like this
# market: the topic itself, a competitor, or the adjacent gut/wellness terms
# the brief asked for.
_RELEVANT_SLUG_HINTS = (
    "colostrum", "calostro", "colostro", "kolostrum",
    "armra", "miracle-moo", "miraclemoo", "micro-moo", "wondercow", "wonder-cow",
    "cowabunga", "cowboy", "rhea", "wellah", "cymbiotika", "lemme", "nutricost",
    "bloom-nutrition", "micro-ingredients", "physicians-choice", "magic-milk",
)
# Adjacent wellness terms are useful as *seeds* -- plenty of colostrum content
# ranks under them -- but must not be crawled onwards. Following them walked
# straight into the generic wellness corpus ('gut-health-meaning' and its own
# 16 neighbours), and since resolving a video costs a request each, a low-
# precision branch is paid for in the stage that is actually the bottleneck.
# Farming/veterinary language. Note what is deliberately NOT here: 'bovino',
# 'bovina' and 'bovinos' are the Spanish *product* words ("calostro bovino"),
# so excluding them would throw away exactly the Spanish-language content the
# brief asks for. Only terms with no consumer-supplement reading belong here.
_IRRELEVANT_SLUG_HINTS = (
    "razas", "inseminar", "insemination", "inseminatrice", "engorde",
    "curral", "confinamento", "steakhouse", "restaurante", "gelatina",
    "grenetina", "vacuno", "ganado", "veterinar", "cisticercose", "gabarro",
    "comederos", "saleros", "bezerro", "ternero", "becerro", "ordeño",
)


def slugify(keyword: str) -> str:
    return _SLUG_RE.sub("-", keyword.strip().lower().lstrip("#")).strip("-")


def is_relevant_slug(slug: str) -> bool:
    """Whether a related discover slug is worth following.

    The topic test wins over the exclusion test, and must: the farming
    vocabulary overlaps the Spanish product vocabulary, so checking exclusions
    first threw away 'calostro-bovino-opiniones' -- an exact match for what we
    are looking for -- because it contains 'bovino'. Exclusions only decide
    slugs that named no colostrum term of their own.
    """
    if not any(hint in slug for hint in _RELEVANT_SLUG_HINTS):
        return False
    # Named the topic, but in a farming/veterinary sense ("calostro para
    # bezerros") -- that is a different audience entirely.
    return not any(bad in slug for bad in _IRRELEVANT_SLUG_HINTS)


class DiscoverProvider(PlaywrightProvider):
    """Harvests (handle, video_id) pairs off /discover/<keyword> pages."""

    name = "discover"

    def fetch_discover_urls(
        self, keyword: str, limit: int = 120, max_scrolls: int = 30
    ) -> list[tuple[str, str]]:
        """Unique (handle, video_id) pairs for one keyword."""
        pairs, _ = self.fetch_discover_page(keyword, limit=limit, max_scrolls=max_scrolls)
        return pairs

    def fetch_discover_page(
        self, keyword: str, limit: int = 120, max_scrolls: int = 30
    ) -> tuple[list[tuple[str, str]], list[str]]:
        """One discover page: its videos, and the related slugs it links to.

        Returns ([(handle, video_id)], [related_slug]). A grid tops out around
        60 videos however far you scroll, so breadth comes from crawling the
        related slugs rather than from scrolling any one page harder.
        """
        slug = slugify(keyword)
        if not slug:
            return [], []

        page = self._ctx.new_page()
        found: dict[str, str] = {}   # video_id -> handle, dedupes as we scroll
        related: list[str] = []
        try:
            page.goto(
                f"https://www.tiktok.com/discover/{slug}",
                wait_until="domcontentloaded",
                timeout=60_000,
            )
            time.sleep(self._delay)

            html = page.content()
            if any(marker in html for marker in _CAPTCHA_MARKERS):
                raise BlockedError(
                    f"captcha wall on /discover/{slug} — back off and retry later"
                )

            stalls = 0
            for _ in range(max_scrolls):
                html = page.content()
                for handle, video_id in _VIDEO_HREF_RE.findall(html):
                    found.setdefault(video_id, handle)
                if len(found) >= limit:
                    break
                before = len(found)
                # End keys the grid's own lazy-load reliably; a raw wheel event
                # alone stalls around 36 of the ~60 a page will give up.
                page.keyboard.press("End")
                page.mouse.wheel(0, 6000)
                time.sleep(self._delay)
                stalls = stalls + 1 if len(found) == before else 0
                if stalls >= 4:
                    break

            for candidate in dict.fromkeys(_DISCOVER_HREF_RE.findall(page.content())):
                if candidate != slug and is_relevant_slug(candidate):
                    related.append(candidate)
        finally:
            page.close()

        return [(handle, vid) for vid, handle in list(found.items())[:limit]], related

    def fetch_creator(self, handle: str):
        raise NotImplementedError("discover provider only sources video URLs")

    def fetch_creator_videos(self, handle: str, limit: int = 30):
        raise NotImplementedError("discover provider only sources video URLs")
