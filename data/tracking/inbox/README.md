# Screenshot inbox

Drop this week's TikTok Shop analytics screenshots here, then the Friday job
reads them. Anything in here is treated as belonging to the week being
reported, so clear it out between weeks — the scheduled run archives what it
reads into `../archive/<week>/` automatically, which keeps that true.

Useful screens to capture:

| Screen | Fills in |
|---|---|
| Shop → Analytics → Overview (set to the report week) | GMV, Orders, Items Sold, Customers, AOV, Refunds |
| Shop → Analytics → Traffic | Impressions, Clicks, CTR, CTOR |
| Shop → Analytics → Creators / Affiliate | Affiliate GMV, Videos Posted |
| GMV Max / ad manager | Cost, ad Orders, ROI |
| Shop performance score | Shop Performance Score |

Two things the screenshots can't tell the job, because they aren't on any
TikTok screen:

- **Retainer & whitelisting payments** — pass it in: `--set retainer_payments=2050`
- **Samples sent** — counted from the sample tracker, or `--samples-sent 26`

Make sure each screenshot shows the **date range**. Where the period is
ambiguous the job returns null rather than guessing, and you get an empty cell
plus a flag in the digest instead of a wrong number.
