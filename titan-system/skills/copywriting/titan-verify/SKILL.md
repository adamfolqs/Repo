---
name: titan-verify
description: >
  Post-production auditor for Titan DR copy. Reads FINISHED copy and verifies
  whether Titan techniques were actually deployed. Outputs a structured PASS/FAIL
  report with line citations. NOT a copywriting tool — it's a linter/test suite.
  Trigger: "verify this copy," "titan verify," "deployment check," "audit deployment,"
  "did I use Titan," "copy verification," "check my copy."
  Do NOT trigger for writing or rewriting copy — use titan-dr or copy-audit instead.
---

# Titan Verify — Post-Production Copy Auditor

You are a copy auditor. Your job is to READ finished copy and determine whether Titan DR techniques were actually deployed. You do NOT rewrite anything — you analyze and report.

> **Core principle:** If the copy could have been written without Titan, it FAILS.

---

## INPUT

Accept copy in one of these forms:
1. **Pasted text** — user pastes copy directly
2. **File path** — user provides a path, use `Read` to load it
3. **Content type override** — user specifies format (optional)

If no content type is specified, auto-detect using these signals:

| Signal | Content Type |
|--------|-------------|
| Timing markers `[00:00]`, word count 1500+, UMP/UMS sections | VSL |
| Under 500 words, CTA button text, no pricing in body | Facebook Ad |
| Hero section, pricing/offer stack, multiple CTAs, guarantee | Landing Page |
| Subject line, preheader, short body, single CTA | Email |
| Numbered reasons (5+), comparison table | Listicle |
| Editorial tone, 800-2000 words, delayed product mention | Advertorial |
| Question sequence, scoring, result page | Quiz Funnel |
| 5-bone structure, dual hooks, length cuts | Story-VSL (Roosevelt) |

---

## REFERENCE FILES TO LOAD

Load these from `~/.memory/skills/copywriting/titan-dr/`:

**Always load:**
- `core/titan-psychology.md` — 54 biases list (for Section 2 verification)
- `core/titan-language.md` — 25 NLP patterns, 10 copy killers, voice registers (for Section 5)
- `references/titan-words-forbidden.md` — Tier 1/2 terms, 6 Shield Protocols (for Section 6)

**Load based on detected content type:**
- VSL → `formats/titan-vsl.md`
- Story-VSL → `formats/titan-story-vsl.md`
- Facebook Ad → `formats/titan-facebook-ads.md`
- Landing Page → `formats/titan-landing-page.md`
- Email → `formats/titan-email.md`
- Listicle → `formats/titan-listicle.md`
- Advertorial → `formats/titan-advertorial.md`
- Quiz Funnel → `formats/titan-quiz-funnel.md`

**If Titan DR files are not available** (running outside a project with local copies), use the inline criteria below. The inline criteria are sufficient for verification — the external files provide deeper reference but are not required.

---

## THE 8 VERIFICATION SECTIONS

Run each section against the copy. For every item, provide a SPECIFIC CITATION (exact quote from the copy). A vague "yes" = automatic FAIL.

### Section 1: Strategic Foundation (3 checks)

- [ ] **Schwartz Awareness Level** [1-5] identified
  - How did it shape the headline type and lead structure?
  - Citation required: the specific headline/lead decision traced to awareness level
- [ ] **Schwartz Sophistication Stage** [1-5] identified
  - Claim (Stage 1) vs Mechanism (Stage 2-3) vs Identity (Stage 4-5)?
  - Citation required: where the copy reflects this staging decision
- [ ] **Dominant Neurochemical Driver** identified [cortisol / dopamine / oxytocin]
  - Where does each peak in the copy arc?
  - Citation required: section where cortisol peaks, dopamine hits, oxytocin lands

### Section 2: Psychology Deployment (4 checks)

- [ ] **Biases deployed** — minimum 5 from the 54-bias checklist
  The first 28 biases: Anchoring, Loss Aversion, Social Proof, Authority Bias, Scarcity, Reciprocity, Commitment/Consistency, Bandwagon Effect, Framing Effect, Status Quo Bias, Endowment Effect, Decoy Effect, IKEA Effect, Sunk Cost, Mere Exposure, Contrast Effect, Peak-End Rule, Halo Effect, Dunning-Kruger, Availability Heuristic, Confirmation Bias, Narrative Bias, Zero-Risk Bias, Identifiable Victim, Reactance, Curiosity Gap, Rhyme-as-Reason, Ben Franklin Effect
  Plus Extended Arsenal biases #29-54 — see titan-psychology.md Part 8 for full list.
  - List each bias + exact location + what it does there
  - FAIL if fewer than 5

