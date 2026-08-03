# XLSX / XLSM 保護解除 技術調査資料

> 対象: runlocally「unlock-xlsx」(https://runlocally.app/unlock-xlsx/ja/) と、提供された VBA マクロ
> 日付: 2026-08-01
> 用途: 保護解除ツールを実装する前の技術的調査メモ

---

## 1. 前提知識: OOXML パッケージの構造

XLSX / XLSM は、中身が **XML ファイル群を束ねた ZIP アーカイブ** である。

```
book.xlsx (ZIP)
├── [Content_Types].xml
├── _rels/.rels
└── xl/
    ├── workbook.xml              … ブック全体の設定（workbookProtection がここ）
    ├── _rels/workbook.xml.rels   … シート名→ファイルパスの対応付け
    └── worksheets/
        ├── sheet1.xml            … シート1（sheetProtection がここ）
        └── sheet2.xml
```

| 保護種別 | 保存場所 | 要素名 |
|---|---|---|
| シート編集保護 | `xl/worksheets/sheetN.xml` | `<sheetProtection …>` |
| セル範囲の編集保護 | `xl/worksheets/sheetN.xml` | `<protectedRange …>` / `<protectedRanges>…</protectedRanges>` |
| ブック構造保護（シート移動/削除禁止） | `xl/workbook.xml` | `<workbookProtection …>` |
| 共有ブックのパスワード保護 | `xl/workbook.xml` | `<fileSharing …>` |

### 重要な性質

- シート保護・ブック保護は**暗号化ではなく、平文 XML のフラグ**に過ぎない。
- パスワードは同要素内に埋まった **16bit ハッシュ値**（例: `password="CDEF"`）であり、認証はこのハッシュ比較のみ。
- したがって「保護要素を削除する」だけで、パスワードを知らなくても編集制限を外せる。
- **ただし** これは「開封パスワード（ファイル暗号化）」には使えない。
  - 開封パスワード付きファイルは ZIP ではなく **CFB (Compound File Binary) コンテナ**（先頭 8 バイトが `D0 CF 11 E0 A1 B1 1A E1`）で、中身ごと暗号化されている。

---

## 2. runlocally「unlock-xlsx」の実装分析

### 2.1 概要

- 構成: Astro + Preact + TypeScript + `@zip.js/zip.js`。完全ブラウザ内（クライアントサイド）処理。サーバー送信なし。
- コアロジックは単一ファイル `src/utils/xlsxUnlockEngine.ts`（MIT ライセンス、公開）。

### 2.2 処理フロー

1. **ファイルシグネチャ検査** (`assertZipPackage`)
   - 先頭 8 バイトが CFB シグネチャ → 「開封パスワード付き」として拒否 (`errOpenPasswordProtected`)
   - ZIP シグネチャ (`50 4B 03 04` / `05 06` / `07 08`) 以外 → 非対応として拒否 (`errInvalidWorkbook`)
2. **ZIP 読み込み** — `ZipReader(new BlobReader(file))` で全エントリ取得
   - `entry.encrypted === true` のエントリがある場合も「開封パスワード付き」として拒否
3. **対象 XML のパース**
   - `xl/workbook.xml` → DOM 化し `<workbookProtection>` を検出
   - `xl/_rels/workbook.xml.rels` → リレーションID と Target を読み、シート名→パッケージ内パスの対応を解決（シート名を結果表示するため）
4. **再パッケージング**（全エントリ走査）
   - `xl/workbook.xml` → `<workbookProtection>` を **DOM から全削除**
   - `xl/worksheets/sheet*.xml` → `<sheetProtection>` を **DOM から全削除**
   - それ以外のエントリ → **バイト列そのままコピー**（タイムスタンプ・コメント・属性も維持）
5. **出力** — 保護を検出した場合のみ `-unlocked.xlsx` として ZIP を書き出し

### 2.3 技術的特徴

- **DOM ベース**: `DOMParser` + `elementsByLocalName()`（ローカル名・プレフィックス除去で要素特定）+ `XMLSerializer` で再直列化。正規表現ではなくパーサ経由なので、属性の順序がどうであれ確実に消せる。
- **他のエントリは無変更**: セル値・書式・VBA バイナリは一切触らない。パッケージを壊さない設計。
- **対象外**: 開封パスワード / VBA プロジェクト保護 / `<protectedRange>` / `<fileSharing>`（後者2つは処理しない）。

### 2.4 制限

| 項目 | 対応 |
|---|---|
| sheetProtection（シート編集保護） | ✅ 削除 |
| workbookProtection（ブック構造保護） | ✅ 削除 |
| protectedRange（セル範囲保護） | ❌ 未対応 |
| fileSharing（共有ブック保護） | ❌ 未対応 |
| 開封パスワード（CFB 暗号化） | ❌ 拒否（エラー表示） |
| VBA プロジェクト保護 | ❌ 未対応 |
| パスワードの復元・総当たり | ❌ 未実装 |

---

## 3. 提供 VBA マクロの分析

### 3.1 概要

Excel VBA から実行するマクロ。`SaveCopyAs` でアクティブブックを **.zip に変換**し、PowerShell で展開 → 正規表現で保護タグを削除 → Explorer の ZIP 機能で再圧縮 → 拡張子を戻す。

### 3.2 処理フロー

1. **保存確認** — `ActiveWorkbook.FullName` が空なら中断（未保存ファイルは扱えない）
2. **ZIP 変換** — `ActiveWorkbook.SaveCopyAs "<Temp>\<BookName>.zip"`
   - **重要**: `SaveCopyAs` で拡張子を `.zip` に変えても、中身は正しい OOXML ZIP のまま。Excel が保存時に XLSX/XLSM パッケージを作るため、この方法で手軽に ZIP 化できる。
3. **展開** — PowerShell (`System.IO.Compression.ZipFile::OpenRead`) で全エントリを `%TEMP%\TempExtracted` へ書き出し（ディレクトリ構造を維持）
4. **XML 書き換え**（正規表現 `VBScript.RegExp`）
   - `xl/worksheets/*.xml`:
     - 削除: `</?sheetProtection\b[^>]*>` （`sheetProtection` タグ）
     - 削除: `</?protectedRanges?\b[^>]*>` （`protectedRange` / `protectedRanges` タグ）
   - `xl/workbook.xml`:
     - 削除: `</?workbookProtection\b[^>]*>`
     - 削除: `</?fileSharing\b[^>]*>`
   - 書き込みは `ADODB.Stream`（UTF-8）
5. **再圧縮** — Explorer の COM (`Shell.Application` → `CopyHere`) でフォルダ→ZIP
   - コメント: 「`.NET` の `ZipFile` クラスで圧縮すると Excel ファイル構造が崩れる」ため Explorer 方式を採用
   - サイズ変動を監視する `WaitForCopyCompletion` でコピー完了を待つ
6. **後処理** — 一時ファイル削除、保存先フォルダをダイアログで選択、拡張子を元に戻して保存

### 3.3 技術的特徴

- **正規表現ベース** のタグ除去。属性の有無・順序に関わらず `<sheetProtection>` タグ全体（開始/終了）を除去できる。ただし XML としての正当性検証はしない。
- **シート範囲保護 (`protectedRange`) と共有ブック保護 (`fileSharing`) にも対応**している点が、runlocally 版より広い。
- 拡張子を **元 (.xlsx / .xlsm) に戻す**ので、XLSM（マクロ入り）も扱える。VBA プロジェクト自体は変更しないため、マクロは維持される。
- Windows 前提（PowerShell / WScript / Shell.Application / FileSystemObject / ADODB）。

### 3.4 制限・注意点

| 項目 | 対応 |
|---|---|
| sheetProtection | ✅ 正規表現で削除 |
| protectedRange / protectedRanges | ✅ 正規表現で削除 |
| workbookProtection | ✅ 正規表現で削除 |
| fileSharing | ✅ 正規表現で削除 |
| 開封パスワード（CFB 暗号化） | ❌ 対応外（Excel が開けないとそもそもマクロ実行不可） |
| VBA プロジェクト保護 | ❌ 未対応 |
| パスワードの復元・総当たり | ❌ 未実装 |
| 正規表現による副作用 | ⚠ コメント内や文字列内に同名タグがあっても削除対象（実用上ほぼ無害） |
| 再圧縮の再現性 | ⚠ Explorer の ZIP は圧縮方式・タイムスタンプを独自設定するため、厳密なバイト再現はしない |

---

## 4. 2 実装の比較

| 観点 | runlocally (web) | VBA マクロ |
|---|---|---|
| 実行環境 | ブラウザ（全クライアントサイド） | Excel VBA + PowerShell（Windows のみ） |
| ZIP 読込 | zip.js（`ZipReader`) | PowerShell `ZipFile` / `SaveCopyAs` |
| ZIP 書込 | zip.js（`ZipWriter`） | Explorer `Shell.Application.CopyHere` |
| XML 操作 | DOM（DOMParser / XMLSerializer） | 正規表現（VBScript.RegExp） |
| sheetProtection | ✅ | ✅ |
| workbookProtection | ✅ | ✅ |
| protectedRange | ❌ | ✅ |
| fileSharing | ❌ | ✅ |
| 拡張子 | `.xlsx`（`-unlocked.xlsx`） | 元のまま（`（保護解除済）.xlsm` 等） |
| XLSM 対応 | ✅ 入力可（出力は xlsx） | ✅ 入力可・出力も xlsm |
| 開封パスワード検知 | ✅ シグネチャで明示拒否 | 前提として開ける必要あり |
| 他エントリへの影響 | 無変更（バイトコピー） | 展開→再圧縮のため再圧縮差分あり |
| 非 Windows | 可 | 不可 |

