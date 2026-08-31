---
name: workflow-enforcement
description: "Hook-based enforcement layer that makes Claude finish multi-phase plugin workflows (/cro, /titan) before ending a turn. Stop hook reads ~/.memory/workflows/active.json, blocks (exit 2) if any contract phase is missing its artifact."
metadata:
  type: project
---

# Workflow Enforcement System

**Shipped:** 2026-05-26
**Scope v1:** CRO + Titan plugins, hard-block Stop hook
**Status:** Live in `~/.claude/settings.json`

## What this solves

Slash commands and skills are prompt templates — Claude can skip steps. This system makes
multi-phase plugins (`/cro`, `/titan`) produce every required artifact on disk before the
turn can end.

**Why:** /cro and /titan have multi-step pipelines (blueprint → copy → build, or intake → script → scene-breakdown). Without enforcement, Claude can declare "done" with only some phases produced.

**How to apply:** When working on /cro or /titan SKILL.md, preserve the workflow-claim/workflow-mark calls. If adding a new multi-phase plugin, write a contract at `contracts/{plugin}-{mode}.json` and add the claim+mark calls to its SKILL.md.

## Architecture

- **Contracts**: `~/.memory/skills/ops/workflow-enforcement/contracts/{plugin}-{mode}.json` — list phases + required_artifact_glob + min_bytes
- **State**: `~/.memory/workflows/active.json` (single active workflow at a time)
- **Phase markers**: `~/.memory/workflows/{plugin}/{session_id}/{phase}.done.json`
- **Archive**: `~/.memory/workflows/_archive/` (completed/cancelled/stale)
- **Stuck log**: `~/.memory/workflows/_stuck.log`

## Scripts (all at `~/.memory/scripts/`)

| Script | Purpose |
|---|---|
| `workflow-claim.sh <plugin> <mode> [workspace]` | SKILL.md calls at start. Idempotent for nested same-plugin calls. |
| `workflow-mark.sh <phase> <artifact_path>` | SKILL.md calls after writing each artifact. Validates min_bytes. |
| `workflow-cancel.sh [reason]` | Manual abandon. Backs `/cancel-workflow` command. |
| `workflow-gate.sh` | **Stop hook.** Exit 0 if no active or all phases done. Exit 2 with feedback if missing. Safety-valve releases after 3 fires. |
| `workflow-session-start.sh` | **SessionStart hook.** Archives stale workflows (>6h), resets fire counter. |

## Settings wiring

`~/.claude/settings.json`:
- Stop hook chain: `workflow-gate.sh` runs BEFORE `on-stop-capture.sh`
- SessionStart hook: `workflow-session-start.sh`

## Plugin integration

- [`cro/SKILL.md`](~/.claude/plugins/local/cro/skills/cro/SKILL.md) — Step 0 added (claim) + workflow-mark calls in each Stage of BUILD and at end of AUDIT.
- [`titan/SKILL.md`](~/.claude/plugins/local/titan/skills/titan/SKILL.md) — Step 1.5 added with format→mode mapping. Intake gets marked in Step 3, main artifact(s) in Step 8.

## Escape hatches

- `/cancel-workflow` slash command (calls `workflow-cancel.sh`)
- Safety valve: gate releases after 3 fires
- Stale workflows auto-archived at session start

## v2 / future

Not built yet — only add if data shows need:
- **Layer C validators**: PostToolUse on Write that runs per-artifact structural validators (e.g., copy must have hook + body + CTA sections)
- **Dispatch plugin contract**: non-linear workflow model
- **Supabase analytics**: `workflow_runs` table for cross-machine stats

## Spec

Full design: [SPEC.md](SPEC.md)
