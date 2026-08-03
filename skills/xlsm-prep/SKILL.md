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
