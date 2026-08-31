# COPY → DESIGN → PRODUCTION WORKFLOW

> The 5-phase system for producing any DTC ad image.
> Each phase has a defined input, process, and output. Output of one feeds input of the next.

---

## OVERVIEW

```
PHASE 1: COPY ANALYSIS (Titan DR)
User brief → Awareness level + Dominant bias + Hook + Copy text
        ↓
PHASE 2: DESIGN BRIEF (Titan Conversion Designer)
Copy signal → Visual pattern + Color + Layout + Reference images from index
        ↓
PHASE 3: GENERATION (Gemini)
Design brief + Reference images → Generated base ad image (no text)
        ↓
PHASE 4: COMPOSITE (HTML Templates / ImageMagick)
Base image + Copy text → Final ad with headline, offer strip, CTA overlay
        ↓
PHASE 5: QA (Checklist)
Final ad → Verified against Design Brief → Ship
```

---

## PHASE 1 — COPY ANALYSIS

**Load**: Titan DR (`titan-psychology.md` + `titan-language.md` + relevant format file)

**Input**: User's product description, target audience, ad objective

**Process**:
1. Assign Schwartz awareness level (L1–L5)
2. Assign sophistication stage (S1–S5)
3. Identify dominant bias to exploit
4. Select hook type (from 21 hook types in `titan-hook-library.md`)
5. Write hero hook + headline + body copy + CTA text

**Output** (hand to Phase 2):
```
COPY SIGNAL:
- Product: [name]
- Audience: [avatar description]
- Awareness Level: L[N] — [what they know]
- Sophistication Stage: S[N]
- Dominant Bias: [bias name]
- Hook Type: [type from hook library]

COPY TEXT:
- Headline (on-image): [3-8 words, all caps]
- Subhead (optional): [8-15 words]
- Offer text (if applicable): [e.g., "70% OFF TODAY ONLY"]
- CTA button: [text + color suggestion]
- Ad body copy: [full text for the ad body field]
```

---

## PHASE 2 — DESIGN BRIEF

**Load**: `SKILL.md` + `design-psychology.md` + `visual-patterns.md`

**Input**: Copy Signal + Copy Text from Phase 1

**Process**:
1. Map awareness level → layout type (using Quick Mapping table in SKILL.md)
2. Map sophistication stage → design complexity
3. Map dominant bias → color/visual signal
4. Map hook type → image category
5. Select pattern from `visual-patterns.md` that matches all signals
6. **Query `pattern-reference-index.json`** for matching reference images:
   - Filter to selected pattern_id
   - Sort by used_count DESC
   - Prefer brand diversity (different brands in top 2-3)
   - Match product niche if possible
7. Write the full Design Brief

**Output** (hand to Phase 3):
```
DESIGN BRIEF — [Product/Campaign Name]

Copy Signal: [from Phase 1]

Layout:
- Pattern: [Pattern # and name from visual-patterns.md]
- Structure: [e.g., "Full-bleed product hero, text overlay bottom third"]
- Rationale: [1 sentence — why this pattern matches the copy signal]

Color Palette:
- Background: [hex or descriptor]
- Accent/CTA: [hex or descriptor]
- Typography: [light/dark/colored]
- Rationale: [1 sentence — psychology reason]

Visual Hierarchy (top to bottom):
1. [Element] — [size/weight]
2. [Element]
3. [Element]

Face/Person:
- Include: Yes/No
- If yes: [age, gender, emotional state, eye direction]
- Rationale: [conversion reason]

Product Placement: [Hero / Supporting / Absent] — [placement]

CTA Button: [color] — [text] — [placement]

Reference Images (from pattern-reference-index.json):
- [filename1.jpg] — [brand], used_count: [N]
- [filename2.jpg] — [brand], used_count: [N]

Gemini Prompt (ready to execute):
[Full Gemini text prompt — NO text in image, base visual only]
```

---

## PHASE 3 — GENERATION

**Load**: `gemini-image-gen/SKILL.md` + `references/gemini-multimodal.md`

