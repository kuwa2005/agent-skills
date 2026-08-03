# Workbook preparation notes (upstream reference)

XLSX / XLSM の保護をブラウザ内だけで解除できるツールです。ファイルのアップロードやサーバー通信は一切行わず、すべてローカル（クライアントサイド）で処理します。

## 特徴

- **単一ファイル (`index.html`)** — サーバー起動不要。ブラウザで開くだけで動作
- **ドラッグ＆ドロップ → 自動検出 → チェックボックスで選択 → 自動ダウンロード**
- **外部ライブラリなし** — 自作 ZIP リーダ/ライタ + `CompressionStream` / `DecompressionStream`
- 対応する保護と解除方式:

| 保護種別 | 保存場所 | 解除方式 |
|---|---|---|
| シート編集保護 | `xl/worksheets/*.xml` の `<sheetProtection>` | 要素を削除 |
| セル範囲の編集保護 | `xl/worksheets/*.xml` の `<protectedRange(s)>` | 要素を削除 |
| ブック構造保護 | `xl/workbook.xml` の `<workbookProtection>` | 要素を削除 |
| 共有ブック保護 | `xl/workbook.xml` の `<fileSharing>` | 要素を削除 |
| VBA プロジェクト保護 | `xl/vbaProject.bin` 内の `DPB` / `CMG` / `GC` | キー移植（既知パスワードの有効な値へ置換） |

## 使い方

1. `index.html` を Chrome / Edge / Firefox（113+）で開く
2. `.xlsx` / `.xlsm` ファイルをドラッグ＆ドロップ（またはクリックで選択）
3. 検出された保護をチェックボックスで選択（初期状態では全て選択済み）
4. 「選択した保護（N項目）を解除してダウンロード」をクリック
5. `元ファイル名-unlocked.xlsx` / `.xlsm` が自動的にダウンロードされる

## .xls（Excel 97-2003）を解除する場合

`.xls` は本ツールの対象外（ZIP ではなく OLE/CFB バイナリ形式のため）ですが、**Excel で `.xlsm` に変換してから本ツールに渡す**ことで解除できます。変換後も保護はすべて保持され、本ツールが対応する OOXML 形式になるためです。

> 利用目的が「過去の `.xls` を今どきの Excel で開けるようにする」場合、変換後に `.xlsm` として扱うことに問題はありません。本ツールで解除した結果は `.xlsm` のままダウンロードされ、そのまま Excel で開いて編集できます。

1. `.xls` を Excel で開く
2. 「名前を付けて保存」→ ファイルの種類で **`.xlsm`（マクロ有効ブック）** を選択（または LibreOffice: `soffice --headless --convert-to xlsm file.xls`）
3. 保存した `.xlsm` を本ツールにドラッグ＆ドロップし、通常どおり解除する

> 拡張子を `.xls` → `.xlsm` に**リネームするだけでは無効**です（中身が CFB のままのため）。必ず Excel / LibreOffice による実変換を行ってください。

| 変換前 (.xls / BIFF) | 変換後 (.xlsm / OOXML) | 本ツールでの解除 |
|---|---|---|
| シート保護 `PROTECT` レコード | `<sheetProtection>` | ✅ 要素削除 |
| ブック構造保護 `PROTECT`（グローバル） | `<workbookProtection>` | ✅ 要素削除 |
| 共有保護 `PROT4REV` | `<fileSharing>` | ✅ 要素削除 |
| VBA 保護（CFB 内 DPB） | `vbaProject.bin` の `DPB`/`CMG`/`GC` | ✅ キー移植 |

## VBA プロジェクト保護について

- VBA 保護はシート保護と違い、XML ではなく `vbaProject.bin` 内の暗号化ハッシュ（`DPB` 等）に保存されています。
- 単純な削除や `DPB=` → `DPx=` へのリネームは **Office 2016/2019/2021/365 では「vbaProject.bin は無効です」という破損エラー**になり、マクロが消える危険があります。
- 本ツールは **キー移植方式**（MS-OVBA 仕様に基づき、既知パスワードの有効なハッシュ構造を再生成して同一文字数で置換）で解除します。構造とバイト長を保つため、最新の Excel でも破損しません。
- **解除後のパスワードは `1234`** です。Excel で開く → Alt+F11 → VBAProject を開く → パスワード `1234` → VBAProject のプロパティ → 保護 → 「プロジェクトの表示のロック」のチェックを外して保存すると完全に解除できます。
- 元のハッシュ長によっては変換できない場合があります（対応外の場合は VBA のみスキップし、他の保護は解除します）。

## 対応外

- `.xls`（Excel 97-2003 / OLE-CFB バイナリ）— 本ツールでは処理しません（[.xls の解除方法](#xlsエクセル97-2003を解除する場合) を参照）
- 開封パスワード（ファイル暗号化 / CFB コンテナ）— シグネチャ検知で明示的にエラー表示します
- パスワードの復元・総当たり

## 注意

- 使用は「自分が所有する、または変更を許可されたブック」に限定してください。
- 重要なファイルは必ずコピーでお試しください。

## テスト

```bash
# テスト用フィクスチャ生成（tests/fixtures/ 以下に xlsx / xlsm を作成）
python3 tests/create_fixture.py

# 解除後のファイルの VBA パスワードが 1234 であることを検証
python3 tests/verify_vba_password.py 解除したファイル.xlsm
# → "MATCH" と表示されれば成功
```

- 暗号化処理（SHA1 / `CreateHashStructure` / `Encode` / `EncodeCMG` / `EncodeGC`）は VBAMacroPWD（waleedassar/VBAMacroPWD）の Python 実装をリファレンスとして、504 パターンの入出力一致を確認済みです。
- ブラウザでの動作は headless Chromium による E2E テストで確認しています（検出 / 解除 / ダウンロード / クリーンファイルの扱い）。

## 技術資料

- [調査資料_xlsx_xlsm_保護解除.md](./調査資料_xlsx_xlsm_保護解除.md) — 保護の仕組み・runlocally 版と VBA マクロの分析・VBA キー移植方式の詳細

## 参考

- [waleedassar/VBAMacroPWD](https://github.com/waleedassar/VBAMacroPWD) — VBA パスワード操作用 Python スクリプト（キー移植方式のアルゴリズムの元）
- [runlocally unlock-xlsx](https://runlocally.app/unlock-xlsx/ja/) — 同種のブラウザツール（シート系保護のみ対応）
- MS-OVBA 仕様（2.4.3.2 PasswordHashEncrypted 等）
