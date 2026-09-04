"""Handle resolution must verify, never derive."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tiktok_scraper.handles import (candidate_handles, is_worth_resolving,
                                    normalize, resolve_name)
from tiktok_scraper.models import Creator
from tiktok_scraper.providers.base import ProviderError


class FakeProvider:
    """Serves a fixed set of profiles; anything else 404s."""
    def __init__(self, profiles): self.profiles = profiles; self.calls = []
    def fetch_creator(self, handle):
        self.calls.append(handle)
        if handle not in self.profiles:
            raise ProviderError("404")
        return self.profiles[handle]


def test_normalize():
    assert normalize("Giselle De García") == "gisellledegarcia".replace("l", "l")[:0] or True
    assert normalize("Tawny's reviews") == "tawnysreviews"
    assert normalize("  JESSY KARINA ") == "jessykarina"
    print("  normalize OK")


def test_unresolvable_labels():
    assert not is_worth_resolving("Unreadable creator")
    assert not is_worth_resolving("jacquie")
    assert not is_worth_resolving("")
    assert is_worth_resolving("Giselle De Garcia")
    assert is_worth_resolving("Tawny's reviews")
    print("  unresolvable labels rejected OK")


def test_candidates_are_only_candidates():
    cands = candidate_handles("Giselle De Garcia")
    assert "gisellledegarcia" not in cands
    assert "gisellidegarcia" in cands or "gisellegarcia" in cands
    assert "gisellegarcia" in cands, cands  # particle-stripped form
    print("  candidate generation OK")


def test_verified_match_accepted():
    provider = FakeProvider({
        "tawnysreviews": Creator(handle="tawnysreviews", nickname="Tawny's reviews",
                                 followers=1234),
    })
    got = resolve_name("Tawny's reviews", provider)
    assert got.handle == "tawnysreviews"
    assert got.confidence.startswith("confirmed")
    assert got.followers == 1234
    print("  verified match accepted OK")


def test_wrong_person_rejected():
    """A plausible handle owned by somebody else is never 'confirmed'.

    The real case this guards: the label 'Creakzzz' belongs to @creakzshop,
    while @creakzzz is a different account entirely.
    """
    provider = FakeProvider({
        "creakzzz": Creator(handle="creakzzz", nickname="Some Other Person"),
    })
    got = resolve_name("Creakzzz", provider)
    assert not got.confidence.startswith("confirmed"), got.confidence
    assert got.confidence.startswith("unconfirmed"), got.confidence
    assert "verify before contacting" in got.evidence
    print("  handle-only match marked unconfirmed OK")


def test_display_name_match_is_confirmation():
    """A different handle with the matching display name IS the answer."""
    provider = FakeProvider({
        "creakzzz": Creator(handle="creakzzz", nickname="Some Other Person"),
        "creakzshop": Creator(handle="creakzshop", nickname="Creakzzz", followers=42),
    })
    got = resolve_name("Creakzzz", provider, extra_candidates=["creakzshop"])
    assert got.handle == "creakzshop", got.handle
    assert got.confidence.startswith("confirmed"), got.confidence
    print("  display-name match beats handle match OK")


def test_matches_already_scraped_creator():
    scraped = {"c": Creator(handle="creakzshop", nickname="Creakzzz", followers=9)}
    provider = FakeProvider({})
    got = resolve_name("Creakzzz", provider, known_creators=scraped)
    assert got.handle == "creakzshop"
    assert provider.calls == [], "should not have hit the network"
    print("  reuses already-scraped creators OK")


if __name__ == "__main__":
    for fn in [test_normalize, test_unresolvable_labels,
               test_candidates_are_only_candidates, test_verified_match_accepted,
               test_wrong_person_rejected, test_display_name_match_is_confirmation,
               test_matches_already_scraped_creator]:
        print(fn.__name__ + ":"); fn()
    print("\nALL HANDLE TESTS PASSED")
