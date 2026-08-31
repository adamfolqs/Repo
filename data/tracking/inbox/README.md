# Screenshot inbox

Drop this week's TikTok Shop screenshots here, then the Friday job reads them.
Everything in here is treated as belonging to the week being reported, so it
must not carry over between weeks — the scheduled run archives what it reads
into `../archive/<week>/` automatically, which keeps that true.

## Where each number comes from

TikTok splits these across **three separate places** — Seller Center, Ads
Manager, and Account Health — so this is several screenshots, not one.

| # | Where | Fills in |
|---|---|---|
| 1 | **Analytics → Shop analytics** | GMV, Orders (SKU Orders), Items Sold, Customers, AOV, Refunds, CTOR |
| 2 | **Analytics → Product analytics → Product traffic analysis** | Impressions, Clicks, CTR |
| 3 | **Analytics → Creator** tab | Affiliate GMV, Videos Posted |
| 4 | **Orders → Awaiting Shipment → All → Filters → Order Tag → both free-sample options → Apply** | Samples Sent — the "xx orders" total |
| 5 | **Ads Manager** (GMV Max campaign) | Cost, ad Orders, ROI |
| 6 | **Account Health → Shop Performance Score** | Shop Performance Score |

Notes on a few of these:

- The left sidebar is labelled **"Data Compass"** in some regions and versions
  and **"Analytics"** in others. Same thing.
- **Traffic metrics are not on the Shop analytics homepage.** TikTok moved
  product-level traffic (impressions/clicks/CTR) out to Product analytics, so
  screen 2 is a separate capture from screen 1.
- **Shop Performance Score is not under Analytics** — it lives in Account
  Health, and only exists once the shop has 30+ orders in the last 90 days.
- **Samples: the order-tag filter is what makes the count correct.** An
  unfiltered order total is not the sample count. Set the date range too. If a
  screenshot doesn't visibly show the free-sample Order Tag filter applied, the
  job returns null rather than using the number.

## Two things no TikTok screen can tell it

- **Retainer & whitelisting payments** — from your expense tracker:
  `--set retainer_payments=2050`
- A sanity check on samples comes from the retainer sample tracker sheet
  automatically. It only sees warehouse POs, so it will usually read lower than
  the order-tag count; the digest flags a gap rather than picking a winner.

## Getting the period right

**Every screenshot must show its date range**, and the range must be the
reporting week (Friday→Thursday). Screenshots often also show lifetime, 7-day,
28-day or comparison figures side by side. Where the period is ambiguous the
job returns null and flags it, so you get an empty cell plus a line in the
digest instead of a confident wrong number.
