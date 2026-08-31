# Titan Direct Response System — Handoff Package

This is the complete Titan DR copywriting + visual production system, packaged for handoff to another Claude Code user.

## What's inside

| Folder | What it is |
|---|---|
| `plugin/` | The `/titan` slash command + entry SKILL (the router that detects format and loads only the files needed). |
| `skills/copywriting/titan-dr/` | The brain: psychology, language, storytelling, all 9 format files (FB ad, VSL, story VSL, email, landing page, advertorial, listicle, quiz funnel), references, swipe file, forbidden/approved words. |
| `skills/copywriting/titan-verify/` | Standalone compliance/quality verifier for any Titan output. |
| `skills/copywriting/titan-video-analyzer/` | Analyzes competitor video ads frame-by-frame against Titan principles. |
| `skills/design/titan-ads/` | Ad-image production playbook (creative patterns, copy-on-image, brand examples). |
| `skills/design/titan-conversion-designer/` | Phase 2 of any copy+visual task — turns Titan copy signals into design briefs + Gemini multimodal prompts. |
| `scripts/` | `workflow-claim.sh` + `workflow-mark.sh` — the workflow enforcement scripts the `/titan` plugin calls to mark phases complete. |
| `workflow-enforcement/` | Spec + JSON contracts that define which artifacts each Titan format must produce. |
| `install.sh` | One-shot installer that copies everything into the right places on the colleague's machine. |

**Package size:** ~830KB.

---

## Install (for your colleague)

### Option A — one command

```bash
cd titan-system
bash install.sh
```

That copies everything into:
- `~/.claude/plugins/local/titan/`
- `~/.memory/skills/copywriting/titan-dr/`
- `~/.memory/skills/copywriting/titan-verify/`
- `~/.memory/skills/copywriting/titan-video-analyzer/`
- `~/.memory/skills/design/titan-ads/`
- `~/.memory/skills/design/titan-conversion-designer/`
- `~/.memory/skills/ops/workflow-enforcement/`
- `~/.memory/scripts/workflow-claim.sh` + `workflow-mark.sh`

The installer is non-destructive: if a destination already exists it backs the old copy up to `~/.titan-backup-<timestamp>/` before overwriting.

### Option B — manual

If they don't want to run the script, mirror the folder structure into `~/.memory/` and `~/.claude/plugins/local/` exactly as listed above.

### Register the plugin (one-time)

In Claude Code, the plugin is auto-detected from `~/.claude/plugins/local/titan/`. If `/titan` doesn't appear after install, restart Claude Code. If it still doesn't appear, run `/plugin install local` and pick `titan`.

---

## How to use it (for your colleague)

Just type `/titan` followed by what they want. The router auto-detects the format and loads only the files needed.

Examples:

```
/titan write a Facebook ad for [product]
/titan write a 1500-word VSL for [product]
/titan write a Roosevelt-style story VSL for [product]
/titan write a 7-email post-purchase sequence
/titan write a landing page for [offer]
/titan write an advertorial that opens with a true story
/titan write 10 scroll-stop hooks for [product]
/titan audit this copy: [paste]
```

The plugin will:
1. Detect the format (Facebook ad, VSL, story VSL, email, landing page, advertorial, listicle, quiz, hooks, UGC, audit, production).
2. Load ONLY the files needed — never all 26 files. Three targeted files outperform eight unfocused ones.
3. Output a Strategic Assessment (awareness level, sophistication stage, UMP/UMS, voice register, biases to deploy) before writing.
4. Write the copy.
5. Run a silent 10-lens quality gate + War Room compliance audit.
6. Deliver with a footer showing format, awareness, register, biases, word count, and compliance status.

### Workflow enforcement (optional but recommended)

For enforced formats (FB ad, VSL, story VSL, email, landing page, advertorial, hooks), the plugin claims a workflow via the scripts and writes the deliverable to standard filenames (`intake.md`, `copy.md`, `script.md`, `scene-breakdown.md`, etc.) in the workspace. This only ENFORCES turn-end blocking if the colleague has the Stop hook wired up (see `workflow-enforcement/SPEC.md`). Without the hook, the scripts still run, they just don't block — perfectly fine for first use.

---

## Quick smoke test (after install)

```
/titan write 5 scroll-stop hooks for a beef organ supplement
```

Expected: a Strategic Assessment table, then 5 hooks, then a footer block. If you get that, the system is live.

---

## What this system is built on

- Schwartz 5-level awareness model
- 28-bias persuasion stack (loss aversion, social proof, authority, scarcity, identity, etc.)
- Cortisol → dopamine → oxytocin neurochemical sequence
- 20-register voice library (R1-R20) so copy matches the avatar exactly
- 6-Shield compliance system + Meta 2025 + FDA Tier 1/2 word lists
- 9 format blueprints with enforced boundary rules (no pricing in listicles, delayed product reveal in advertorials, etc.)

v1.0 of the plugin shipped after a full system audit — 29 fixes across 18 files, 97/97 eval assertions passed.

---

## Questions / issues

The whole system is text + scripts — no binaries, no external deps beyond `bash` and `jq` (jq only needed if the colleague turns on workflow enforcement). If something breaks after install, the first place to look is `~/.claude/plugins/local/titan/skills/titan/SKILL.md` — that file is the entire control flow.
