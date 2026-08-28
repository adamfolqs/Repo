# Why TikTok Shop orders arrive in bursts

Research note. Question: nothing for hours, then six orders (MV79066–MV79071)
between 12:32 and 13:11, all Fulfilled by TikTok Shop-Standard, AOV ~$39.

## Short answer

TikTok Shop demand is triggered by impressions, not by shelf browsing, and
impressions are delivered to whole cohorts at once in discrete steps. Orders
inherit the shape of the thing upstream of them. A flat order curve would be
the anomaly.

## Four stacked causes

1. **Distribution steps up, it doesn't ramp.** A video is retrieved and ranked
   for a cohort of similar users, then released to a wider cohort if engagement
   clears thresholds. Seller education calls these "traffic pools" (~500 users
   first, then exponentially larger); TikTok's transparency docs describe
   prediction scores combined into a ranking, not tiers. Observable behaviour is
   the same: reach moves in jumps, so purchases compress into the jump.
2. **The model retrains in minutes.** ByteDance's *Monolith* paper documents
   online training with minute-scale parameter updates. Your first conversion is
   itself a training signal that raises predicted CVR, buying more distribution,
   producing the next conversion. A feedback loop with a minutes-long time
   constant produces clusters, not evenly spaced arrivals.
3. **The commerce layer rewards velocity.** A Shop-specific layer weights
   conversion rate, sales velocity and shop health. FBT compounds it: FBT stock
   qualifies for the free 3-day delivery tag and feeds dedicated FBT / "Deals
   for You" surfaces, so a product can be flipped into new placement as a
   discrete event.
4. **Content supply is bursty.** ~90% of GMV for top shops comes via affiliate
   creators; sales track how many creators posted and when. Attribution windows
   keep it tight — 7-day click / 1-day view for Shop Ads, commonly 24–72h for
   affiliate.

## Is six-in-forty unusual? Depends on daily volume

Chance that a day contains at least one 40-minute window holding 6+ orders,
treating arrivals as random:

| Orders/day | Expected per 40 min | Chance of a 6+ cluster | Read |
|---|---|---|---|
| 20 | 0.6 | ~0.5% | real demand event |
| 50 | 1.4 | ~10% | probably real |
| 100 | 2.8 | ~90% | expected by chance |
| 200 | 5.6 | >99% | noise |

Under ~30/day, go find the video. Over ~100/day, it's just a busy hour. Real
numbers skew higher than the table because orders concentrate in the afternoon
and the 19:00–22:00 window rather than spreading over 24 hours.

Independently: human activity is inherently bursty — Barabási showed
inter-event gaps are heavy-tailed rather than Poisson.

## Rule out first

- **Shopify's view is not TikTok's view.** Native integration creates orders
  near-real-time but they land *On-Hold for up to an hour* (buyer cancellation
  window); third-party connectors run 5–15 min behind. All six show *Archived* —
  Shopify archives on fulfilment and FBT fulfilment events land in batches, which
  can render an ordinary morning as one block. Compare against Seller Center.
- **New Shop Probation caps.** 50/day Beginner, 100/day Standard, 200/day
  Premium, uncapped at Pro. Hitting a cap produces exactly "burst then silence".

## Diagnostic

1. Seller Center → Analytics, split GMV by video / LIVE / product card.
2. Video Analytics sorted by GMV and SKU orders — find the video whose orders
   bunch 12:20–13:15.
3. GMV against product cards or search instead means a placement change, not
   creator content.
4. Check creator posting volume for the prior 24h — leading indicator.
5. Ads Manager credits the interaction date, Seller Center the transaction date;
   the same orders can land on two different days.
6. GMV Max under ~$50/day spends erratically — the pattern is the budget.

**Operational consequence:** concentration beats spread. Ten creator posts in
one afternoon out-earn ten spread over a fortnight, because each conversion
feeds the next inside the same training window. Never let a burst break
fulfilment; FBT already shields SPS from late-delivery and on-time-delivery
penalties.

## Evidence quality

Reddit blocks our crawler, so r/TikTokshop and the seller subreddits could not
be read first-hand, and Facebook seller groups are unreachable. Community
reporting below is second-hand via seller education, agency writeups and the
Shopify forum. The strongest-sourced claims are the ByteDance retraining paper
and TikTok's own probation-cap and Shopify on-hold documentation.

## Sources

- ByteDance, *Monolith: Real Time Recommendation System With Collisionless Embedding Table* — https://arxiv.org/pdf/2209.07663
- TikTok, Introduction to the recommendation system — https://www.tiktok.com/transparency/en/recommendation-system
- TikTok Newsroom, How TikTok recommends videos #ForYou — https://newsroom.tiktok.com/en-us/how-tiktok-recommends-videos-for-you
- TikTok Seller University, New Shop Probation Program — https://seller-us.tiktok.com/university/essay?knowledge_id=3238037484062465&lang=en
- TikTok Seller University, TikTok for Shopify onboarding — https://seller-us.tiktok.com/university/essay?knowledge_id=6184952698373890&lang=en
- TikTok Seller University, Fulfilled by TikTok (FBT) — https://seller-us.tiktok.com/university/essay?knowledge_id=8644984183162670&lang=en
- TikTok Ads, About attribution for TikTok Shop Ads — https://ads.tiktok.com/help/article/about-tiktok-shop-ads-attribution?lang=en
- Emplicit, Ultimate Guide to TikTok Shop Traffic Attribution — https://emplicit.co/ultimate-guide-tiktok-shop-traffic-attribution/
- MomentIQ, TikTok Shop Category Ranking — https://bemomentiq.com/blog/tiktok-shop-category-ranking-secrets-how-algorithm-decides-which
- Barabási, The origin of bursts and heavy tails in human dynamics, Nature — https://www.nature.com/articles/nature03459
- Shopify Community, TikTok Shop App Order Syncing Issue — https://community.shopify.com/t/tiktok-shop-app-order-syncing-issue/382028
- ZonFlip, TikTok Shop GMV Max Budget Rules — https://zonflip.com/tiktok-shop-gmv-max-budget-rules-the-operators-breakdown-for-2026/