### 補足: なぜどちらも「パスワードを解かずに」解除できるのか

両者とも、パスワードハッシュの照合・復元は一切行っていない。保護が機能するのは「Excel が XML に `<sheetProtection>` 等の要素があるのを見て、編集操作をブロックする」ためであり、**要素を消せばブロック理由がなくなる**。パスワードハッシュが残っていようがいまいが、参照されなくなる。

---

## 5. ツール実装への示唆

VBA マクロの知見を踏まえ、汎用ツール（Python 等）で実装する場合の要点。

### 5.1 削除対象と正規表現（マクロと同等の挙動）

| 対象ファイル | 削除パターン |
|---|---|
| `xl/worksheets/*.xml` | `</?sheetProtection\b[^>]*>` |
| `xl/worksheets/*.xml` | `</?protectedRanges?\b[^>]*>` |
| `xl/workbook.xml` | `</?workbookProtection\b[^>]*>` |
| `xl/workbook.xml` | `</?fileSharing\b[^>]*>` |

### 5.2 実装上の推奨

1. **ZIP は破壊的に再読込・再書込せず、エントリ単位で書き換える**
   - 対象 XML のみテキスト置換し、それ以外のエントリはバイト列のままコピー（runlocally 方式）。再圧縮による破損リスクを減らせる。
