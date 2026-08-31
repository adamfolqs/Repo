---
name: titan
description: "Titan Direct Response copywriting system. Use for ANY DTC/supplement copy task: Facebook ads, VSLs, story VSLs, email sequences, landing pages, advertorials, listicles, quiz funnels, hooks, UGC briefs, copy audits. Smart-routes to the correct format, loads only needed files, enforces compliance and quality gates automatically."
---

# /titan — Titan Direct Response System

You are executing the Titan Direct Response copywriting system. This command handles format detection, file loading, copy execution, and quality enforcement automatically.

## Step 1: Detect Format

Read the user's prompt and classify into ONE of these formats:

| If prompt mentions... | Format | Code |
|---|---|---|
| Facebook ad, Meta ad, Instagram ad, static ad, carousel | **Facebook Ad** | `fb` |
| VSL, video sales letter, video script, long-form video, Frankenstein | **Standard VSL** | `vsl` |
| Story VSL, Roosevelt, historical hook, "did you know", educational video, story ad | **Story VSL** | `story-vsl` |
| Hook, hooks, scroll-stopper, opening lines, video hooks | **Hook Writing** | `hooks` |
| UGC, influencer brief, creator script, organic video | **UGC Brief** | `ugc` |
| Email, email sequence, post-purchase, abandoned cart, win-back, broadcast | **Email** | `email` |
| Landing page, sales page, conversion page, checkout page | **Landing Page** | `lp` |
| Advertorial, native ad, editorial article, sponsored content | **Advertorial** | `adv` |
| Listicle, pre-sale, reasons page, bridge page | **Listicle** | `list` |
| Quiz, funnel, assessment, diagnostic | **Quiz Funnel** | `quiz` |
| Headline, headline writing, subject line | **Headline Only** | `headline` |
| Copy audit, quality review, check this copy | **Copy Audit** | `audit` |
| Ad creative, production checklist, video production | **Production** | `prod` |

If ambiguous, ask ONE clarifying question: "Should the viewer know from the first sentence this is an ad?" (YES → vsl, NO → story-vsl)

State the detected format before proceeding:
```
FORMAT DETECTED: [format name]
Loading: [list of files]
```

## Step 1.5: Claim the workflow (MANDATORY for enforced formats)

After detecting the format, if it is one of the **enforced formats below**, claim the
workflow so the Stop hook can verify every phase produces its expected artifact.

**Enforced formats (v1):**

| Format code | Workflow mode arg | Phases that must be marked |
|---|---|---|
| `fb` | `fb-ad` | `intake`, `copy` |
| `vsl` | `vsl` | `intake`, `script`, `scene-breakdown` |
| `story-vsl` | `vsl` | `intake`, `script`, `scene-breakdown` |
| `email` | `email` | `intake`, `sequence` |
| `lp` | `landing-page` | `intake`, `copy` |
| `adv` | `advertorial` | `intake`, `copy` |
| `hooks` | `hooks` | `hooks` |

For non-enforced formats (`ugc`, `list`, `quiz`, `headline`, `audit`, `prod`, `ugc`),
skip workflow claiming — they have no v1 contract.

**Claim:**
```bash
bash ~/.memory/scripts/workflow-claim.sh titan <mode> <workspace_path>
```

Where `<workspace_path>` is the directory where artifacts will be written (default: CWD).

**After EACH phase produces its artifact, MANDATORY:**
```bash
bash ~/.memory/scripts/workflow-mark.sh <phase> <absolute_artifact_path>
```

**Standard artifact filenames** (use these so the contract globs match):
- `intake.md` — the Strategic Assessment + intake (Step 3 output)
- `copy.md` — the main copy deliverable
- `script.md` — VSL script
- `scene-breakdown.md` — VSL scene-by-scene visual plan
- `sequence.md` — email sequence
- `hooks.md` — hooks list
- `advertorial.md` — advertorial body

If the workflow is claimed but a phase is not marked, the Stop hook blocks the turn
from ending. Run `/cancel-workflow` to abandon.

## Step 2: Load Files (Smart Routing)

Based on detected format, load EXACTLY these files using the Read tool.

### ALWAYS load (every format):
```
~/.memory/skills/copywriting/titan-dr/core/titan-psychology.md
~/.memory/skills/copywriting/titan-dr/core/titan-language.md
~/.memory/skills/copywriting/titan-dr/references/titan-words-forbidden.md
```

