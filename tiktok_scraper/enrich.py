"""Derived columns: language, contact email, product tagging, brand matching.

These are computed from already-scraped text. Keeping them separate from the
providers means they can be re-run over an existing sheet without re-scraping,
and they are testable without network.
"""

from __future__ import annotations

import re
import unicodedata

# --------------------------------------------------------------- language

# Function words are the reliable signal. Content words (colostrum/calostro)
# are not: plenty of Spanish captions name English brands and vice versa.
_ES_WORDS = {
    "que", "para", "con", "los", "las", "del", "una", "por", "mas", "muy",
    "pero", "como", "esta", "este", "esto", "mi", "tu", "su", "yo", "ya",
    "porque", "cuando", "todo", "todos", "hace", "tiene", "puedes", "mejor",
    "dias", "meses", "gracias", "salud", "piel", "cuerpo", "probando",
    # Short function words with no English collision. "no" and "me" are
    # deliberately excluded -- both are common English words too.
    "el", "la", "en", "es", "un", "al", "sin", "sobre", "entre", "bien",
    "desde", "hasta", "tambien", "siempre", "nunca", "aqui", "ahora",
    "realmente", "ayudado", "mucho", "muchisimo", "ha", "han", "solo",
    "producto", "suplemento", "probado", "tomando", "resultados",
}
_EN_WORDS = {
    "the", "and", "for", "with", "you", "your", "this", "that", "have",
    "has", "was", "are", "not", "but", "all", "get", "got", "been", "just",
    "really", "after", "before", "week", "weeks", "month", "days", "gut",
    "since", "started", "taking", "review", "honest",
    "my", "way", "favorite", "love", "best", "how", "what", "when",
    "these", "there", "here", "them", "than", "then", "into", "out",
}
_ES_CHARS = set("ñáéíóúü¿¡")


def detect_language(text: str | None) -> tuple[str, str]:
    """Return (language, confidence).

    Deliberately conservative: returns 'unknown' rather than guessing on very
    short captions, because a wrong language tag sends outreach in the wrong
    language, which is worse than an empty cell.
    """
    if not text or not text.strip():
        return "unknown", "none"

    lowered = text.lower()
    words = set(re.findall(r"[a-zñáéíóúü]+", lowered))

    es_hits = len(words & _ES_WORDS)
    en_hits = len(words & _EN_WORDS)
    if any(ch in _ES_CHARS for ch in lowered):
        es_hits += 2  # accented characters are a strong Spanish signal

    if es_hits == 0 and en_hits == 0:
        return "unknown", "none"
    if es_hits > en_hits:
        return "Spanish", "high" if es_hits >= 3 else "low"
    if en_hits > es_hits:
        return "English", "high" if en_hits >= 3 else "low"
    return "unknown", "tied"


# ------------------------------------------------------------------ email

_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

# Creators obfuscate to dodge scrapers: "name (at) gmail dot com".
_OBFUSCATED_RE = re.compile(
    r"([A-Za-z0-9._%+-]+)\s*[\(\[]?\s*(?:at|@|arroba)\s*[\)\]]?\s*"
    r"([A-Za-z0-9.-]+)\s*[\(\[]?\s*(?:dot|punto|\.)\s*[\)\]]?\s*([A-Za-z]{2,})",
    re.I,
)


def extract_email(*texts: str | None) -> str:
    """Pull a contact email out of bio / caption text.

    Returns '' when there is none. Only reads text the creator published
    publicly as their business contact.
    """
    for text in texts:
        if not text:
            continue
        cleaned = unicodedata.normalize("NFKC", text)
        match = _EMAIL_RE.search(cleaned)
        if match:
            return match.group(0).strip(".,;:").lower()
        obfuscated = _OBFUSCATED_RE.search(cleaned)
        if obfuscated:
            user, domain, tld = obfuscated.groups()
            return f"{user}@{domain}.{tld}".lower()
    return ""


# ---------------------------------------------------------------- product

