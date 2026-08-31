---
name: titan-video-analyzer
description: >
  Reverse-engineers video ads using the Titan DR framework. Takes video-to-context output
  (frames + transcript) and maps every scene to Titan vocabulary: hooks (21 types),
  biases (54), structure (7 UGC body types), neurochemical arc, compliance, and visual
  techniques. Produces an 8-section analysis report + summary card.

  TRIGGERS: "analyze this video ad," "break down this ad," "titan analyze," "video breakdown,"
  "deconstruct this ad," "what techniques does this ad use," "competitor ad analysis,"
  or when user provides a Facebook Ad Library URL or video-to-context output folder.

  NOT FOR writing copy — use titan-dr for that.
  NOT FOR verifying YOUR OWN copy — use titan-verify for that.
  THIS IS FOR reverse-engineering COMPETITOR or REFERENCE ads.
---

# Titan Video Analyzer — Competitive Ad Deconstruction Skill

> **Purpose:** Reverse-engineer any video ad into its Titan DR components.
> Turn competitor intelligence into actionable creative strategy.

---

## PREREQUISITES

### Video Extraction (must happen before analysis)
Run `video-to-context.py` to extract frames + transcript:
```bash
# Local video
python3 ~/Downloads/Workforce/video-to-context.py <video.mp4>

# Facebook Ad Library
python3 ~/Downloads/Workforce/video-to-context.py "https://facebook.com/ads/library/?id=..." --cookies-from-browser chrome

# Loom
python3 ~/Downloads/Workforce/video-to-context.py "https://www.loom.com/share/..."
```
Output: `video-context-output/<name>/` with `context.md`, `frames/`, `transcript.txt`

**Cost: $0** — all local processing (ffmpeg + whisper-cli + yt-dlp).

### Reference Files to Load
Before analysis, load these Titan DR files for vocabulary:
1. `titan-dr/core/titan-psychology.md` — 54 biases (Core 23 + FOTW 5 + Extended Arsenal 26), Triune Brain, Schwartz levels, neurochemicals
2. `titan-dr/references/titan-hook-library.md` — 21 hook types from 6,812 ads
3. `titan-dr/references/titan-video-hooks.md` — 3-part alignment, story locks, re-hooks, UGC structures
4. `titan-dr/references/titan-words-forbidden.md` — compliance vocabulary

Location: `~/Downloads/Workforce/ECOM TOOL/montage-master/skills/titan-dr/`

---

## EXECUTION WORKFLOW

### Step 1: Ingest
- Read `context.md` for timestamped transcript + frame mapping
- View key frames: frame_00001 (hook), product reveal frame, CTA frame, and 3-5 scene change frames
- Note total duration, frame count, scene change frequency

### Step 2: Strategic Assessment
Determine:
- **Schwartz Awareness Level** (1-5) the ad targets
- **Schwartz Sophistication Stage** (1-5) the ad operates at
- **Escape Tactic** if Stage 3-5 (mechanism naming / numerical superiority / identity offering)
- **Target Avatar** — who is this ad speaking to?

### Step 3: Hook Deconstruction
- Identify **Hook Type** from the 21-type library (match to closest type)
- Check **3-Part Hook Alignment**: do Visual + Spoken + Text say the same thing in 0-3 seconds?
- If story-based: identify **Hook A Source Type** (historical/animal/science/cultural/statistical/personal)
- If organic-style: identify **Organic Archetype** (Fortune Teller/Experimenter/Teacher/Magician/Investigator/Contrarian)
- For videos 60s+: identify **Re-hooks** (mid-video attention resets) and their timestamps

### Step 4: Bias Audit
Walk through the 54-bias checklist and map each deployed bias to its timestamp/scene:

**Core 23:**
1. Loss Aversion, 2. Specificity, 3. Social Proof/Bandwagon, 4. Identifiable Victim,
5. Authority/Halo, 6. Anchoring, 7. Scarcity, 8. Commitment/Consistency,
9. Confirmation, 10. Curiosity Gap/Zeigarnik, 11. Negativity, 12. Sunk Cost,
13. Zero Risk/Risk Reversal, 14. IKEA Effect, 15. Contrast/Decoy Pricing,
16. Endowment, 17. Hyperbolic Discounting, 18. In-Group/Out-Group (Polarity),
19. Reciprocity, 20. Reactance, 21. Status Quo, 22. Cognitive Dissonance/Shadow Self,
23. Urgency/FOMO

**FOTW 5 (2026):**
24. Blame Transfer, 25. Mechanism Naming, 26. Quiz Commitment (IKEA Extended),
27. Delegation Appeal, 28. Cultural Moment Hijack