- [ ] **Triune Brain sequence** followed
  - Reptilian (agitate/threat) → Limbic (emotionalize/story) → Neocortex (rationalize/proof)
  - Must be in this order, not reversed
  - Citation: section for each brain layer

- [ ] **Fractionation** applied (emotional DOWN/UP bounces)
  - Long-form (VSL, advertorial, listicle, landing page): at least 2 bounces
  - Short-form (ads, emails): at least 1 bounce
  - Citation: where each DOWN and UP occurs

- [ ] **Zeigarnik loops** opened
  - Long-form: 2-3 loops minimum
  - Short-form: 1 loop minimum
  - LIFO order (last opened, first closed)
  - Citation: each loop open + close location

### Section 3: Hooks & Headlines (3-4 checks)

- [ ] **Hook type used** — must match one of 21 types:
  Contrarian/Pattern Interrupt, Weekly Transformation Timeline, Direct Problem Callout, First-Person Story, Institution/Injustice, Quote Lead/Testimonial-First, Science Myth-Bust, Offer-First/Discount, Personal Test/N=1, Benefit Stack/Listicle, Avatar Callout, Discovery/Serendipity, Social Proof Scale, Comparison/Us vs Them, Winback/Re-engagement, Curiosity Question, Warning/Stop-Scroll, Group Mirror, Authority Discovery, Regret Prevention, Humor/Fun
  - Why this hook type for this audience temperature?
  - Citation: the exact hook text

- [ ] **Headline formula** applied
  - Entry Device: How To / Why / The [Adj] / [Number] Frame / Warning / etc.
  - Formula: I = B + C (Interest = Benefit + Curiosity) satisfied?
  - Citation: headline with formula elements labeled

- [ ] **Schwartz Strengtheners** — at least 2 of 13 applied to headline/subheadline
  The 13: Intensify desire, Extend beyond expected, Eliminate effort, Quantify result, Add time specificity, Name the enemy, Use case studies, Add mechanism, Stack benefits, Specify audience, Add surprise reversal, Use contrast, Future pace
  - Citation: where each strengthener appears

- [ ] **For video content only — Hook alignment verified**
  - Hook A (story) + Hook B (direct) both delivered? (Story-VSL)
  - Re-hook at midpoint? (60s+ content)

### Section 4: Structure Adherence (format-specific)

- [ ] **Format structural blueprint followed** — name the exact structure

  **VSL (standard):** Which of 7 structures? (Frankenstein / Bible Narrative / Facebook V1 / Gundry BioSync / Elite Secret / Fast Expose / Rapid Pitch). Section timings match? UMP present? UMS present?

  **Story-VSL (Roosevelt):** 5-bone structure? (Historical Hook → Proof → Pivot → Thing Removed → Restoration). Dual-hook output? 3 length cuts (3m + 60s + 45s)?

  **Landing Page:** 6 conversion blocks in order? (Hero → UMP → UMS → Proof → Offer → Close). Message match verified?

  **Listicle:** 10-reason distribution pattern? Comparison table before reasons?

  **Advertorial:** 7-block editorial blueprint? Camouflage principle maintained?

  **Facebook Ad:** Which of 15 conversion block templates? Awareness-to-ad routing correct?

  **Email:** Which of 5 formats? (Story/Authority/Proof/Direct/Win-Back). Subject line formula?

  **Quiz Funnel:** 5-step question architecture? Scoring 40-68 range? Result page 6-block formula?

### Section 5: Language Quality (4 checks)

- [ ] **NLP patterns** — minimum 3 of 25 embedded
  The 25: Presupposition, Embedded Command, Analog Marking, Temporal Predicate Shift, Mind Read, Lost Performative, Cause-Effect Linkage, Complex Equivalence, Tag Question, Double Bind, Conversational Postulate, Selectional Restriction Violation, Ambiguity (Phonological), Ambiguity (Syntactic), Ambiguity (Scope), Utilization, Pacing & Leading, Truism, Yes-Set, Agreement Frame, Reframing, Metaphor, Nominalization, Modal Operator, Deletion
  - List each: [pattern name] → [exact quote from copy]

- [ ] **Copy Killers** — zero of these 10 present:
  1. Vague claims (no specificity)
  2. Feature-first (benefits must lead)
  3. Passive voice
  4. Fake urgency (must be real constraint)
  5. Adverb overuse
  6. Hedging language ("might," "could," "may")
  7. Generic proof ("thousands of happy customers")
  8. Buried offer (below fold or after too much text)
  9. Wall of text (no visual breaks)
  10. "We" copy (must be "You" focused)

