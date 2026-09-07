---
name: workflow-compose
description: "Autonomous compose pipeline — brainstorms context, designs (spec/plan), implements via parallel per-task worktrees with TDD, verifies, reviews, reports, and merges. Bounded retry, never-ask mode."
---

# Workflow: compose

**When to use:** Use to drive a feature, bugfix, refactor, or review-feedback task through the full compose flow without user prompting. Pass args.task = the user's request. Optionally args.type to set the task type (feature/bugfix/refactor/feedback; otherwise inferred), args.feature_name for the report filename, args.skip_brainstorm / args.skip_report to drop those phases, args.maxConcurrent to bound per-batch parallelism. Independent tasks auto-run in parallel, each in its own worktree, then merge back; pass args.isolate_worktrees=false to force all-sequential or =true to force isolation.

## Phases

1. **Brainstorm** — Context recon (never-ask): conventions, recent changes, relevant files
2. **Design** — Apply compose:plan, compose:debug, or compose:feedback; emit task list with deps
3. **Implement** — Topo-sorted batches; independent tasks parallelize in per-task worktrees, then integrate
4. **Verify** — Run project verify commands; structured pass/fail
5. **Review** — compose:review for critical/important/minor issues
6. **Report** — compose:report per-iteration + final consolidated report
7. **Merge** — compose:merge to commit (and optionally push/PR)

## Portable orchestration

oimo runs this as `.oimo/workflows/compose.js` with a `workflow` tool. On Cursor/OpenCode, **you** orchestrate the phases: spawn subtasks or follow the phase list sequentially, writing checkpoints to disk between phases.

Source: `packages/opencode/src/workflow/builtin/compose.js` in OpenMimoCode.