2. **正規表現より XML パーサを優先**（Python なら `lxml` 等）
   - 属性に順序違い・名前空間プレフィックス（`x:sheetProtection`）があっても確実。
   - ただし実務ではシンプルな正規表現で十分なケースが多い（VBA マクロも正規表現で実績あり）。
3. **CFB 検知を入れる**
   - 先頭 8 バイト `D0 CF 11 E0 A1 B1 1A E1` なら開封パスワード付きとして明確にエラー報告。
4. **拡張子を維持**
   - `.xlsm` なら `.xlsm` のまま出力（VBA 部分は触らないのでマクロは保持される）。
   - `.xlsx` → `.xlsx`。必要に応じ `-unlocked` 等の接尾辞。
5. **置換前後の検証**
   - 置換後に対象タグが 0 件になったことを確認。
   - 少なくとも `[Content_Types].xml` は変更しない。
6. **パスワードの復元はしない**（仕様として明記）

### 5.3 実装順序（推奨タスク）

1. ZIP を開き、エントリ一覧・CFB 検知
2. `workbook.xml` と各 `worksheets/sheet*.xml` の読み込み
3. 対象 4 タグの除去（パーサ or 正規表現）
4. 対象外エントリはバイトコピーで再書込
5. 拡張子維持で出力、保護検出数のサマリ表示
6. 単体テスト（シート保護のみ / ブック保護のみ / 両方 / 保護なし / CFB 拒否）

---

## 6. 使用上の注意（法的・技術的）

- 本手法は他人のファイルを「ハック」するものではなく、**オープンな OOXML 仕様に基づく保護フラグの除去**。
- 対象は「自分が所有する、または変更を許可されたブック」に限定すること（runlocally も明記）。
- 開封パスワード（暗号化）の解除は本手法では不可。総当たり等は行わないこと。
- VBA プロジェクトの保護解除は「既知パスワードへのキー移植」方式（第8章）で実装。対象は自分が所有する、または変更を許可されたブックに限定すること。

