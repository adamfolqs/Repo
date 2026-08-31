# GEMINI MULTIMODAL — Passing Reference Images to Gemini API

## Mandatory Inputs (NEVER SKIP)

Every Gemini image generation call MUST include:

1. **Actual product photo** — the real product image from the brand's website. This is the source of truth for packaging, colors, and label design. Without this, Gemini will hallucinate the product appearance.
2. **2-3 reference ads** — winning ads from `pattern-reference-index.json` for the target pattern. These teach Gemini the layout/composition style.
3. **"No text" instruction** — always include "DO NOT render any text on the image" in the prompt. Text overlays are added separately via HTML composite.

### Prompt Structure
```
[TEXT]: "This is the actual product — use this EXACT product appearance:"
[IMAGE]: actual_product_photo.png
[TEXT]: "These are high-performing ads using the [PATTERN] layout:"
[IMAGE]: reference_ad_1.jpg
[IMAGE]: reference_ad_2.jpg
[TEXT]: "Create a new Facebook ad that:
- Uses the EXACT product from the first image
- Follows the layout/style of the reference ads
- [Scene/composition instructions]
- DO NOT render any text
- Aspect ratio: [4:5 or 1:1]"
```

---

## The Core Concept

Instead of describing winning ads to Gemini in text, pass the actual images as visual few-shot examples. Gemini sees what the pattern actually looks like and reproduces it for your product.

This is dramatically better than text-only prompts because:
- Text describes. Images show. Gemini's visual understanding is pixel-accurate.
- A 2,000-token text description of a layout is less precise than a 1-second image read.
- You're leveraging the same images that already proved they work (most-copied templates from 84 verified DTC brands).

---

## IMAGE SOURCES (in priority order)

1. **Pattern Reference Index** — `~/Downloads/Workforce/ad-library-v5/pattern-reference-index.json`
   - **Use first.** This index maps visual pattern → ranked image filenames (sorted by `used_count` DESC).
   - Query by pattern_id to get the top 2-3 reference images for any pattern.
   - Images are in `~/Downloads/Workforce/ad-library-v5/images/`
   - Filenames encode performance: `ColonBroom_61d_W_63163974.jpg` = 61 days active, Winning

2. **Full v5 image library** — `~/Downloads/Workforce/ad-library-v5/images/` (6,812 images from 84 verified brands)
   - Metadata: `~/Downloads/Workforce/ad-library-v5/ads_metadata_targeted.json`
   - Searchable by brand, ad_type, used_count, days_active
   - All 30-150 days active, sorted by used_count (most-copied templates)

3. **Re-scrape via GetHookd API** — if more coverage needed
   - API: `https://app.gethookd.ai/api/v1/explore`
   - API key in `~/.config/api-keys/.env` → stored in scraper scripts
   - Brand whitelist: `~/Downloads/Workforce/ad-library-v5/brand-whitelist-final.json` (91 brands)

---

## API CALL PATTERN

### Via curl (recommended — no Python SDK needed)

```bash
# Step 1: Encode reference images
REF1_B64=$(base64 -i ~/Downloads/Workforce/ad-library-v5/images/ColonBroom_61d_W_63163974.jpg)
REF2_B64=$(base64 -i ~/Downloads/Workforce/ad-library-v5/images/Mane-Strong_72d_W_12345678.jpg)

# Step 2: Build payload JSON (save to temp file — base64 is too large for CLI args)
python3 -c "
import json, base64

ref1_b64 = open('/path/to/ref1.jpg', 'rb').read()
ref2_b64 = open('/path/to/ref2.jpg', 'rb').read()

payload = {
    'contents': [{'role': 'user', 'parts': [
        {'text': 'These are examples of high-converting DTC supplement ads from verified brands:'},
        {'inlineData': {'mimeType': 'image/jpeg', 'data': base64.b64encode(ref1_b64).decode()}},
        {'inlineData': {'mimeType': 'image/jpeg', 'data': base64.b64encode(ref2_b64).decode()}},
        {'text': 'Create a new ad image following the same visual pattern for [PRODUCT]. Design brief: [BRIEF]'}
    ]}],
    'generationConfig': {
        'responseModalities': ['IMAGE', 'TEXT'],
        'imageConfig': {'imageSize': '1K'}
    }
}

with open('/tmp/gemini_payload.json', 'w') as f:
    json.dump(payload, f)
"

# Step 3: Call API
curl -s 'https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-flash-image-preview:generateContent?key=$GEMINI_API_KEY' \
  -H 'Content-Type: application/json' \
  -d @/tmp/gemini_payload.json \
  -o /tmp/gemini_response.json

# Step 4: Extract image
python3 -c "
import json, base64
with open('/tmp/gemini_response.json') as f:
    data = json.load(f)
for part in data['candidates'][0]['content']['parts']:
    if 'inlineData' in part:
        ext = part['inlineData']['mimeType'].split('/')[-1]
        with open(f'output.{ext}', 'wb') as out:
            out.write(base64.b64decode(part['inlineData']['data']))
        print(f'Saved: output.{ext}')
"
```

---

## HOW TO SELECT REFERENCE IMAGES

1. **Use the Pattern Reference Index**: After Phase 2 produces the Design Brief with a pattern name, read `pattern-reference-index.json` → filter to that pattern_id → get the top images sorted by `used_count`.

2. **Prefer brand diversity**: Among the top images, pick from DIFFERENT brands when possible. This gives Gemini a more generalized understanding of the pattern.

3. **Match by product category**: If available, prefer reference images from the same product category (gut health → gut health ads, hair → hair ads). The visual context transfers better.

4. **Limit to 2-3 images**: More than 3 reference images adds token cost without improving output. 2 is usually optimal.

---

## PROMPT STRUCTURE (RECOMMENDED)

```
[TEXT]: "These are examples of high-performing DTC ads using the [PATTERN NAME] visual pattern:"
[IMAGE 1] (highest used_count for this pattern)
[IMAGE 2] (second example, different brand)
[TEXT]: "Create a new ad image for [PRODUCT]. Design brief: [FULL DESIGN BRIEF FROM PHASE 2]"
[TEXT]: "Match the visual pattern (layout, color approach, hierarchy) of the examples. Do not copy any brand, logo, or specific product imagery. Generate only the base image — text overlays will be added separately."
```

**Important**: Always tell Gemini NOT to render text on the image. Text overlays are composited in Phase 4 using HTML/Puppeteer or ImageMagick (see `copy-on-image.md`).

---

## MODELS

| Task | Model | Why |
|------|-------|-----|
| Image generation | `gemini-3.1-flash-image-preview` | Best for visual generation, cheapest |
| Image generation (high quality) | `gemini-3-pro-image-preview` | 2x cost, better detail |
| Vision/classification | `gemini-2.5-flash` | For analyzing/classifying existing images (note: uses thought tokens, set maxOutputTokens >= 1024) |

---

## ENVIRONMENT

- Gemini API key: `~/.config/api-keys/.env` → `GEMINI_API_KEY`
- Existing Gemini skill: `~/.memory/skills/design/gemini-image-gen/SKILL.md` — load for full production workflow
- Pattern reference index: `~/Downloads/Workforce/ad-library-v5/pattern-reference-index.json`
- v5 image library: `~/Downloads/Workforce/ad-library-v5/images/` (6,812 images)
