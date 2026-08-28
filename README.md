# TikTok Scraper → Spreadsheet

Pulls TikTok videos and creator profiles into a spreadsheet (CSV + XLSX, and
optionally straight into Google Sheets).

## Why there's a provider abstraction

TikTok has no usable public data API — the Research API is academia-only and
the Display API only reads accounts that have authorized you. So this scrapes,
and scraping TikTok means getting past bot detection: signed request params
(`X-Bogus` / `msToken`, which rotate), device fingerprinting, and IP reputation.

Rather than betting the project on one approach, the fetch layer is swappable.
The output schema is identical either way, so switching is one env var:

| Provider | Cost | Holds up? |
|---|---|---|
| `playwright` | free | Fine from a residential IP. Datacenter IPs get captcha'd fast. |
| `brightdata` | ~$0.50–1.50 / 1k records | Yes — maintained TikTok extractors + unblocking. |

**Measured:** from a datacenter IP, `GET tiktok.com/@nasa` returns HTTP 200 with
a **captcha wall** as the body, and `/api/user/detail/` returns 200 with **zero
bytes**. That is what the paid provider is buying you. From a normal home
connection, `playwright` is usually enough.

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# only needed for the free provider
playwright install chromium

cp .env.example .env    # then edit
```

## Usage

```bash
# Creators listed in a sheet you already have
python -m tiktok_scraper creators --input data/input/creators.csv --limit 30

# Ad-hoc handles
python -m tiktok_scraper creators --handles nasa,bbc --limit 10

# Discovery by keyword / hashtag  (brightdata provider only)
python -m tiktok_scraper search --query "colostrum,#guthealth" --limit 50

# Straight into Google Sheets as well as files
python -m tiktok_scraper creators --input creators.csv --sink both
```

### Input sheets

`--input` accepts `.csv` or `.xlsx` and is forgiving about how you've labelled
things. It auto-detects a column named `handle`, `creator`, `username`,
`profile`, `url`, and similar, and it normalizes the contents:

| Cell in your sheet | Parsed as |
|---|---|
| `@Nasa` | `Nasa` |
| `https://www.tiktok.com/@nasa?lang=en` | `nasa` |
| `nasa` | `nasa` |
| `Creator Name Here` | ignored |

Duplicates are dropped case-insensitively. Use `--column "TikTok URL"` to point
at a specific column if auto-detection picks the wrong one.

## Output

Two tabs / two files, joinable on `handle`:

- **Videos** — `video_url`, `handle`, `description`, `created_at`,
  `duration_seconds`, `views`, `likes`, `comments`, `shares`, `saves`,
  `engagement_rate`, `hashtags`, `music_title`, `music_author`, `matched_query`,
  `video_id`, `cover_url`, `scraped_at`, `source`
- **Creators** — `handle`, `profile_url`, `nickname`, `followers`, `following`,
  `total_likes`, `video_count`, `verified`, `bio`, `bio_link`, `region`,
  `user_id`, `avatar_url`, `scraped_at`, `source`

`engagement_rate` is `(likes + comments + shares) / views` as a percentage —
usually the column you actually sort by, since a 5k-view video at 12% is often
a better creator signal than a 500k-view video at 0.8%.

Every row carries `scraped_at`, `source`, and `matched_query`, so when the sheet
has data from several runs you can always tell where a row came from.

Missing values stay **empty**, never `0` — otherwise a failed field would drag
down every average computed over the column.

### Google Sheets

1. Google Cloud Console → new project → enable **Google Sheets API**
2. Create a **service account** → Keys → Add key → JSON → save as `service_account.json`
3. **Share your Sheet with the service account's `client_email`, as Editor**

Step 3 is the one people miss; without it you get a 403.

Then set `GOOGLE_SHEET_ID` in `.env` (the `/d/<THIS>/edit` part of the URL) and
run with `--sink both`. Rows are appended by default, so scheduled runs
accumulate; `--sheet-mode replace` overwrites instead.

## Tests

```bash
python tests/test_mapping.py
```

Covers provider-response → schema mapping for both providers, missing-field
handling, and schema/sink agreement. No network required.

## Notes

- `REQUEST_DELAY_SECONDS` (default 2.5) throttles requests. Don't lower it much.
- This reads **public** profile data only. Check TikTok's ToS and your own legal
  position before scraping at volume, and don't collect personal data you don't
  have a basis to hold.
- If `playwright` starts returning `BlockedError`, that is the IP, not the code —
  switch provider or route through a residential IP.

## Sourcing creators from TikTok Shop product pages

The reliable way to build a creator list. A Shop product page lists the actual
creators posting about that exact product, with canonical `@handles` — far
better than matching display names, which are not unique and are often
misread when taken from a screen recording.

```bash
# 1. Get creators + their videos from the product pages
python -m tiktok_scraper shop --links data/input/product_links.txt

# 2. Then pull each creator's full profile + back catalogue
python -m tiktok_scraper creators --input data/output/handles.csv --sink both
```

Step 1 writes `data/output/handles.csv`, which is directly the input to step 2.

Notes:
- `shop.tiktok.com` is less defended than the main site — it serves product
  pages without a captcha wall.
- The creator section renders client-side, so this needs a real browser
  (`playwright install chromium`). Plain HTTP returns the page shell only.
- `--dump-raw <dir>` saves the raw intercepted JSON. Worth using on the first
  run: TikTok reshapes these payloads periodically, and the raw capture makes a
  low result count diagnosable without re-scraping.
- Short share links (`tiktok.com/t/...`) are resolved automatically. Note they
  embed the sharing account's id — avoid pasting them anywhere public.
