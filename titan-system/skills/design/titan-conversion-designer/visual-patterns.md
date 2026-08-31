# VISUAL PATTERNS — 26 DTC Ad Creative Patterns

> **Source:** 248 curated Tier 1 ads from 84 verified DTC brands (v5, March 2026)
> **Classification:** Gemini Vision auto-classified by visual layout pattern
> **Reference images:** `~/Downloads/Workforce/ad-library-v5/pattern-reference-index.json`
> **Supersedes:** titan-visual-patterns.md (v4, 18 patterns) + titan-ads/creative-patterns.md (15 patterns)

---

## HOW TO USE THIS LIBRARY

1. Look up your **Copy Signal** from Phase 1 (awareness level, dominant bias, hook type)
2. Match to the **Quick Mapping table** in `SKILL.md` to narrow to 2–3 candidate patterns
3. Read the full pattern entry below to confirm fit (psychology, niche, "when NOT to use")
4. Query `pattern-reference-index.json` for the top 2-3 reference images (sorted by used_count)
5. Use the **Gemini prompt template** as starting point for Phase 3 generation

---

## THE 26 PATTERNS

---

### Pattern 1: Benefit-Stack + Price Strike

**What it looks like:**
Left column: 3–5 benefit bullets with icons/emojis replacing standard bullets. Right: model holding product (face optional, looking slightly away). Below benefits: crossed-out original price → lower price with "JUST $X" framing.

**Color palette:** Warm/lifestyle — cream, beige, soft whites. Product/model natural tones. CTA accent in orange or brand color.

**Face/Person:** Yes — holding product, slight smile, looking slightly away from camera (aspirational, not salesy)

**Typography:** Benefit bullets at medium weight, price strike with color contrast (red/green on crossed-out price)

**Psychology:** Combines rational (benefits = value justification) with emotional (face = trust) and price anchoring in one frame. The strikethrough price creates loss aversion — "saving" money you already feel entitled to.

**When to use:** L3–L4 awareness. Customer knows the problem and the product category. Strong for mid-funnel and retargeting.

**When NOT to use:** Cold audiences (L1–L2) who don't know the category. Doesn't work without context.

**Gemini prompt template:**
"Facebook ad for [PRODUCT]. Warm lifestyle background (cream/beige). Left: benefit bullet list with [✓ / ✅ / icon] bullets — 4 short benefit lines addressing [PAIN POINTS]. Right: [woman/man] holding product, slight smile, looking slightly away. Below: crossed-out price [$X] → 'JUST $Y' in green. Brand name bottom. 1080×1080. Lifestyle photography style, soft natural light. NO TEXT — text will be composited separately."

---

### Pattern 2: Before/After

**What it looks like:**
Two photos side by side. Left = undesired state (before). Right = desired state (after). Close-up of face, smile, body area, or hair — whichever shows the result most dramatically. Minimal overlay — brand logo only.

**Color palette:** Neutral/clinical — natural skin tones, no heavy filtering. Plain or gradient background. Let the result speak.

**Face/Person:** Yes — the faces ARE the ad. Before face: neutral/unhappy expression. After face: open smile, confident.

**Typography:** Brand logo only. Zero copy on image. All persuasion is visual.

**Psychology:** Mirror neurons + transformation desire. The viewer mentally inserts themselves into the before (identification) and the after (aspiration). No copy needed to convey the entire message.

**When to use:** Any awareness level. Works cold because the before state triggers instant problem recognition. Priority format for any product with a visible physical transformation.

**When NOT to use:** Products without a visible result. Don't use if the transformation isn't dramatic.

**Compliance:** Meta restricts B/A for weight loss. Hair/skin is generally safe. No misleading edits. Include timeframe ("After 8 weeks") for believability.

**Gemini prompt template:**
"Facebook ad split layout. Left panel: [BEFORE state — e.g., 'thinning hair', 'rough skin'] — neutral/slightly unhappy expression. Right panel: [AFTER state — e.g., 'thick hair', 'smooth glowing skin'] — confident open smile. Both panels: close-up [face/hair/body area], natural light, realistic photography. Center: [BRAND] logo in [COLOR]. No other text. 1080×1080. Believable transformation, not stock photo."

---

### Pattern 3: Social Proof Number

**What it looks like:**
A large, specific number as the headline: "20,000+ Happy Customers," "150,000 professionals." Paired with a short emotional outcome statement or the product in a clean setting.