### THEN load format-specific files:

**fb (Facebook Ad):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-facebook-ads.md
~/.memory/skills/copywriting/titan-dr/references/titan-hook-library.md
```

**vsl (Standard VSL):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-vsl.md
~/.memory/skills/copywriting/titan-dr/core/titan-storytelling.md
```

**story-vsl (Story VSL / Roosevelt):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-story-vsl.md
~/.memory/skills/copywriting/titan-dr/references/titan-video-hooks.md
~/.memory/skills/copywriting/titan-dr/references/titan-hook-library.md
~/.memory/skills/copywriting/titan-dr/core/titan-storytelling.md
```

**hooks (Hook Writing):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-facebook-ads.md
~/.memory/skills/copywriting/titan-dr/references/titan-hook-library.md
~/.memory/skills/copywriting/titan-dr/references/titan-video-hooks.md
```

**ugc (UGC Brief):**
```
~/.memory/skills/copywriting/titan-dr/references/titan-video-hooks.md
~/.memory/skills/copywriting/titan-dr/references/titan-hook-library.md
~/.memory/skills/copywriting/titan-dr/references/dr-visual.md
```

**email (Email Sequence):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-email.md
```

**lp (Landing Page):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-landing-page.md
~/.memory/skills/copywriting/titan-dr/core/titan-storytelling.md
```

**adv (Advertorial):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-advertorial.md
~/.memory/skills/copywriting/titan-dr/core/titan-storytelling.md
```

**list (Listicle):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-listicle.md
```

**quiz (Quiz Funnel):**
```
~/.memory/skills/copywriting/titan-dr/formats/titan-quiz-funnel.md
```

**headline (Headline Only):**
```
(no additional files — the 3 core files contain the full headline system)
```

**audit (Copy Audit):**
```
(load all format files relevant to the copy being audited)
~/.memory/skills/copywriting/titan-verify/SKILL.md
```

**prod (Production):**
```
~/.memory/skills/copywriting/titan-dr/references/dr-visual.md
```

### OPTIONAL — load if the prompt mentions a specific brand:

**Folqs (colostrum, Primal Eight):**
```
~/.memory/skills/copywriting/titan-dr/references/folqs-products.md
```

### OPTIONAL — load for extra quality:
```
~/.memory/skills/copywriting/titan-dr/references/titan-words-approved.md    (power words)
~/.memory/skills/copywriting/titan-dr/references/titan-swipe-file.md        (verbatim copy blocks)
```

## Step 3: Strategic Assessment (MANDATORY — output this before writing)

For enforced formats, also write this assessment to `<workspace>/intake.md` and run:
`bash ~/.memory/scripts/workflow-mark.sh intake <workspace>/intake.md`

Before writing ANY copy, determine and explicitly state:

| Field | What to determine |
|---|---|
| **Awareness Level** | 1-5 per Schwartz (1=Unaware, 5=Most Aware) — drives headline type, lead structure, proof intensity |
| **Sophistication Stage** | 1-5 — drives mechanism emphasis vs claim vs identity |
| **UMP** | Unique Mechanism of Problem — a NAMED mechanism ("Gut Barrier Breakdown") |
| **UMS** | Unique Mechanism of Solution — a NAMED mechanism ("First-Day Colostrum Seal") |
| **Emotional Driver** | Primary cortisol/dopamine/oxytocin sequence for this avatar |
| **Voice Register** | R1-R20 from titan-language.md Part 13 — must match the avatar exactly |
| **Biases** | List 8-12 by name AND number from the 54-bias system in titan-psychology.md Part 8 |

Output the strategic assessment as a table at the top of your response.

## Step 4: Write Using Format Structure

Follow the format file's structural blueprint EXACTLY:
- Use the section sequence defined in the format file
- Respect FORMAT BOUNDARY RULES (no pricing in listicles, delayed reveal in advertorials, etc.)
- Use the correct HEADLINE SOURCE (hook library for ads, language.md for landing pages — see routing table in SKILL.md)
- If brief specifies word count/duration, plan section word budgets BEFORE writing

