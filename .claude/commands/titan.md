---
name: titan
description: "Write high-converting DTC/supplement copy using the Titan Direct Response system. Smart-routes to the correct format (ads, VSL, story VSL, email, landing page, advertorial, listicle, quiz funnel, hooks, UGC brief). Loads only the files needed for the detected format. Use when writing any persuasion-driven copy: 'write a Facebook ad', 'write a VSL', 'write an email sequence', 'write hooks', 'write a landing page', 'write an advertorial', etc."
---

First, make sure the Titan System is installed in this environment. If
`~/.memory/skills/copywriting/titan-dr/SKILL.md` does not exist, run:

```bash
bash "$CLAUDE_PROJECT_DIR/titan-system/install.sh"
```

Then load and follow the Titan skill at this path:

**Skill path:** `~/.claude/plugins/local/titan/skills/titan/SKILL.md`
(fallback if missing: `$CLAUDE_PROJECT_DIR/titan-system/plugin/skills/titan/SKILL.md`)

Read that file now and follow its instructions to execute the user's copy task.
