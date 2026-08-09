---
name: babysit
description: >-
  Keep a PR merge-ready by triaging comments, resolving clear conflicts, and
  fixing CI in a loop.
---
# Babysit PR
Your job is to get this PR to a merge-ready state.

Check PR status, comments, and latest CI and resolve any issues until the PR is ready to merge.

## 到達点

各ループの報告を読んだ人が、**今マージできるか／何がブロッカーか／次に何をするか**を即断できること。  
「コメントを確認して CI を直しています」で止まったら失敗。

## 具体性の下限（悪い例 / 良い例）

悪い例（不十分）:
> CI が落ちていたので直して push しました。コメントもだいたい対応済みです。

良い例（このレベルまで求める）:
> PR #442: mergeable=false（behind `main` by 3）。CI run `98765`: job `test` fail — `auth.spec.ts:42` expected 401 got 500。修正: `src/auth/middleware.ts` で未ログイン時の early return を復元。push `abc1234` → 再 watch。未解決コメント 1 件（Bugbot: N+1）→ 不同意（既存の dataloader でバッチ済み、スレッドに理由を返信）。次: CI 緑化待ち → squash merge 可否を報告。

## 図必須（毎ループ）

各イテレーションの開始時または報告時に、状態を ASCII / mermaid で示す。文章だけは不可。

```
[PR status] mergeable? conflicts? behind?
    │
    ├─ conflicts → resolve (意図衝突なら abort & ask)
    ├─ CI fail (in scope) → fix & push & re-watch
    ├─ CI fail (unrelated) → merge main if behind; else report
    └─ comments open → triage (valid fix / disagree+explain)
    │
    v
[ready?] mergeable + green CI + comments triaged → stop
```

## Loop actions

1. Merge conflicts: Intelligently resolve any merge conflicts, preserving the intent and correctness of changes on your branch and the base branch. If intents conflict, abort the merge and ask for clarification.
2. Comments: Review active unresolved comments (including Bugbot) and resolve change requests / bug reports where valid. When fetching GitHub comments, filter out resolved threads first. Read only each comment body and the minimum location/URL needed to act on it; do not read the entire JSON output or other unnecessary payload data. Carefully validate issues reported by Bugbot and only take action on those that are valid; explain when you disagree or are unsure.
3. CI: Fix CI issues caused by changes within this PR's scope. Never change CI checks/workflows just to make failures pass, or make unrelated code changes; if that would be required, report back instead. For merge-blocking failures that seem unrelated to this PR, check whether the branch is behind the base branch and merge latest changes, since another PR may have fixed them. Push scoped fixes and re-watch CI until mergeable + green + comments triaged.