# Competitors seen in the sourcing sheet, plus obvious spelling variants.
COMPETITOR_BRANDS = {
    "ARMRA": ["armra"],
    "Bloom Nutrition": ["bloom nutrition", "bloomnutrition", "bloom greens"],
    "Cymbiotika": ["cymbiotika", "cymbiotica"],
    "Lemme": ["lemme"],
    "Micro Ingredients": ["micro ingredients", "microingredients"],
    "Miracle Moo": ["miracle moo", "miraclemoo", "micro moo", "milagroso moo"],
    "Nutricost": ["nutricost"],
    "Physician's Choice": ["physician's choice", "physicians choice", "physicianschoice"],
    "Wellah": ["wellah"],
    "Magic Milk": ["magic milk"],
}

# Words that mean "this video is selling something", in both languages.
_PRODUCT_SIGNALS = [
    "tiktokshop", "tiktokmademebuyit", "creatorpicks", "link in bio",
    "linkinbio", "use code", "discount", "descuento", "codigo", "código",
    "shop now", "comprar", "en la tienda", "affiliate", "ad", "sponsored",
    "gifted", "partner",
]

_COLOSTRUM_TERMS = ["colostrum", "calostro", "colostro", "bovine colostrum"]


def match_brand(*texts: str | None) -> str:
    """Which competitor brand this video is about, '' if none named."""
    blob = " ".join(t.lower() for t in texts if t)
    for brand, aliases in COMPETITOR_BRANDS.items():
        if any(alias in blob for alias in aliases):
            return brand
    return ""


def is_colostrum(*texts: str | None) -> bool:
    blob = " ".join(t.lower() for t in texts if t)
    return any(term in blob for term in _COLOSTRUM_TERMS)


def has_product_tag(description: str | None, hashtags=None, extra=None) -> bool:
    """Whether the video looks like it tags/sells a product.

    A named competitor brand counts on its own -- a video saying 'Miracle Moo'
    is a product video whether or not it also shouts 'link in bio'.
    """
    blob = " ".join(
        [description or "", " ".join(hashtags or []), extra or ""]
    ).lower()
    if match_brand(blob):
        return True
    return any(signal in blob for signal in _PRODUCT_SIGNALS)


# --------------------------------------------------------------- pipeline

def enrich_videos(videos, creators=None):
    """Fill the derived columns on every video, in place. Returns the list.

    creators: optional list of Creator objects; their email/follower count is
    joined onto each video so one sheet is enough for outreach.
    """
    by_handle = {}
    for creator in creators or []:
        by_handle[creator.handle.lower()] = creator

    for video in videos:
        text = video.description or ""
        tags = " ".join(video.hashtags or [])

        lang, conf = detect_language(f"{text} {tags}")
        video.language = lang
        video.language_confidence = conf
        video.competitor_brand = match_brand(text, tags, video.music_title) or None
        video.is_colostrum = is_colostrum(text, tags, video.music_title)
        video.has_product_tag = has_product_tag(text, video.hashtags)

        creator = by_handle.get((video.handle or "").lower())
        if creator:
            video.creator_email = creator.email
            video.creator_followers = creator.followers
            # A creator-level language read is steadier than one short caption.
            if video.language == "unknown" and creator.language:
                video.language = creator.language
                video.language_confidence = "from_creator"
    return videos


def enrich_creators(creators):
    """Fill email + language on creator rows from their public bio."""
    for creator in creators:
        creator.email = extract_email(creator.bio, creator.bio_link) or None
        lang, _ = detect_language(creator.bio)
        creator.language = lang
    return creators


def filter_videos(videos, min_likes=0, colostrum_only=False, product_only=False,
                  language=None):
    """Apply the sheet's inclusion rules."""
    out = []
    for video in videos:
        if min_likes and (video.likes or 0) < min_likes:
            continue
        if colostrum_only and not video.is_colostrum:
            continue
        if product_only and not video.has_product_tag:
            continue
        if language and (video.language or "").lower() != language.lower():
            continue
        out.append(video)
    return out
