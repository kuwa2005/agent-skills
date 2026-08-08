"""抽出成果物 → 設計書13種（Markdown）生成。"""
import os

from md_utils import demote, insert_toc, strip_toc

DOC_SPECS = [
    ("01_提案書.md", "提案書", "提案"),
    ("02_要件定義書.md", "要件定義書", "要件"),
    ("03_外部設計書_基本設計.md", "外部設計書（基本設計）", "外部設計"),
    ("04_内部設計書_詳細設計.md", "内部設計書（詳細設計）", "内部設計"),
    ("05_プログラム設計書.md", "プログラム設計書", "プログラム"),
    ("06_テスト仕様書.md", "テスト仕様書", "テスト"),
    ("07_業務フロー.md", "業務フロー", "フロー"),
    ("08_画面設計書.md", "画面設計書", "画面"),
    ("09_マクロ仕様.md", "マクロ仕様", "マクロ"),
    ("10_VBA仕様.md", "VBA仕様", "VBA"),
    ("11_機能一覧.md", "機能一覧", "機能"),
    ("12_操作マニュアル.md", "操作マニュアル", "操作"),
    ("13_説明書.md", "説明書", "説明"),
]


def doc_name(i, base):
    return DOC_SPECS[i - 1][0]


def _read(out_tmp, name):
    path = os.path.join(out_tmp, name)
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    return "（抽出成果物なし）"


def _embed(out_tmp, name):
    """抽出成果物を設計書へ埋め込む（目次除去 + 見出しを 2 段深くする）。"""
    return demote(strip_toc(_read(out_tmp, name)))


def _index_md(base, out_tmp, out_docs):
    lines = [f"# {base} 設計書一覧", "",
             "> access2spec による静的解析結果。推論部分は（推定）と明記している。", "",
             "## 設計書（13種）", ""]
    for fname, title, _kind in DOC_SPECS:
        lines.append(f"- [{fname}]({fname}) — {title}")
    lines += ["", "## 抽出成果物（解析の中間成果物）", "",
              "- 設計書の根拠データ。再解析時は extract.py で再生成される。", ""]
    for name in sorted(os.listdir(out_tmp)):
        if name.endswith(".md"):
            rel = os.path.relpath(os.path.join(out_tmp, name), out_docs)
            lines.append(f"- [{name}]({rel})")
    lines += ["", "## 生成方法", "",
              "- `extract.py <file.mdb>` で抽出成果物を生成",
              "- `docs_gen.py <file.mdb>` で設計書13種と本 index.md を生成", ""]
    return "\n".join(lines)


def _er_diagram(rels):
    """リレーション実測から ER 図（mermaid）を生成する（事実ベース）。"""
    lines = ["```mermaid", "erDiagram", "    %% リレーション定義（解析事実）"]
    for r in rels:
        lines.append(f"    {r['table']} ||--o{{ {r['referenced']} : \"参照\"")
    lines.append("```")
    return "\n".join(lines)


