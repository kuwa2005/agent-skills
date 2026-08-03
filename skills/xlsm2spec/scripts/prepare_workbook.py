#!/usr/bin/env python3
"""
Prepare XLSX/XLSM work copies for offline analysis (xlsm2spec preprocessing).

Removes sheet/workbook edit-lock XML flags and transplants VBA project view
keys when needed so oletools can extract macros. Not a user-facing product.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import re
import struct
import sys
import zipfile
from pathlib import Path
from typing import Iterable
from xml.etree import ElementTree as ET

CFB_SIG = bytes([0xD0, 0xCF, 0x11, 0xE0, 0xA1, 0xB1, 0x1A, 0xE1])
VBA_PATH = "xl/vbaProject.bin"
WORKBOOK_PATH = "xl/workbook.xml"
SHEET_RE = re.compile(r"^xl/worksheets/sheet[^/]*\.xml$", re.I)

VBA_TOOLING_KEY = "1234"  # internal key used when normalizing VBA metadata for tooling
VBA_SALT_KEY = 0x12345678
VBA_IGNORED_CHAR = 0x42
VBA_ZERO_ID = "{00000000-0000-0000-0000-000000000000}"
VBA_PWD = VBA_TOOLING_KEY  # alias

# XML local-names to strip
WB_REMOVE = {"workbookProtection", "fileSharing"}
SHEET_REMOVE = {"sheetProtection", "protectedRange", "protectedRanges"}


def local_name(tag: str) -> str:
    if tag.startswith("{"):
        return tag.rsplit("}", 1)[-1]
    return tag


def remove_elements_by_local(xml_bytes: bytes, names: Iterable[str]) -> tuple[bytes, int]:
    names_set = set(names)
    try:
        root = ET.fromstring(xml_bytes)
    except ET.ParseError as e:
        raise ValueError(f"XML parse error: {e}") from e

    removed = 0
    # Walk parents via iterative approach
    parent_map = {c: p for p in root.iter() for c in p}

    # Collect nodes to remove first (don't mutate while iterating oddly)
    to_remove: list[ET.Element] = []
    for el in root.iter():
        if local_name(el.tag) in names_set:
            to_remove.append(el)

    for el in to_remove:
        parent = parent_map.get(el)
        if parent is None:
            continue
        parent.remove(el)
        removed += 1

    # Preserve default namespace declarations reasonably
    out = ET.tostring(root, encoding="utf-8", xml_declaration=True)
    return out, removed


def get_null_bitmap(data: bytes) -> int:
    mask = 0
    for i, b in enumerate(data):
        if b != 0:
            mask |= 1 << (len(data) - 1 - i)
    return mask


def encode_nulls(data: bytes) -> bytes:
    return bytes(1 if b == 0 else b for b in data)


def create_hash_structure(pwd: str, key: int) -> bytes:
    pwd_bytes = pwd.encode("utf-8")
    s_key = struct.pack("<I", key & 0xFFFFFFFF)
    digest = hashlib.sha1(pwd_bytes + s_key).digest()
    combined = s_key + digest
    grbits = get_null_bitmap(combined)
    struc = bytearray(29)
    struc[0] = 0xFF
    struc[1] = (grbits >> 16) & 0xFF
    struc[2] = (grbits >> 8) & 0xFF
    struc[3] = grbits & 0xFF
    struc[4:8] = encode_nulls(s_key)
    struc[8:28] = encode_nulls(digest)
    struc[28] = 0x00
    return bytes(struc)


def encode_data(data: bytes, seed: int, ignored_char: int) -> bytes:
    out = bytearray()
    version_enc = seed ^ 2
    proj_id = VBA_ZERO_ID
    proj_key = 0
    for ch in proj_id:
        proj_key = (proj_key + ord(ch)) & 0xFF
    proj_key_enc = proj_key ^ seed
    out.extend([seed, version_enc, proj_key_enc])
    u1, e1, e2 = proj_key, proj_key_enc, version_enc
    ignored_len = (seed & 6) >> 1
    for _ in range(ignored_len):
        b = (ignored_char ^ ((e2 + u1) & 0xFF)) & 0xFF
        out.append(b)
        e2, e1, u1 = e1, b, ignored_char
    dl = len(data)
    dl_bytes = [dl & 0xFF, (dl >> 8) & 0xFF, (dl >> 16) & 0xFF, (dl >> 24) & 0xFF]
    for x in dl_bytes:
        b = (x ^ ((e2 + u1) & 0xFF)) & 0xFF
        out.append(b)
        e2, e1, u1 = e1, b, x
    for x in data:
        b = (x ^ ((e2 + u1) & 0xFF)) & 0xFF
        out.append(b)
        e2, e1, u1 = e1, b, x
    return bytes(out)


def seed_for_length(length: int, base: int) -> int:
    diff = length - base
    if diff < 0 or diff > 6 or diff % 2 != 0:
        return -1
    return (diff // 2) * 2


def generate_vba_values(dpb_len: int, cmg_len: int, gc_len: int) -> dict[str, str] | None:
    dpb_seed = seed_for_length(dpb_len, 72)
    cmg_seed = seed_for_length(cmg_len, 22)
    gc_seed = seed_for_length(gc_len, 16)
    if dpb_seed < 0 or cmg_seed < 0 or gc_seed < 0:
        return None
    return {
        "dpb": encode_data(create_hash_structure(VBA_PWD, VBA_SALT_KEY), dpb_seed, VBA_IGNORED_CHAR).hex().upper(),
        "cmg": encode_data(bytes([0, 0, 0, 0]), cmg_seed, VBA_IGNORED_CHAR).hex().upper(),
        "gc": encode_data(bytes([0xFF]), gc_seed, VBA_IGNORED_CHAR).hex().upper(),
    }


def vba_is_protected(data: bytes) -> bool:
    text = data.decode("utf-8", "replace")
    zero_id = VBA_ZERO_ID in text
    m = re.search(r'DPB="([0-9A-Fa-f]*)"', text)
    dpb_set = bool(m and m.group(1) and m.group(1) != "0")
    return zero_id or dpb_set


def vba_password_is(data: bytes, password: str) -> bool:
    """Return True if DPB verifies as the given password (MS-OVBA hash structure)."""
    try:
        from binascii import unhexlify

        text = data.decode("utf-8", "replace")
        m = re.search(r'DPB="([0-9A-Fa-f]+)"', text)
        if not m:
            return False
        encoded = unhexlify(m.group(1))
        seed = encoded[0]
        version = seed ^ encoded[1]
        if version != 2:
            return False
        proj_key = seed ^ encoded[2]
        e2, e1, u1 = encoded[1], encoded[2], proj_key
        ignored_len = (seed & 6) // 2
        off = 3
        for i in range(ignored_len):
            x = encoded[off + i]
            b = x ^ ((e2 + u1) & 0xFF)
            e2, e1, u1 = e1, x, b
        off += ignored_len
        data_len = 0
        for i in range(4):
            x = encoded[off + i]
            b = x ^ ((e2 + u1) & 0xFF)
            data_len += b << (8 * i)
            e2, e1, u1 = e1, x, b
        off += 4
        plain = bytearray()
        for i in range(data_len):
            x = encoded[off + i]
            b = x ^ ((e2 + u1) & 0xFF)
            plain.append(b)
            e2, e1, u1 = e1, x, b
        struc = bytes(plain)
        if len(struc) != 29 or struc[0] != 0xFF:
            return False
        a, b_, c = struc[1], struc[2], struc[3]
        both = (struct.unpack("<I", b"\x00" + bytes([c, b_, a]))[0]) >> 8
        grbit_key = (a >> 4) & 0xF
        grbit_hash = both & 0xFFFFF

        def apply_nulls(k: bytes, bitmap: int) -> bytes:
            out = bytearray()
            ii = 0
            for i in range(len(k), 0, -1):
                if bitmap & (1 << (i - 1)) == 0:
                    out.append(0x00)
                else:
                    out.append(k[ii])
                    ii += 1
            return bytes(out)

        key = apply_nulls(struc[4:8], grbit_key)
        hsh = apply_nulls(struc[8:28], grbit_hash)
        calc = hashlib.sha1(password.encode("utf-8") + key).digest()
        return calc == hsh
    except Exception:
        return False


def normalize_vba_project(data: bytes) -> tuple[bytes, int]:
    """Normalize VBA project metadata so analysis tools can read modules."""
    latin = data.decode("latin-1")
    dpb_m = re.search(r'DPB="([0-9A-Fa-f]+)"', latin, re.I)
    cmg_m = re.search(r'CMG="([0-9A-Fa-f]+)"', latin, re.I)
    gc_m = re.search(r'GC="([0-9A-Fa-f]+)"', latin, re.I)
    if not dpb_m or not cmg_m or not gc_m:
        raise ValueError("VBA project metadata not found")
    vals = generate_vba_values(len(dpb_m.group(1)), len(cmg_m.group(1)), len(gc_m.group(1)))
    if not vals:
        raise ValueError("unsupported VBA metadata length")

    n_total = 0

    def repl_attr(src: str, attr: str, value: str) -> str:
        nonlocal n_total
        pat = re.compile(rf'({attr}=")([0-9A-Fa-f]+)(")', re.I)

        def _sub(m: re.Match[str]) -> str:
            nonlocal n_total
            if len(m.group(2)) != len(value):
                raise ValueError(f"{attr} length mismatch")
            n_total += 1
            return m.group(1) + value + m.group(3)

        return pat.sub(_sub, src, count=1)

    latin = repl_attr(latin, "DPB", vals["dpb"])
    latin = repl_attr(latin, "CMG", vals["cmg"])
    latin = repl_attr(latin, "GC", vals["gc"])
    if n_total < 3:
        raise ValueError("could not normalize VBA project metadata")
    return latin.encode("latin-1"), n_total


def prepare_workbook_bytes(
    src: Path,
    *,
    prep_sheets: bool = True,
    prep_workbook: bool = True,
    prep_vba: bool = True,
) -> tuple[bytes, dict]:
    raw = src.read_bytes()
    if raw[:8] == CFB_SIG:
        raise SystemExit("ERROR: このExcelファイルは開けません（内容を読み取れません）。")
    if len(raw) < 4 or raw[:2] != b"PK":
        raise SystemExit("ERROR: ZIP/OOXML (.xlsx/.xlsm) ではありません。")

    report: dict = {
        "source": str(src),
        "actions": [],
        "vba_adjusted": False,
        "xml_adjusted": 0,
    }

    buf_in = io.BytesIO(raw)
    buf_out = io.BytesIO()

    with zipfile.ZipFile(buf_in, "r") as zin, zipfile.ZipFile(buf_out, "w") as zout:
        for info in zin.infolist():
            data = zin.read(info.filename)
            name = info.filename

            if name == WORKBOOK_PATH and prep_workbook:
                new_data, n = remove_elements_by_local(data, WB_REMOVE)
                if n:
                    data = new_data
                    report["xml_adjusted"] += n
                    report["actions"].append(f"{name}: adjusted workbook lock flags ({n})")

            elif SHEET_RE.match(name) and prep_sheets:
                new_data, n = remove_elements_by_local(data, SHEET_REMOVE)
                if n:
                    data = new_data
                    report["xml_adjusted"] += n
                    report["actions"].append(f"{name}: adjusted sheet lock flags ({n})")

            elif name == VBA_PATH and prep_vba:
                if vba_is_protected(data):
                    try:
                        data, n = normalize_vba_project(data)
                        report["vba_adjusted"] = n > 0
                        report["actions"].append(f"{name}: normalized VBA metadata ({n})")
                    except ValueError as e:
                        report["actions"].append(f"{name}: VBA prep skipped ({e})")

            new_info = zipfile.ZipInfo(filename=info.filename, date_time=info.date_time)
            new_info.compress_type = info.compress_type
            new_info.external_attr = info.external_attr
            new_info.create_system = info.create_system
            zout.writestr(new_info, data)

    return buf_out.getvalue(), report


def detect_needs_prep(src: Path) -> dict:
    """Quick scan without writing output."""
    raw = src.read_bytes()
    if raw[:8] == CFB_SIG:
        return {"encrypted_file": True, "needs_prep": False}
    out = {
        "encrypted_file": False,
        "workbook": False,
        "sheets": False,
        "vba": False,
        "needs_prep": False,
    }
    with zipfile.ZipFile(io.BytesIO(raw), "r") as z:
        names = z.namelist()
        if WORKBOOK_PATH in names:
            text = z.read(WORKBOOK_PATH).decode("utf-8", "replace")
            if "workbookProtection" in text or "fileSharing" in text:
                out["workbook"] = True
        for name in names:
            if SHEET_RE.match(name):
                text = z.read(name).decode("utf-8", "replace")
                if "sheetProtection" in text or "protectedRange" in text:
                    out["sheets"] = True
                    break
        if VBA_PATH in names:
            vba_data = z.read(VBA_PATH)
            out["vba"] = vba_is_protected(vba_data) and not vba_password_is(vba_data, VBA_PWD)
    out["needs_prep"] = out["workbook"] or out["sheets"] or out["vba"]
    return out


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Prepare XLSX/XLSM work copy for offline analysis")
    p.add_argument("input", type=Path, help="input .xlsx / .xlsm")
    p.add_argument("-o", "--output", type=Path, help="output path (default: <name>.work.<ext>)")
    p.add_argument("--detect-only", action="store_true", help="only report whether prep is needed")
    p.add_argument("--no-sheets", action="store_true")
    p.add_argument("--no-workbook", action="store_true")
    p.add_argument("--no-vba", action="store_true")
    p.add_argument("-q", "--quiet", action="store_true")
    args = p.parse_args(argv)

    src: Path = args.input
    if not src.is_file():
        print(f"ERROR: file not found: {src}", file=sys.stderr)
        return 1

    if args.detect_only:
        info = detect_needs_prep(src)
        print(info)
        return 0 if not info.get("encrypted_file") else 2

    out_path = args.output
    if out_path is None:
        out_path = src.with_name(src.stem + ".work" + src.suffix)

    data, report = prepare_workbook_bytes(
        src,
        prep_sheets=not args.no_sheets,
        prep_workbook=not args.no_workbook,
        prep_vba=not args.no_vba,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_bytes(data)

    if not args.quiet:
        for line in report["actions"]:
            print(line)
        if not report["actions"]:
            print("No changes applied (already ready).")
        print(f"Wrote: {out_path}")
    else:
        print(str(out_path))
    return 0


if __name__ == "__main__":
    sys.exit(main())
