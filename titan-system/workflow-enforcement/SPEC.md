# Workflow Enforcement — Design Spec

**Date:** 2026-05-23
**Status:** Awaiting user review
**Owner:** Mike
**Scope v1:** CRO + Titan plugins, hard-block Stop hook
**Scope v2 (future):** Quality validators (Layer C), Dispatch plugin, Supabase analytics

---

## Problem

Slash commands and skills are prompt templates. Claude reads them and decides how to act — there is no enforcement layer. Multi-step plugins like `/cro` (blueprint → copy → build) and `/titan` (intake → format-load → produce) can be silently shortcut: Claude declares "done" after producing only some of the expected artifacts.

The realistic enforcement target is **observable state on disk**. Hooks cannot make Claude internalize a reasoning step, but they can make it impossible for Claude to end a turn without having produced the expected artifact files.

## Goal

Build a 3-layer enforcement system. Implement Layers A and B in v1. Defer Layer C.

- **Layer A** — Workflow Contract declared inside each SKILL.md. SKILL claims a workflow at start, marks each phase done as artifacts are written.
- **Layer B** — Stop hook gate. Reads the active workflow, verifies every required artifact exists and is non-empty. If not, exits non-zero with feedback. Claude cannot end the turn.
- **Layer C** — Per-artifact validators (PostToolUse on Write). Skipped in v1. Added later, plugin-by-plugin, only where Layer B reveals quality issues.

## Non-Goals (v1)

