"""Markdown ユーティリティ（GitHub 互換アンカー・目次生成・見出し降格）。"""
import re

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")


def github_slug(text):
    """GitHub 互換のアンカー ID（小文字化・記号除去・空白→ハイフン・日本語は保持）。"""
    out = []
    for ch in text.strip().lower():
        if ch.isspace() or ch == "-":
            out.append("-")
        elif ch.isalnum() or ch == "_":
            out.append(ch)
    slug = re.sub(r"-+", "-", "".join(out)).strip("-")
    return slug or "section"


def toc(md_text, max_level=2):
    """H1 を除く max_level 以下の見出しから「## 目次」ブロックを生成。"""
    headings, counts = [], {}
    for line in md_text.splitlines():
        m = HEADING_RE.match(line)
        if not m:
            continue
        level, text = len(m.group(1)), m.group(2).strip()
        if level == 1 or level > max_level:
            continue
        slug = github_slug(text)
        n = counts.get(slug, 0)
        counts[slug] = n + 1
        if n:
            slug = f"{slug}-{n}"
        headings.append((level, text, slug))
    if not headings:
        return ""
    lines = ["## 目次", ""]
    for level, text, slug in headings:
        lines.append(f"{'  ' * (level - 2)}- [{text}](#{slug})")
    return "\n".join(lines) + "\n"


def insert_toc(md_text, max_level=2, back_link=None):
    """H1 直後に目次を挿入（既存目次があれば挿入しない）。back_link は目次の上に配置する。"""
    if re.search(r"^## 目次$", md_text, re.M):
        return md_text
    t = toc(md_text, max_level)
    if not t:
        return md_text
    parts = md_text.split("\n", 1)
    if len(parts) == 1:
        return md_text + "\n\n" + t
    extra = (back_link + "\n\n") if back_link else ""
    return parts[0] + "\n\n" + extra + t + "\n" + parts[1].lstrip("\n")


def strip_toc(md_text):
    """「## 目次」ブロックを除去する（別文書への埋め込み用）。"""
    out, skipping = [], False
    for line in md_text.splitlines():
        if line.strip() == "## 目次":
            skipping = True
            continue
        if skipping:
            if line.startswith("#"):
                skipping = False
            else:
                continue
        out.append(line)
    return "\n".join(out)


def demote(md_text, shift=2):
    """全見出しのレベルを shift だけ深くする（別文書への埋め込み用）。"""
    lines = []
    for line in md_text.splitlines():
        m = HEADING_RE.match(line)
        if m:
            lines.append("#" * min(len(m.group(1)) + shift, 6) + " " + m.group(2))
        else:
            lines.append(line)
    return "\n".join(lines)
