# Titan Ads — Production Pipeline

> End-to-end workflow for producing ready-to-publish Facebook/Instagram ad creatives.
> Combines: GetHookd research → Titan DR copy → Gemini image gen → text composite.

---

## Overview

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. RESEARCH  │───▶│  2. CONCEPT   │───▶│  3. GENERATE  │───▶│  4. COMPOSITE │
│  GetHookd API │    │  Pattern +    │    │  Gemini API   │    │  Text overlay │
│  + Titan Ads  │    │  Titan DR     │    │  (image gen)  │    │  + final QA   │
└──────────────┘    └──────────────┘    └──────────────┘    └──────────────┘
```

---

## Step 1: Research (GetHookd API)

### API Connection
```bash
# Auth check
curl -s -H "Authorization: Bearer $GETHOOKD_API_KEY" \
  "https://app.gethookd.ai/api/v1/authcheck"

# Search ads
curl -s -H "Authorization: Bearer $GETHOOKD_API_KEY" \
  "https://app.gethookd.ai/api/v1/explore?PARAMS"
```

### Key Parameters
| Param | Values | Notes |
|-------|--------|-------|
| `niche` | 30=Supplements, 16=Health, 5=Beauty, 13=Food | CSV for multiple |
| `performance_scores` | testing, scaling, growing, optimized, winning | CSV |
| `ad-format` | image, video, carousels, dco, dpa | CSV |
| `sort_column` | created_at, start_date, days_active, used_count | |
| `sort_direction` | asc, desc | |
| `per_page` | 1-100 (default 20) | |
| `language` | EN, ES, etc. | ISO 639-1 |
| `platform` | facebook, instagram | CSV |
| `creative_categories` | 1=B/A, 2=Testimonial, 16=Reasons Why, 17=Facts, 18=Features, 20=Us vs Them | |
| `run-time` | integer | Minimum days active |
| `status` | active, inactive | |

### Research Queries (Cost: 0.20 credits each)
```bash
# Winning supplement image ads, longest running
?niche=30&performance_scores=winning&ad-format=image&sort_column=days_active&sort_direction=desc&per_page=50&language=EN

# Competitor search
?query=BRAND_NAME&performance_scores=optimized,winning&per_page=50