- Quality scoring of artifacts (Layer C)
- Cross-session analytics / Supabase logging
- Dispatch plugin (non-linear, doesn't fit phase model)
- Soft-warn mode (decision locked: hard block only)

---

## Architecture

### Storage layout

```
~/.workflows/
  active.json                    # Currently active workflow (one at a time)
  cro/
    2026-05-23-1430-abc123/      # session_id
      blueprint.done.json
      copy.done.json
      build.done.json
  titan/
    2026-05-23-1500-def456/
      intake.done.json
      copy.done.json
  _archive/                       # Completed/cancelled workflows moved here
    2026-05-23-1430-abc123.json
```

**Backup**: `~/.workflows/` is added to `mem-sync.sh`'s rsync targets, so workflow state flows to the existing GitHub backup repo automatically.

**Supabase**: NOT wired in v1. If we want cross-machine analytics later, a `workflow_runs` table in Supabase logged on completion is a clean addition — but defer until there's a question worth answering.

### Workflow Contract format

Stored at `~/.memory/skills/ops/workflow-enforcement/contracts/{plugin}-{mode}.json`.

```json
{
  "plugin": "cro",
  "mode": "build",
  "phases": [
    {
      "name": "blueprint",
      "required_artifact_glob": "*blueprint*.md",
      "min_bytes": 1500,
      "description": "CRO blueprint with structure, sections, UX rationale"
    },
    {
      "name": "copy",
      "required_artifact_glob": "*copy*.md",
      "min_bytes": 1000,
      "description": "Titan-generated copy for each section"
    },
    {
      "name": "build",
      "required_artifact_glob": "index.html",
      "min_bytes": 2000,
      "description": "Frontend implementation"
    }
  ]
}
```

**Glob, not exact path**: lets SKILL.md write artifacts under any workspace folder.
**min_bytes**: catches "Claude wrote 2 sentences" failures without full Layer C validators.

### Active workflow state

`~/.workflows/active.json`:

```json
{
  "plugin": "cro",
  "mode": "build",
  "session_id": "2026-05-23-1430-abc123",
  "started_at": "2026-05-23T14:30:00Z",
  "workspace": "/Users/mykhailokoshatko/Downloads/Workforce/cro-projects/landing-x/",
  "contract_path": "~/.memory/skills/ops/workflow-enforcement/contracts/cro-build.json",
  "phases_complete": ["blueprint"],
  "phases_remaining": ["copy", "build"],
  "stop_hook_fires": 0
}
```

### Phase marker

`~/.workflows/cro/{session_id}/{phase}.done.json`:

```json
{
  "phase": "blueprint",
  "marked_at": "2026-05-23T14:35:00Z",
  "artifact_path": "/Users/.../cro-projects/landing-x/blueprint.md",
  "artifact_size_bytes": 4521
}
```

---

## Components

### 1. Helper scripts (at `~/.memory/scripts/`)

#### `workflow-claim.sh`
```
Usage: workflow-claim.sh <plugin> <mode> <workspace_path>
Purpose: Called by SKILL.md at the start of a multi-phase workflow.
Behavior:
  - If active.json exists and matches same plugin+session, no-op (handles nested calls)
  - Otherwise: generate session_id, copy contract, write active.json
  - Echo session_id to stdout for SKILL to reference
```

#### `workflow-mark.sh`
```
Usage: workflow-mark.sh <phase_name> <artifact_path>
Purpose: Called by SKILL.md after producing a phase artifact.
Behavior:
  - Read active.json
  - Verify artifact_path exists and meets min_bytes from contract
  - Write phase.done.json under ~/.workflows/{plugin}/{session_id}/
  - Move phase from phases_remaining → phases_complete in active.json
  - Exit non-zero if phase isn't in contract or artifact is too small
```

#### `workflow-cancel.sh`
```
Usage: workflow-cancel.sh [reason]
Purpose: Manual escape hatch — user explicitly abandons a workflow.
Behavior:
  - Move active.json to _archive/ with cancellation metadata
  - Exit 0
Exposed as a slash command: /cancel-workflow
```

#### `workflow-gate.sh` (the Stop hook)
```
Stop hook entry point. Receives Claude Code hook input JSON on stdin.
Behavior:
  1. If no active.json → exit 0 (nothing to enforce)
  2. Read active.json + contract
  3. For each phase in phases_remaining:
       - Check that phase.done.json exists
       - Check that artifact_path from done.json exists
       - Check size >= min_bytes
  4. If all complete:
       - Move active.json to _archive/ (success)
       - Exit 0
  5. If incomplete:
       - Increment stop_hook_fires in active.json
       - If stop_hook_fires >= 3:
           - Log to ~/.workflows/_stuck.log
           - Exit 0 (safety valve — let user intervene)
           - Echo guidance to stderr: "Workflow stuck after 3 attempts. Run /cancel-workflow or finish manually."
       - Otherwise:
           - Exit 2 with stderr message listing missing phases + how to resolve
```

### 2. SessionStart hook addition

Add `workflow-session-start.sh` that:
- Checks if `active.json` exists and is older than 6 hours → archive it (stale)
- Resets `stop_hook_fires` counter to 0 if active.json exists (fresh session)

Wire into existing SessionStart chain.

### 3. Workflow contracts (v1)

- `contracts/cro-build.json` — blueprint → copy → build
- `contracts/cro-audit.json` — audit findings only (single phase)
- `contracts/cro-answer.json` — Q&A only (no phases, no enforcement — claim is a no-op)
- `contracts/titan-fb-ad.json` — intake → copy
- `contracts/titan-vsl.json` — intake → script → scene-breakdown
- `contracts/titan-email.json` — intake → sequence
- `contracts/titan-landing-page.json` — intake → copy
- `contracts/titan-advertorial.json` — intake → copy
- `contracts/titan-hooks.json` — intake → hooks-list

For Titan, the existing format router decides which contract to claim. Unknown formats fall through to no-contract (no enforcement, no false-positive blocking).

### 4. SKILL.md updates

#### `cro/SKILL.md` additions
Append a `## Workflow Contract` section near the top with:
- Trigger rules: which user input claims which mode
- Mandatory commands: `workflow-claim.sh cro {mode} {workspace}` at start, `workflow-mark.sh {phase} {artifact}` after each phase write
- Recovery instructions: if Stop hook blocks, here's how to resume

#### `titan/SKILL.md` additions
Same pattern. Format detection routes to the right contract.

### 5. Settings wiring

`~/.claude/settings.json`:
- Add `workflow-gate.sh` to the Stop hook chain (BEFORE existing `on-stop-capture.sh` so the gate fires first)
- Add `workflow-session-start.sh` to SessionStart hook
- No PreToolUse / PostToolUse changes in v1

### 6. `mem-sync.sh` extension

Add `~/.workflows/` to its rsync target list so workflow state persists across machines via existing GitHub backup.

### 7. Slash command: `/cancel-workflow`

New plugin-less command at `~/.claude/commands/cancel-workflow.md` that invokes `workflow-cancel.sh`. One-line escape hatch when user wants to abandon a stuck workflow.

---

## Edge Cases

| Case | Handling |
|------|----------|
| User runs `/clear` mid-workflow | SessionStart hook archives stale active.json (>6h) on next session. Manual `/cancel-workflow` if user wants to clear sooner. |
| Nested workflows (CRO calls Titan internally) | `workflow-claim.sh` is idempotent — if active.json already claimed by parent, child no-ops. Parent CRO owns the workflow. |
| Stop hook fires in infinite loop | `stop_hook_fires` counter caps at 3, then exits 0 with stuck-workflow guidance. |
| User asks a question mid-workflow ("what time is it?") | Stop hook still fires; Claude has to either advance the workflow or user has to `/cancel-workflow`. Acceptable trade-off — the alternative is non-enforcement. |
| SKILL.md forgets to call `workflow-claim.sh` | No enforcement happens. This is a SKILL.md bug, fixed by updating the SKILL. Layer A is on the honor system; Layer B only kicks in once Layer A runs. |
| Workflow legitimately doesn't need a phase (e.g., CRO audit-only) | Contract has fewer phases. CRO-answer mode has zero phases — claim is a no-op. |
| Artifact written outside Claude's tool calls (e.g., user manually drops a file in workspace) | `workflow-mark.sh` still works — it just checks the path. User can mark a phase done manually if needed. |
| Multiple parallel workflows (user wants both CRO and Titan running) | v1 supports one active at a time. Second claim is rejected with a clear error. User cancels or finishes the first. v2 may extend to a stack. |
| Hook returns wrong exit code accidentally | Bash strict mode (`set -euo pipefail`) + explicit exit codes. Tested with both passing and failing workflows before rollout. |

---

## Rollout Plan

1. **Build infrastructure** (Day 1, ~2h)
   - Write 4 shell scripts (claim/mark/cancel/gate) + session-start hook
   - Create `cro-build.json`, `cro-audit.json`, `cro-answer.json` contracts
   - Wire settings.json (in DRY-RUN mode — gate logs but exits 0)
   - Test manually with fake workflows

2. **Onboard CRO** (Day 1, ~30min)
   - Add Workflow Contract section to cro/SKILL.md
   - Switch gate from DRY-RUN to enforce
   - Test with a real `/cro build` invocation end-to-end

3. **Onboard Titan** (Day 2, ~1h)
   - Build 6 titan contracts
   - Add Workflow Contract section to titan/SKILL.md (with format-router → contract mapping)
   - Test with one format

4. **Backup wiring** (Day 2, ~15min)
   - Extend `mem-sync.sh` rsync targets
   - Verify state lands in GitHub repo

5. **Slash command** (Day 2, ~10min)
   - Create `/cancel-workflow` command

6. **Observe for a week**
   - Watch `~/.workflows/_stuck.log` for patterns
   - Identify which artifacts fail Layer B quality (size minimums) most often → seeds Layer C priority list

---

## Open Questions

1. **Workspace path discovery** — How does the SKILL.md know which workspace folder to claim? Default: current working directory. If user wants a specific folder, they pass it to the slash command (`/cro build ./projects/landing-x`). Decision needed: is CWD acceptable as default, or require explicit workspace?

2. **min_bytes thresholds** — What's the right floor per artifact? Best to start with rough numbers (1500 for blueprint, 1000 for copy, 2000 for HTML) and adjust based on real runs.

3. **Subagent workflows** — If a subagent does CRO blueprint work, does it count? Probably yes, since the artifact lands on disk regardless of which Claude wrote it. Confirm during testing.

---

## Risk Assessment

**Low risk** — purely additive. If the gate has a bug, worst case is Claude can't end turns. User can `/cancel-workflow` or comment out the hook in settings.json. No risk to existing plugins, backups, or memory system. Hook is sandboxed to its own scripts.

**Moderate risk** — Stop hook firing too aggressively (false positives) could be annoying. Mitigated by: (a) workflow-claim being explicit (no claim = no enforcement), (b) 3-strike safety valve, (c) hard escape hatch via `/cancel-workflow`.

---

## Success Criteria

After 2 weeks of production use:
- ≥90% of `/cro build` runs produce all three artifacts before turn ends (vs. estimated current ~40-60%)
- ≥90% of `/titan {format}` runs produce all phase artifacts
- Zero unrecoverable stuck-workflow situations (safety valve always provides escape)
- `_stuck.log` reveals at most 1-2 plugin-level bugs needing SKILL.md tightening
