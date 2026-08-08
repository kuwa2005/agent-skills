"""mdbtools CLI ラッパー。MSysObjects/MSysQueries の列名は mdb-schema から取得する。"""
import csv
import io
import os
import re
import shutil
import subprocess

REQUIRED_BINS = ["mdb-ver", "mdb-tables", "mdb-export", "mdb-schema", "mdb-count", "mdb-prop"]

MSYS_OBJECTS_COLS = ["Id", "ParentId", "Name", "Type", "DateCreate", "DateUpdate",
                     "Owner", "Flags", "Database", "Connect", "ForeignName",
                     "RmtInfoShort", "RmtInfoLong", "Lv", "LvProp", "LvModule", "LvExtra"]
MSYS_QUERIES_COLS = ["ObjectId", "Attribute", "Order", "Name1", "Name2", "Expression", "Flag", "LvExtra"]
MSYS_RELATIONS_COLS = ["szRelationship", "grbit", "ccolumn", "icolumn",
                       "szObject", "szColumn", "szReferencedObject", "szReferencedColumn"]


def _run(cmd, *args, timeout=120):
    r = subprocess.run([cmd, *args], capture_output=True, text=True,
                       encoding="utf-8", errors="replace", timeout=timeout)
    if r.returncode != 0 and cmd != "mdb-prop":
        raise RuntimeError(f"{cmd} failed: {r.stderr[:500]}")
    return r


def _csv_rows(text, cols):
    out = []
    for row in csv.reader(io.StringIO(text)):
        if not row or all(not c for c in row):
            continue
        if row[0] == cols[0]:
            continue  # ヘッダ行（mdb-export は -H なしでヘッダ行を出力するため除去）
        d = {}
        for i, c in enumerate(cols):
            d[c] = row[i] if i < len(row) else ""
        out.append(d)
    return out


class MdbReader:
    def __init__(self, path):
        self.path = os.path.abspath(path)
        if not os.path.exists(self.path):
            raise FileNotFoundError(self.path)
        ext = os.path.splitext(self.path)[1].lower()
        if ext not in (".mdb", ".mde", ".accdb", ".accde"):
            raise ValueError(f"非対応拡張子: {ext}（.mdb/.mde/.accdb/.accde のみ）")

    @staticmethod
    def verify_tools():
        for b in REQUIRED_BINS:
            if not shutil.which(b):
                raise OSError(f"mdbtools の {b} が見つかりません。apt install mdbtools を実行してください。")

    def version(self):
        return _run("mdb-ver", self.path).stdout.strip()

    def list_tables(self):
        # mdb-tables -1 は 1 行 1 テーブル（名前は空白を含むため改行区切りで分割）
        r = _run("mdb-tables", "-1", self.path)
        return [t.strip() for t in r.stdout.splitlines() if t.strip() and not t.startswith("MSys")]

    def list_all_objects(self):
        # -S で MSys テーブルも含む全 68 オブジェクト
        r = _run("mdb-tables", "-1", "-S", self.path)
        return [t.strip() for t in r.stdout.splitlines() if t.strip()]

    def export_csv(self, table):
        # -H は「ヘッダなし」の意味（mdbtools 実測）→ ヘッダ行を含めて返す
        return _run("mdb-export", self.path, table).stdout

    def export_hex(self, table):
        out = _run("mdb-export", "-b", "hex", "-H", self.path, table).stdout
        return [row for row in csv.reader(io.StringIO(out))]

    def schema_text(self):
        return _run("mdb-schema", self.path).stdout

    def schema_cols(self, table):
        """mdb-schema -T <table> から列名を抽出。システムテーブルのヘッダ補完に使用。"""
        out = _run("mdb-schema", "-T", table, self.path).stdout
        cols = re.findall(r"^\s*\[([^\]]+)\]", out, re.M)
        return cols

    def object_rows(self):
        out = _run("mdb-export", "-H", self.path, "MSysObjects").stdout
        return _csv_rows(out, MSYS_OBJECTS_COLS)

    def query_rows(self):
        out = _run("mdb-export", "-H", self.path, "MSysQueries").stdout
        return _csv_rows(out, MSYS_QUERIES_COLS)

    def relationship_rows(self):
        out = _run("mdb-export", "-H", self.path, "MSysRelationships").stdout
        return _csv_rows(out, MSYS_RELATIONS_COLS)

    def properties(self, obj_name):
        return _run("mdb-prop", self.path, obj_name).stdout

    def table_row_count(self, table):
        # この mdbtools 版には -q オプションが無い（実測）→ 素の出力の数値を解釈
        out = _run("mdb-count", self.path, table).stdout
        m = re.search(r"(\d+)", out)
        return int(m.group(1)) if m else -1
