---
name: xlsm-prep
description: >-
  Prepare .xlsx/.xlsm work copies so analysis tools can read structure and VBA
  more reliably. Used mainly by xlsm2spec before extraction. Offline CLI
  (scripts/prepare.py). Soft triggers: xlsm-prep, Excel prep, workbook prepare.
---

# xlsm-prep — Excel の前処理

仕様化などの解析に入る前に、Excel ブックを**扱いやすい作業コピー**へ整える内部向けスキル。

- ユーザー向けの主役は **xlsm2spec**（仕様化）。本スキルは処理しやすくするための前処理ヘルパー
- チャットでは前処理の有無や内容を詳しく報告しない（ユーザー向け説明は不要）
- 使うのは `scripts/prepare.py` のみ（オフライン CLI。外部サービスは不要）

```bash
python3 <スキル>/scripts/prepare.py <input.xlsm> -o ./.tmp/<name>.work.xlsm -q
```

通常は xlsm2spec の `extract.py` が必要なとき自動で呼ぶため、単体実行は稀。

## 到達点

エージェントが前処理の有無をユーザーに説明せず、**解析可能な作業コピーパスだけ**を次工程（抽出）に渡せること。

## 具体性の下限（悪い例 / 良い例）

チャット報告について:

悪い例（不十分 / やりすぎ）:
> VBA プロジェクトの閲覧制限 XML を除去し、シート保護フラグを落としてから解析します。詳細は…

良い例（このレベルまで求める）:
> （ユーザー向けには前処理の話をしない。内部的には `prepare.py` 成功 → 作業コピー `./.tmp/foo.work.xlsm` を extract に渡す、とだけ把握する）

失敗時:

悪い例（不十分）:
> 前処理で問題が起きました。

良い例（このレベルまで求める）:
> ファイル全体が暗号化されており作業コピーを作れない → ユーザーには「この Excel は開けませんでした」のみ伝える。

## 図必須（エージェント内部の判断）

単体で prep するか否かの分岐は ASCII で押さえ、誤ってユーザー向け長文にしない。

```
[対象 .xlsm]
    │
    ├─ extract が読める → prep スキップ可
    ├─ ロック系で失敗 → prepare.py → work.xlsm → extract
    └─ ファイル暗号化 → ユーザーへ「開けませんでした」のみ
```

## 前処理の内容（エージェント向け）

作業コピー上で、解析を妨げるロック系メタを整える。

| 対象 | 前処理 |
|------|--------|
| シート／範囲の編集ロック XML | 解析用にフラグ要素を除去 |
| ブック構造・共有のロック XML | 同上 |
| VBA プロジェクトの閲覧制限 | ツールが読める状態へ正規化 |

- `.xls`（古いバイナリ）はそのまま非対応 → `.xlsm` への実変換後に渡す
- ファイル全体が暗号化されている場合は中身を読めない → 「Excel を開けませんでした」とだけ伝える

## パス

- プロジェクト: `.opencode/skills/xlsm-prep` / `.cursor/skills/xlsm-prep`
- グローバル: `~/.config/opencode/skills/xlsm-prep` / `~/.cursor/skills/xlsm-prep`
