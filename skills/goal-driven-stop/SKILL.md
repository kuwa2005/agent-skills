---
name: goal-driven-stop
description: Use when an autonomous agent loop should not stop until explicit success criteria are met. Portable pattern from oimo /goal — define stop conditions, require evidence before claiming done, and use an independent reviewer pass before accepting completion.
---

# Goal-driven stop conditions (portable)

Pattern exported from oimo's `/goal` command and judge model.

## When to use

- Long autonomous runs (implement until done, fix CI until green)
- User says "don't stop until X" or "keep going until Y passes"

## Protocol

1. **Capture goal** — Write measurable stop conditions (tests pass, PR ready, spec section S3 satisfied).
2. **Before each stop attempt** — Agent must cite evidence (command output, file state).
3. **Reviewer gate** — A separate pass (subagent or fresh context) checks conditions without assuming the worker's summary.
4. **Reject optimistic stop** — If any condition lacks evidence, continue working.

## On oimo

Use `/goal` to register conditions; the runtime invokes a judge model automatically.

## Elsewhere

Keep conditions in `GOAL.md` or the task prompt; run a explicit "goal check" subtask before ending the turn.