**Input**: Design Brief from Phase 2 (including reference image filenames)

**Process**:
1. Load 2-3 reference images from `~/Downloads/Workforce/ad-library-v5/images/` as base64
2. Write payload to temp file (images are too large for CLI args)
3. Build multimodal Gemini prompt:
   - [TEXT]: "These are examples of high-performing DTC ads using the [PATTERN NAME] pattern:"
   - [IMAGE 1]: First reference image (highest used_count)
   - [IMAGE 2]: Second reference image (different brand if possible)
   - [TEXT]: Full Design Brief with generation instructions
   - [TEXT]: "Generate only the base image. Do NOT render any text, headlines, or words on the image. Text will be added separately."
4. Call Gemini API (`gemini-3.1-flash-image-preview` for speed, `gemini-3-pro-image-preview` for quality)
5. Save generated image to `~/Downloads/Workforce/generated-ads/`

**Output**:
```
~/Downloads/Workforce/generated-ads/[campaign]-base.jpg
```

**Model selection:**
| Quality Need | Model | Cost |
|-------------|-------|------|
| Draft/testing | `gemini-3.1-flash-image-preview` | ~$0.067/image |
| Final production | `gemini-3-pro-image-preview` | ~$0.134/image |

---

## PHASE 4 — COMPOSITE

**Load**: `copy-on-image.md` + appropriate template from `templates/`

**Input**: Base image from Phase 3 + Copy Text from Phase 1

**Process**:

### Method A: HTML Template + Puppeteer (recommended for multi-element overlays)
1. Select template based on the overlay needs:
   - `templates/headline-only.html` — single headline + brand logo
   - `templates/headline-offer.html` — headline + subhead + bottom offer strip
   - `templates/review-quote.html` — star rating + review + product + offer badge
   - `templates/mechanism-callouts.html` — product + 4 callout bubbles
   - `templates/text-card.html` — full text card (no Gemini base needed)
2. Replace template variables with Copy Text values
3. Set `{{BACKGROUND_IMAGE}}` to the Phase 3 output file path
4. Screenshot with Puppeteer: `npx puppeteer screenshot template.html --width=1080 --height=1350`
5. Save as final composite

### Method B: ImageMagick (for simple single-line overlays)
```bash
magick input.png \
  -gravity North \
  -font "Montserrat-Bold" \
  -pointsize 72 \
  -fill white \
  -stroke black -strokewidth 2 \
  -annotate +0+40 "HEADLINE TEXT" \
  output.png
```

### Method C: Gemini Re-pass (fastest, less control)
Send the base image back to Gemini with: "Add text '[HEADLINE]' in white bold at the top of this image."

**Output**:
```
~/Downloads/Workforce/generated-ads/[campaign]-final.png
```

---

## PHASE 5 — QA CHECKLIST

Before marking the ad complete, verify:

- [ ] Design Brief includes ALL elements from the template (no gaps)
- [ ] Pattern selected from `visual-patterns.md` — not invented ad hoc
- [ ] Reference images are the highest used_count examples for that pattern
- [ ] Color decisions traced to a psychological principle (not preference)
- [ ] Face decision justified (if using, eye direction specified)
- [ ] CTA button color creates contrast against background
- [ ] Headline follows `copy-on-image.md` rules (3-8 words, correct tier)
- [ ] Generated image checked against Design Brief before compositing
- [ ] Final composite is 1080×1350 (4:5) or 1080×1080 (1:1) at minimum
- [ ] No text rendered by Gemini that should have been composited
- [ ] Meta ad policy compliance checked (see `copy-on-image.md` policy section)

---

## STANDALONE MODES

Each phase runs independently:

| Mode | Load | Use When |
|------|------|----------|
| Copy analysis only | Titan DR | Writing copy without visual production |
| Design brief only | This skill (Phase 2) | Briefing a human designer |
| Design audit | This skill + `design-psychology.md` | Analyzing why a competitor ad converts |
| Generation only | `gemini-image-gen/SKILL.md` | Already have a design brief |
| Composite only | `copy-on-image.md` + templates | Have a base image, need overlays |