**Color palette:** Clean/clinical white or brand color with high contrast on the number. Number in bold typography, larger than any other element.

**Face/Person:** Optional — some versions feature a customer face, others are pure text + product.

**Typography:** Number is the visual anchor — largest element. Specific numbers feel more credible: "23,417 customers" beats "20,000+ customers."

**Psychology:** Social proof + herd instinct. Specific numbers feel audited, not inflated. If 150,000 people use it, it must work.

**When to use:** L3+ awareness. Best when trust is the primary barrier.

**When NOT to use:** Early-stage brands without real numbers. Don't fabricate. Don't use round numbers.

**Gemini prompt template:**
"Facebook ad. Clean white background. Center: bold statement '[NUMBER]+ [CATEGORY] trust [BRAND/PRODUCT]' in dark navy, large weight. Below: [2-line outcome statement]. Bottom: product image (small, supporting). Brand name and logo. 1080×1080. Clean, authoritative."

---

### Pattern 4: Press/Media Endorsement

**What it looks like:**
Product photographed in a clean, aspirational setting (warm beige, marble, soft whites). A recognized media logo overlaid — "As seen in," "Featured in," or logo only.

**Color palette:** Clean/premium — warm beige, natural light, marble, editorial white. The media logo is the only strong visual element beyond the product.

**Face/Person:** No — the product and media logo do all the work.

**Psychology:** Authority transfer. The media brand's credibility attaches to the product instantly. Critical evaluation is suppressed.

**When to use:** L2–L3 awareness. Any brand with press mentions. Most effective for new or unconventional products.

**When NOT to use:** If the press mention is minor/obscure. Never fabricate. Only works with publications the target audience recognizes.

**Gemini prompt template:**
"Facebook ad. Premium editorial style. Warm beige/cream background with soft natural light. Center: [PRODUCT] on [marble/wood/linen]. Top-left: '[MEDIA LOGO]' in black, editorial weight. Brand logo bottom-right. 1080×1080. Magazine editorial photography, no harsh shadows. NO TEXT beyond logos."

---

### Pattern 5: Us vs Them / Comparison

**What it looks like:**
Two products shown side by side. Below: parallel bullet columns — left lists YOUR product's benefits (checkmarks), right lists competitor problems (X marks). Never names the competitor. Clinical trust colors.

**Color palette:** Bright clinical blue or clean white. High contrast. Conveys authority and objectivity.

**Face/Person:** No — all content, no emotional appeal. The logic IS the ad.

**Typography:** Bullet lists, clean sans-serif. Checkmarks or X's to encode positive/negative quickly.

**Psychology:** Comparative framing without legal risk. The reader infers superiority while the brand maintains deniability. The competitor's negatives must be genuinely painful and real.

**When to use:** L3–L4 awareness. Customer knows the competitor solution exists. Medical, dental, supplement categories.

**When NOT to use:** Never name the competitor directly. Don't use if your differentiators aren't genuinely credible.

**Gemini prompt template:**
"Facebook ad. Bright clinical blue (#1E90FF) background. Top: two product images side by side — [YOUR PRODUCT] left, [GENERIC COMPETITOR TYPE] right. Below: parallel comparison columns. Brand name bottom. 1080×1080. Clinical, objective. NO TEXT — comparison text composited separately."

---

### Pattern 6: Premium-Discount Tension

**What it looks like:**
Premium visual language (gold accents, luxury materials, textured backgrounds, heritage brand logo) combined with a bold discount offer. The design looks expensive — but the offer is accessible.

**Color palette:** Warm premium — tan, gold, dark brown, burgundy. Textured backgrounds. Gold typography on dark for headline. Red or orange for discount callout.

**Face/Person:** No — product focus. The product IS the aspiration.

**Psychology:** Status acquisition at reduced risk. The buyer gets to feel premium while paying promotional prices. Activates both aspiration AND deal-seeking simultaneously.

**When to use:** L3–L5 awareness. Mid-funnel and retargeting. Strong for fashion, apparel, accessories, premium DTC.

**When NOT to use:** Health/supplement brands where premium-discount tension undermines clinical credibility. Low-AOV products where "50% off" is $3.

**Gemini prompt template:**
"Facebook ad. Premium/luxury aesthetic. Dark warm background (deep brown/charcoal) with subtle leather or fabric texture. Center: [PRODUCT] in premium packaging. Brand logo in gold top-center. No faces. 1080×1080. Looks like a high-end brand. NO TEXT — offer overlay composited separately."

