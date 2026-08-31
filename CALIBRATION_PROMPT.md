# Prompt for Claude in Chrome — Seller Center calibration

Paste everything below the line into a Claude session that has the Chrome
extension, in a browser already logged into TikTok Seller Center.

Bring the JSON it produces back to the Claude Code session working on
`folqs_tracker`, which will fold it into `capture_plan.json`.

---

I need you to do a **read-only reconnaissance** of my TikTok Seller Center so I
can automate a weekly reporting job. I am logged in already.

## Rules — please follow these exactly

This is a **live business account**. Treat it as read-only:

- **Do not click anything that changes state.** No shipping, approving or
  rejecting samples; no editing, pausing, starting or adjusting ad campaigns or
  budgets; no messaging creators; no changing settings, prices or inventory.
- Navigating, opening menus, setting a date-range filter, and applying a view
  filter are all fine. Anything with a verb like Save, Submit, Confirm, Ship,
  Approve, Pause, Delete or Send is not.
- **Do not type, read back, or record any password, or the contents of any
  password manager.** You do not need credentials — I am already signed in.
- If a screen asks you to re-authenticate, stop and tell me rather than
  attempting it.
- If anything is ambiguous, stop and ask instead of guessing.

## What I need

For each of the six screens below: navigate to it, **set the date range to
3 July 2026 – 9 July 2026** where the screen has one, then record what I ask for.

I have picked that specific week on purpose: if those dates appear anywhere in
the URL, I can tell exactly which query parameters carry the range.

| # | key | Screen |
|---|---|---|
| 1 | `shop_analytics` | Analytics → Shop analytics (GMV, orders, items sold, customers, AOV, refunds, CTOR) |
| 2 | `product_traffic` | Analytics → Product analytics → Product traffic analysis (impressions, clicks, CTR) |
| 3 | `creator` | Analytics → Creator tab (affiliate GMV, videos posted) |
| 4 | `samples` | Orders → Awaiting Shipment → All → Filter → Order Tag → the free-sample options → Apply |
| 5 | `ads` | Ads Manager → the GMV Max campaign view (cost, orders, ROI) |
| 6 | `account_health` | Account Health → Shop Performance Score |

For each screen tell me:

- **`url`** — the full URL **after** the date range is applied. Copy it exactly,
  including every query parameter. This matters more than anything else here.
- **`dates_in_url`** — true/false: do `2026-07-03` / `2026-07-09` (in any
  format — ISO, `07/03/2026`, or a 10- or 13-digit timestamp) actually appear in
  the URL? If the date range lives only in the page's own controls and never
  reaches the URL, say so plainly; that changes how I automate it.
- **`expect_text`** — a short, distinctive phrase that is visibly on that screen
  and would **not** appear on a login page or an error page. A metric label like
  "Items Sold" is ideal. Two or three words.
- **`menu_path`** — the actual sidebar/menu labels you clicked, in order. My
  notes may be out of date, and I would rather have what you actually saw. Note
  in particular whether the sidebar says "Analytics" or "Data Compass".
- **`notes`** — anything surprising: a screen that does not exist, a metric
  that has moved, a different sub-tab, an interstitial.

## Extra questions

1. **Samples (screen 4) is the one I care most about.** Under Filter → Order
   Tag, list **every** option shown, verbatim. I believe one is called "Free
   Sample from Seller"; I need the exact wording of that one *and* of any other
   sample-related option, since I am told there are two.
   After applying the filter, also tell me:
   - the exact click sequence you used, in order, with the visible label of each
     thing you clicked;
   - whether the applied filter stays visible on screen afterwards (e.g. as a
     chip or tag) and its exact text — I use that to prove the filter really
     applied, because an unfiltered order list looks identical but means
     something completely different;
   - where the total order count appears and its exact wording (e.g. "47
     orders").

2. **Ads Manager (screen 5)** — is it a separate site (`ads.tiktok.com`) with
   its own login, or reachable from Seller Center in the same session?

3. Is there **any export or download** on the analytics screens (CSV/XLSX)? If
   so, where? Structured data would beat reading numbers off a screenshot.

## Output format

Finish with one JSON block in exactly this shape, so I can paste it straight in:

```json
{
  "targets": [
    {
      "key": "shop_analytics",
      "name": "Analytics -> Shop analytics",
      "url": "<full URL with the dates applied>",
      "dates_in_url": true,
      "expect_text": "Items Sold",
      "menu_path": "Analytics > Shop analytics",
      "notes": ""
    }
  ],
  "order_tag_options": ["<verbatim>", "<verbatim>"],
  "samples_click_sequence": ["Filter", "Order Tag", "<label>", "Apply"],
  "samples_applied_filter_text": "<the chip text, verbatim>",
  "samples_count_wording": "<e.g. '47 orders'>",
  "ads_manager_separate_login": true,
  "export_available": "<where, or 'none found'>"
}
```

Do all six screens if you can. If one is genuinely unreachable, include it with
an empty `url` and say why in `notes` — a known gap is far more useful to me
than a guess.
