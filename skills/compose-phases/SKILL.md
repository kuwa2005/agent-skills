---
name: compose-phases
description: Spec-driven development phase skills exported from oimo Compose (plan, execute, verify, review, debug, TDD, worktree, merge, parallel, brainstorm, ask, feedback, report, subagent). Use compose-next for the end-to-end user-facing workflow; load individual phases from references/ when orchestrating manually on Cursor, OpenCode, or oimo.
---

# Compose phases (portable)

Exported from Open Mimo Code `skill/compose/.bundle`. Each phase lives under `references/<phase>/`.

| Phase | Path | Original skill name |
|-------|------|-------------------|
| ask | references/ask/SKILL.md | compose:ask |
| brainstorm | references/brainstorm/SKILL.md | compose:brainstorm |
| debug | references/debug/SKILL.md | compose:debug |
| execute | references/execute/SKILL.md | compose:execute |
| feedback | references/feedback/SKILL.md | compose:feedback |
| merge | references/merge/SKILL.md | compose:merge |
| parallel | references/parallel/SKILL.md | compose:parallel |
| plan | references/plan/SKILL.md | compose:plan |
| report | references/report/SKILL.md | compose:report |
| review | references/review/SKILL.md | compose:review |
| subagent | references/subagent/SKILL.md | compose:subagent |
| tdd | references/tdd/SKILL.md | compose:tdd |
| verify | references/verify/SKILL.md | compose:verify |
| worktree | references/worktree/SKILL.md | compose:worktree |

## Usage

1. **Full workflow on any host:** use the **compose-next** skill (also exported).
2. **Single phase:** read the matching `references/<phase>/SKILL.md` and announce which phase you are running.
3. **On oimo:** native `compose:*` skills and `compose` workflow JS may still be preferred when available.

Do not start compose phases unless the user asked for structured spec-driven work.
