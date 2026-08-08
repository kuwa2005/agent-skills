---
name: access2spec
description: MS Access（.mdb/.mde/.accdb）を静的解析し、設計書13種（提案書・要件定義書・外部設計書・内部設計書・プログラム設計書・テスト仕様書・業務フロー・画面設計書・マクロ仕様・VBA仕様・機能一覧・操作マニュアル・説明書）を Markdown で生成する。XLSM は xlsm2spec と連携。
---

# access2spec

MS Access 資産 → 設計書一式（Markdown）生成スキル。

## 前提
- mdbtools（apt: `sudo apt install -y mdbtools`）
- Python 3.12 + venv（`python3 -m venv .venv && .venv/bin/pip install access_parser`）
  - access_parser は ACCDB フォールバック用。MDB は mdbtools で解析する。

## 手順
1. 解析対象（.mdb/.mde/.accdb）を指定する。
2. `python scripts/extract.py <file> -o ./.tmp` で抽出（抽出成果物: 00_〜80_ + data/*.csv + extract_log.md）。
3. `python scripts/docs_gen.py <file>` で設計書13種 + `index.md`（一覧・リンク集）を `<対象名>_設計書/` に生成。
4. 全ドキュメントに「## 目次」が付与される（アンカーは GitHub 互換スラッグ）。設計書内の文書参照は相対リンク。
5. 出力を確認し、コード生成エージェントに引き継ぐ（起点: `<対象名>_設計書/index.md`）。

## 抽出の限界（必ず明記する）
- マクロのアクション定義・フォームの完全なコントロール定義は抽出不能 → 「（要Access確認・推定）」を明記。
- クエリ SQL は MSysQueries ツリーからの再構築（復元不能は「（復元不能）」明記）。
- MDE は VBA ソースなし（コンパイル済み）。ACCDB は未実機検証。

## テスト
テスト一式は開発元リポジトリ（https://github.com/kuwa2005/access2spec）に同梱されています（`python3 -m unittest discover -s tests -v`）。このスキルは agent-skills からも配布されます（配布物は SKILL.md + scripts/ のみ）。