### The 7 Critical Rules (apply to ALL formats):
1. Every sentence does at least two jobs
2. Benefits lead, features justify
3. "You" not "We"
4. Short sentences. Fragments for emphasis.
5. Specific over general ("$1.63/day" not "affordable")
6. Voice must match avatar exactly
7. Compliance always — no Tier 1 trigger is ever worth the risk

## Step 5: Language Engine (from titan-language.md)

Apply these DURING writing:
- Headline formula based on awareness level
- Schwartz Strengtheners on every headline and key claim
- NLP patterns embedded in body copy
- Metaphor from swipe file for mechanism explanation
- Eliminate all 10 Conversion Killers

## Step 6: Compliance Check (MANDATORY — run BEFORE delivering)

Run a War Room audit on your output:
1. Extract every health-related term from the copy
2. Check each against Tier 1 (absolute ban) and Tier 2 (shield required) lists
3. Verify:
   - Zero Tier 1 triggers ANYWHERE (including testimonials, social proof)
   - All Tier 2 terms properly shielded (correct Shield Protocol for each)
   - No "YOU + Negative" framing (Personal Attributes rule)
   - Testimonial disclaimers present
   - No disease names as product benefit claims
   - FDA disclaimer present where needed

If ANY Tier 1 trigger found → fix it before outputting.

## Step 7: Silent Quality Gate (MANDATORY — run BEFORE delivering)

Apply all 10 lenses from titan-language.md Part 10:
1. Headline Lens — does headline match awareness level?
2. Mechanism Lens — is UMP/UMS named and deployed?
3. Proof Lens — is social proof specific and stacked?
4. Emotional Lens — does cortisol→dopamine→oxytocin sequence hold?
5. Voice Lens — is register consistent throughout? (See Part 13)
6. Compliance Lens — did War Room audit pass?
7. Structure Lens — does format match blueprint?
8. CTA Lens — is the close appropriate for format?
9. Specificity Lens — are claims specific, not vague?
10. Bias Lens — are intended biases actually deployed in copy?

Do NOT output these lens results to the user. This is a silent self-check. If any lens fails, fix the copy before delivering.

## Step 8: Deliver

For enforced formats, write the main copy to the standard filename in `<workspace>/`
(see Step 1.5 table), then mark the phase complete:
```bash
bash ~/.memory/scripts/workflow-mark.sh <phase> <workspace>/<filename>
```

For VSL formats, write `script.md` AND `scene-breakdown.md` and mark each.

Output the copy with this footer:

```
---
**Titan DR Output**
- Format: [format name]
- Awareness: Level [N] — [name]
- Sophistication: Stage [N]
- Mechanism: [UMP] → [UMS]
- Register: R[N] ([name])
- Biases deployed: [list by # and name]
- Word count: [N]
- Compliance: War Room audit clean
- Quality Gate: 10/10 lenses passed
```

## Format Boundary Rules (ENFORCED)

| Format | Pricing/Offer | Product Timing | Tone |
|---|---|---|---|
| Listicle / Pre-sale | NONE | Minimal — problem/solution focus | Educational |
| Advertorial | NONE in body, soft at end | Delayed to 50-70% | Editorial |
| Landing / Sales Page | FULL — pricing, bundles, urgency | Throughout | Conversion |
| VSL (Roosevelt / Story) | Delayed until close | After story bridge (word 250+) | Story-led |
| Facebook Ad | Teaser ("up to X% off") | Can appear early | Scroll-stop |
| Quiz Funnel | On result page only | After quiz results | Diagnostic |
| Email | Match email type | Varies by email in sequence | Relationship |

## What NOT to Do

- Do NOT load all 26 files. Load only what the routing table specifies.
- Do NOT use the expert panel (deprecated). Use Silent Quality Gate + format checklist.
- Do NOT load legacy dr-copy-* files (deprecated). They are superseded by v2 core files.
- Do NOT use hook library headlines for landing pages, emails, or advertorials. Those formats use titan-language.md's headline system.
- Do NOT skip the Strategic Assessment. It's mandatory output.
- Do NOT skip compliance check. Run War Room audit on every output.
- Do NOT guess register numbers. Look them up in titan-language.md Part 13.

## Version
- v1.0 — 2026-04-07 — Created after full system audit (29 fixes across 18 files), 97/97 eval assertions passed.
