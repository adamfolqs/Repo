"""Shop-page payload harvesting. No network."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from tiktok_scraper.providers.shop import _harvest_videos, _to_video

# Videos buried at different depths, as they arrive in real TikTok payloads.
PAYLOAD = {
    "code": 0,
    "data": {
        "modules": [
            {"type": "banner", "content": {"img": "x.jpg"}},
            {"type": "videos", "items": [
                {"video_id": "7300000000000000001",
                 "desc": "my colostrum routine",
                 "author": {"unique_id": "gigi.wellness", "nickname": "Shop With Gigi"},
                 "statistics": {"play_count": 88000, "digg_count": 5200,
                                "comment_count": 130, "share_count": 44},
                 "create_time": 1735689600},
                {"aweme_id": "7300000000000000002",
                 "title": "3 weeks in",
                 "creator": {"uniqueId": "@tawnysreviews"},
                 "stats": {"playCount": 12000, "diggCount": 900}},
            ]},
        ]
    },
}

NOISE = {"data": {"id": "12", "title": "a product", "desc": "not a video"}}


def test_finds_nested_videos():
    found = _harvest_videos(PAYLOAD)
    assert len(found) == 2, f"expected 2, got {len(found)}"
    print(f"harvest OK: found {len(found)} videos nested 3 levels deep")


def test_maps_both_shapes():
    a, b = [_to_video(i, "999") for i in _harvest_videos(PAYLOAD)]
    assert a.handle == "gigi.wellness" and a.views == 88000 and a.likes == 5200
    assert a.engagement_rate == 6.11
    assert b.handle == "tawnysreviews", "leading @ must be stripped"
    assert b.views == 12000
    assert a.matched_query == "product:999", "must record which product it came from"
    print(f"mapping OK: @{a.handle} {a.views:,} views {a.engagement_rate}% ER")
    print(f"           @{b.handle} {b.views:,} views (alternate key shape)")


def test_rejects_non_videos():
    """Product blurbs must not become fake creator rows."""
    assert _to_video({"id": "12", "title": "a product", "author": {}}, None) is None
    assert _to_video({"video_id": "abc", "author": {"unique_id": "x"}}, None) is None
    assert _to_video({"video_id": "7300000000000000003", "author": {}}, None) is None, \
        "a video with no identifiable creator is useless -- drop it"
    print("junk rejection OK: short ids, non-numeric ids, and authorless rows dropped")


def test_survives_reshuffle():
    """A reshaped response must degrade, not crash."""
    for weird in [{}, [], {"data": None}, {"a": [[[{"x": 1}]]]}, "string"]:
        assert _harvest_videos(weird) == []
    print("resilience OK: malformed payloads return empty, no exception")


if __name__ == "__main__":
    for fn in [test_finds_nested_videos, test_maps_both_shapes,
               test_rejects_non_videos, test_survives_reshuffle]:
        fn()
    print("\nALL SHOP TESTS PASSED")
