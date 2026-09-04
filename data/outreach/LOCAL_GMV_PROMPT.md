# Prompt for a LOCAL Claude Code session — pull creator GMV

Why local: creator-level GMV only exists behind a TikTok Shop **seller login**.
No public page or free API exposes it, and every third-party tracker
(Kalodata, FastMoss, EchoTik, Shoplus) is paywalled. A local session can drive
the browser you are already logged into, which the cloud session cannot.

Copy everything below the line.

---

I want TikTok Shop GMV for a list of creators I'm negotiating retainers with.

## Repo

`adamfolqs/Repo`, branch `claude/tiktok-colostrum-scraping-1m98qn`. Clone it and
read `README.md` first — there's a working scraper, and don't rebuild it.

What's already there:
- `data/outreach/campaign_roster.csv` — 138 creators I emailed, with
  `reply_status`. The ones I care about are `interested` and `replied`.
- `tiktok_scraper/` — the scraper. `providers/http_ssr.py` reads TikTok's SSR
  blob over plain HTTP; `providers/discover.py` drives a browser.
- `build_sheet.py` — rebuilds `data/output/colostrum_creator_list.xlsx`.
- `track_replies.py` — reconciles email replies into the roster.

## The job

For every creator in the roster with `reply_status` of `interested` or
`replied` (13 right now), get their TikTok Shop GMV, and write it back.

**The door is the TikTok Shop Creator Marketplace / affiliate creator search,
in my logged-in seller account.** Search each `handle`, open the creator, and
read the figures it shows — typically 30-day GMV, average video GMV, items
sold, and category. Take whatever it actually shows.

### Use my existing Chrome session, don't log in yourself

Don't try to script a login and don't ask me for credentials. Attach to the
browser I'm already signed into:

```bash
# quit Chrome fully first, then:
# macOS
/Applications/Google\ Chrome.app/Contents/MacOS/Google\ Chrome \
  --remote-debugging-port=9222 --user-data-dir="$HOME/chrome-tiktok"
# then sign in to TikTok Shop seller centre in that window, once
```

```python
from playwright.sync_api import sync_playwright
with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp("http://localhost:9222")
    ctx = browser.contexts[0]          # my real, logged-in session
    page = ctx.new_page()
```

Two things from the cloud run that do **not** apply locally: the
`--ssl-version-max=tls1.2` flag and the proxy `server=` argument exist only to
get through this sandbox's egress proxy. Drop both — locally they just slow
the handshake.

Keep `REQUEST_DELAY_SECONDS=2.5` between requests. It's a logged-in session on
my own account; getting it rate-limited is a real cost.

### Rules

- **Never invent or estimate a GMV number.** If the marketplace has no data for
  a handle, leave it empty and set `gmv_status` to say why (`not on marketplace`,
  `no sales data`, `handle not found`). A made-up number here decides what I pay
  someone.
- Record what the figure actually is: a 30-day GMV and a lifetime GMV are not
  the same column. Put the window in `gmv_window`.
- Screenshot each creator's marketplace page into `data/outreach/gmv_shots/` so
  I can check any number myself.

### Output

Add to `campaign_roster.csv`, and to the `Outreach` tab via `build_sheet.py`:

`gmv_30d`, `gmv_lifetime`, `avg_video_gmv`, `items_sold`, `gmv_window`,
`gmv_status`, `gmv_checked_at`

Then tell me: who has real GMV, who doesn't, and the ranking of the 13 by GMV
against what they're asking. Two of them came through an agency claiming
$162k (@adoseofwellness) and $60k (@therealjnic_ole) 30-day GMV — those are
unverified sales claims, so flag whether the marketplace agrees.

## If you have spare time after that

`data/output/discovered_urls.csv` has ~4,400 discovered colostrum video URLs
still unresolved (1,214 of 5,687 done). From a residential IP you'll get a
better hit rate than the cloud run did:

```bash
python -m tiktok_scraper resolve --priority-handles
python -m tiktok_scraper profiles
python build_sheet.py
```

Every stage is resumable and skips what's already stored. Commit and push to
the same branch as you go.
