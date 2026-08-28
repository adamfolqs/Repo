"""Provider response -> normalized model mapping.

These run without network. They are the tests that actually matter: the fetch
layer is thin, but the field mapping is where silent data corruption hides
(a null becoming 0, a count landing in the wrong column).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tiktok_scraper.models import VIDEO_COLUMNS, Creator, Video
from tiktok_scraper.sinks.files import to_rows


def _bare(cls):
    """An instance without running __init__ (no browser, no API token needed)."""
    return cls.__new__(cls)

# Shaped like a real entry in TikTok's /api/post/item_list itemList.
TIKTOK_ITEM = {
    "id": "7300000000000000000",
    "desc": "day 3 of the reset #wellness #gutheath",
    "createTime": 1735689600,
    "author": {"uniqueId": "someone", "nickname": "Some One"},
    "stats": {"playCount": 250000, "diggCount": 31000,
              "commentCount": 412, "shareCount": 890, "collectCount": 5600},
    "video": {"duration": 27, "cover": "https://p16.tiktokcdn.com/x.jpg"},
    "music": {"title": "original sound", "authorName": "someone"},
    "textExtra": [{"hashtagName": "wellness"}, {"hashtagName": "gutheath"}, {}],
}

# Shaped like a Bright Data TikTok post row.
BRIGHTDATA_POST = {
    "post_id": "7300000000000000001",
    "url": "https://www.tiktok.com/@creator/video/7300000000000000001",
    "description": "before vs after",
    "profile_username": "@creator",
    "play_count": 1000, "digg_count": 250, "comment_count": 10, "share_count": 4,
    "date_posted": "2026-01-02T10:00:00Z",
    "hashtags": ["#before", "after"],
}


def test_playwright_mapping():
    from tiktok_scraper.providers.playwright_provider import PlaywrightProvider
    v = _bare(PlaywrightProvider)._to_video(TIKTOK_ITEM, "someone")

    assert v.video_id == "7300000000000000000"
    assert v.handle == "someone"
    assert v.views == 250000 and v.likes == 31000
    assert v.comments == 412 and v.shares == 890 and v.saves == 5600
    assert v.duration_seconds == 27
    assert v.hashtags == ["wellness", "gutheath"], "empty textExtra entries must be dropped"
    assert v.created_at is not None and v.created_at.year == 2025
    assert v.engagement_rate == 12.92
    print("playwright mapping OK ->", v.video_url, v.engagement_rate, "%")


def test_brightdata_mapping():
    from tiktok_scraper.providers.brightdata import BrightDataProvider
    v = _bare(BrightDataProvider)._to_video(BRIGHTDATA_POST, query="before after")

    assert v.video_id == "7300000000000000001"
    assert v.handle == "creator", "leading @ must be stripped"
    assert v.views == 1000 and v.likes == 250
    assert v.hashtags == ["before", "after"], "leading # must be stripped"
    assert v.matched_query == "before after"
    assert v.created_at.year == 2026
    print("brightdata mapping OK ->", v.video_url, v.engagement_rate, "%")


def test_missing_fields_do_not_crash():
    """Real payloads have holes. Nothing may raise, nothing may fake a zero."""
    from tiktok_scraper.providers.playwright_provider import PlaywrightProvider
    v = _bare(PlaywrightProvider)._to_video({"id": "1", "author": {}}, "x")
    assert v.views is None, "missing views must stay None, not become 0"
    assert v.engagement_rate is None
    assert v.hashtags == []

    from tiktok_scraper.providers.brightdata import BrightDataProvider
    b = _bare(BrightDataProvider)._to_video({"url": "https://www.tiktok.com/@a/video/99"})
    assert b.video_id == "99", "video id must fall back to parsing the URL"
    print("missing-field handling OK")


def test_schema_and_sink_agree():
    """Every declared column must exist on the model."""
    v = Video(video_id="1", handle="h")
    dumped = v.model_dump()
    missing = [c for c in VIDEO_COLUMNS if c not in dumped]
    assert not missing, f"columns not on model: {missing}"

    row = to_rows([v], VIDEO_COLUMNS)[0]
    assert len(row) == len(VIDEO_COLUMNS)
    assert all(cell is not None for cell in row), "None must flatten to '' for sheets"
    print(f"schema/sink agree OK ({len(VIDEO_COLUMNS)} columns)")


if __name__ == "__main__":
    for fn in [test_playwright_mapping, test_brightdata_mapping,
               test_missing_fields_do_not_crash, test_schema_and_sink_agree]:
        fn()
    print("\nALL MAPPING TESTS PASSED")
