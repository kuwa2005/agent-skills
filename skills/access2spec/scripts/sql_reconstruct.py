"""MSysQueries からのクエリ SQL 再構築（第一原理・実測属性マッピング）。

属性マッピング（sample.mdb 実測）:
  attr1 = 追加クエリのターゲット表（name1）
  attr5 = FROM ソース / attr6 = SELECT 列（n1=エイリアス, n2=追加先列, expr=式）
  attr7 = JOIN ON 条件（n1=左, n2=右, expr=ON式）
  attr8 = WHERE / attr9 = GROUP BY / attr10・11 = ORDER BY（attr11 n1='D' で DESC）
"""
import os
import re

from md_utils import insert_toc

SUB_TYPE_VERB = {
    0x8E: "INSERT", 0x0A: "INSERT", 0x32: "INSERT",
    0xA6: "DELETE",
    0xBA: "TRANSFORM", 0xEA: "TRANSFORM", 0xD6: "TRANSFORM",
    0x02: "TRANSFORM", 0x08: "TRANSFORM", 0x2E: "TRANSFORM",
    0x1A: "SELECT",
}


def verb_from_blob(blob_hex):
    """MR2 ブロブ offset4 の 2バイト LE 値で動詞を判定（完全一致）。"""
    if not blob_hex:
        return "SELECT"
    hexdigits = re.sub(r"[^0-9a-fA-F]", "", blob_hex)
    if not hexdigits.startswith("4D523200") or len(hexdigits) < 12:
        return "SELECT"
    val = int.from_bytes(bytes.fromhex(hexdigits[8:12]), "little")
    return SUB_TYPE_VERB.get(val, "SELECT")


def _fmt_col(name1, expr):
    if expr and name1 and "." not in name1:
        return f"{expr} AS {name1}"
    return expr or name1 or ""


def _bracket(name):
    return f"[{name}]" if re.search(r"\s", name) else name


def _from_clause(sources, joins):
    if not sources:
        return ""
    if not joins:
        return ", ".join(_bracket(s) for s in sources)
    parts = [_bracket(sources[0])]
    used = {sources[0]}
    for j in joins:
        left, right, cond = (j + ("", "", ""))[:3]
        for cand in (right, left):
            if cand and cand in sources and cand not in used:
                parts.append(f"INNER JOIN {_bracket(cand)} ON {cond}")
                used.add(cand)
                break
    for s in sources:
        if s not in used:
            parts.append(f", {_bracket(s)}")
    return " ".join(parts)


def rows_to_sql(rows, verb_hint=None):
    sources, cols, joins, wheres, groups, orders = [], [], [], [], [], []
    insert_target = None
    for r in rows:
        attr = str(r.get("Attribute", ""))
        n1, n2, expr = r.get("Name1", ""), r.get("Name2", ""), r.get("Expression", "")
        if attr == "1" and n1:
            insert_target = n1
        elif attr == "5" and n1:
            sources.append(n1)
        elif attr == "6":
            cols.append((n1, n2, expr))
        elif attr == "7" and expr:
            joins.append((n1, n2, expr))
        elif attr == "8" and expr:
            wheres.append(expr)
        elif attr == "9" and (expr or n1):
            groups.append(expr or n1)
        elif attr in ("10", "11") and (expr or n1):
            orders.append(f"{expr or n1} DESC" if (attr == "11" and n1 == "D") else (expr or n1))

    if insert_target:
        verb = "INSERT"
    elif verb_hint == "DELETE" or (sources and not cols and not groups):
        verb = "DELETE"
    elif verb_hint == "TRANSFORM":
        verb = "TRANSFORM"
    else:
        verb = "SELECT"

    from_clause = _from_clause(sources, joins)
    if verb == "INSERT":
        target_cols = [c[1] or c[0] for c in cols if c[1] or c[0]]
        sel = ", ".join(c[2] or c[0] for c in cols) or "*"
        where = "\nWHERE " + " AND ".join(wheres) if wheres else ""
        return (f"INSERT INTO {_bracket(insert_target)} ({', '.join(target_cols)})\n"
                f"SELECT {sel}\nFROM {from_clause}{where};")
    if verb == "DELETE":
        tgt = _bracket(sources[0]) if sources else ""
        where = "\nWHERE " + " AND ".join(wheres) if wheres else ""
        return f"DELETE FROM {tgt}{where};"
    if verb == "TRANSFORM":
        agg = cols[-1][2] if cols else ""
        sel_cols = [_fmt_col(c[0], c[2]) for c in cols] or ["*"]
        sql = f"TRANSFORM {agg}\nSELECT {', '.join(sel_cols)}"
        if from_clause:
            sql += f"\nFROM {from_clause}"
        if wheres:
            sql += "\nWHERE " + " AND ".join(wheres)
        if groups:
            sql += "\nGROUP BY " + ", ".join(groups)
        sql += "\n-- PIVOT 列: （推定不能・要Accessでの確認）"
        return sql + ";"
    sel_cols = [_fmt_col(c[0], c[2]) for c in cols] or ["*"]
    sql = f"SELECT {', '.join(sel_cols)}"
    if from_clause:
        sql += f"\nFROM {from_clause}"
    if wheres:
        sql += "\nWHERE " + " AND ".join(wheres)
    if groups:
        sql += "\nGROUP BY " + ", ".join(groups)
    if orders:
        sql += "\nORDER BY " + ", ".join(orders)
    return sql + ";"


