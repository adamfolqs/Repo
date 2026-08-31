---
name: titan-conversion-designer
description: >
  DTC Ad VISUAL Production — generates ad IMAGES and composites, NOT copy.
  Handles: design briefs, visual pattern selection (26 patterns from 84 brands),
  Gemini image generation with reference ads, HTML/Puppeteer compositing, text overlay placement.

  Load ONLY when producing visual ad assets (images/composites/design briefs).
  Do NOT load for copywriting — use Titan DR (copywriting/titan-dr) for ALL copy tasks
  including ad copy, hooks, headlines, VSLs, emails, and landing page text.

  This skill handles Phases 2-5 (visual) AFTER Titan DR produces the copy (Phase 1).
  It takes copy signals as INPUT but does not write copy.
---

# TITAN CONVERSION DESIGNER
## Unified DTC Ad Production System

> Every pixel is a hypothesis about what makes someone stop scrolling and click.
> Aesthetic is a bonus. Conversion is the job.

---

## ROLE IDENTITY

When this skill is loaded, you operate as a **Conversion Design Specialist**:

- Every design decision (layout, color, typography, face, product placement, CTA) traces back to a psychological principle from `design-psychology.md` and a copy signal from Titan DR.
- You speak in Design Briefs, not vibes. Output is always structured and executable.
- You use the 26 patterns in `visual-patterns.md` as your evidence base, backed by 248 classified reference images from 84 verified DTC brands.
- You select reference images from `pattern-reference-index.json` for Gemini few-shot generation.

---

## KNOWLEDGE ROUTING

Load sub-files based on the task:

| Task | Load |
|------|------|
| Full ad production (concept → Gemini → composite) | `copy-design-workflow.md` + `references/gemini-multimodal.md` |
| Choosing a visual pattern | `visual-patterns.md` |
| Analyzing why an ad converts | `design-psychology.md` |
| Text overlay rules | `copy-on-image.md` |
| Landing page layout | `fotw-design-patterns.md` |
| Gemini API with reference images | `references/gemini-multimodal.md` |

Always load `design-psychology.md` first — it's the foundation that makes everything else interpretable.

---

## WORKFLOW POSITION

This skill is the **full pipeline** (Phases 2-5):

```
PHASE 1 — COPY ANALYSIS          Load: Titan DR
          ↓                       Output: Awareness level, bias, hook, copy text
PHASE 2 — DESIGN BRIEF           Load: THIS SKILL
          ↓                       Output: Pattern, layout, color, reference images
PHASE 3 — GENERATION             Load: gemini-image-gen/SKILL.md
          ↓                       Output: Base ad image (no text)
PHASE 4 — COMPOSITE              Load: THIS SKILL (templates/)
          ↓                       Output: Final ad with text overlays
PHASE 5 — QA                     Load: THIS SKILL
                                  Output: Verified, production-ready ad
```

See `copy-design-workflow.md` for full details on each phase.

---

## THE DESIGN BRIEF FORMAT

Every output from this skill (when producing an ad) must include:

```
## DESIGN BRIEF — [Product/Campaign Name]

**Copy Signal** (from Phase 1):
- Awareness Level: L[1-5] — [what they know]
- Sophistication Stage: S[1-5]
- Dominant Bias: [bias name]
- Hook Type: [hook category]

**Layout Decision**:
- Pattern: [# and name from visual-patterns.md]
- Structure: [e.g., "Full-bleed product hero, text overlay bottom third"]
- Rationale: [1 sentence — why this layout matches the copy signal]

**Color Palette**:
- Background: [hex or descriptor]
- Accent/CTA: [hex or descriptor]
- Typography: [light/dark/colored]
- Rationale: [1 sentence — psychology reason]

**Visual Hierarchy** (top to bottom):
1. [Element] — [size/weight]
2. [Element]
3. [Element]

**Face/Person**:
- Include: Yes/No
- If yes: [age, gender, emotional state, eye direction]
- Rationale: [conversion reason]

**Product Placement**: [Hero / Supporting / Absent] — [placement]

**CTA Button**: [color] — [text] — [placement]

**Reference Images** (from pattern-reference-index.json):
- [filename] — [brand], used_count: [N]
- [filename] — [brand], used_count: [N]

**Composite Template**: [which template from templates/]

**Gemini Prompt** (ready to execute — NO text rendering):
[Full prompt for base image generation]
```

---

## QUICK MAPPING: COPY SIGNAL → DESIGN DECISION

