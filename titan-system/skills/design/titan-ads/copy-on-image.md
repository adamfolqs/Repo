# Titan Ads — Copy-on-Image Rules

> How to place text on ad images for maximum impact. Rules extracted from 509 winning image ads.

---

## The 3 Text Tiers

Every ad image has at most 3 tiers of text. Most winning ads use only 1-2.

### Tier 1: HEADLINE (Required for text-on-image ads)
- **Length**: 3-8 words
- **Style**: Bold, ALL CAPS or Title Case, largest text on image
- **Placement**: Top 1/3 of image (above product) or center
- **Color**: White on dark, Black on light — NEVER low contrast
- **Font**: Bold sans-serif. Montserrat Black, Inter Bold, Impact, or brand font

### Tier 2: SUBHEAD / OFFER (Optional)
- **Length**: 8-15 words
- **Style**: Smaller than headline, may use accent color
- **Placement**: Below headline or in offer strip at bottom
- **Examples**: "70% OFF TODAY ONLY", "Rewind the Clock with E27 Liquid Collagen"

### Tier 3: BODY TEXT / BULLETS (Optional — only for text-heavy patterns)
- **Length**: Up to 300 words (Pattern 5: Text-Heavy Card only)
- **Style**: Regular weight, centered, 16-18pt
- **Placement**: Below headline, fill the card

---

## Headline Formulas (From Winning Ads)

### Formula 1: Provocative Statement
> `[PROVOCATIVE CLAIM ABOUT THEIR CURRENT SOLUTION]`
- "YOUR $100 COLOSTRUM IS LITERAL ANIMAL FEED"
- "TIRED OF BEING FAT."
- "WE'RE SAYING GOODBYE"

### Formula 2: "Don't Let X" / Challenge
> `Don't let [obstacle] be the excuse for [their goal]`
- "Don't let age be the excuse for your belly"

### Formula 3: Event + Offer
> `[EVENT] OFFER ENDS [TIMEFRAME]`
- "MEMORIAL OFFER ENDS TODAY"
- "This Black Friday — RejuvaKnee 60% off"

### Formula 4: Problem Hook + Cliffhanger
> `[Problem statement], but did you know... more`
- "Most People with Sleep Apnea don't use this to stop snoring, but did you know... more"
- The "...more" is intentional — mimics FB's truncation to create curiosity

### Formula 5: Apology / Behind-the-Scenes
> `WE OWE YOU AN APOLOGY`
- Works as headline for text-heavy story ads
- Creates curiosity through brand vulnerability

### Formula 6: Mechanism Reveal
> `FIRST-DAY COLOSTRUM IS GOLDEN. [BRAND] IS GOLDEN.`
- Bottom of image, after mechanism explanation
- Concludes the education with brand positioning

---

## Color Rules (From 100 Analyzed Images)

### Background Colors That Win
| Color | Hex | Used By | Best For |
|-------|-----|---------|----------|
| Deep Purple | #2D1B4E | ColonBroom | Premium, health |
| Navy/Indigo | #1E1B4B | Javvy | Story cards, trust |
| Pure Black | #1A1A1A | LuluTox, Mane Strong | Urgency, premium |
| Warm Cream | #F5F0EB | SpoiledChild | Clean, feminine |
| White | #FFFFFF | Derila | Cartoon/illustration |
| Dark Gold Gradient | #1A0E00→#8B6914 | Folqs | Premium comparison |
| Light Gray | #F3F4F6 | Mane Strong | Product + review |

### Text Colors
- **On dark backgrounds**: White (#FFFFFF) for headlines, #E5E5E5 for body
- **On light backgrounds**: Black (#1A1A1A) for headlines, #4A4A4A for body
- **Accent/offer text**: Orange (#FF6B00), Yellow (#FFD700), Red (#FF0000), Brand color

### Offer Strip Colors
- **Red bar + white text**: Most common (Drivse, RejuvaCare)
- **Orange badge**: Mane Strong (70% OFF)
- **Dark background + white text**: LuluTox, ColonBroom

---

## Text Placement Rules

### Rule 1: Text and Product Don't Compete
The headline and product image should occupy different zones. Never overlay text on the product.

### Rule 2: The F-Pattern
Eye tracking: Top-left → across → down-left → across. Place headlines top, supporting text below.

### Rule 3: Bottom Strip = Offer Zone
The bottom 20-25% of the image is where offers, CTAs, and disclaimers live.

### Rule 4: One Message Per Ad
Don't try to communicate benefits AND offer AND social proof in one image. Pick one primary message:
- **Awareness**: Problem statement OR mechanism
- **Consideration**: Social proof OR comparison
- **Conversion**: Offer OR urgency

---

## Text Overlay Technical Specs

### For Gemini-Generated Images
Gemini's text-in-image rendering is unreliable. Always:
1. Generate the image WITHOUT text
2. Composite text using ImageMagick or HTML→screenshot

### ImageMagick Text Overlay Command
```bash
convert input.png \
  -gravity North \
  -font "Montserrat-Bold" \
  -pointsize 72 \
  -fill white \
  -stroke black -strokewidth 2 \
  -annotate +0+40 "HEADLINE TEXT" \
  output.png
```

### HTML→Screenshot Method (More Control)
```html
<div style="position:relative; width:1080px; height:1350px;">
  <img src="generated-image.png" style="width:100%; height:100%; object-fit:cover;">
  <div style="position:absolute; top:40px; left:40px; right:40px;
    font-family:'Montserrat',sans-serif; font-weight:900;
    font-size:64px; color:white; text-shadow:0 2px 8px rgba(0,0,0,0.5);">
    HEADLINE TEXT
  </div>
</div>
```
Then screenshot with Puppeteer: `npx puppeteer screenshot overlay.html --width=1080`

---

## Aspect Ratios

| Ratio | Pixels | Platform | Use Case |
|-------|--------|----------|----------|
| 4:5 | 1080×1350 | FB/IG Feed | Primary format for DTC |
| 1:1 | 1080×1080 | FB/IG Feed | Product hero, comparison |
| 9:16 | 1080×1920 | Stories/Reels | UGC, problem-state, full-screen |
| 16:9 | 1200×628 | FB Link Ads | Rarely used for DTC |

**Default**: 4:5 (1080×1350) — takes maximum feed real estate.

---

## Meta Ad Policy Quick Reference (Supplement Ads)

### Allowed
- "Supports healthy digestion"
- "May help with occasional bloating"
- Star ratings and real customer quotes
- Before/after for hair, skin (with disclosures)
- Lifestyle imagery showing the benefit state

### Not Allowed
- Disease claims ("cures IBS", "treats diabetes")
- Before/after for weight loss (with implied causation)
- Zooming in on body parts in a negative way
- "You" + negative state combo ("You're overweight")
- Fake UI elements that trick users into clicking

### Safe Patterns
- Third-person: "She noticed a difference in 3 weeks"
- Mechanism: "First-day colostrum contains 2x the immunoglobulins"
- Question: "What if your morning routine could support your gut?"
- Social proof: "17,000 moms have tried this"
