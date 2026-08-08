"""VBA 有無の検出・ドキュメントプロパティ・リレーション抽出。"""
import os

from md_utils import insert_toc

VBA_TABLES = ("MSysModules2", "MSysModules")


def detect_vba(reader):
    objs = reader.list_all_objects()
    present = any(t in objs for t in VBA_TABLES)
    note = "VBAソースあり（MSysModules2 を検出）" if present else "VBAソースなし・マクロ駆動型"
    return {"present": present, "modules": [], "note": note}


def extract_vba(reader, out_dir):
    d = detect_vba(reader)
    lines = ["# VBA モジュール", "", "## VBA 有無の判定", "", f"- 判定: {d['note']}", "", "## モジュール一覧", ""]
    if d["present"]:
        lines.append("- モジュール一覧・ソースは MSysModules2 から抽出（要拡張）。")
    else:
        lines.append("- ビジネスロジックはクエリ・マクロ駆動で構成されている（推定）。")
        lines.append("- 空の VBA モジュールオブジェクトのみ存在する場合は、プログラム設計書にその旨を明記する。")
    with open(os.path.join(out_dir, "70_vba.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))
    return d


def extract_doc_props(reader, out_dir):
    """SummaryInfo / UserDefined の mdb-prop 出力を 00_file_info 用素材として保存。"""
    lines = {}
    for name in ("SummaryInfo", "UserDefined", "AccessLayout"):
        out = reader.properties(name)
        kept = [l.strip() for l in out.splitlines()
                if l.strip() and not l.startswith("name:") and "binary data" not in l]
        lines[name] = kept
    path = os.path.join(out_dir, "data", "doc_props.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("# ドキュメントプロパティ（mdb-prop）\n\n")
        for name, kept in lines.items():
            f.write(f"## {name}\n\n")
            for l in kept:
                f.write(f"- {l}\n")
            f.write("\n")
    return lines


def extract_relationships(reader, out_dir):
    rels = reader.relationship_rows()
    seen = set()
    out_rows = []
    for r in rels:
        # 実測列名: szObject / szReferencedObject（計画の szTable/szReferencedTable は誤り）
        pair = (r.get("szObject", ""), r.get("szReferencedObject", ""))
        if pair in seen or not pair[0] or not pair[1]:
            continue
        if pair[0].startswith("MSys") or pair[1].startswith("MSys"):
            continue
        seen.add(pair)
        out_rows.append({"table": pair[0], "referenced": pair[1],
                         "relationship": r.get("szRelationship", ""),
                         "grbit": r.get("grbit", "")})
    lines = ["# リレーション定義", "", f"- リレーション数（ユーザー定義）: {len(out_rows)}", "",
             "## リレーション一覧", ""]
    for r in out_rows:
        lines.append(f"- `{r['table']}` → `{r['referenced']}`（{r['relationship']}・grbit={r['grbit']}）")
    lines += ["", "## 注記", "",
              "- grbit の意味（1=一対多・2=必須・4=更新カスケード等）は Access の定義に基づく（推定）。", ""]
    with open(os.path.join(out_dir, "25_relationships.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))
    return {"total": len(out_rows), "rows": out_rows}