**Extended Arsenal 26 (#29-54):**
See titan-psychology.md Part 8 for the complete list of biases #29-54.

Output as table:
```
| # | Bias | Timestamp | Scene Description | How Deployed |
|---|------|-----------|-------------------|--------------|
```

### Step 5: Structure Analysis
- **Triune Brain Sequence**: Map which scenes target Reptilian (agitate) → Limbic (emotionalize) → Neocortex (rationalize). Verify order is correct.
- **Neurochemical Arc**: Where does cortisol peak? Dopamine? Oxytocin? Map to timestamps.
- **Video Body Structure** (from 7 UGC types):
  - Breakdown / Newscaster / Case Study / Listicle / Problem Solver / Tutorial / Educational Story
- **Fractionation**: Identify DOWN/UP emotional bounces
- **Zeigarnik Loops**: Open loops and where they close (LIFO order)
- **Story Locks** detected:
  - Term Branding (proprietary names)
  - Embedded Truths (absolute vs conditional language)
  - Thought Narration (speaking viewer's thoughts)
  - Negative Frames (loss inversion)
  - Contrast Words (but/actually/instead/turns out)

### Step 6: Language & Copy Analysis
From the transcript:
- **NLP Patterns** detected (from the 25 in titan-language.md)
- **Copy Killers** present or successfully avoided (10 killers checklist)
- **Schwartz Strengtheners** in captions/text overlays
- **Specificity** — exact numbers, dollar amounts, timeframes used
- **Voice Register** estimate (R1-R20 scale)

### Step 7: Visual Technique Analysis
From the frames:
- **Caption style**: font weight, color, outline, position, animation style
- **Scene change frequency**: cuts per minute, fast-cut vs sustained
- **Color psychology**: dominant palette, warm/cool shifts, emotional mapping
- **Product reveal timing**: what second, how introduced (character presents / standalone / lifestyle)
- **Social proof visuals**: star ratings, review counts, testimonials on screen
- **AI generation style**: Pixar/3D, realistic, UGC-feel, mixed

### Step 8: Compliance Check
- **Tier 1 Death Zone**: Any cure/treat/diagnose/prevent claims?
- **Tier 2 Terms**: Identified and shielded?
- **Personal Attributes Trap**: Any "YOU + Negative State" framing?
- **Platform Risk Assessment**: Would this pass Meta 2025+ CAPI review? Risk level (Low/Medium/High)

---

## OUTPUT FORMAT

### Full Report
Produce all 8 sections above with specific citations (timestamps, frame numbers, transcript quotes).

### Summary Card (always include at end)
```
=== TITAN VIDEO ANALYSIS ===
Ad:                    [title]
Brand:                 [brand name]
Duration:              [Xm Xs]
Format:                [vertical 9:16 / horizontal 16:9 / square 1:1]
Visual Style:          [AI 3D / Live action / UGC / Mixed]

--- STRATEGIC ---
Awareness Level:       [1-5] — [name]
Sophistication Stage:  [1-5] — [escape tactic if 3-5]
Target Avatar:         [description]

--- HOOKS ---
Hook Type:             [from 21 types]
Hook Alignment:        [ALIGNED / MISALIGNED] (Visual + Spoken + Text)
Hook A Source:         [if applicable]
Re-hooks:              [count] at [timestamps]

--- PSYCHOLOGY ---
Biases Deployed:       [count]/54 — [list names]
Triune Sequence:       [CORRECT / VIOLATED] — R(0:XX) → L(0:XX) → N(0:XX)
Neurochemical Arc:     Cortisol(0:XX-0:XX) → Dopamine(0:XX-0:XX) → Oxytocin(0:XX-0:XX)
Body Structure:        [from 7 UGC types]
Fractionation:         [count] bounces
Open Loops:            [count]
Story Locks:           [list which of 5]

--- LANGUAGE ---
NLP Patterns:          [count] — [list]
Voice Register:        R[X]
Specificity Score:     [HIGH/MEDIUM/LOW]

--- COMPLIANCE ---
Tier 1 Violations:     [count or CLEAN]
Tier 2 Unshielded:     [count or CLEAN]
Personal Attributes:   [CLEAN / VIOLATION at 0:XX]
Platform Risk:         [LOW / MEDIUM / HIGH]

--- VERDICT ---
Key Takeaway:          [1 sentence — what makes this ad work or why it fails]
Steal This:            [1-2 techniques worth adapting for our own ads]
===
```

---

## QUALITY RULES

1. **Every claim must cite a timestamp or frame.** No vague analysis.
2. **Use Titan vocabulary precisely.** Don't say "emotional appeal" — say "Limbic targeting via oxytocin through Identifiable Victim Effect (Bias #4) at 0:22."
3. **View enough frames.** Minimum: hook frame, mid-point, product reveal, CTA. For detailed analysis: every 3-5 seconds through key scenes.
4. **Read the full transcript.** The context.md has it timestamped — use it.
5. **Don't force biases that aren't there.** If a bias isn't deployed, say so. Absence is data.
6. **The Summary Card is mandatory.** Even if the full report is provided, always end with the card.

---

## INTEGRATION NOTES

### For Claude Code conversations
When user provides a Facebook Ad Library URL:
1. Run `video-to-context.py` on it
2. Load this skill
3. Produce the full analysis

### For ECOM Tool (future integration)
This skill's output format (especially the Summary Card) is designed to be parseable.
The structured analysis can feed into:
- Competitive analysis dashboards
- Creative brief generation (reverse the analysis into a brief for YOUR ad)
- Hook library expansion (add discovered techniques to titan-hook-library.md)
- Template categorization (map visual styles to template types)