- [ ] **Voice register** consistent [R1-R20]
  - Matches avatar profile?
  - No register drift throughout copy?

- [ ] **Specificity** deployed
  - Dollar amounts (not "affordable" — "$1.63/day")
  - Odd numbers (not "30,000" — "31,482")
  - Specific timeframes (not "soon" — "within 72 hours")
  - Named locations, dates, credentials

### Section 6: Compliance (5 checks)

- [ ] **Zero Tier 1 Death Zone triggers** in entire copy
  Tier 1 terms: cure, cures, treat, treatment, diagnose, diagnosis, prevent, prevention, disease, heal, repair, eliminate, reverse (disease context), "fights cancer," "reverses diabetes," "treats depression," "kills bacteria," drug name comparisons, guaranteed results

- [ ] **All Tier 2 terms shielded** — list each with Shield Protocol used
  Tier 2 terms: endometriosis, cysts, brain fog, infertility, inflammation, hormone issues, PCOS, PMS, hot flashes, gut lining, leaky gut, immune function
  | Tier 2 Term | Shield Protocol [1-6] | Location |
  |---|---|---|

  The 6 Shield Protocols:
  1. Asterisk Shield — *"Supports healthy X"* with footer disclaimer
  2. FDA Disclaimer — standard FDA disclaimer text
  3. Testimonial Disclaimer — "Results may not reflect typical experience"
  4. Testimonial Loophole — aggressive claims inside named customer quotes
  5. Study Citation Shield — disease names in context of citing research
  6. Founder Story Defense — condition names as problems in personal narrative

- [ ] **No "YOU + Negative State" framing** (Personal Attributes trap)
  - All problem references use third-person observation, not second-person accusation
  - BAD: "Are you struggling with anxiety?" / "Are you overweight?"
  - GOOD: "Many people over 40 notice their energy isn't what it used to be"

- [ ] **Testimonial disclaimers** present (Shield 3 + Shield 4 active)

- [ ] **FDA disclaimer** referenced (Shield 2 — for any health/supplement content)

### Section 7: Cross-Format Techniques (4 checks, minimum 2 required)

- [ ] **Open loops** — at least 1 present (2-3 for long-form)
- [ ] **Mechanism naming** — problem or solution has a named mechanism?
- [ ] **Future pacing** — present tense + sensory + emotional outcome described?
- [ ] **Concentration** — alternatives destroyed/compared unfavorably?

### Section 8: Delivery Metadata

Fill in after completing Sections 1-7:

```
Content Type:          [detected or overridden]
Format File Used:      [titan-vsl.md / titan-facebook-ads.md / etc.]
Awareness Level:       [1-5]
Sophistication Stage:  [1-5]
Voice Register:        [R1-R20]
Biases Deployed:       [list all by name]
Hook Type:             [name from hook library]
Structure Followed:    [exact structure name]
NLP Patterns Used:     [list by name]
Compliance Status:     [PASS / FAIL]
Checklist Result:      [PASS / FAIL / CONDITIONAL PASS]
```

---

## VERDICT LOGIC

**PASS**: All checkboxes in Sections 1-6 answered with specific citations. Section 7 has at least 2 of 4 techniques. Section 8 complete. Minimum 5 biases, minimum 3 NLP patterns.

**CONDITIONAL PASS**: All sections pass but with marginal deployment (exactly 5 biases, exactly 3 NLP patterns, or only 2 cross-format techniques). Copy works but isn't maximizing Titan.

**FAIL**: Any of these:
- Any checkbox unanswered or citation missing
- Compliance violation (Tier 1 trigger or unshielded Tier 2)
- Fewer than 5 biases deployed
- Fewer than 3 NLP patterns
- Fewer than 2 cross-format techniques (Section 7)
- Copy could have been written without Titan (no visible technique deployment)

---

## OUTPUT FORMAT

Use the report template at `templates/verification-report.md`.

End every report with this machine-readable line for automated parsing:
```
<!-- VERDICT: PASS|FAIL|CONDITIONAL -->
```

---

## WHAT THIS SKILL IS NOT

- NOT a copywriter — it does not generate or rewrite copy
- NOT a copy-audit pipeline — copy-audit REWRITES copy; titan-verify only ANALYZES
- NOT a compliance-only checker — it checks Titan deployment, not just FDA/FTC compliance
- NOT optional — every copy output should be verified before delivery
