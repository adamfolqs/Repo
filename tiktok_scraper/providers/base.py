"""Provider interface.

A provider knows how to *fetch* TikTok data. It does not know anything about
spreadsheets. Swapping providers must never change the output schema.
"""

from __future__ import annotations

import abc
from typing import Iterable

from ..models import Creator, Video


class ProviderError(RuntimeError):
    """Fetching failed in a way the caller should see."""


class BlockedError(ProviderError):
    """TikTok served a captcha / empty body instead of data.

    Raised distinctly from other errors because the remedy is different:
    this means 'change your egress path', not 'retry harder'.
    """


class Provider(abc.ABC):
    """Base class for all fetch backends."""

    name: str = "base"

    @abc.abstractmethod
    def fetch_creator(self, handle: str) -> Creator:
        """Profile metadata for one @handle."""

    @abc.abstractmethod
    def fetch_creator_videos(self, handle: str, limit: int = 30) -> list[Video]:
        """Most recent videos for one @handle."""

    def search_videos(self, query: str, limit: int = 30) -> list[Video]:
        """Videos matching a keyword or #hashtag.

        Optional: not every backend supports discovery. Default raises so the
        CLI can fall back or report clearly instead of silently returning [].
        """
        raise NotImplementedError(
            f"provider '{self.name}' does not support keyword search"
        )

    def fetch_videos_by_url(self, urls: Iterable[str]) -> list[Video]:
        """Enrich a list of known video URLs."""
        raise NotImplementedError(
            f"provider '{self.name}' does not support URL enrichment"
        )

    def close(self) -> None:
        """Release resources (browsers, HTTP pools). Safe to call twice."""


def get_provider(name: str, **kwargs) -> Provider:
    """Factory. Imports lazily so optional deps stay optional."""
    key = (name or "").strip().lower()

    if key == "brightdata":
        from .brightdata import BrightDataProvider
        return BrightDataProvider(**kwargs)

    if key == "playwright":
        from .playwright_provider import PlaywrightProvider
        return PlaywrightProvider(**kwargs)

    raise ValueError(
        f"unknown provider {name!r}. Valid options: 'playwright', 'brightdata'"
    )
