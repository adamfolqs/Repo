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

if __name__ == "__main__":
    for fn in [test_language, test_email, test_brand_and_product, test_colostrum_filter]:
        print(fn.__name__ + ":"); fn()
    print("\nALL ENRICH TESTS PASSED")