---

## WORKED EXAMPLE

**User brief**: "Create a Facebook ad for Folqs colostrum targeting gut health problem-aware women 35-55"

### Phase 1 Output
```
COPY SIGNAL:
- Product: Folqs Colostrum
- Audience: Women 35-55, gut issues, tried other supplements
- Awareness Level: L3 — Solution-aware
- Sophistication Stage: S3 — Feature-fatigued
- Dominant Bias: Specificity + Authority
- Hook Type: Science/Mechanism (Hook Type 2 from Titan)

COPY TEXT:
- Headline: "WHY 99% OF GUT SUPPLEMENTS FAIL"
- Subhead: "The gut lining problem nobody talks about"
- Offer: "TRY RISK-FREE — 90 DAY GUARANTEE"
- CTA: "See How It Works →" (orange button)
- Body: [full mechanism copy...]
```

### Phase 2 Output
```
DESIGN BRIEF — Folqs Gut Mechanism Ad

Layout:
- Pattern: #12 Educational Diagram
- Structure: Product center, 4 callout bubbles radiating out
- Rationale: L3 + mechanism hook → education converts

Color Palette:
- Background: dark gradient (#1A0E00 → #18193F) — premium authority
- Accent: gold (#C5A13E) — Folqs brand color
- Typography: white on dark
- Rationale: Dark + gold = premium positioning for S3 audience

Reference Images:
- Dr.-Josh-Axe_42d_W_12345678.jpg — Dr. Axe, used_count: 5
- Gundry-MD_38d_W_87654321.jpg — Gundry MD, used_count: 4

Gemini Prompt:
"Create a Facebook ad base image. Dark gradient background (#1A0E00 to #18193F).
Center: glass of golden colostrum powder with warm lighting and glow effect.
Leave clear space at top for headline text and around the product for callout
bubbles. No text. No words. Premium supplement aesthetic. 1080×1350 at 4:5."
```

### Phase 3: Generate with Gemini (2 reference images + prompt)
### Phase 4: Composite using `mechanism-callouts.html` template
### Phase 5: QA against checklist → ship

---

## TROUBLESHOOTING

**Gemini output doesn't match the pattern:**
→ Increase reference images to 3. Reduce text prompt length. Gemini's visual mimicry > text interpretation.

**Pattern doesn't exist in visual-patterns.md:**
→ Build prompt from `design-psychology.md` principles. Flag for addition to pattern library.

**Reference images not found in index:**
→ Check `pattern-reference-index.json`. If pattern has few/no images, use the closest pattern's images as references and describe the difference in the Gemini prompt.

**Text overlay looks wrong:**
→ Switch from Method C (Gemini) to Method A (HTML template). HTML gives pixel-perfect control.

**User wants a landing page section (not an ad):**
→ Switch to `fotw-design-patterns.md` for design reference. Phase 2 process is identical; pattern library differs.

---

## Production Method Routing (Phase 2 Addition)

Before generating, route each ad to the correct production method:

| Category | Patterns | Method |
|----------|----------|--------|
| **A: Gemini Scene** | 2, 9, 15, 19, 20 | Gemini generates scene with actual product photo input |
| **B: HTML Design** | 1, 3, 5, 7, 11, 13, 24, 25, 26 | Full HTML/CSS with real product photos — NO Gemini |
| **C: Real Content Only** | 21, 23 | Requires actual UGC/real photos. Cannot be AI-generated. |

## Quality Gate (Phase 3 Addition)

For Category A (Gemini Scene) ads:
1. Generate **5 variants** (temperature=1.0, parallel)
2. Score each with Gemini Vision (gemini-2.5-flash) on: product accuracy, layout quality, photography quality, scroll-stopping power (1-10 each)
3. Only use variants scoring ≥ 7/10 average
4. If none pass → fall back to Category B (HTML design)
