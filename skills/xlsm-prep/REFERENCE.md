# Excel 作業コピー前処理 — メモ

`scripts/prepare.py` が行うことの技術メモ。ユーザー向け説明ではない。

## 目的

マクロ解析・仕様化の前に、OOXML（`.xlsx` / `.xlsm`）をツールが読みやすい作業コピーにする。

## パッケージ概要

XLSX / XLSM は ZIP + XML のパッケージ。シートやブックの「編集ロック」は、多くの場合 XML 上のフラグ要素として存在する。作業コピーではこれらを取り除き、構造データと VBA ストリームを取り出しやすくする。

VBA を含むブックでは `xl/vbaProject.bin` に閲覧制限用のメタが付くことがある。前処理では解析ツールが読めるよう正規化する（ファイル全体の暗号化とは別問題）。

## 対象外

- `.xls`（Excel 97-2003 バイナリ）— 先に `.xlsm` へ実変換が必要
- ファイル全体の暗号化（CFB コンテナ）— 中身を読めないため前処理不可
- パスワードの推測・総当たり

## 使い方

```bash
python3 scripts/prepare.py input.xlsm -o .tmp/input.work.xlsm -q
python3 scripts/prepare.py input.xlsm --detect-only
```

通常は `xlsm2spec` の抽出処理から自動実行される。
