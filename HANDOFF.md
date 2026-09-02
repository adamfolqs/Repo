# Handoff — Folqs colostrum creator sourcing + outreach

State as of **2026-09-01 08:30 UTC**. Everything below is committed and pushed.

- **Repo/branch:** `adamfolqs/Repo` → `claude/tiktok-colostrum-scraping-1m98qn` (PR #2)
- **Workbook:** `data/output/colostrum_creator_list.xlsx` — 6 tabs, `Outreach` first
- **Drive:** folder *Colostrum Creator Sourcing — TikTok Scrape (Aug 2026)*
  `13Tdh00xvY2exeQPQ5e7h5LArPhOtuih_` (snapshot, not live — see caveats)

---

## 1. What was built

A four-stage TikTok scraper. The important finding is the **surface map** —
which TikTok pages actually serve data, measured not assumed:

| Surface | Serves data? | Notes |
|---|---|---|
| `/@handle` | yes | SSR blob: profile + follower counts |
| `/@handle/video/<id>` | yes | SSR blob: exact like/view/comment/share/save |
| `/embed/@handle` | yes | 10 most recent posts, no pagination |
| `/discover/<keyword>` | yes | client-rendered grid, ~60 videos, needs browser |
| `/search?q=` | **no** | login-walled, renders skeletons only |
| `/tag/<hashtag>` | **no** | client-rendered, nothing behind it |
| profile video grid | **no** | login-walled; `/api/post/item_list/` needs signing |
| `shop.tiktok.com` PDP | **partial** | product data yes, creator videos are app-only |

Consequence: **discovery and enrichment are separate problems.** Keyword pages
name videos but carry no numbers; every number comes from opening the video's
own page. Nothing in the pipeline can estimate a like count.

```bash
python -m tiktok_scraper discover --keyword-file data/input/discover_keywords.txt --crawl-depth 2
python -m tiktok_scraper catalogue                 # each creator's other posts
python -m tiktok_scraper resolve --priority-handles # URLs -> real numbers
python -m tiktok_scraper profiles                  # followers + bio email
python -m tiktok_scraper names                     # sourcing-sheet names -> verified handles
python build_sheet.py                              # assemble the workbook
```

Every stage appends to a JSONL store and skips ids already present, so any
stage resumes rather than restarts.

## 2. Data collected

- **1,214** videos resolved of **5,687** discovered (the rest still queued)
- **441** colostrum videos, **143** qualifying (50+ likes, product-tagged)
- **351** creator profiles — 292 with followers, **138** with a real email
- Original 177-row sourcing sheet: **125 handles filled**, up from 20

## 3. Campaign sent 2026-08-31 14:2x UTC

134 creators, nine BCC blobs from `adam@folqs.co`, all threaded to that inbox.
One blob per competitor anchor so the opener names the brand they posted about
("Loved your **Cymbiotika** colostrum video 🙌"), plus generic and Spanish.
Thread ids: `data/outreach/campaign_threads.json`. Copy:
`data/outreach/email_templates.md`.

**4 excluded on purpose:** brand-owned accounts, and creators who posted
critical/debunking colostrum content — a retainer pitch to them backfires.

### Replies so far — 22 / 134 (16%)

**Interested (16):**

| Handle | Followers | Anchor | Email | Ask |
|---|---|---|---|---|
| @nutritionbyjulie | 306k | generic | julie@mightyjoy.com | via mgr Philip — **no WhatsApp**, wants details + budget |
| @jennymurcia9 | 81.3k | Miracle Moo (ES) | jennycollab9@gmail.com | claims **$2.5M GMV** in Spanish-speaking US — unverified |
| @themayhughs | 58.5k | Bloom | kaily@a-listme.com | via agency Logan — **sent rates + analytics link** |
| @daniloshopfinds | 41.6k | Physician's Choice | huntersipovac@gmail.com | open to hearing more |
| @o_m_briii | 30.7k | Cymbiotika | ombri.24@lumasocialagency.com | **$800/video, $1,600/3 videos**; WhatsApp +1 (310) 948-7728 |
| @11lisamariet | 12.9k | ARMRA | contactlisamarie11@gmail.com | interested, **prefers email** |
| @hellomrshockett | 12.6k | generic | hellomrshockett@gmail.com | **6056900645** |
| @mollymcshane13 | 8.5k | Miracle Moo | mollymcshane13@gmail.com | wants retainer details |
| @dawndeeeeee | 7.8k | Bloom | dawndcreator@gmail.com | wants deliverables, video count, rate |
| @oliviaa_x6 | 5.1k | Miracle Moo | oliviaslifestyle22@gmail.com | interested, **no WhatsApp** |
| @renatovar | 3.8k | Bloom | renasttshop@gmail.com | quotes **$500 flat** |
| @herbfairytiera | 3.8k | ARMRA | herbfairytiera@gmail.com | checked out Folqs, keen |
| @lifebeyondthelisting | 3.8k | ARMRA | lifebeyondthelisting@gmail.com | wants details |
| @icedbeverly4l | 2.9k | Cymbiotika | emilywarumugc@gmail.com | **516-668-3243** |
| @kodyhatt | 2.9k | generic | ttshopkodyhatt@gmail.com | wants rate, deliverables, timeline |
| @ciarathemodel | 811 | generic | ciaraalicia2001@gmail.com | wants details |

**Replied (4):** @adoseofwellness (107.9k) and @therealjnic_ole (80.3k), both via
`kaspar@nowadaystalent.com` claiming **$162k** and **$60k** 30-day GMV —
unverified sales claims from someone pitching us; @creakzshop (64.1k, positive);
@katzammuto (16.3k) — **asked "what is the name of the brand?" and is still
waiting on an answer.**

**Declined (2):** @in.good.hands.collective (129.2k — human colostrum /
breastfeeding education, not bovine: a targeting miss); @thegutgirlie (12.4k —
workload).
**Bounced (2):** @leeleesfavfinds (75.9k) — `leeleecreates.com` does not
resolve; @click.flicks.ugc (30.9k) — Gmail address does not exist. Neither
was ever delivered, so 132 of the 134 actually landed.
**Auto-replies (4).**

**Signal worth acting on:** 6 of 16 pushed back on WhatsApp. The CTA is the
friction point with this list — they skew manager/email.

## 4. Live automation

Routine `trig_01VXoygdwzeuU3LuFAQ32YXQ` — "Colostrum outreach — hourly reply
sweep", fires **:23 past each hour** into the original session. It reads the
nine campaign threads by id, appends to `data/outreach/replies.json`, runs
`track_replies.py`, rebuilds the workbook, commits, and reports only what
changed. **Delete it when the campaign is done.**

## 5. Traps already hit — don't rediscover

- **Chromium behind the sandbox proxy:** TLS 1.3 ClientHello carries a
  post-quantum key share; the proxy killed *every* navigation as
  `ERR_CONNECTION_RESET` for all hosts. Fix is `--ssl-version-max=tls1.2`,
  **not** `--ignore-certificate-errors`. Locally, drop both.
- **Captcha detection:** don't match a bare `/captcha/` — the captcha SDK's
  asset URL is on every normal TikTok page.
- **Fabricated emails:** the obfuscated-email regex matched "at"/"dot" inside
  ordinary words and invented 3 addresses (`detoxheather.com` →
  `detoxhe@her.com`). Fixed + tested; separators must be standalone tokens.
- **Autoresponders scoring as leads:** one says "thanks for your interest",
  which any keyword matcher reads as hot. Auto-replies are now ruled out
  before enthusiasm is scored.
- **Replies come from someone else:** 4 of 14 came from a manager, an agency,
  or mailer-daemon rather than the address mailed. `attribute()` resolves
  these, but never guesses when two recipients share an agency domain.
- **Alix Earle** is a fan of *colostrum*, not of Folqs — every mention in the
  scrape is Cymbiotika's liquid colostrum from a podcast. The copy keeps her
  inside the trend sentence. Don't move her next to the product.

- **Gmail search previews hide new replies:** `search_threads` returns only the
  ~5 *oldest* messages per thread and shows no truncation marker. On a BCC blob
  thread with dozens of recipients that silently buries every later reply — it
  cost 3 missed replies before it was caught. Sweep by `get_thread` on each
  campaign thread id, and use search only to catch bounces and autoresponders,
  which arrive on threads of their own.
- **The workbook is rebuilt from scratch every run.** `build_sheet.py`
  creates a new `Workbook()`, so any tab assembled by a one-off script is
  silently dropped on the next rebuild -- which is exactly what happened to
  the Outreach tab. It is now built inside `build_sheet.py` from
  `campaign_roster.csv`. Never add a tab from outside that file.
- **Bounces never match a subject search:** a Gmail bounce is subject
  "Delivery Status Notification (Failure)", so `subject:("Folqs Bovine
  Colostrum")` cannot find one. It only surfaces because it sits on the
  campaign thread — another reason to sweep by thread id. One bounce hid
  this way for 18 hours.

## 6. Open threads

1. **GMV** — not obtainable from here. Needs a TikTok Shop seller login; every
   third-party tracker is paywalled. Use `data/outreach/LOCAL_GMV_PROMPT.md`
   in a local session. @themayhughs' agency already sent an analytics link.
2. **Follow-up email** to the 11 — asking rate + recent shop GMV screenshot,
   and dropping WhatsApp-only. Drafted in conversation, not yet written or sent.
3. **~4,400 URLs unresolved.** `resolve --priority-handles` picks up where it
   left off. Better hit rate from a residential IP.
4. **Product specs still missing.** The Primal 8 email won on "3000mg vs
   300mg". Colostrum mg / IgG % / sourcing would make the brand-anchored
   variant much stronger.
5. **Drive is a snapshot.** The connector can only change a file's title or
   location, never its contents, so hourly refreshes would pile up duplicates.
   Re-upload on request.
