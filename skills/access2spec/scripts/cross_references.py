"""フォーム→クエリ→テーブルの参照連鎖を構築する。"""
import os
import re

from md_utils import insert_toc


def build_cross_refs(reader, queries):
    from inventory import classify
    from sql_reconstruct import table_refs_in_sql

    inv = classify(reader)
    form_to_query = {}
    for row in inv["forms"]:
        fname = row["Name"]
        qs = []
        for q in queries:
            # フォーム名（…のサブフォーム 等の接尾を除いた部分）がクエリ名に含まれる
            base = re.sub(r"のサブフォーム$", "", fname)
            if base and base in q["name"] and not q["name"].startswith("~sq_f"):
                qs.append(q["name"])
        if qs:
            form_to_query[fname] = sorted(set(qs))

    query_to_table = {}
    for q in queries:
        refs = table_refs_in_sql(q["sql"])
        if refs:
            query_to_table[q["name"]] = refs
    return {"form_to_query": form_to_query, "query_to_table": query_to_table}


def extract_cross_references(reader, out_dir):
    from sql_reconstruct import reconstruct
    qres = reconstruct(reader, out_dir)
    refs = build_cross_refs(reader, qres["queries"])

    lines = ["# クロスリファレンス（フォーム → クエリ → テーブル）", "", "## フォーム → クエリ", ""]
    for form, qs in sorted(refs["form_to_query"].items()):
        lines.append(f"- **{form}**")
        for q in qs:
            lines.append(f"  - → `{q}`")
    lines += ["", "## クエリ → テーブル", ""]
    for q, tables in sorted(refs["query_to_table"].items()):
        lines.append(f"- `{q}` → {' , '.join(tables)}")
    lines += ["", "## 参照連鎖（フォーム→クエリ→テーブル）", ""]
    chains = 0
    for form, qs in sorted(refs["form_to_query"].items()):
        for q in qs:
            if q in refs["query_to_table"]:
                lines.append(f"- {form} → {q} → {' , '.join(refs['query_to_table'][q])}")
                chains += 1
    if chains == 0:
        lines.append("- （参照連鎖は検出できず・要Access確認）")
    lines.append("")
    lines.append("- 注記: フォーム↔クエリの対応は名前の包含一致による推定。")
    with open(os.path.join(out_dir, "80_cross_references.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))
    return refs