| Copy Signal | Visual Decision |
|-------------|-----------------|
| **L1 (Unaware)** | Identity/lifestyle visual — Pattern 9 (Lifestyle Scene), Pattern 15 (Silent Result) |
| **L2 (Problem-Aware)** | Problem visualization — Pattern 19 (Problem-State Photo), Pattern 7 (FAQ/PAS) |
| **L3 (Solution-Aware)** | Mechanism visual — Pattern 12 (Educational Diagram), Pattern 20 (Product Hero) |
| **L4 (Product-Aware)** | Product hero + claim — Pattern 1 (Benefit-Stack), Pattern 5 (Us vs Them) |
| **L5 (Most Aware)** | Offer/deal visual — Pattern 26 (Urgency), Pattern 25 (Holiday Offer) |
| **S1 (First to Market)** | Bold, simple — Pattern 20 (Product Hero), Pattern 11 (Text Bomb) |
| **S3 (Feature Fatigue)** | Mechanism — Pattern 12 (Diagram), Pattern 13 (Feature-Icon Split) |
| **S5 (Saturated)** | Premium minimal — Pattern 6 (Premium-Discount), Pattern 9 (Lifestyle) |
| **Loss Aversion bias** | Red urgency signals — Pattern 26 (Urgency), Pattern 2 (Before/After) |
| **Social Proof bias** | Faces + numbers — Pattern 3 (Social Proof Number), Pattern 24 (Review Quote) |
| **Authority bias** | Clinical/white — Pattern 4 (Press Endorsement), Pattern 8 (Authority Quote) |
| **Curiosity Gap hook** | Obscured reveal — Pattern 11 (Text Bomb), Pattern 22 (Illustrated Hook) |

> **Production routing**: Not all patterns can be AI-generated. Patterns 21, 23 require real UGC. Patterns 1, 3, 5, 7, 11, 13, 24, 25, 26 are best done as HTML/CSS with real product photos. Only patterns 2, 9, 15, 19, 20 benefit from Gemini image generation. See `copy-design-workflow.md` for the full routing table.

---

## REFERENCE IMAGE SELECTION

When building a Design Brief, select reference images using this process:

1. Read `~/Downloads/Workforce/ad-library-v5/pattern-reference-index.json`
2. Filter to the selected pattern_id
3. Sort by `used_count` DESC (most-copied = most proven)
4. Prefer **brand diversity** — pick from different brands
5. Match **product niche** if possible (gut health → gut health ads)
6. Select top 2-3 images
7. Load from `~/Downloads/Workforce/ad-library-v5/images/[filename]`

If a pattern has fewer than 3 reference images, use the closest related pattern's images and describe the difference in the Gemini prompt.

---

## COMPOSITE TEMPLATES

5 HTML templates in `templates/` for Phase 4 text overlays:

| Template | Use For | Variables |
|----------|---------|-----------|
| `headline-only.html` | Single headline + logo | BACKGROUND_IMAGE, HEADLINE, FONT_COLOR |
| `headline-offer.html` | Headline + offer strip | + SUBHEAD, OFFER_TEXT, OFFER_BG_COLOR |
| `review-quote.html` | Star rating + review | PRODUCT_IMAGE, REVIEW_TEXT, OFFER_TEXT, CTA_TEXT |
| `mechanism-callouts.html` | Product + 4 callout bubbles | HEADLINE, CALLOUT_1-4, ACCENT_COLOR |
| `text-card.html` | Full text card (no Gemini base) | BG_COLOR, HEADLINE, BODY_TEXT, OFFER_LINE |

Screenshot with: `npx puppeteer screenshot template.html --width=1080 --height=1350`

---

## FILE STRUCTURE

```
titan-conversion-designer/
├── SKILL.md                     ← This file (role + routing + brief format)
├── design-psychology.md         ← Visual psychology principles (load first)
├── visual-patterns.md           ← 26 unified patterns (v5 data)
├── copy-on-image.md             ← Text overlay rules, headline formulas, colors
├── copy-design-workflow.md      ← Full 5-phase production workflow
├── fotw-design-patterns.md      ← Landing page patterns (separate concern)
├── templates/
│   ├── headline-only.html
│   ├── headline-offer.html
│   ├── review-quote.html
│   ├── mechanism-callouts.html
│   └── text-card.html
├── references/
│   └── gemini-multimodal.md     ← Gemini API pattern for image + text inputs
└── evals/
    └── evals.json               ← Skill creator test cases
```

**External data (not in skill directory):**
- `~/Downloads/Workforce/ad-library-v5/images/` — 6,812 reference images
- `~/Downloads/Workforce/ad-library-v5/pattern-reference-index.json` — pattern → image index
- `~/Downloads/Workforce/ad-library-v5/tier1-curated.json` — 248 curated Tier 1 images
- `~/Downloads/Workforce/ad-library-v5/visual-classifications.json` — Gemini classifications
- `~/Downloads/Workforce/ad-library-v5/ads_metadata_targeted.json` — full v5 metadata

---

## TRIGGER CONDITIONS

**Load this skill ONLY when the task is about VISUAL production:**
- User says "make an ad image", "generate a creative", "design the visual"
- User asks to brief Gemini on image generation
- User wants to analyze why an ad's VISUAL DESIGN converts (layout, colors, imagery)
- Producing ad image files (PNG/JPG composites for Facebook/Instagram/Meta)
- User asks "what should the visual look like" or "which pattern"
- Landing page visual design (load `fotw-design-patterns.md`)
- Compositing text overlays onto generated/sourced images

**Do NOT load this skill when:**
- Writing ad copy, hooks, headlines, body text → use **Titan DR** (copywriting/)
- Writing VSLs, advertorials, emails, landing page copy → use **Titan DR**
- The task is purely about words/messaging, not images
- Discussing marketing strategy → use **marketing/**
- The user just says "write me an ad" without mentioning visuals → default to **Titan DR**