---

## 7. 参考リンク

- ツール本体: https://runlocally.app/unlock-xlsx/ja/
- ソースコード: https://github.com/GeppettoAndRomero/unlock-xlsx (`src/utils/xlsxUnlockEngine.ts`)
- OOXML 仕様: ECMA-376（`sheetProtection` / `workbookProtection` / `protectedRange` / `fileSharing` のスキーマ定義）

---

## 8. VBA プロジェクト保護の解除（キー移植方式）— 追加実装

> XLSM の `xl/vbaProject.bin` に設定される「プロジェクトの表示のロック」を、**既知パスワードの有効な暗号化ハッシュに置換**することで解除する実装。

### 8.1 保存場所

シート保護系とは異なり、VBA 保護は XML ではなく **`xl/vbaProject.bin`**（OLE/CFB コンテナ）内の **PROJECT ストリーム** に保存される。

```
PROJECT ストリーム（UTF-8 テキスト混在のバイナリ）
  ID="{00000000-0000-0000-0000-000000000000}"   ← 保護ありを示すゼロGUID
  DPB="<hex>"   … パスワードハッシュ（MS-OVBA 2.4.3.2 PasswordHashEncrypted）
  CMG="<hex>"   … 一致判定用の既定値ハッシュ
  GC="<hex>"    … 一致判定用の既定値ハッシュ
```

### 8.2 方式の変遷と結論

| 方式 | 内容 | 最新Excelでの結果 |
|---|---|---|
| **タグ削除** | シート保護と同様に `DPB=` 行を削除 | ❌ ストリーム構造が壊れ「vbaProject.bin は無効です」→マクロ消去リスク |
| **リネーム** | `DPB=` → `DPx=` / `CMG=` → `CMx=` / `GC=` → `Gx=`（無効化） | ❌ Office 2016/2019/2021/365 では破損扱い（有効な 16進値が必須） |
| **キー移植（採用）** | `DPB`/`CMG`/`GC` を**既知パスワードの有効な値へ再生成・同一文字数で置換** | ✅ 構造・長さを保つため Excel が正常に開ける |

### 8.3 キー移植の仕組み

1. 既存の `DPB` から 16進文字数 `Len` を取得し、`(Len - 72) / 2` を「無視バイト数」として **Seed** を選定
   - 条件: `(Seed & 6) / 2 == 無視バイト数`（`CMG` は `(Len-22)/2`、`GC` は `(Len-16)/2`）
   - これにより再生成値のバイト長が元と**必ず一致**する
2. 既知パスワード（本実装では `1234`、任意に変更可）と固定 salt から 29 バイトのハッシュ構造を生成
   - `0xFF` + grbit（24bit: null位置ビットマップ）+ salt(4B) + SHA1(MBCSパスワード+salt)(20B) + `0x00`
3. **DPB/CMG/GC をそれぞれ暗号化**（`Encode` / `EncodeCMG(0)` / `EncodeGC(0xFF)`）
   - ストリーム暗号風の Xor 状態機械（Seed / Version=2 / プロジェクトキー、無視バイト挿入、LE 長、データ）
   - ヘッダ: `Seed` `Seed^2`（Version） `プロジェクトキー^Seed`
4. 元の `DPB="..."` `CMG="..."` `GC="..."` を、生成した値で**同一文字数**のまま置換

結果: 保護は維持されるがパスワードは既知値（`1234`）になり、VBA プロジェクトを開ける。構造を壊さないため最新 Excel でも破損しない。

### 8.4 実装上の注意

- 元の 16進長が `(Len - base) / 2 > 3` になるケース（無視バイト数が3超）は `Seed & 6` で表現不能のため**非対応**（`unsupported VBA hash length`）。
- 単純な「タグ削除」は最新 Excel では無効（破損→マクロ消失の危険）のため、**必ず有効値への置換**を行うこと。
- 再生成には VBAMacroPWD（waleedassar/VBAMacroPWD）の `Encode` / `EncodeCMG` / `EncodeGC` / `CreateHashStructure` を JS 移植して検証済み（504 パターンの入出力一致）。

