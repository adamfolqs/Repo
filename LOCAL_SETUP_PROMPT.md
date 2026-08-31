# Prompt for a local Claude Code session

Paste everything below the line into Claude Code running **on your own Mac**,
in a clone of this repo. It has to be local: the capture step needs a real
browser logged into Seller Center from a residential IP.

---

Help me get the weekly TikTok Shop performance tracker in this repo actually
running. It is already built and tested — **read `README.md` first, and extend
it rather than rebuilding it.**

**Repo:** `adamfolqs/Repo`, branch `claude/weekly-performance-tracking-bot-n94781`
(PR #1). Start with `git pull`.

## What it does

Replaces my manual Friday routine — screenshot the TikTok dashboards, paste them
into Claude, retype the numbers into our wiki — with one scheduled job:

```
screenshots ─► Claude vision ─┐
sample tracker ─► samples ────┼─► derive + cross-check ─► "Weekly Performance (1)" tab
manual --set values ──────────┘                        └─► email + Telegram
```

It writes into the **Folqs TikTok Shop Wiki**, tab **`Weekly Performance (1)`**.
That tab is transposed — metrics are rows, each week is a new **column** — and
week labels are `DD/MM–DD/MM` with an **en dash**, Friday to Thursday.

## Do this in order

```bash
./scripts/setup.sh                              # venv, deps, Chromium, .env
python tests/test_tracker.py                    # 27 tests, no network — expect all pass
```

Then fill in `.env` and `service_account.json` (see below), and:

```bash
.venv/bin/python -m folqs_tracker login         # a browser opens — I log in, 2FA and all
.venv/bin/python -m folqs_tracker calibrate     # walk the 6 screens, it records their URLs
.venv/bin/python -m folqs_tracker check         # verifies credentials + tab layout
.venv/bin/python -m folqs_tracker capture --headed --only shop_analytics
.venv/bin/python -m folqs_tracker run --capture --dry-run --print-report
```

Only once that dry run looks right:

```bash
.venv/bin/python -m folqs_tracker run --capture          # write this week for real
.venv/bin/python -m folqs_tracker backfill --capture --dry-run   # then the missing weeks
./scripts/install_schedule.sh                            # launchd, Fridays 09:00
```

**Show me the output of `check` and the first headed capture before going
further.** I want to see it work on one screen before it touches six.

## Credentials I need to provide

Ask me for these — do not invent or guess them:

1. `ANTHROPIC_API_KEY` in `.env` — reads the screenshots.
2. `service_account.json` — a Google service account. **Both** the wiki and the
   sample tracker must be shared with its `client_email` as **Editor**. Missing
   that share is a 403 and is the step everyone forgets.
3. SMTP (a Gmail App Password, not my login password) and a Telegram bot token +
   chat id. A Telegram bot cannot message me until I have messaged it first.

## The six screens

TikTok splits these across three surfaces, so this is several captures:

| key | Where |
|---|---|
| `shop_analytics` | Analytics → Shop analytics — GMV, orders, items sold, customers, AOV, refunds, CTOR |
| `product_traffic` | Analytics → Product analytics → Product traffic — impressions, clicks, CTR |
| `creator` | Analytics → Creator tab — affiliate GMV, videos posted |
| `samples` | Orders → Awaiting Shipment → All → Filter → Order Tag → free-sample options → Apply |
| `ads` | Ads Manager (GMV Max) — cost, ad orders, ROI |
| `account_health` | Account Health → Shop Performance Score |

The sidebar reads "Analytics" in some regions and "Data Compass" in others.

Two values no TikTok screen provides:

- **Retainer & whitelisting payments** — from our expense tracker:
  `--set retainer_payments=2050`
- **Samples sent** — read from the Orders screen above. The retainer sample
  tracker sheet is only a cross-check; it sees warehouse POs only and reads
  low.

## Rules that matter more than finishing

- **Never invent a number.** If a metric cannot be read, it stays `null`, the
  cell stays empty, and the digest flags it. An estimate is indistinguishable
  from a reading once it is in the sheet, and these numbers drive real spend.
- **Empty, never zero** — a `0` drags down every average over that row.
- **Do not clobber manual edits.** A re-run keeps an existing differing value
  and reports the conflict; `--overwrite` is opt-in.
- The wiki is a **live shared spreadsheet**. Prefer `--dry-run` first, and do
  not touch tabs other than `Weekly Performance (1)`.
- The wiki's **Homepage tab contains plaintext passwords**. Do not read, copy,
  echo or commit them. (Separately: they should not be there — worth telling me
  again if you see them.)
- Browser automation runs against a **live business account**. Navigating and
  filtering is fine; anything that ships, approves, pauses, sends or edits is
  not.

## Known gaps — please close these

1. **The Claude vision extraction has never actually executed.** No API key was
   available where it was written. The first `run --capture --dry-run` is its
   first real test. Check the extracted numbers against the screens by eye
   before trusting a write.
2. **The samples Order Tag has a second option whose exact label I need.**
   `capture_plan.json` currently encodes "Free Sample from Seller". During
   `calibrate`, get the verbatim label of the other sample option and add it.
   The target's `expect_text` must be the **applied-filter chip text** — that is
   what proves the filter applied, since an unfiltered order list looks
   identical but means something an order of magnitude different.
3. **Any screen whose date range is not in its URL** cannot be pointed at a past
   week. `import-calibration` warns about these. Those screens need their date
   range set via clicks in `actions`, or backfill will silently report the same
   week repeatedly.
4. **Is there a CSV/XLSX export** on any analytics screen? If so, tell me —
   structured data beats reading numbers off a screenshot and would let us drop
   the vision step for those metrics.

## Backfill

The tracker is ~6 weeks behind. Last complete column is `10/07–16/07`; the
weeks needing filling are `17/07–23/07` through `21/08–27/08`. `backfill` runs
the normal pipeline once per week, oldest first, skipping weeks already done.
Dry-run it first — with `--capture` it is six browser runs and six vision calls.

## Done looks like

`check` all green; one real week written to the tab with an email and Telegram
that arrived; the six missing weeks filled; the launchd job installed. Commit
and push to `claude/weekly-performance-tracking-bot-n94781` as you go — that
updates PR #1.
