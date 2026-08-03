# OOXML 作業コピー前処理 — 実装メモ

エージェント／メンテ用。公開機能説明ではない。

## OOXML

- ブックは ZIP。シート・ブックの編集ロックは `sheetProtection` / `workbookProtection` 等の XML 要素として付くことが多い
- 前処理では作業コピー上で当該要素を除去し、セル・数式・リレーション等のデータはそのまま残す

## VBA ストリーム

- `xl/vbaProject.bin` に閲覧制限メタ（`DPB` / `CMG` / `GC`）が付く場合がある
- 単純削除はストリーム破損のリスクがあるため、解析ツールが読める有効なメタへ同一長で正規化する
- ファイル全体の暗号化（開封時の暗号化）とは別物

## 実装

- 実装本体: `../scripts/prepare.py`
- xlsm2spec 連携: `../../xlsm2spec/scripts/prepare_workbook.py`（同内容）と `extract.py` からの自動呼び出し
