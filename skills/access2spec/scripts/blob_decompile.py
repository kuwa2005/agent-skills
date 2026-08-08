"""フォーム/レポート/マクロの設計情報を LvProp ブロブ（文字列抽出）と mdb-prop から抽出する。"""
import os
import re

from md_utils import insert_toc

# 日本語文字列の許容文字: 仮名・ASCII・日本語約物（バイナリ誤デコードの CJK ゴミを除外）
ALLOW_RE = re.compile(r"[\u3040-\u30ff\u0020-\u007e\u3000-\u303f\u2010-\u203f\u30fb\u30fc\uff01-\uff65]")


def known_japanese_chars(reader):
    """DB 内の信頼できる日本語（オブジェクト名・リレーション・テーブル名）から既知漢字セットを構築。"""
    from inventory import classify
    inv = classify(reader)
    known = set()
    for r in inv["rows"]:
        for c in (r.get("Name") or ""):
            if "\u4e00" <= c <= "\u9fff":
                known.add(c)
    for row in reader.relationship_rows():
        for cell in row:
            for c in str(cell):
                if "\u4e00" <= c <= "\u9fff":
                    known.add(c)
    for row in reader.object_rows():
        for c in (row.get("Name") or ""):
            if "\u4e00" <= c <= "\u9fff":
                known.add(c)
    for t in inv["tables"]:
        for c in t:
            if "\u4e00" <= c <= "\u9fff":
                known.add(c)
    return known


def utf16_strings(blob_hex, known=None, min_len=2):
    """MR2 ブロブ hex を UTF-16LE でデコードし可読文字列を抽出（順序保持・重複除去）。

    ブロブ先頭は ASCII ヘッダ（MR2\\x00 + バイナリ）のため、UTF-16 文字列
    （GUID/NameMap 等）の開始位置からデコードする。デコード結果は
    仮名/ASCII/約物/既知漢字の連続ランに分割し、バイナリ誤デコードによる
    CJK ゴミ文字列のみ除去する（モジバケ対策）。
    """
    if not blob_hex:
        return []
    try:
        raw = bytes.fromhex(blob_hex)
    except ValueError:
        return []
    start = len(raw)
    for anchor in ("GUID", "NameMap"):
        i = raw.find(anchor.encode("utf-16-le"))
        if i >= 0:
            start = min(start, i)
    if start == len(raw):
        start = 0
    text = raw[start:].decode("utf-16-le", errors="ignore")
    known = known or set()
    runs, cur = [], []
    for c in text:
        if ALLOW_RE.match(c) or c in known:
            cur.append(c)
        else:
            if cur:
                runs.append("".join(cur))
                cur = []
    if cur:
        runs.append("".join(cur))
    seen, out = set(), []
    for s in runs:
        if len(s) < min_len:
            continue
        if s in ("GUID", "NameMap") and s in seen:
            continue
        if s not in seen:
            seen.add(s)
            out.append(s)
    return out


def _hex_map(reader):
    """MSysObjects の Id -> LvProp hex マップ。"""
    m = {}
    for row in reader.export_hex("MSysObjects"):
        if len(row) > 14:
            m[row[0]] = row[14]
    return m


def _guid_from_props(reader, name):
    out = reader.properties(name)
    m = re.search(r"GUID: \{[^}]+\}", out)
    return m.group(0) if m else "（取得不能）"


def _blob_len(blob_hex):
    if not blob_hex:
        return 0
    try:
        return len(bytes.fromhex(blob_hex))
    except ValueError:
        return 0


def extract_forms(reader, out_dir):
    from inventory import classify
    inv = classify(reader)
    hexmap = _hex_map(reader)
    known = known_japanese_chars(reader)
    forms = {}
    for row in inv["forms"]:
        blob = hexmap.get(row["Id"], "")
        forms[row["Name"]] = {
            "date_update": row.get("DateUpdate", ""),
            "lvprop_len": _blob_len(blob),
            "strings": utf16_strings(blob, known=known),
        }
    lines = ["# フォーム一覧", "",
             f"- フォーム数: {len(forms)}",
             "- 各フォームの RecordSource・コントロールは LvProp ブロブの文字列から推定。",
             "- 完全なコントロール定義は Access での確認が必要（推定）。", ""]
    for name, d in forms.items():
        lines += [f"## {name}", "",
                  f"- 更新日: {d['date_update']}・LvProp: {d['lvprop_len']} バイト",
                  "- 検出文字列（RecordSource 列名・コントロール名等の推定）:"]
        for s in d["strings"]:
            lines.append(f"  - {s}")
        lines.append("")
    with open(os.path.join(out_dir, "40_forms.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))
    return {"total": len(forms), "forms": forms}


def extract_reports(reader, out_dir):
    from inventory import classify
    inv = classify(reader)
    hexmap = _hex_map(reader)
    known = known_japanese_chars(reader)
    reports = {}
    for row in inv["reports"]:
        blob = hexmap.get(row["Id"], "")
        reports[row["Name"]] = {
            "date_update": row.get("DateUpdate", ""),
            "strings": utf16_strings(blob, known=known),
        }
    lines = ["# レポート一覧", "",
             f"- レポート数: {len(reports)}",
             "- 各レポートのデータソースは LvProp ブロブの文字列から推定。", ""]
    for name, d in reports.items():
        lines += [f"## {name}", "",
                  f"- 更新日: {d['date_update']}",
                  "- 検出文字列（推定）:"]
        for s in d["strings"]:
            lines.append(f"  - {s}")
        lines.append("")
    with open(os.path.join(out_dir, "50_reports.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))
    return {"total": len(reports), "reports": reports}


def extract_macros(reader, out_dir):
    from inventory import classify
    inv = classify(reader)
    macros = {}
    for row in inv["macros"]:
        macros[row["Name"]] = {
            "date_update": row.get("DateUpdate", ""),
            "guid": _guid_from_props(reader, row["Name"]),
        }
    lines = ["# マクロ一覧", "",
             f"- マクロ数: {len(macros)}",
             "- **注記**: マクロのアクション定義は本ツールでは抽出不能（LvProp 不在）。",
             "- アクション・引数は Access での確認が必要（要Access確認・推定）。", ""]
    for name, d in macros.items():
        lines += [f"## {name}", "",
                  f"- 更新日: {d['date_update']}・{d['guid']}",
                  "- アクション: （要Access確認）", ""]
    with open(os.path.join(out_dir, "60_macros.md"), "w", encoding="utf-8") as f:
        f.write(insert_toc("\n".join(lines)))
    return {"total": len(macros), "macros": macros}
