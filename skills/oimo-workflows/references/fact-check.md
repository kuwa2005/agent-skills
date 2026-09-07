---
name: workflow-fact-check
description: ""
---

# Workflow: fact-check

**When to use:** 

## Phases

1. **Plan** — Break the question (from args) into several complementary search lines
2. **Search** — One web-search agent per line, in parallel
3. **Extract** — De-duplicate URLs, read the top sources, pull out checkable facts
4. **Group** — Fold facts that assert the same thing into one so each is checked once
5. **Crosscheck** — Adversarial jury per fact — a majority of reject votes drops it
6. **Report** — Rank survivors by certainty, merge, and cite

## Portable orchestration

oimo runs this as `.oimo/workflows/fact-check.js` with a `workflow` tool. On Cursor/OpenCode, **you** orchestrate the phases: spawn subtasks or follow the phase list sequentially, writing checkpoints to disk between phases.

Source: `packages/opencode/src/workflow/builtin/fact-check.js` in OpenMimoCode.
