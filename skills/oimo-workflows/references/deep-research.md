---
name: workflow-deep-research
description: "Deep research report generator — brief → plan angles → parallel sub-agents → reflect → single-writer cited report → cold review. Convergent (resumable via file checkpoints)."
---

# Workflow: deep-research

**When to use:** 

## Phases

1. **Brief** — Refine the question into an unambiguous research brief
2. **Plan** — Decompose brief into independent research angles
3. **Research** — One sub-agent per angle in parallel, writing structured findings to disk
4. **Reflect** — Gap-check against brief; spawn delta sub-agents if budget allows
5. **Write** — Single agent writes the full cited Markdown report
6. **Review** — Independent reviewer spot-checks citations; fix pass if needed

## Portable orchestration

oimo runs this as `.oimo/workflows/deep-research.js` with a `workflow` tool. On Cursor/OpenCode, **you** orchestrate the phases: spawn subtasks or follow the phase list sequentially, writing checkpoints to disk between phases.

Source: `packages/opencode/src/workflow/builtin/deep-research.js` in OpenMimoCode.
