---
name: workflow-research-experiment
description: "Autonomous experiment loop — establishes a baseline, then runs stateless iterations (hypothesize → implement → run → dual-gate) with a JS-enforced escalation ladder, a cheating audit by fresh eyes, and a report where every number traces to results.tsv."
---

# Workflow: research-experiment

**When to use:** Use when the user wants to autonomously improve a mechanically-verifiable metric of a codebase (training loss, benchmark score, latency, solver quality) without supervision. Requires up-front: an eval command with a fixed budget that prints the metric, and an explicit editable-file scope. Not for tasks whose success cannot be reduced to one number.

## Phases

1. **Baseline** — Record PLAN.md, git-commit current state, run the eval once, seed results.tsv
2. **Loop** — Stateless iterations; keep/revert decided by the script, not the agent; 3-fail REFINE / 5-fail PIVOT / 3-pivot STOP ladder
3. **Audit** — Independent agent checks kept diffs for metric gaming (eval tampering, hardcoded outputs, leakage)
4. **Report** — Baseline vs best, per-change delta table, dead ends, reproduce command

## Portable orchestration

oimo runs this as `.oimo/workflows/research-experiment.js` with a `workflow` tool. On Cursor/OpenCode, **you** orchestrate the phases: spawn subtasks or follow the phase list sequentially, writing checkpoints to disk between phases.

Source: `packages/opencode/src/workflow/builtin/research-experiment.js` in OpenMimoCode.
