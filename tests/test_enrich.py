import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tiktok_scraper.enrich import (detect_language, extract_email, match_brand,
                                   has_product_tag, is_colostrum)

def test_language():
    cases = [
        ("Puedes encontrar el calostro bovino en la TikTok Shop!", "Spanish"),
        ("Mi experiencia con el milagroso producto miracle moo", "Spanish"),
        ("day 3 of taking this and my gut has never been better", "English"),
        ("honest review after 2 weeks, this really works for bloating", "English"),
        ("colostrum", "unknown"),          # single content word: no signal
        ("", "unknown"),
        ("🥛✨", "unknown"),
    ]
    for text, want in cases:
        got, conf = detect_language(text)
        assert got == want, f"{text!r}: got {got}, want {want}"
        print(f"  {want:8} ({conf:4}) <- {text[:48]!r}")

def test_email():
    assert extract_email("collab: jane.doe@gmail.com") == "jane.doe@gmail.com"
    assert extract_email("business (at) creator dot com") == "business@creator.com"
    assert extract_email("contacto: hola arroba marca punto es") == "hola@marca.es"
    assert extract_email("no contact here") == ""
    assert extract_email(None, "", "reach me: A.B@Brand.CO.UK") == "a.b@brand.co.uk"
    print("  email extraction incl. obfuscated forms OK")

def test_brand_and_product():
    assert match_brand("loving my miracle moo routine") == "Miracle Moo"
    assert match_brand("#cymbiotica review") == "Cymbiotika", "spelling variant"
    assert match_brand("just a random video") == ""
    assert has_product_tag("my ARMRA routine", [])
    assert has_product_tag("use code SAVE20", [])
    assert has_product_tag("", ["tiktokshop"])
    assert not has_product_tag("just chatting about my day", ["fyp"])
    print("  brand matching + product-tag detection OK")

def test_colostrum_filter():
    assert is_colostrum("bovine colostrum changed my gut")
    assert is_colostrum("el calostro bovino es increible")
    assert not is_colostrum("my protein shake routine")
    print("  colostrum topic filter OK (EN + ES)")



def test_brand_disambiguation():
    """A caption naming several brands must resolve to the right one."""
    from tiktok_scraper.enrich import match_brand
    # Real caption: WonderCow video that also carries #tryarmra
    assert match_brand("Anyone else taking this!? Loving it so far! @WonderCow "
                       "Colostrum #colostrum #colostrumbenefits #tryarmra") == "WonderCow"
    # ARMRA genuinely the subject
    assert match_brand("my honest first impressions of armra colostrum!!! "
                       "#colostrum #tryarmra #armracolostrum") == "ARMRA"
    # Substring must not fire on its own
    assert match_brand("#tryarmra") == "ARMRA", "hashtag-only still counts, just weaker"
    assert match_brand("no brands here at all") == ""
    print("  brand disambiguation OK (@mention and word-boundary scoring)")

def test_brand_accounts():
    """The brand's own account is not an outreach target."""
    from tiktok_scraper.enrich import is_brand_account
    for handle in ["trymiraclemoo", "try.miraclemoo", "wondercowusa", "drinkarmra",
                   "cowboycolostrum", "nutricost"]:
        assert is_brand_account(handle), handle
    # Creators who merely review a brand must NOT be flagged -- mislabelling
    # one drops a real outreach target from the list entirely.
    for handle in ["sarahtriedwondercow", "jenlaurenn", "whatmojoloves",
                   "leahdajud", "creakzshop", "nicollefigueroaa"]:
        assert not is_brand_account(handle), handle

    # The display name is often the only tell: Bloom Nutrition posts as
    # '@bloom', whose handle gives away nothing at all.
    assert is_brand_account("bloom", "Bloom Nutrition")
    assert is_brand_account("enjoywondercow", "WonderCow Colostrum 🐮✨")
    assert is_brand_account("wondercowusa", None)

    # ...but a creator whose display name merely mentions a brand is a
    # creator. Flagging them would drop a real outreach target.
    assert not is_brand_account("sarahtries", "Sarah tries Bloom Nutrition")
    assert not is_brand_account("gutgirl", "Kayla | ARMRA obsessed")
    print("  brand-owned account flagging OK (handle and display name)")


def test_skeptical():
    """Debunking videos are kept and marked, not dropped."""
    from tiktok_scraper.enrich import is_skeptical
    assert is_skeptical("Deinfluencing colostrum.. is colostrum worth it?")
    assert is_skeptical("honest review: this was a waste of money")
    assert is_skeptical("el calostro no funciona para nada")
    assert not is_skeptical("day 30 of colostrum and my gut feels amazing")
    print("  skeptical/debunking detection OK")


def test_product_tag_not_erased():
    """A provider's commerce-anchor signal survives text enrichment."""
    from tiktok_scraper.models import Video
    from tiktok_scraper.enrich import enrich_videos
    # Caption names no brand and no shop words, but TikTok said it sells.
    video = Video(video_id="7" + "0" * 18, handle="someone",
                  description="my morning routine", has_product_tag=True)
    enrich_videos([video])
    assert video.has_product_tag is True, "structural product tag was erased"
    print("  structural product-tag signal preserved OK")


if __name__ == "__main__":
    for fn in [test_language, test_email, test_brand_and_product, test_colostrum_filter,
               test_brand_disambiguation, test_brand_accounts, test_skeptical,
               test_product_tag_not_erased]:
        print(fn.__name__ + ":"); fn()
    print("\nALL ENRICH TESTS PASSED")
