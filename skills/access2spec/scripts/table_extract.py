"""テーブルスキーマ（mdb-schema DDL パース）とデータ抽出（先頭N行 CSV）。"""
import os
import re

TYPE_RE = re.compile(r"^\s*\[([^\]]+)\]\s+([A-Za-z ]+?)(?:\s*\((\d+)\))?\s*[,)]")


def sanitize_filename(name):
    return re.sub(r"[/\\:*?\"<>|]", "_", name)


def parse_schema(schema_text, tables):
    """mdb-schema の CREATE TABLE ブロックをパースして列定義を返す。"""
    result = {}
    blocks = re.split(r"CREATE TABLE \[", schema_text)
    for blk in blocks[1:]:
        m = re.match(r"([^\]]+)\]", blk)
        if not m:
            continue
        tname = m.group(1)
        if tname not in tables:
            continue
        cols = []
        body = blk.split("\n", 1)[1]
        for line in body.splitlines():
            cm = TYPE_RE.match(line)
            if cm:
                cname, ctype, csize = cm.group(1), cm.group(2).strip(), cm.group(3)
                cols.append({
                    "name": cname,
                    "type": ctype,
                    "size": int(csize) if csize else None,
                    "required": "NOT NULL" in line,
                })
        result[tname] = cols
    return result


def extract_tables(reader, out_dir, limit=100):
    tables = reader.list_tables()
    schema = parse_schema(reader.schema_text(), tables)
    data_dir = os.path.join(out_dir, "data")
    os.makedirs(data_dir, exist_ok=True)
    row_counts = {}
    samples = {}
    for t in tables:
        csv_out = reader.export_csv(t)
        lines = [l for l in csv_out.splitlines() if l.strip()]
        header = lines[0] if lines else ""
        data = lines[1:]
        row_counts[t] = len(data)
        samples[t] = data[:limit]
        fname = sanitize_filename(t) + ".csv"
        with open(os.path.join(data_dir, fname), "w", encoding="utf-8") as f:
            f.write(header + "\n")
            f.write("\n".join(samples[t]))
            if samples[t]:
                f.write("\n")
    return {"schema": schema, "row_counts": row_counts, "samples": samples}
