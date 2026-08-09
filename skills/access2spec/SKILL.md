---
name: access2spec
description: MS Access（.mdb/.mde/.accdb）を静的解析し、設計書13種（提案書・要件定義書・外部設計書・内部設計書・プログラム設計書・テスト仕様書・業務フロー・画面設計書・マクロ仕様・VBA仕様・機能一覧・操作マニュアル・説明書）を Markdown で生成する。XLSM は xlsm2spec と連携。
---

# access2spec

MS Access 資産 → 設計書一式（Markdown）生成スキル。

## 到達点

設計書を読み終えた人が、**Access を開かなくても**次を実行できること:

- どの画面/マクロ/クエリがどのテーブルをどう更新するか説明できる
- 主キー・結合・状態の持ち方を挙げてデータ移行方針を立てられる
- 抽出限界で不明な点を「要 Access 確認」としてヒアリングできる

「テーブルがいくつかある」「フォームで入力する」で止まったら失敗。

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
6. 生成物が抽象的なら、下記の具体性下限・図必須に合わせて **追記・修正**する（スクリプト出力をそのまま納品しない）。

## 具体性の下限（悪い例 / 良い例）

生成・追記する設計書は、悪い例の抽象度を禁止する。

**テーブル説明**

悪い例（不十分）:
> T_Customer は顧客情報を管理します。

良い例（このレベルまで求める）:
> `T_Customer` は取引先1件を表す。主キー `CustomerID`（AutoNumber）。`Status` が 0=見込 / 1=取引中 / 9=停止。受注フォーム `F_Order` のコンボは `Q_CustomerActive`（Status=1）を RowSource にし、受注ヘッダ `T_Order.CustomerID` が参照する。削除はマクロ `mcr_CustomerSoftDelete` が Status=9 に更新（物理 DELETE なし）。

**業務フロー**

悪い例（不十分）:
> 受注登録後に出荷処理を行います。

良い例（このレベルまで求める）:
> 担当はスイッチボードから `F_OrderList` を開き、未出荷（`T_Order.ShipDate IS NULL`）を絞り込む。「出荷確定」はマクロ `mcr_ShipConfirm` → アクションで `Q_ShipUpdate` を実行し `ShipDate=Date()` と在庫 `T_Stock.Qty` を減算。在庫不足時は MsgBox 相当の失敗をログテーブルへ（抽出不能なら「要 Access 確認」）。

## 図必須（文章のみ不可）

次を扱う文書では **mermaid または ASCII を必須**にする。「文章でも図でもよい」は禁止。

| 文書・節 | 必須の図 |
|----------|----------|
| 業務フロー | 画面/マクロ → クエリ/テーブル更新の流れ |
| 外部・内部設計のデータ節 | ER（主テーブル・FK・カーディナリティ） |
| 状態を持つエンティティ | 状態遷移図 |
| 機能一覧の依存 | 機能 → 依存オブジェクトの関係（簡潔で可） |

```
[F_OrderList] --出荷確定--> [mcr_ShipConfirm]
                                 │
                                 v
                          [Q_ShipUpdate]
                           /          \
                          v            v
                   T_Order.ShipDate   T_Stock.Qty--
```

## 抽出の限界（必ず明記する）
- マクロのアクション定義・フォームの完全なコントロール定義は抽出不能 → 「（要Access確認・推定）」を明記。
- クエリ SQL は MSysQueries ツリーからの再構築（復元不能は「（復元不能）」明記）。
- MDE は VBA ソースなし（コンパイル済み）。ACCDB は未実機検証。

## 品質チェックリスト（納品前）

- [ ] index.md から全13種へ辿れる
- [ ] 主要テーブル説明が「〜を管理する」だけで終わっていない
- [ ] 業務フロー・ER・状態のうち該当するものに図がある
- [ ] 抽出不能箇所が「要 Access 確認」として列挙されている
- [ ] XLSM 連携がある場合は xlsm2spec 成果物への参照がある

## テスト
テスト一式は開発元リポジトリ（https://github.com/kuwa2005/access2spec）に同梱されています（`python3 -m unittest discover -s tests -v`）。このスキルは agent-skills からも配布されます（配布物は SKILL.md + scripts/ のみ）。