def generate(reader, out_tmp, out_docs):
    from inventory import classify
    from vba_extract import extract_relationships

    base = os.path.splitext(os.path.basename(reader.path))[0]
    os.makedirs(out_docs, exist_ok=True)
    inv = classify(reader)
    c = inv["counts"]
    rels_res = extract_relationships(reader, out_tmp)
    er = _er_diagram(rels_res["rows"])

    file_info = _embed(out_tmp, "00_file_info.md")
    queries = _embed(out_tmp, "30_queries.md")
    forms = _embed(out_tmp, "40_forms.md")
    reports = _embed(out_tmp, "50_reports.md")
    macros = _embed(out_tmp, "60_macros.md")
    vba = _embed(out_tmp, "70_vba.md")
    rels = _embed(out_tmp, "25_relationships.md")
    refs = _embed(out_tmp, "80_cross_references.md")
    tables = _embed(out_tmp, "20_tables.md")

    vba_modules = [r["Name"] for r in inv["rows"] if r["label"] == "VBAモジュール"]
    vba_modules_list = "\n".join(f"- {n}" for n in vba_modules) or "- （VBAモジュールオブジェクトなし）"
    rel_extract_log = os.path.relpath(os.path.join(out_tmp, "extract_log.md"), out_docs)

    docs = {
        "01_提案書.md": f"""# {base} 提案書

> 本ドキュメントは access2spec による静的解析の結果に基づく。業務の背景・課題は解析事実から推論した内容を含む（推定）。

## 1. 現状分析（解析事実）
{file_info}

## 2. 現状の課題（推定）
- 業務ロジックが Access 内のクエリ・マクロに分散している（推定）。
- VBA ソースがないため、処理の追跡はクエリ・マクロ・フォームの構造解析に依存する（推定）。
- ドキュメントが存在しない場合、再構築（リプレース）時の要件把握にコストがかかる（推定）。

## 3. 提案システムの構成
- 解析で把握した機能・データ構造を、新システムの要件・設計の起点とする。
- 移行対象: テーブル {c.get('テーブル', 0)} 件・クエリ {c.get('クエリ', 0)} 件・フォーム {c.get('フォーム', 0)} 件・レポート {c.get('レポート', 0)} 件・マクロ {c.get('マクロ', 0)} 件。

## 4. 移行方針（推定）
- データ移行: テーブル構造・リレーションを維持した移行を推奨（推定）。
- ロジック移行: クエリ SQL は再構築結果（[04_内部設計書_詳細設計.md](04_内部設計書_詳細設計.md)）を基に、新技術へ翻訳する（推定）。

## 5. 工数観点の要因分解
- クエリ数・フォーム数・レポート数・マクロ数に応じた工数見積りを推奨（推定）。
""",
        "02_要件定義書.md": f"""# {base} 要件定義書

> 機能要件は解析事実（機能一覧・画面・クエリ）から導出（推定）。

## 1. 機能要件
- 解析で確認した機能は [11_機能一覧.md](11_機能一覧.md) を参照。各機能のインプット・処理・アウトプットは画面・クエリ・マクロの解析結果から導出する（推定）。
- 主要機能（推定）:
  - 顧客・売上管理（売上伝票テーブル等）
  - 売上分析（月次・年次・商品区分別・Staff別の集計クエリ）
  - 顧客コミュニケーション（ご無沙汰リスト・メール送信・はがき宛名）

## 2. 非機能要件（推定）
- データ保全: リレーション整合性の維持
- 性能: 集計クエリの応答性（マクロ駆動のため低負荷前提）

## 3. 業務ルール（推定）
- 売上伝票は商品区分・menu・Staff の組み合わせで集計される（クエリ構造から推定）。
- 目標設定は年月・Staff別（目標設定テーブルの構造から推定）。

## 4. 要確認事項
- マクロのアクション定義（Access での確認が必要）
- フォームの完全なコントロール定義（Access での確認が必要）
- 業務フロー・運用ルールの実担当者への確認
""",
        "03_外部設計書_基本設計.md": f"""# {base} 外部設計書（基本設計）

## 1. システム構成
- Access クライアント（フォーム・レポート・マクロ駆動）単体構成（推定）。

## 2. 画面構成（フォーム一覧）
{forms}

## 3. 帳票一覧（レポート一覧）
{reports}

## 4. データモデル概要
{er}
{rels}

## 5. 機能-画面-帳票対応表
- 機能一覧（[11_機能一覧.md](11_機能一覧.md)）の各機能について、起動フォーム・関連帳票を対応付ける（推定・Access での確認が必要）。
""",
        "04_内部設計書_詳細設計.md": f"""# {base} 内部設計書（詳細設計）

## 1. テーブル定義
{tables}

## 2. リレーション
{rels}

## 3. クエリ定義（SQL 再構築）
> SQL は MSysQueries ツリーからの再構築結果。復元不能のものは「（復元不能・要Accessでの確認）」と明記。
{queries}
""",
        "05_プログラム設計書.md": f"""# {base} プログラム設計書

> 本システムは VBA ソースを持たないマクロ駆動型のため、処理の設計はクエリ・マクロ・フォーム構造から復元する（推定）。

## 1. 処理フロー（マクロ駆動）
- フォーム → マクロ → クエリ → テーブル の連鎖で処理が構成される（推定）。
{refs}

## 2. 各処理の疑似コード
- 各クエリの処理内容は [04_内部設計書_詳細設計.md](04_内部設計書_詳細設計.md) の SQL を参照。
- マクロのアクション定義は Access での確認が必要（要Access確認・推定）。

## 3. フォームイベント → 処理の対応
- フォーム・コントロールのイベントは Access での確認が必要（要Access確認・推定）。
""",
        "06_テスト仕様書.md": f"""# {base} テスト仕様書

> テストケースは解析事実から導出（推定）。移行先システムでのテスト実施を想定。

## 1. 機能別テストケース
- 正常系: 各フォームからの登録・更新・削除・検索・集計表示
- 異常系: 必須項目未入力・該当データなし・参照整合性違反
- 具体的な入力・期待値は Access での確認が必要（要Access確認・推定）。

## 2. データ移行テスト
- テーブル数・行数の突合（抽出成果物 data/*.csv と新システム DB の比較）
- リレーション整合性の検証

## 3. 非機能テスト（推定）
- 集計クエリの性能確認・大量データ時の応答性
""",
        "07_業務フロー.md": f"""# {base} 業務フロー

> フローはフォーム・クエリ・マクロの構造解析から推定。

## 1. 業務プロセス
```mermaid
flowchart TD
    A[業務開始] --> B[顧客来店・施術]
    B --> C[売上伝票入力（フォーム）]
    C --> D[売上データ登録（テーブル）]
    D --> E[集計処理（クエリ: 月次・年次・商品区分別）]
    E --> F[売上分析レポート出力]
    F --> G[目標達成確認（目標設定テーブル）]
    G --> H[次月目標設定]
    H --> I[業務終了]
```

## 2. 操作手順の要約
- 各フォームの起動・入力・実行手順は [12_操作マニュアル.md](12_操作マニュアル.md) を参照（推定）。

## 3. 参照連鎖（解析事実）
{refs}
""",
        "08_画面設計書.md": f"""# {base} 画面設計書

> コントロール定義は LvProp ブロブの文字列抽出による推定。完全なレイアウトは Access での確認が必要（推定）。

## フォーム一覧・データソース
{forms}

## レイアウト概要
- 各フォームの配置・コントロール名は抽出文字列から推定し、Access での実確認を推奨（推定）。
""",
        "09_マクロ仕様.md": f"""# {base} マクロ仕様

> 本ツールではマクロのアクション定義を抽出できない（LvProp 不在）。アクション・引数は Access での確認が必要（要Access確認）。

## 1. マクロ一覧（解析事実）

{macros}

## 2. 制約事項
- マクロのアクション・引数は Access での確認が必要（要Access確認・推定）。
""",
        "10_VBA仕様.md": f"""# {base} VBA仕様

{vba}

## モジュール一覧（解析事実）
- VBA モジュールオブジェクト数: {len(vba_modules)} 件
{vba_modules_list}
- 各モジュールのソースは MSysModules2 不在のため抽出できない（要Access確認・推定）。
""",
        "11_機能一覧.md": f"""# {base} 機能一覧

> 機能はオブジェクト構造から導出（推定）。各機能の起動元・関連オブジェクトを列挙。

## 機能一覧表

| 機能（推定） | 種別 | 関連フォーム | 関連クエリ | 関連マクロ |
|---|---|---|---|---|
| 売上伝票入力 | 入力 | 売上伝票フォーム（推定） | 売上伝票フォーム用クエリ（推定） | Data更新マクロ（推定） |
| 顧客管理 | 入力・照会 | 顧客名簿系フォーム（推定） | 顧客系クエリ（推定） | - |
| 売上分析 | 照会・集計 | 売上分析系フォーム（推定） | 6…年…売上高系クエリ（推定） | - |
| 目標設定 | 入力・集計 | 目標設定系フォーム（推定） | 目標系クエリ（推定） | - |
| レポート出力 | 出力 | - | 7…ご無沙汰リスト系クエリ（推定） | - |

## オブジェクト内訳（解析事実）
- テーブル {c.get('テーブル', 0)} 件・クエリ {c.get('クエリ', 0)} 件・フォーム {c.get('フォーム', 0)} 件・レポート {c.get('レポート', 0)} 件・マクロ {c.get('マクロ', 0)} 件
""",
        "12_操作マニュアル.md": f"""# {base} 操作マニュアル

> 操作手順はフォーム・マクロ・クエリの構造から推定。

## 1. 基本操作（推定）
1. Access で本ファイルを開く。
2. メインフォーム（管理フォーム）から各業務フォームを起動する（推定）。
3. 売上伝票入力: 伝票フォームで顧客・商品・数量を入力し、マクロでデータ更新する（推定）。
4. 売上分析: 分析フォームで年・月・商品区分を指定し、集計クエリを実行する（推定）。
5. レポート: ご無沙汰リスト等を印刷・メール送信する（推定）。

## 2. 注意事項
- マクロのアクション内容は Access での確認が必要（要Access確認）。
""",
        "13_説明書.md": f"""# {base} 説明書

## 1. ファイル構成
{file_info}

## 2. データ構造の全体像
- 主要テーブル: 売上伝票テーブル・顧客名簿テーブル・商品区分売上IDテーブル・社員名簿テーブル・目標設定テーブル群（解析事実）。
- 詳細は [03_外部設計書_基本設計.md](03_外部設計書_基本設計.md) / [04_内部設計書_詳細設計.md](04_内部設計書_詳細設計.md) を参照。

## 3. 保守・移行の注意点
- クエリ SQL は再構築結果（[04_内部設計書_詳細設計.md](04_内部設計書_詳細設計.md)）を参照。復元不能クエリは Access での確認が必要。
- マクロのアクション定義は Access での確認が必要。
- 抽出ログ: [extract_log.md]({rel_extract_log})
""",
    }

    written = []
    back = "[← 設計書一覧に戻る](index.md)"
    for fname, title, _kind in DOC_SPECS:
        content = docs.get(fname, f"# {base} {title}\n\n（該当なし）\n")
        content = insert_toc(content, back_link=back)
        content += "\n\n" + back + "\n"
        with open(os.path.join(out_docs, fname), "w", encoding="utf-8") as f:
            f.write(content)
        written.append(fname)
    index_path = os.path.join(out_docs, "index.md")
    with open(index_path, "w", encoding="utf-8") as f:
        f.write(insert_toc(_index_md(base, out_tmp, out_docs)))
    written.append("index.md")
    return written


def main(argv=None):
    import argparse
    import sys

    from extract import run_extract

    ap = argparse.ArgumentParser(description="access2spec: 抽出成果物 → 設計書13種生成")
    ap.add_argument("file")
    ap.add_argument("-o", "--out", default=".tmp")
    ap.add_argument("--docs", default=None, help="設計書出力先（既定: <対象名>_設計書/）")
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args(argv)

    from mdb_reader import MdbReader
    reader = MdbReader(args.file)
    base = os.path.splitext(os.path.basename(reader.path))[0]
    out_docs = args.docs or f"{base}_設計書"
    run_extract(args.file, args.out, limit=args.limit)
    files = generate(reader, args.out, out_docs)
    print(f"設計書生成完了: {out_docs}/（{len(files)} ファイル）")
    for f in files:
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())

