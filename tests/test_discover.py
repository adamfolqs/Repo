"""Which related discover slugs the crawler will follow."""
import sys, pathlib
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from tiktok_scraper.providers.discover import is_relevant_slug, slugify


def test_slugify():
    assert slugify("bovine colostrum") == "bovine-colostrum"
    assert slugify("#colostrumBenefits") == "colostrumbenefits"
    assert slugify("  Calostro Bovino  ") == "calostro-bovino"
    print("  slugify OK")


def test_follows_on_topic():
    for slug in ["bovine-colostrum-costco", "armra-colostrum-review",
                 "colostrum-harvesting", "wondercow-colostrum",
                 "bovine-colostrum-original-vs-fake"]:
        assert is_relevant_slug(slug), slug
    print("  follows on-topic slugs OK")


def test_follows_spanish():
    """'bovino' is the Spanish product word, not a farming-only word.

    Excluding it as agricultural vocabulary silently dropped the entire
    Spanish half of the brief.
    """
    for slug in ["calostro-bovino", "calostro-bovino-opiniones",
                 "calostro-bovino-beneficios", "beneficios-del-calostro"]:
        assert is_relevant_slug(slug), slug
    print("  follows Spanish product slugs OK")


def test_skips_off_topic():
    # Generic wellness: fine as a seed, but crawling it leaves the market.
    for slug in ["gut-health-meaning", "bloating-remedy", "healthygut"]:
        assert not is_relevant_slug(slug), slug
    # Farming/veterinary, including ones that do name colostrum.
    for slug in ["razas-de-bovinos", "inseminar-bovinos", "bovinos-steakhouse",
                 "calostro-para-bezerros", "grenetina-bovino"]:
        assert not is_relevant_slug(slug), slug
    print("  skips off-topic and farming slugs OK")


if __name__ == "__main__":
    for fn in [test_slugify, test_follows_on_topic, test_follows_spanish,
               test_skips_off_topic]:
        print(fn.__name__ + ":"); fn()
    print("\nALL DISCOVER TESTS PASSED")
