"""MSysObjects の分類。Type 対応表は sample.mdb で実測確定。"""
import re

TYPE_LABELS = {
    "5": "クエリ",
    "-32768": "フォーム",
    "-32766": "マクロ",
    "-32764": "レポート",
    "8": "リレーション",
    "3": "ナビグループ",
    "-32757": "ドキュメントプロパティ",
    "2": "MSysDb",
    "-32761": "VBAモジュール",
    "-32758": "ユーザー情報",
    "1": "テーブル",
}

SYSTEM_TABLE_NAMES = {"MSysObjects", "MSysACEs", "MSysQueries", "MSysRelationships",
                      "MSysAccessObjects", "MSysAccessXML", "MSysNavPaneGroups",
                      "MSysNavPaneObjectIDs", "MSysNavPaneGroupCategories",
                      "MSysNavPaneGroupToObjects", "MSysDb"}


def classify(reader):
    rows = reader.object_rows()
    counts = {v: 0 for v in TYPE_LABELS.values()}
    unclassified = []
    queries = []
    for row in rows:
        typ = row.get("Type", "")
        label = TYPE_LABELS.get(typ, "システム")
        row["label"] = label
        if typ == "5":
            row["hidden"] = row["Name"].startswith("~sq")
            row["~sq"] = row["hidden"]
            queries.append(row)
        else:
            row["hidden"] = False
            row["~sq"] = False
        if label in counts:
            counts[label] += 1
        else:
            unclassified.append(row.get("Name", "?"))
    # テーブル = ユーザーテーブル58 + MSys テーブル10（MSysDb は Type2 で別集計）
    msys_count = sum(1 for n in reader.list_all_objects() if n in SYSTEM_TABLE_NAMES)
    counts["テーブル"] = msys_count + len(reader.list_tables())
    return {
        "rows": rows,
        "counts": counts,
        "unclassified": unclassified,
        "queries": queries,
        "forms": [r for r in rows if r["label"] == "フォーム"],
        "reports": [r for r in rows if r["label"] == "レポート"],
        "macros": [r for r in rows if r["label"] == "マクロ"],
        "tables": reader.list_tables(),
    }


def forms_from_sq(reader):
    """~sq_f<フォーム名>… の親参照からフォーム名を復元する。"""
    names = set()
    for row in reader.object_rows():
        n = row.get("Name", "")
        m = re.match(r"~sq_f(.+?)(?:~sq_|$)", n)
        if m:
            names.add(m.group(1))
    return names
