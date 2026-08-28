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

---

# Weekly performance tracker

An automated, scheduled bot for the weekly TikTok Shop review. It replaces the
manual loop — count the samples, screenshot the dashboards, paste them into
Claude, retype the numbers into the wiki — with one Friday job.

```
screenshots ─► Claude (vision) ─┐
sample tracker ─► samples sent ─┼─► derive + cross-check ─► Weekly Performance tab
manual --set values ────────────┘                        └─► email digest + Telegram
```

## What it writes into

The **Folqs TikTok Shop Wiki**, tab **`Weekly Performance (1)`**. That tab is
*transposed* — metrics are rows and each week is a new **column** — so the job
appends a column, it does not append a row. Week labels are `DD/MM–DD/MM` with
an **en dash**, Friday to Thursday, matching every column already there.

Six rows are computed rather than read, using formulas checked against the
tracker's own May–July history: `AOV = GMV/Orders`, `CTR = Clicks/Impressions`,
`CTOR = Orders/Clicks`, `GMV Per Video = Affiliate GMV/Videos Posted`,
`Cost Per Order = Cost/Ad Orders`, `Sample COGS = Samples × $15`.

If a screenshot *also* shows one of those, both are kept and any disagreement is
flagged — that is how a misread digit gets caught before it reaches the sheet.

## Setup

```bash
pip install -r requirements.txt
cp .env.example .env          # fill in the tracker section
```

Three credentials are needed:

1. **`ANTHROPIC_API_KEY`** — reads the screenshots.
2. **`service_account.json`** — a Google service account. **Share the wiki and
   the sample tracker with its `client_email` as an Editor**; without that you
   get a 403.
3. **SMTP + Telegram** — see the comments in `.env.example`. Gmail needs an App
   Password, and a Telegram bot cannot message you until you message it first.

Then confirm everything the scheduled job depends on:

```bash
python -m folqs_tracker check      # credentials, tab layout, which column it would write
python -m folqs_tracker notify-test # proves the email and Telegram actually arrive
```

## Weekly use

Drop the week's analytics screenshots in `data/tracking/inbox/` — that folder's
README lists the exact Seller Center paths for each metric, which span Shop
analytics, Product analytics, the Creator tab, the Orders tab (free-sample
order tag), Ads Manager and Account Health. Then:

```bash
python -m folqs_tracker run --dry-run --print-report   # read + report, write nothing
python -m folqs_tracker run                            # the real thing
python -m folqs_tracker run --set retainer_payments=2050
```

Useful flags: `--week 21/08-27/08` or `--week-ending 2026-08-27` to redo an
earlier week, `--samples-sent 26` to override the counted figure, `--overwrite`
to replace existing cells, `--no-notify` to stay quiet.

## Taking the screenshots automatically

The bot can collect the screens itself instead of waiting for you to paste them
in. Set it up once:

```bash
python -m folqs_tracker login       # opens a browser; log in by hand (incl. 2FA)
python -m folqs_tracker calibrate   # walk the 6 screens, it records their URLs
python -m folqs_tracker capture --headed   # test a capture run, watch it work
```

Then the weekly job takes its own screenshots:

```bash
python -m folqs_tracker run --capture
```

**No password is ever stored.** `login` opens a real browser, you log in
yourself (2FA included), and only the resulting browser session is saved — to
`.tiktok_session.json`, owner-readable, gitignored. When it expires the run
stops with exit code 2 and tells you to run `login` again.

`calibrate` exists because Seller Center URLs carry account-specific ids and
change between releases, so shipping guessed URLs would be worse than asking
once. It writes `capture_plan.json`, which then takes precedence over the
built-in defaults. The samples screen needs a click sequence rather than a URL
(Filters → Order Tag → free-sample options → Apply), so its `actions` list has
to be filled in by hand — the file has a comment saying so, and until it is,
that target fails with an explanation instead of capturing the wrong screen.

Two guards make automated capture safe to leave unattended:

- **A login page is never captured.** A logged-out Seller Center screenshots
  perfectly, and feeding that to the extractor would produce a week of blanks
  with no visible cause. Every capture is checked, before and after its click
  script, and an expired session aborts the run rather than continuing.
- **Every screen must prove it is the right screen.** Each target asserts a
  string it must contain (`GMV`, `Impressions`, `Cost`, …). Proxy errors,
  TikTok's own "something went wrong", and empty states all render and
  screenshot just fine — the assertion is what stops one being saved as data.
  A screen that fails is reported in the digest; the other five still run.

## Catching up on missed weeks

The tracker had drifted about six weeks behind. `backfill` runs the ordinary
weekly pipeline once per week over a range:

```bash
python -m folqs_tracker backfill --dry-run          # show the plan, write nothing
python -m folqs_tracker backfill --capture          # collect and fill each week
python -m folqs_tracker backfill --from 17/07-23/07 --to 21/08-27/08
```

With no `--from` it starts at the first week that is not already complete, and
with no `--to` it stops at the last complete week. Weeks that already have
their numbers are skipped (`--redo` forces them), and existing cells are kept
unless you pass `--overwrite`.

Three things make it safe to point at a long range:

- **Weeks are processed oldest first.** The tab appends each new week as the
  next column, so order is structural, not cosmetic. The sheet is re-read after
  each write so the following week lands in the column after it.
- **One bad week does not cost the others.** A week whose screenshots are
  missing or unreadable is recorded as failed and the run continues; the exit
  code is non-zero and the digest names it. The exception is an expired login,
  which stops the run, because every later week would fail identically.
- **One digest for the whole catch-up**, not six emails.

With `--capture` this is a lot of browser work and one vision call per week, so
it prints what it is about to spend before it starts.

## Scheduling

```bash
./scripts/install_schedule.sh              # Fridays 09:00
./scripts/install_schedule.sh --at 17:30
./scripts/install_schedule.sh --status
./scripts/install_schedule.sh --uninstall
```

macOS gets a **launchd** agent, Linux a **cron** entry. launchd is the better
of the two here: it runs a job it missed while the Mac was asleep, whereas cron
silently skips it. Every run logs to `data/tracking/logs/`.

Weeks close Thursday night, so the job runs Friday morning. If the inbox is
empty when it fires, the digest says so plainly and tells you to drop the
screenshots and re-run — it does not quietly report a week of blanks.

## Design rules

- **Never invent a number.** Anything unreadable comes back `null`, stays an
  empty cell, and is listed in the digest. A plausible guess is indistinguishable
  from a reading once it is in the sheet, and these numbers drive spend.
- **Empty, never zero.** A `0` would drag down every average computed over the row.
- **A re-run never clobbers a manual edit.** If a cell already holds a different
  value the job keeps it and reports the conflict; `--overwrite` opts out.
- **Screenshots are archived once read**, so next week's unattended run cannot
  re-read them and report stale numbers as current.
- **Numbers are snapshotted to disk before anything remote is touched**, so a
  failed sheet write or a bounced email never costs the extraction.

## Tests

```bash
python tests/test_tracker.py
```

13 tests, no network. Covers the week math against the tracker's real labels,
every derived formula against real July figures, section scoping (`Orders`
exists under both `OVERALL METRICS` and `GMV MAX`), new-column writes,
idempotent re-runs, sample counting, and digest rendering.
