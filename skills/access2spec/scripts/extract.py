#!/usr/bin/env python3
"""access2spec 抽出パイプライン: MDB → ./.tmp/ 抽出成果物。

使い方: python extract.py <file.mdb> [-o out_dir] [--limit N]
"""
import argparse
import datetime
import os
import sys

from mdb_reader import MdbReader
from inventory import classify, forms_from_sq
from md_utils import insert_toc
from table_extract import extract_tables
from sql_reconstruct import reconstruct
from blob_decompile import extract_forms, extract_reports, extract_macros
from vba_extract import extract_vba, extract_relationships
from cross_references import extract_cross_references


def run_extract(mdb_path, out_dir, limit=100):
    warnings = []
    reader = MdbReader(mdb_path)
    ext = os.path.splitext(mdb_path)[1].lower()
    # ACCDB/ACCDE は mdbtools が JET4 中心のため未実機検証・MDE は VBA ソースが除去済み
    if ext in (".accdb", ".accde"):
        warnings.append("ACCDB は未実機検証（mdbtools は JET4 中心・要Access確認）")
    if ext == ".mde":
        warnings.append("MDE は VBA ソースがコンパイル除去済みのため VBA 仕様書は構造情報のみ")
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "data"), exist_ok=True)

    inv = classify(reader)
    vba = extract_vba(reader, out_dir)
    tbl = extract_tables(reader, out_dir, limit=limit)
    rels = extract_relationships(reader, out_dir)
    qres = reconstruct(reader, out_dir)
    forms_res = extract_forms(reader, out_dir)
    reports_res = extract_reports(reader, out_dir)
    macros_res = extract_macros(reader, out_dir)
    extract_cross_references(reader, out_dir)
    sq_forms = forms_from_sq(reader)

    summary = {
        "tables": len(inv["tables"]),
        "queries": qres["total"],
        "query_ok": qres["ok"],
        "forms": forms_res["total"],
        "reports": reports_res["total"],
        "macros": macros_res["total"],
        "vba": "あり" if vba["present"] else "なし（マクロ駆動）",
        "relationships": rels["total"],
    }
    for q in qres["queries"]:
        if not q["ok"]:
            warnings.append(f"クエリ SQL 復元不能: {q['name']}")

    lines = ["# ファイル情報", "",
             f"- ファイル: {os.path.basename(mdb_path)}",
             f"- パス: {os.path.abspath(mdb_path)}",
             f"- サイズ: {os.path.getsize(mdb_path)} バイト",
             f"- Jet バージョン: {reader.version()}",
             f"- 抽出日時: {datetime.datetime.now().isoformat()}",
             "", "## オブジェクト数サマリ", ""]
    for k, v in summary.items():
        lines.append(f"- {k}: {v}")
    lines += ["", "## システムテーブル", "",
              "- " + ", ".join(reader.list_all_objects()), ""]
    with open(os.path.join(out_dir, "00_file_info.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))

    lines = ["# オブジェクト棚卸し", "", "## 分類内訳", ""]
    for k, v in sorted(inv["counts"].items()):
        lines.append(f"- {k}: {v}")
    lines += ["", f"## ~sq_f 親参照から復元したフォーム名（{len(sq_forms)} 件）", ""]
    for n in sorted(sq_forms):
        lines.append(f"- {n}")
    lines += ["", "## 全オブジェクト", ""]
    for row in inv["rows"]:
        hidden = "（隠れ~sq）" if row.get("~sq") else ""
        lines.append(f"- [{row['label']}{hidden}] {row['Name']} (Id={row['Id']}, Type={row['Type']}, 更新={row.get('DateUpdate','')})")
    with open(os.path.join(out_dir, "10_object_inventory.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))

    lines = ["# テーブル定義", "", f"- テーブル数: {len(tbl['schema'])}", ""]
    for tname, cols in tbl["schema"].items():
        lines += [f"## {tname}（行数: {tbl['row_counts'].get(tname, '?')}）", "",
                  "| 列名 | 型 | サイズ | 必須 |", "|---|---|---|---|"]
        for c in cols:
            lines.append(f"| {c['name']} | {c['type']} | {c['size'] or '-'} | {'✓' if c['required'] else ''} |")
        lines.append("")
    with open(os.path.join(out_dir, "20_tables.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))

    log = ["# 抽出ログ\n", f"- 対象: {os.path.abspath(mdb_path)}", f"- 日時: {datetime.datetime.now().isoformat()}", ""]
    log.append("## 警告\n")
    if warnings:
        for w in warnings:
            log.append(f"- [WARN] {w}")
    else:
        log.append("- なし")
    log.append("\n## 注記\n")
    log.append("- マクロのアクション定義は抽出不能（要Access確認）。")
    log.append("- フォーム/レポートの完全なコントロール定義は Access での確認が必要（推定）。")
    log.append("- クエリ SQL は MSysQueries ツリーから再構築した。")
    with open(os.path.join(out_dir, "extract_log.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(log) + "\n")

    return {"ok": not warnings or len(warnings) < 50, "summary": summary,
            "warnings": warnings, "files": os.listdir(out_dir)}


def main(argv=None):
    ap = argparse.ArgumentParser(description="access2spec: MDB → 設計書材料の抽出")
    ap.add_argument("file")
    ap.add_argument("-o", "--out", default=".tmp")
    ap.add_argument("--limit", type=int, default=100)
    args = ap.parse_args(argv)
    res = run_extract(args.file, args.out, limit=args.limit)
    print(f"抽出完了: {args.file}")
    for k, v in res["summary"].items():
        print(f"  {k}: {v}")
    if res["warnings"]:
        print(f"警告 {len(res['warnings'])} 件（extract_log.md 参照）")
    return 0 if res["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
