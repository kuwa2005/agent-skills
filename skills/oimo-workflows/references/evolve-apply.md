---
name: workflow-evolve-apply
description: "Human-approved semi-automatic apply of an oimo evolve brief: implement in an isolated worktree, verify, and open a draft PR. Never applies without args.approved=true."
---

# Workflow: evolve-apply

**When to use:** Use after evolve-review recommends adopt/revise and the USER explicitly approved. Pass args.brief and args.approved=true. Optional args.branch, args.title. Does not merge. Dangerous scopes (permissions, auth, schema migrations) must stay out of scope unless the brief already marks them approved.

## Phases

1. **Guard** — Require explicit args.approved=true; refuse otherwise
2. **Load brief** — Read brief + INDEX; refuse high-risk scopes without explicit allow_dangerous
3. **Implement** — Worktree-isolated agent implements acceptance criteria
4. **Verify** — typecheck / targeted tests; run evolve_status gate if possible
5. **PR** — Open a draft pull request for human merge

## Portable orchestration

oimo runs this as `.oimo/workflows/evolve-apply.js` with a `workflow` tool. On Cursor/OpenCode, **you** orchestrate the phases: spawn subtasks or follow the phase list sequentially, writing checkpoints to disk between phases.

Source: `packages/opencode/src/workflow/builtin/evolve-apply.js` in OpenMimoCode.
