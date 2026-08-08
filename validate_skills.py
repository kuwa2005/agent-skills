#!/usr/bin/env python3
"""agent-skills 配布スキルの健全性検証。

全 skills/<name>/SKILL.md のフロントマターを検証する:
- YAML としてパース可能（name / description 必須・非空）
- frontmatter の name がディレクトリ名と一致
エラーがあれば非ゼロ終了。PyYAML がある場合は YAML フルパース、
無い場合は簡易チェックにフォールバックする。
"""
import os
import re
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
SKILLS_DIR = os.path.join(ROOT, "skills")

try:
    import yaml  # type: ignore
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


def parse_frontmatter(content):
    m = re.match(r"^---\s*\n(.*?)\n---", content, re.S)
    if m is None:
        return None, "frontmatter が無い（先頭の `---` 〜 `---` が見つからない）"
    body = m.group(1)
    if HAS_YAML:
        try:
            data = yaml.safe_load(body)
        except Exception as e:
            return None, f"YAML パース失敗: {e}"
        if not isinstance(data, dict):
            return None, "frontmatter が YAML マッピングではない"
        return data, None
    # フォールバック: 最低限 name/description の存在だけ確認
    name = re.search(r"^name:\s*(.+)$", body, re.M)
    desc = re.search(r"^description:\s*(.+)$", body, re.M)
    if name is None or desc is None:
        return None, "name または description が見つからない（簡易チェック）"
    return {"name": name.group(1).strip(), "description": desc.group(1).strip()}, None


def main():
    errors = []
    checked = 0
    if not os.path.isdir(SKILLS_DIR):
        errors.append(f"skills/ ディレクトリが無い: {SKILLS_DIR}")
    for entry in sorted(os.listdir(SKILLS_DIR)):
        d = os.path.join(SKILLS_DIR, entry)
        if not os.path.isdir(d) or entry.startswith("."):
            continue
        skill_md = os.path.join(d, "SKILL.md")
        if not os.path.exists(skill_md):
            errors.append(f"SKILL.md が無い: {entry}/")
            continue
        with open(skill_md, encoding="utf-8") as fh:
            content = fh.read()
        data, err = parse_frontmatter(content)
        checked += 1
        if err:
            errors.append(f"{entry}/SKILL.md: {err}")
            continue
        name = data.get("name", "")
        desc = data.get("description", "")
        if not name:
            errors.append(f"{entry}/SKILL.md: name が空")
        if not desc or not isinstance(desc, str) or len(desc) < 10:
            errors.append(f"{entry}/SKILL.md: description が空または短すぎる")
        if name != entry:
            errors.append(f"{entry}/SKILL.md: name({name!r}) がディレクトリ名({entry!r})と不一致")
        print(f"OK  {entry}/SKILL.md" + ("" if not err else f"  ({err})"))
    print(f"---\nchecked: {checked} skill(s), yaml={'on' if HAS_YAML else 'off (fallback)'}")
    if errors:
        print("ERRORS:")
        for e in errors:
            print(f"  - {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