REF_RE = re.compile(r"(?:FROM|JOIN)\s+(\[[^\]]*\]|[^\s,]+)")


def table_refs_in_sql(sql):
    refs = set()
    for m in REF_RE.finditer(sql):
        tok = m.group(1)
        ref = tok[1:-1] if tok.startswith("[") else tok.rstrip(";")
        if ref:
            refs.add(ref)
    return sorted(refs)


def _sql_verb(sql):
    if "INSERT INTO" in sql:
        return "INSERT"
    if sql.startswith("DELETE"):
        return "DELETE"
    if sql.startswith("TRANSFORM"):
        return "TRANSFORM"
    if sql.startswith("SELECT"):
        return "SELECT"
    return None


def reconstruct(reader, out_dir):
    from inventory import classify
    qrows = {}
    for r in reader.query_rows():
        qrows.setdefault(r["ObjectId"], []).append(r)
    inv = classify(reader)
    by_id = {row["Id"]: row for row in inv["rows"] if row["Type"] == "5"}
    blob_map = {}
    for row in reader.export_hex("MSysObjects"):
        if len(row) > 14:
            blob_map[row[0]] = row[14]
    queries = []
    for oid, row in by_id.items():
        verb_hint = verb_from_blob(blob_map.get(oid, ""))
        sql = rows_to_sql(qrows.get(oid, []), verb_hint)
        verb = _sql_verb(sql) or verb_hint
        queries.append({
            "id": oid,
            "name": row["Name"],
            "verb": verb,
            "sql": sql,
            "ok": bool(sql),
        })
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    with open(os.path.join(data_dir, "queries.csv"), "w", encoding="utf-8") as f:
        f.write("Id,Name,Verb,SQL\n")
        for q in queries:
            f.write(f'{q["id"]},{q["name"]},{q["verb"]},"{q["sql"].replace(chr(34), chr(34)*2)}"\n')
    with open(os.path.join(out_dir, "30_queries.md"), "w", encoding="utf-8") as f:
        lines = ["# クエリ定義一覧（SQL 再構築）", "",
                 f"クエリ総数: {len(queries)} / 再構築成功: {sum(1 for q in queries if q['ok'])}"
                 f" / 復元不能: {sum(1 for q in queries if not q['ok'])}", "",
                 "> 再構築は MSysQueries の属性行から第一原理で生成したものです。"
                 "クロス集計の PIVOT 列・複雑な式は Access での確認が必要です。", "",
                 "## 復元不能クエリ", ""]
        for q in queries:
            if not q["ok"]:
                lines.append(f"- {q['name']} (Id: {q['id']})（復元不能・要Access確認）")
        lines += ["", "## クエリ一覧", ""]
        for q in queries:
            lines += [f"### {q['name']}（Id: {q['id']}・{('復元OK' if q['ok'] else '復元不能')}）", "",
                      f"```sql\n{q['sql']}\n```", ""]
        f.write(insert_toc("\n".join(lines)))
    return {
        "total": len(queries),
        "ok": sum(1 for q in queries if q["ok"]),
        "queries": queries,
        "md_path": os.path.join(out_dir, "30_queries.md"),
    }