# By creative category
?niche=30&creative_categories=20&performance_scores=winning&per_page=50  # Us vs Them
```

### API Key Location
`~/.config/api-keys/.env` → `GETHOOKD_API_KEY`

### Credits Budget
- Starting balance: ~31,000 credits
- Cost per explore query: 0.20 credits
- Budget: ~155,000 queries available

---

## Step 2: Concept Development

### Input Required
1. **Product**: What are we advertising? (from Titan DR's folqs-products.md or user input)
2. **Angle**: Which emotional angle? (from research or Titan DR's psychology framework)
3. **Pattern**: Which of the 15 creative patterns? (from creative-patterns.md)
4. **Copy**: Write the ad copy using Titan DR (headline, body, CTA)

### Concept Brief Template
```markdown
## Ad Concept Brief
- **Product**: [name + key claim]
- **Target**: [audience segment]
- **Angle**: [emotional angle from research]
- **Pattern**: [#1-15 from creative-patterns.md]
- **Headline (on image)**: [3-8 words]
- **Body Copy**: [written via Titan DR]
- **CTA**: SHOP_NOW / LEARN_MORE
- **Aspect Ratio**: 4:5 / 1:1 / 9:16
- **Visual Direction**: [scene description for Gemini]
```

---

## Step 3: Image Generation (Gemini API)

### Load Skill
`~/.memory/skills/design/gemini-image-gen/SKILL.md`

### JSON Visual Prompt Template (for product/scene shots)
```json
{
  "resolution": "1K",
  "aspect_ratio": "4:5",
  "style": "commercial product photography",
  "subject": "[product or scene description]",
  "background": "[solid color / gradient / environment]",
  "lighting": "soft studio lighting with rim light",
  "lens": "50mm",
  "aperture": "f/2.8",
  "color_palette": ["#2D1B4E", "#FFFFFF", "#F5F0EB"],
  "mood": "[premium / urgent / authentic / clinical]",
  "composition": "centered product, negative space for text overlay top and bottom"
}
```

### Key Generation Rules
1. **DO NOT include text in the prompt** — Gemini text rendering is unreliable
2. **Leave negative space** for text overlay (top 30%, bottom 20%)
3. **Specify "no text, no words, no letters"** in the prompt
4. **Generate at 1K** (1024px) for speed, upscale to 2K/4K if needed
5. **4:5 ratio** = 819×1024 at 1K, 1638×2048 at 2K

### Image Types by Pattern
| Pattern | What to Generate | What to Composite After |
|---------|-----------------|----------------------|
| #1 Problem-State | Full scene (person + environment) | Annotation overlays only |
| #2 Product Hero | Product on colored background with space | Headline + subhead |
| #3 UGC | Cannot generate — use real UGC | — |
| #4 Illustrated | Illustration of scene | Text overlay above/below |
| #5 Text-Heavy | Solid color background only | ALL text |
| #6 Billboard | Scene with blank billboard surface | Text + product on billboard |
| #7 Product + Review | Product on neutral background | Review text + offer badge |
| #8 Holiday Offer | Product with seasonal accents | Event text + offer strip |
| #9 Us vs Them | Product or comparison scene | Callout bubbles + text |
| #10 Urgency | Dark background + product | Urgency text |
| #11 Before/After | Cannot generate — use real photos | Labels |
| #12 Mechanism | Product/ingredient scene | Callout bubbles |
| #13 Science/Ingredient | Macro ingredient shot | Ingredient labels |
| #14 Listicle | Background only | All list text |
| #15 Dark Mode | Product with dramatic lighting | Minimal text |

---

## Step 4: Text Composite

### Method A: ImageMagick (Simple overlays)
```bash
# Headline overlay
convert generated.png \
  -gravity North \
  -font "/path/to/Montserrat-Bold.ttf" \
  -pointsize 72 \
  -fill white \
  -stroke "rgba(0,0,0,0.3)" -strokewidth 1 \
  -annotate +0+60 "HEADLINE TEXT HERE" \
  output.png

# Offer strip at bottom
convert output.png \
  -gravity South \
  -fill "#FF0000" -draw "rectangle 0,1270 1080,1350" \
  -fill white -font "/path/to/Montserrat-Bold.ttf" \
  -pointsize 48 -annotate +0-20 "70% OFF TODAY ONLY" \
  final.png
```

### Method B: HTML→Screenshot (Complex layouts)
```bash
# Create HTML template with positioned elements
# Screenshot with Puppeteer
npx puppeteer screenshot composite.html --width=1080 --height=1350 --fullpage
```

### Method C: Gemini Reference Image (Text overlay)
If the text is simple (1-2 lines), Gemini can overlay text on a reference image:
1. Generate base image
2. Send base image back to Gemini with prompt: "Add bold white text '[TEXT]' at the top of this image"
3. Tested and working (see daily log 2026-03-05 — text overlay test)

**Reliability ranking**: HTML→Screenshot > ImageMagick > Gemini Reference
**Speed ranking**: Gemini Reference > ImageMagick > HTML→Screenshot

---

## Full Production Example

### Brief: Folqs Colostrum — "Us vs Them" Ad

**Step 1**: Research shows comparison ads run 90+ days for Folqs
**Step 2**: Concept brief:
- Product: Folqs First-Day Colostrum
- Pattern: #9 Us vs Them
- Headline: "YOUR $100 COLOSTRUM IS LITERAL ANIMAL FEED"
- Visual: Glass of white powder on dark-gold gradient

**Step 3**: Gemini prompt:
```
Commercial product photography of a glass of pale yellow colostrum powder
on a dark background with warm golden gradient lighting. 50mm lens, f/2.8,
studio lighting with warm rim light. Leave negative space at top and bottom
for text overlay. No text, no words, no letters in the image.
```

**Step 4**: Composite:
- Top: "YOUR $100 COLOSTRUM IS LITERAL ANIMAL FEED" (white, bold, 64pt)
- Middle: 3 callout bubbles with icons (overlay via HTML)
- Bottom: "FIRST-DAY COLOSTRUM IS GOLDEN. FOLQS IS GOLDEN." (yellow, bold)

**Step 5**: Write body copy via Titan DR (300-600 chars, mechanism hook)

---

## Batch Production Workflow

For producing multiple ad variants efficiently:

1. **Define the campaign** — 3-5 angles for the same product
2. **Write all copy first** — Titan DR batch (5 variations per angle)
3. **Select patterns** — 1 pattern per angle, don't repeat patterns
4. **Generate all base images** — Gemini batch (1 per angle + 1-2 variants each)
5. **Composite all text** — HTML template with variables, batch screenshot
6. **QA pass** — Check text readability, brand consistency, compliance

### Estimated Output
- Per session: 5-10 complete ad creatives
- Cost: ~$0.50-1.00 Gemini + ~1-2 GetHookd credits
- Time: 30-60 minutes for a 5-ad batch

---

## Data Files

| File | Location | Contents |
|------|----------|----------|
| Raw API data | `~/Downloads/Workforce/gethookd-raw-ads.json` | 1,383 ads (pre-dedup) |
| Unique ads | `~/Downloads/Workforce/gethookd-unique-ads.json` | 1,255 ads (deduped) |
| DTC summary | `~/Downloads/Workforce/ad-library-summary.csv` | 145 DTC image ads |
| Reference images | `~/Downloads/Workforce/ad-library-images/` | 100 images, 13 brands |

### Refreshing Data
To pull fresh ads from GetHookd:
```python
# See /tmp/gethookd_pull.py for the full pull script
# Key: stored in ~/.config/api-keys/.env as GETHOOKD_API_KEY
# Cost: ~15 credits per full pull (brands + categories + top winning)
```