---

### Pattern 7: FAQ / PAS Text Format

**What it looks like:**
Heavy text ad: attention-grabbing emoji → problem identification in "if you've ever..." format → bullet list of pain points → solution reveal and product mention. Often 100–200 words.

**Color palette:** Clean white background with colored accent elements, OR bold patterned background.

**Face/Person:** Optional. Some use a small product image in corner. Often purely text.

**Typography:** Mixed weight — emoji as visual bullets, bold for pain points, lighter for transitions.

**Psychology:** Empathy-first selling. The problem list makes the reader feel deeply understood before any product is mentioned. By the time the solution appears, the reader is emotionally invested.

**When to use:** L2–L3 awareness. Products solving niche professional or lifestyle problems.

**When NOT to use:** L4–L5 audiences. They don't need education — they need proof.

**Production Notes:** Text-heavy — best produced via `text-card.html` template or ImageMagick, not Gemini generation.

---

### Pattern 8: Celebrity/Authority Quote

**What it looks like:**
Solid warm background (orange, terracotta, deep red). Left: pull-quote + celebrity name. Right: celebrity smiling directly at camera, holding product. Brand logo bottom.

**Color palette:** Warm bold — orange (#E8631A), terracotta, deep red. Creates energy and warmth.

**Face/Person:** Yes — direct camera gaze, genuine smile. The face IS the trust signal.

**Psychology:** Credibility transfer + parasocial intimacy. Direct camera gaze creates the feeling of personal recommendation. Warm background feels human, not corporate.

**When to use:** L2–L4 awareness. Most effective when the authority figure is aspirational to the target demographic.

**When NOT to use:** Without a genuinely recognizable or credible person. Generic stock "spokesperson" is worse than no face.

**Gemini prompt template:**
"Facebook ad. Solid warm orange (#E8631A) background. Left 40%: space for pull-quote text. Right 60%: [celebrity/person] in natural clothing, smiling directly at camera, holding [PRODUCT]. Brand logo bottom-left. 1080×1080. Magazine editorial lighting, genuine expression. NO TEXT — quote composited separately."

---

### Pattern 9: Lifestyle Scene

**What it looks like:**
High-quality lifestyle photo — bedroom, kitchen, outdoor space. Zero text overlay. Product either absent or deeply integrated into the scene (used, not displayed).

**Color palette:** Aspirational — Scandinavian neutrals, warm home colors, natural outdoor light. Curated but not over-styled.

**Face/Person:** Optional — often no face, or face turned/not prominent. The SCENE is the star.

**Typography:** None on image. All copy in the Facebook post text.

**Psychology:** Aspirational identity projection. The viewer sees a lifestyle they want. Triggers "I want to feel like this" rather than "I want to buy this."

**When to use:** L1–L2 awareness. Brand-building, awareness campaigns.

**When NOT to use:** Direct response campaigns needing immediate ROAS.

**Gemini prompt template:**
"Lifestyle photography. [SCENE: e.g., 'Scandinavian bedroom with soft morning light, unmade bed with white linen']. [PRODUCT] integrated naturally — not featured, just present. No text overlay. No brand logo. Aspirational but lived-in. Warm natural light. 1080×1080."

---

### Pattern 10: Abundance Flatlay

**What it looks like:**
Top-down or angled flatlay showing many SKUs — 10 to 30+ products on a bold solid-color background. No faces, no text.

**Color palette:** Bold background to maximize product pop — vivid yellow, clean white, rich navy.

**Face/Person:** No.

**Psychology:** Variety = legitimacy and scale. 20+ products = established brand impression. Triggers choice-driven engagement.

**When to use:** L3–L4 awareness. Catalog ads, warm audiences. Strong for food/supplement brands with many SKUs.

**When NOT to use:** Single-product brands.

**Gemini prompt template:**
"Product flatlay photography. [NUMBER] [PRODUCT TYPE] spread across a [BACKGROUND COLOR] background. Loose organic arrangement — not a grid. Products face-up showing labels. No text overlay. Clean studio lighting. 1080×1080."

---

### Pattern 11: Text Bomb / Pattern Interrupt

**What it looks like:**
100% text — no photo, no product. Maximum contrast background (solid red, black, electric blue). Bold all-caps text filling the entire frame. Often includes "..." ellipsis for open loop.

**Color palette:** Maximum contrast pairs: Red + yellow text. Black + white text.

**Face/Person:** None — the text is the image.

**Psychology:** Pure curiosity gap + pattern interrupt. In a feed full of photography, solid color block with giant text is a genuine scroll-stopper. Ellipsis creates open cognitive loop.

**When to use:** L2–L3 awareness for info products, coaching, B2B, finance.

**When NOT to use:** Physical consumer goods where the product is a visual selling point.

**Production Notes:** Create via `text-card.html` template — NOT Gemini (text rendering unreliable).

---

### Pattern 12: Educational Diagram

**What it looks like:**
Clean white/light background. Illustrated diagram showing technique, process, or anatomy with labeled arrows. Minimal text — labels only. A branded technique name (e.g., "The Scoop and Swoop Method").

**Color palette:** Clean white background. 2–3 brand accent colors. Clinical but approachable.

**Face/Person:** No — or illustrated only.

**Psychology:** Competence trigger + reciprocity. Learning creates debt-of-reciprocity toward the brand. One insight per ad.

**When to use:** L2–L3 awareness. Products where education = conversion — lingerie, medical devices, supplements with mechanism claims.

**When NOT to use:** Simple products needing no explanation.

**Gemini prompt template:**
"Educational diagram. White background. Title: '[TECHNIQUE NAME]' in [BRAND COLOR]. Center: clean line-art illustration of [ANATOMY/PRODUCT/PROCESS] with directional arrows. Short text labels at each arrow (3–5 words max). Brand name bottom-right. No photography. 1080×1080. Medical/educational infographic style."

---

### Pattern 13: Feature-Icon + Lifestyle Split

**What it looks like:**
50/50 split. LEFT: brand-color panel with product + 3 feature icons. RIGHT: lifestyle model using product, not looking at camera (aspirational).

**Color palette:** LEFT: strong brand color (deep purple, navy, forest green). RIGHT: neutral grey or lifestyle tones.

**Face/Person:** Yes on right side — NOT looking at camera. Looking upward = aspirational.

**Psychology:** Dual-processing. LEFT satisfies rational evaluation (features). RIGHT satisfies emotional desire (identity). Model looking away creates aspiration, not pressure.

**When to use:** L3–L4 awareness. Products with clear, differentiating features.

**When NOT to use:** Commodity products without real feature differentiators.

**Gemini prompt template:**
"Facebook ad split layout. LEFT 50%: solid [BRAND COLOR] background. Top: [PRODUCT] image. Middle: 3 feature bullets with line-art icons. Bottom: [PRODUCT NAME] in white bold. RIGHT 50%: [person] using product, NOT looking at camera. Natural light. 1080×1080."

---

### Pattern 14: Personalization Trigger

**What it looks like:**
Main product image (top 60%). Below: 4–6 variant thumbnails (breeds, colors, names). Callout badges: "NAME AND BREED CAN BE CHANGED."

**Color palette:** Warm/home — natural materials (wood, brick). Organic, not corporate.

**Face/Person:** Illustrated faces (pet illustrations) or no face.

**Psychology:** Customization = psychological ownership. Seeing their specific variant, buyers begin owning the product mentally before purchase.

**When to use:** L3–L5 awareness. Pet/parent audiences. Q4/gifting especially.

**Gemini prompt template:**
"Facebook ad for personalized [PRODUCT]. TOP 60%: product mockup in [HOME SETTING] showing [CUSTOMIZED VERSION]. Callout badge: '[CUSTOMIZATION CLAIM]'. BOTTOM 40%: 4–6 thumbnails showing variant options. Warm natural light. 1080×1080."

---

### Pattern 15: Silent Result Showcase

**What it looks like:**
Model photographed from behind or side. Physical result IS the ad — hair, skin, body. Zero text. Natural outdoor or warm studio light.

**Color palette:** Natural/organic — outdoor sun, warm studio. No heavy lighting. Naturalness = real.

**Face/Person:** Yes — but turned away. Anonymity = "I could be her."

**Psychology:** Aspirational mirror without intimidation. The back/side view lets the viewer project themselves. Result must be dramatic.

**When to use:** L1–L3 awareness. Cold audience hook for beauty/hair/body products.

**When NOT to use:** Subtle results. Products without visible outcomes.

**Gemini prompt template:**
"Product result photography. Model from [behind/side], face not visible. Subject: [DESIRED RESULT — e.g., 'long healthy curls reaching mid-back']. Outdoor natural light. No text. No product visible — the result is the product. 1080×1080. Authentic."

---

### Pattern 16: Institutional Association

**What it looks like:**
Photo of recognizable institution, company building, or prestigious environment. Brand logo subtly present. No explicit claim — association is visual and implied.

**Color palette:** Natural/documentary — real-world photography, natural light.

**Face/Person:** No — the building/institution IS the authority signal.

**Psychology:** Authority transfer at lowest legal risk. The viewer's brain draws the connection without the brand stating it.

**When to use:** L2–L3 awareness. B2B-adjacent products. Any category where third-party validation converts.

**When NOT to use:** Without a genuine connection to the institution.

**Gemini prompt template:**
"Documentary-style photography. [INSTITUTION/BUILDING]. [BRAND LOGO] visible on [a sign/banner] in the scene. No product. Natural, journalistic style — looks like a real news photo. 1080×1080."

---

### Pattern 17: Color-Variety Luxury Spread

**What it looks like:**
Product in every available colorway, arranged in fan/radial pattern. Premium surface (marble, stone). One hand partially visible for scale.

**Color palette:** Jewel tones (silver, lavender, burgundy, navy) against marble/stone. Color variety IS the spectacle.

**Face/Person:** Partial — hand only for scale.

**Psychology:** Paradox of choice (positive version). More options = more reasons to buy. Luxury surface elevates perceived quality.

**When to use:** L3–L4 awareness. Catalog ads, retargeting, beauty/lifestyle buyers.

**Gemini prompt template:**
"Product photography. [PRODUCT] in [6–8] colorways, arranged in [fan/arc] pattern on [white marble] surface. One human hand touching nearest product. No text. Luxury editorial lighting. 1080×1080."

---

### Pattern 18: Free Lead Magnet

**What it looks like:**
Physical book/report cover on clean background. Bold "FREE EBOOK" badge. "Download Now!" CTA. Botanical imagery for health, professional setting for B2B.

**Color palette:** Natural/trustworthy — soft green, cream, botanical for health. Professional grey/white for B2B.

**Face/Person:** Author face optional on book cover (authority signal).

**Psychology:** Reciprocity + low commitment barrier. Free content starts the reciprocity loop. Physical book cover gives tangible perceived value.

**When to use:** L1–L3 awareness. List-building, top-of-funnel.

**When NOT to use:** Direct-purchase campaigns. A lead magnet trains the audience to receive, not buy.

**Gemini prompt template:**
"Facebook ad for free content. [BOTANICAL/PROFESSIONAL] background. Center: physical book design with title '[GUIDE TITLE]' by [AUTHOR/BRAND]. Starburst badge: 'FREE EBOOK!' in white on [BRAND COLOR]. Below: 'Download Now!'. 1080×1080. Approachable, trustworthy."

---

### Pattern 19: Problem-State Photo

**What it looks like:**
Close-up photo of person experiencing the problem — pain, discomfort, frustration. Raw, emotional, real. No product visible. The problem IS the image.

**Color palette:** Natural, muted. No heavy filtering. Authentic lighting (50mm lens, shallow DOF, natural light).

**Face/Person:** Yes — face expressing the problem. Not overacted — subtle emotional authenticity.

**Typography:** None or minimal on image. Ad body copy carries the entire message.

**Psychology:** "I feel seen" moment. The viewer recognizes their own pain in the image, creating instant identification before any product is introduced.

**When to use:** L1–L2 awareness. Top-of-funnel scroll-stopping. Any product with a relatable physical/emotional problem state.

**When NOT to use:** Products without a relatable problem visual. Don't use if the problem isn't immediately recognizable.

**Production Notes:** Gemini excels at photorealistic problem-state images. Annotations (dashed circles, arrows) added via ImageMagick after generation.

**Gemini prompt template:**
"Close-up portrait photography. [Person] experiencing [PROBLEM — e.g., 'looking at thinning hair in mirror', 'holding stomach in discomfort']. Natural light, 50mm lens, shallow depth of field. Raw, emotional, authentic. No product. No text. 1080×1350 (4:5). Photojournalistic style."

---

### Pattern 20: Product Hero + Bold Claim

**What it looks like:**
Product front-and-center on solid/gradient background. Large bold headline text (3-8 words). Product IS the ad.

**Color palette:** Solid color (#F5F0EB cream, #2D1B4E purple, #1A1A1A dark) or subtle gradient. Background matches brand identity.

**Face/Person:** No — product only.

**Typography:** Bold sans-serif headline (Impact, Montserrat Black). One message — don't dilute.

**Psychology:** Visual simplicity = clarity of proposition. The product becomes the anchor for the claim. Works because it cuts through the noise of complex creatives.

**When to use:** L3–L4 awareness. Product launches, brand recall, single-benefit messaging.

**When NOT to use:** Products that need explanation. Multi-benefit messaging.

**Gemini prompt template:**
"Facebook ad. [SOLID COLOR/GRADIENT] background. Center: [PRODUCT] with shadow for depth, large and prominent. Space at top for headline text. Brand logo bottom. 1080×1350 (4:5). Clean studio lighting. NO TEXT — headline composited separately."

---

### Pattern 21: UGC Selfie + Product

**What it looks like:**
Real person holding/showing product in selfie angle, home environment. UGC aesthetic — no professional styling. Messy background, natural light, non-professional pose.

**Color palette:** Uncontrolled — real home environment. Authenticity markers: natural light, non-studio setting.

**Face/Person:** Yes — smiling, direct camera. The person IS the endorsement.

**Typography:** None on image — pure UGC aesthetic. All copy in ad body.

**Psychology:** Peer endorsement > brand endorsement. The UGC aesthetic bypasses ad-blindness because it looks like a friend's post, not a brand's ad.

**When to use:** Mid-funnel trust building, retargeting, social proof. Any awareness level.

**When NOT to use:** Premium/luxury positioning where UGC undermines brand perception.

**Production Notes:** Cannot be reliably generated by AI — requires real UGC or licensed stock. Gemini can create UGC-style photos but they read as "stock" at close inspection.

---

### Pattern 22: Illustrated/Cartoon Hook

**What it looks like:**
Cartoon or illustration depicting the problem humorously. Bold text hook above or below. "...more" truncation creates curiosity gap.

**Color palette:** Flat color, thick outlines, warm colors. Comic-book adjacent.

**Face/Person:** Illustrated characters only.

**Typography:** Bold text hook (black on white, 3-4 lines), ending with "...more" truncation.

**Psychology:** Pattern interrupt — illustration breaks feed monotony. Humor lowers defenses. "...more" creates open loop. FB policy friendly (no real human bodies for restricted categories).

**When to use:** Pattern interrupt in feed. Restricted categories where real human imagery is policy-risky.

**When NOT to use:** Premium/clinical positioning.

**Gemini prompt template:**
"Flat vector illustration, thick outlines, warm colors. Scene: [PROBLEM depicted humorously — e.g., 'man sleeping with drool puddle', 'woman frustrated with messy hair']. Comic-book style. Space at top for bold text hook. 1080×1080. No realistic photography."

---

### Pattern 23: Testimonial Billboard

**What it looks like:**
Product testimonial placed on a real-world surface — billboard, truck, bus stop, storefront, screen mockup. Implies massive brand reach.

**Color palette:** Scene-dependent. Real-world photography with the testimonial on the "surface."

**Face/Person:** No — or environmental only.

**Psychology:** Scale signaling. "We're so big we're on trucks." The testimonial gains weight from being placed on a physical surface visible to the public.

**When to use:** Social proof at scale. Mid-funnel, brand credibility.

**When NOT to use:** Without compositing capability (Gemini renders text unreliably on surfaces).

**Production Notes:** Gemini generates the scene with blank billboard area → composite text + product mockup in Phase 4.

**Gemini prompt template:**
"Photorealistic scene: [SURFACE — e.g., 'delivery truck side panel', 'city bus stop', 'building billboard'] in [urban/suburban setting]. The [surface] has a BLANK AREA for ad placement (solid [BRAND COLOR] rectangle). Natural daylight. 1080×1350 (4:5). Journalistic photography style. NO TEXT on the billboard — text composited separately."

---

### Pattern 24: Product + Review Quote

**What it looks like:**
Product photo (studio shot) with customer review quote alongside. Star rating + review (60-100 words) + offer badge + SHOP NOW button.

**Color palette:** Light/neutral background (light gray, off-white). Offer badge in high contrast (orange, red, yellow).

**Face/Person:** No — product and social proof carry it.

**Typography:** Star rating prominent. Review quote in readable serif or sans-serif. Reviewer name attributed.

**Psychology:** Social proof + specificity. Reviews mentioning specific results + timeframes are most credible. The star rating is processed pre-attentively (before reading).

**When to use:** L3–L4 awareness. Trust building, retargeting visitors who didn't convert.

**When NOT to use:** Without genuine reviews.

**Production Notes:** Best produced via `review-quote.html` template. Product photo from brand assets.

---

### Pattern 25: Holiday/Event Offer

**What it looks like:**
Product with seasonal/holiday themed background or accents (flags, bows, snowflakes, hearts). Event name + offer + BUY X GET Y or X% OFF.

**Color palette:** Season-appropriate. Red/green for Christmas. Red/white/blue for patriotic events. Black/gold for Black Friday.

**Face/Person:** Optional — product should still be the hero.

**Psychology:** Temporal urgency + cultural context. The holiday frame creates a deadline the buyer didn't set but feels bound by. "Memorial Day Sale" = socially sanctioned shopping occasion.

**When to use:** L4–L5 awareness. Seasonal campaigns. Clear offers with deadline.

**When NOT to use:** Outside the relevant seasonal window.

**Gemini prompt template:**
"Facebook ad. [HOLIDAY THEME — e.g., 'American flag elements', 'gift bows and snowflakes']. Center: [PRODUCT] with seasonal accents (supporting, not overwhelming). Space for event headline at top and offer strip at bottom. 1080×1080. Festive but product-focused. NO TEXT — event/offer text composited separately."

---

### Pattern 26: Urgency/Scarcity Card

**What it looks like:**
Dark background, product image (small), large urgency text ("LAST CHANCE," "WE'RE SAYING GOODBYE," "ENDS TONIGHT"). Offer details prominent.

**Color palette:** Dark — black, deep navy, charcoal. Text in white or high-contrast accent. Seriousness and weight.

**Face/Person:** No — text and urgency carry the ad.

**Typography:** Urgency text LARGE — the creative is the urgency. Product small/secondary.

**Psychology:** Loss aversion at maximum intensity. Emotional language of loss/ending ("saying goodbye") outperforms countdown timers. The dark background creates visual weight and seriousness.

**When to use:** L4–L5 awareness. Bottom-of-funnel, cart abandoners, end-of-sale pushes.

**When NOT to use:** Cold audiences. Overuse dilutes urgency signals.

**Production Notes:** Create via `text-card.html` template or `headline-offer.html` — no Gemini needed.

---

## PATTERN SELECTION DECISION TREE

When you can't decide between patterns, use this:

```
Is the product visible in a TRANSFORMATION?
  → YES → Pattern 2 (Before/After) or Pattern 15 (Silent Result)
  → NO ↓

Is the goal EDUCATION about the mechanism?
  → YES → Pattern 12 (Diagram) or Pattern 13 (Feature-Icon Split)
  → NO ↓

Is there SOCIAL PROOF (reviews, numbers, press)?
  → YES → Pattern 3 (Number), 4 (Press), 8 (Authority Quote), or 24 (Review Quote)
  → NO ↓

Is this a DEAL/OFFER/URGENCY play?
  → YES → Pattern 6 (Premium-Discount), 25 (Holiday), or 26 (Urgency)
  → NO ↓

Is the copy the star (text-heavy, story, FAQ)?
  → YES → Pattern 7 (FAQ/PAS), 11 (Text Bomb)
  → NO ↓

Is the PRODUCT the star (single hero shot)?
  → YES → Pattern 20 (Product Hero), 1 (Benefit-Stack), or 10 (Abundance Flatlay)
  → NO ↓

Is the LIFESTYLE/IDENTITY the star?
  → YES → Pattern 9 (Lifestyle Scene), 19 (Problem-State), or 21 (UGC Selfie)
```

---

## REFERENCE IMAGE SELECTION

After choosing a pattern, get reference images:

1. Read `~/Downloads/Workforce/ad-library-v5/pattern-reference-index.json`
2. Filter to selected `pattern_id`
3. Sort by `used_count` DESC
4. Pick top 2-3 images, preferring brand diversity
5. Load from `~/Downloads/Workforce/ad-library-v5/images/[filename]`
6. Pass to Gemini as visual few-shot examples (see `references/gemini-multimodal.md`)

If a pattern has fewer than 3 reference images, use the closest related pattern's images and describe the difference in the Gemini prompt.

---

*Updated: 2026-03-12 | Source: 248 curated Tier 1 ads from 84 verified DTC brands (v5)*
*Reference images: ~/Downloads/Workforce/ad-library-v5/pattern-reference-index.json*
