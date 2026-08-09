---
name: verify
description: >-
  Use when about to claim work is complete, fixed, or passing, before committing
  or creating PRs. Requires running verification commands and confirming output
  before any success claims; evidence before assertions always. Triggers:
  done, fixed, passing, complete, ready to commit, PR, 完了, 直った, 確認.
---

# Verification Before Completion

## Overview

Claiming work is complete without verification is dishonesty, not efficiency.

**Core principle:** Evidence before claims, always.

**Violating the letter of this rule is violating the spirit of this rule.**

### 到達点

検証報告を読んだ人が、**同じコマンドを再実行せずに**「何が通って、何が未確認か」を判断できること。  
「たぶん直った」「問題なさそう」で止まったら失敗。

### 具体性の下限（悪い例 / 良い例）

悪い例（不十分）:
> テストもビルドも問題ないと思うので完了です。

良い例（このレベルまで求める）:
> `npm test` をこのターンで実行。exit 0、34/34 pass（出力末尾: `Tests: 34 passed`）。`npm run build` も exit 0。未実行: e2e / 本番デプロイ。以上より「単体テストとビルドはパス」と報告する。

悪い例（不十分）:
> CI は緑になるはずです。

良い例（このレベルまで求める）:
> `gh run view 123456789 --log-failed` で job `lint` が成功、`test` は 2 failing（`auth.spec.ts:42`）。修正後に再実行し run `123456790` が success であることを確認した。

### 図必須（複数検証があるとき）

検証が2ステップ以上、または依存があるときは ASCII / mermaid でゲートを示し、**各ノードにコマンドと結果**を書く。文章の箇条書きだけは不可。

```
[IDENTIFY] npm test / npm run build
    │
    v
[RUN] npm test     → 34/34 pass, exit 0
    │
    v
[RUN] npm run build → exit 0
    │
    v
[CLAIM] 単体+ビルドはパス（e2e 未実施と明記）
```

## The Iron Law

```
NO COMPLETION CLAIMS WITHOUT FRESH VERIFICATION EVIDENCE
```

If you haven't run the verification command in this message, you cannot claim it passes.

## The Gate Function

```
BEFORE claiming any status or expressing satisfaction:

1. IDENTIFY: What command proves this claim?
2. RUN: Execute the FULL command (fresh, complete)
3. READ: Full output, check exit code, count failures
4. VERIFY: Does output confirm the claim?
   - If NO: State actual status with evidence
   - If YES: State claim WITH evidence
5. ONLY THEN: Make the claim

Skip any step = lying, not verifying
```

## Common Failures

| Claim | Requires | Not Sufficient |
|-------|----------|----------------|
| Tests pass | Test command output: 0 failures | Previous run, "should pass" |
| Linter clean | Linter output: 0 errors | Partial check, extrapolation |
| Build succeeds | Build command: exit 0 | Linter passing, logs look good |
| Bug fixed | Test original symptom: passes | Code changed, assumed fixed |
| Regression test works | Red-green cycle verified | Test passes once |
| Agent completed | VCS diff shows changes | Agent reports "success" |
| Requirements met | Line-by-line checklist | Tests passing |

## Project-aware checks

Prefer the project's real commands when present:

- `composer test` / `phpunit` / `npm test` / `pytest`
- `npm run build` / `tsc --noEmit`
- linters configured in the repo
- Manual reproduction of the reported bug

If no automated test exists, run the smallest command that proves the claim (e.g. syntax check, HTTP smoke, CLI dry-run) and say what you verified.

## Red Flags - STOP

- Using "should", "probably", "seems to"
- Expressing satisfaction before verification ("Great!", "Perfect!", "Done!", etc.)
- About to commit/push/PR without verification
- Trusting agent success reports
- Relying on partial verification
- Thinking "just this once"
- Tired and wanting work over
- **ANY wording implying success without having run verification**

## Rationalization Prevention

| Excuse | Reality |
|--------|---------|
| "Should work now" | RUN the verification |
| "I'm confident" | Confidence ≠ evidence |
| "Just this once" | No exceptions |
| "Linter passed" | Linter ≠ compiler |
| "Agent said success" | Verify independently |
| "I'm tired" | Exhaustion ≠ excuse |
| "Partial check is enough" | Partial proves nothing |
| "Different words so rule doesn't apply" | Spirit over letter |

## Key Patterns

**Tests:**
```
✅ [Run test command] [See: 34/34 pass] "All tests pass"
❌ "Should pass now" / "Looks correct"
```

**Regression tests (TDD Red-Green):**
```
✅ Write → Run (pass) → Revert fix → Run (MUST FAIL) → Restore → Run (pass)
❌ "I've written a regression test" (without red-green verification)
```

**Build:**
```
✅ [Run build] [See: exit 0] "Build passes"
❌ "Linter passed" (linter doesn't check compilation)
```

**Requirements:**
```
✅ Re-read plan → Create checklist → Verify each → Report gaps or completion
❌ "Tests pass, phase complete"
```

**Agent delegation:**
```
✅ Agent reports success → Check VCS diff → Verify changes → Report actual state
❌ Trust agent report
```

## When To Apply

**ALWAYS before:**

- ANY variation of success/completion claims
- ANY expression of satisfaction
- ANY positive statement about work state
- Committing, PR creation, task completion
- Moving to next task
- Delegating to agents

## The Bottom Line

**No shortcuts for verification.**

Run the command. Read the output. THEN claim the result.

This is non-negotiable.
