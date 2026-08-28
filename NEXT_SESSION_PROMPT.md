# Prompt for the new session

Copy everything below the line into a fresh Claude Code session.

---

We're doing a big TikTok colostrum scraping session. You have Browser Use
installed (Chrome) — use it, that's the whole point.

**Repo:** `adamfolqs/Repo`, branch `claude/tiktok-web-scraping-jdzvkx`.
Read `README.md` first — a working scraper is already built and tested. Don't
rebuild it, extend it.

## What already exists

```bash
python -m tiktok_scraper shop     --links data/input/product_links.txt
python -m tiktok_scraper creators --input data/output/handles.csv --sink both
python -m tiktok_scraper search   --query "colostrum" --limit 100
```

Flags on all three: `--min-likes 50 --colostrum-only --product-only
--language English|Spanish --sink both --dump-raw <dir>`

Output columns already include: video_url, handle, creator_email,
creator_followers, language, competitor_brand, is_colostrum, has_product_tag,
likes, views, comments, shares, saves, engagement_rate, description, hashtags,
music_title, created_at. Enrichment (language / email / brand / product-tag)
lives in `tiktok_scraper/enrich.py` and has passing tests in `tests/`.

## Findings from the last session — don't rediscover these

1. **www.tiktok.com captcha-walls profile pages** from datacenter IPs. HTTP 200
   with a captcha body; `/api/user/detail/` returns 200 with 0 bytes.
2. **shop.tiktok.com does NOT captcha-wall.** Product pages serve fine. This is
   the good door.
3. **Product-page creator lists are client-rendered.** Plain HTTP gets a shell
   (SSR blob ~557 bytes). You need the real browser.
4. **Web search finds handles at only ~62%** and generic names (jacquie, Taylor,
   Nikki) are unresolvable. Handles often differ from display names
   (Creakzzz → @creakzshop, JESSYKARINA → @mrsplaytoomuch). Don't guess handles.

## The job

Build the biggest possible list of **colostrum videos with 50+ likes that tag a
product**, plus the creators behind them.

**Start here** — 7 competitor product pages already saved in
`data/input/product_links.txt`. Run `shop` over them first; that yields exact
handles with zero guessing.

**Then go wide.** Search TikTok for colostrum content across both languages:

- Terms: colostrum, bovine colostrum, colostrum review, colostrum before and
  after, colostrum gut health, colostrum bloating, calostro, calostro bovino,
  calostro bovino opiniones, calostro resultados
- Hashtags: #colostrum #colostrumbenefits #colostrumreview #bovinecolostrum
  #calostrobovino #guthealth #healthygut #bloating #tiktokshopfinds
- Brands: ARMRA, Miracle Moo / Micro Moo, Bloom Nutrition, Cymbiotika, Lemme,
  Nutricost, Micro Ingredients, Physician's Choice, Wellah, Magic Milk,
  WonderCow, Cowabunga, Cowboy Colostrum, Rhea Essentials
- Also scrape each found creator's back catalogue for their other colostrum
  videos — one good creator usually has several.

**Then enrich:** visit each creator's profile for follower count and the
contact email in their bio. `extract_email()` already handles obfuscated forms
("name (at) gmail dot com", "hola arroba marca punto es").

## Rules

- **Never invent engagement numbers.** If you can't read likes/views, leave the
  cell empty. An estimated number silently becomes the sort order for outreach
  decisions, which is worse than a blank.
- **Don't guess a handle from a display name.** Only record a handle you
  actually landed on. Mark confidence.
- **Flag brand-owned accounts** (@trymiraclemoo, @wondercowusa,
  @try.miraclemoo etc). Not outreach targets; useful as creative reference.
- **Note negative/debunking videos** rather than dropping them — @leahdajud and
  @whatmojoloves are critical of colostrum, which is useful objection research.
- Respect `REQUEST_DELAY_SECONDS` (2.5s). Don't hammer.
- Commit and push to `claude/tiktok-web-scraping-jdzvkx` as you go, so a
  crash doesn't lose the haul.

## Deliverable

One xlsx, sortable, tabs:
1. **Videos** — every colostrum video, 50+ likes, product-tagged, with exact
   video URL so the creative can be watched and replicated
2. **Creators** — deduped, with handle, followers, email, language, how many
   colostrum videos, which brands they've worked with
3. **Original Sheet + Handles** — the existing 177-row sheet with handles
   filled in (currently 20/177 done; `data/output/handle_lookup.csv` has them)

Also update `data/output/colostrum_creator_list.xlsx` rather than starting a
new file, and tell me the totals at the end: videos, creators, language split,
brand split, how many have emails.

Go as wide as you can. More is better.
