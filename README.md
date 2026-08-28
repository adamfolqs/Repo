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

## What each TikTok surface actually serves

Measured from this egress path, not assumed. This is the map the sourcing
pipeline is built around, and the thing worth re-checking first if results
suddenly drop:

| Surface | Serves data? | How |
|---|---|---|
| `/@handle` | **yes** | SSR blob: profile + follower/like counts |
| `/@handle/video/<id>` | **yes** | SSR blob: exact like/view/comment/share/save |
| `/embed/@handle` | **yes** | state blob: 10 most recent posts, no pagination |
| `/discover/<keyword>` | **yes** | client-rendered grid, ~60 videos, needs a browser |
| `/search?q=` | no | login-walled — renders skeletons, results XHR never fires |
| `/tag/<hashtag>` | no | client-rendered, nothing behind it |
| profile video grid | no | login-walled; `/api/post/item_list/` needs signed params |
| `shop.tiktok.com` PDP | partial | product data yes, creator videos are in-app only |

The consequence: **discovery and enrichment are separate problems.** Keyword
pages are the only surface that will name videos it has not been asked about,
and they carry no engagement numbers. Every number comes from opening the
video's own page afterwards.

Note the earlier finding that `www.tiktok.com` captcha-walls profile pages did
**not** reproduce here — profile and video pages served full SSR data. Check
before assuming you need a paid provider; the wall is IP-dependent.

### The pipeline

```bash
# 1. keywords -> video URLs (browser; follows related keyword pages)
python -m tiktok_scraper discover --keyword-file data/input/discover_keywords.txt \
    --per-keyword 150 --crawl-depth 2

# 2. every creator found -> their other recent posts, added to the same list
python -m tiktok_scraper catalogue

# 3. video URLs -> full rows with real numbers (plain HTTP, no browser)
#    --priority-handles fetches creators already known to post about colostrum
#    first, which is what you want whenever there are more URLs than time
python -m tiktok_scraper resolve --priority-handles

# 4. handles -> follower count + bio email
python -m tiktok_scraper profiles

# 5. display names from the sourcing sheet -> verified handles
python -m tiktok_scraper names

# 6. assemble the workbook
python build_sheet.py
```

`discover` and `catalogue` both append to the same URL list and can run at the
same time; the list merges on write rather than overwriting.

### Handles are verified, never derived

`names` exists because display names cannot be turned into handles by
transformation — they are not unique, and a handle often looks nothing like the
name it shows (`Creakzzz` is `@creakzshop`; `@creakzzz` is somebody else). So it
proposes candidates, opens each profile, and keeps one only if the account that
loaded says it is that person.

The recording shows **display names**, so a display-name match is the
confirmation. A label that merely spells a real handle is recorded but marked
`unconfirmed`. Labels too generic to identify one account (`jacquie`,
`Unreadable creator`) are reported as unresolvable rather than resolved to
whichever account happens to answer. Externally suggested handles — from a web
search — go through the same check, so a wrong suggestion is rejected rather
than trusted.

Result on the 177-row sheet: 20 handles before, 125 after.

Each stage appends to a JSONL store and skips ids already in it, so a stage
that dies partway **resumes rather than restarts**. The full sweep takes hours
at a polite request rate, so this matters more than it looks.

### Running a browser behind an egress proxy

Two things bite in a sandboxed environment, both already handled in
`playwright_provider.py` but worth knowing:

- Chromium's TLS 1.3 ClientHello carries a post-quantum key share (~1.8 kB).
  Some proxies answer it with a TLS alert and drop the tunnel, so *every*
  navigation fails as `ERR_CONNECTION_RESET` — for all hosts, which is how you
  tell it apart from TikTok blocking you. The fix is `--ssl-version-max=tls1.2`,
  not `--ignore-certificate-errors`.
- Don't test for a captcha by matching `/captcha/` in the HTML. The captcha
  SDK's asset URL is bundled into every normal TikTok page, so that reports a
  wall on pages that loaded perfectly.

## Sourcing creators from TikTok Shop product pages

**This no longer works, and the `shop` command cannot fix it.** A Shop product
page shows a creator-video section *in the app*, but the web PDP does not ship
it. Checked on desktop and mobile user agents and across `shop.tiktok.com/us/pdp/`,
`shop.tiktok.com/view/product/` and `www.tiktok.com/shop/pdp/`: the page data
carries product, price and reviews, and zero `author` / `aweme` / `unique_id`
fields. Review authors are anonymised (`B**8`), so they are not handles either.

What still works is resolving the product links themselves — a short share link
redirects to a PDP whose URL carries the product id and title. That is how the
seven competitor products were confirmed (Micro Ingredients, Physician's Choice,
Miracle Moo, Bloom Nutrition, Nutricost, ARMRA, Lemme). Their creators are then
sourced by running those brand names through `discover`, which reaches the same
people by a working door.

> Careful with resolved share links: they embed the *sharing* account's
> `unique_id` and `user_id`. Don't paste them anywhere public — only the product
> id and title are kept in `data/output/competitor_products.json`.

The original rationale, still true and still why handles matter:
creator sourcing by *display name* is unreliable — names are not unique on
TikTok and OCR'd names are often wrong or truncated, so a canonical `@handle`
is worth much more than a name.

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
