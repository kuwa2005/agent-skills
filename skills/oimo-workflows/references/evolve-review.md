---
name: workflow-evolve-review
description: "Multi-agent review of an oimo Self Evolution brief: parallel reviewers score a product-change brief, then a synthesizer produces adopt/reject guidance for Human-in-the-loop."
---

# Workflow: evolve-review

**When to use:** Use after /evolve wrote a brief under .oimo/evolve/briefs/. Pass args.brief = path to the brief markdown (or its basename). Optional args.focus for emphasis. Does not auto-apply changes.

## Phases

1. **Load brief** — Read the AI-to-AI brief and linked friction/backlog context
2. **Parallel review** — Safety, usefulness, and feasibility reviewers run concurrently
3. **Synthesize** — Merge reviews into adopt / revise / reject with rationale

## Portable orchestration

oimo runs this as `.oimo/workflows/evolve-review.js` with a `workflow` tool. On Cursor/OpenCode, **you** orchestrate the phases: spawn subtasks or follow the phase list sequentially, writing checkpoints to disk between phases.

Source: `packages/opencode/src/workflow/builtin/evolve-review.js` in OpenMimoCode.
