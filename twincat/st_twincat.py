# -*- coding: utf-8 -*-
"""
TwinCAT 3 adapter for StructuredText_Format.py.

Formats and/or checks the Structured Text inside TwinCAT source files
(.TcPOU .TcDUT .TcGVL .TcIO). Only the text inside
<Declaration><![CDATA[...]]></Declaration> and <ST><![CDATA[...]]></ST>
is touched; the rest of the XML is kept byte for byte.

All declaration and implementation parts of one file (POU, methods,
properties, actions...) are formatted together, so ':' / ':=' / '=>'
line up across the whole file.

Usage (Python 3, standard library only):
    python st_twincat.py FILE_OR_FOLDER [...]          format, then check naming
    python st_twincat.py --check FILE_OR_FOLDER [...]  naming check only
    python st_twincat.py --no-check FILE_OR_FOLDER     format only
    python st_twincat.py --dry-run ...                 show what would change
A folder (or a .plcproj / .sln file) is searched recursively.

Naming problems are printed as  file(line,col): warning ST001: ...  so the
Visual Studio / TwinCAT XAE Output window makes them double-clickable.
"""
from __future__ import print_function
import io
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
if _HERE not in sys.path:
    sys.path.insert(0, _HERE)
import StructuredText_Format as stf   # same file as in Notepad++ / CODESYS

# TwinCAT-specific overrides of StructuredText_Format.OPTIONS
TWINCAT_OPTIONS = {
    "ensure_final_newline": False,
    "indent_pou_body": False,   # TwinCAT objects have no END_FUNCTION_BLOCK etc.
}

EXTENSIONS = (".tcpou", ".tcdut", ".tcgvl", ".tcio")
RE_SECTION = re.compile(r"(<(Declaration|ST)>\s*<!\[CDATA\[)(.*?)(\]\]>\s*</\2>)", re.S)
RE_OWNER = re.compile(r'<(POU|Method|Property|Get|Set|Action|Transition|DUT|GVL|Itf)\b[^>]*\bName="([^"]+)"')
MARK = "//@@ST_SPLIT_%d@@"
RE_MARK = re.compile(r"[ \t]*//@@ST_SPLIT_(\d+)@@[ \t]*(?:\r\n|\n|\r)?")


def _opts():
    o = dict(stf.OPTIONS)
    o.update(TWINCAT_OPTIONS)
    return o


def _read(path):
    with io.open(path, "rb") as f:
        raw = f.read()
    bom = raw.startswith(b"\xef\xbb\xbf")
    return raw[3:].decode("utf-8") if bom else raw.decode("utf-8"), bom


def _write(path, text, bom):
    data = text.encode("utf-8")
    with io.open(path, "wb") as f:
        f.write((b"\xef\xbb\xbf" if bom else b"") + data)


def _eol(text):
    m = re.search(r"\r\n|\n|\r", text)
    return m.group(0) if m else "\r\n"


def _owner(xml, pos):
    name = None
    for m in RE_OWNER.finditer(xml, 0, pos):
        name = m.group(2) if name is None or m.group(1) == "POU" else name + "." + m.group(2)
    return name or "?"


def format_xml(xml, o):
    """Return the XML with all ST sections formatted."""
    secs = list(RE_SECTION.finditer(xml))
    work = [(k, m) for k, m in enumerate(secs) if m.group(3).strip()]
    if not work:
        return xml
    eol = _eol(xml)
    combined = eol.join(MARK % k + eol + m.group(3) for k, m in work)
    res = stf.format_st(combined, o)
    pieces = RE_MARK.split(res)
    # pieces = [before, idx, text, idx, text, ...]
    new = {}
    for a in range(1, len(pieces) - 1, 2):
        new[int(pieces[a])] = pieces[a + 1]
    if sorted(new) != [k for k, _ in work]:
        raise RuntimeError("internal split error - file left unchanged")
    out, last = [], 0
    for k, m in enumerate(secs):
        out.append(xml[last:m.start(3)])
        if k in new:
            text = new[k].rstrip("\r\n")
            orig = m.group(3)
            if orig.endswith(("\r\n", "\n", "\r")):
                text += _eol(orig)
            out.append(text)
        else:
            out.append(m.group(3))
        last = m.end(3)
    out.append(xml[last:])
    return "".join(out)


def check_xml(xml, o):
    """Yield (xml_line, col, owner, decl_line, message) for naming problems."""
    for m in RE_SECTION.finditer(xml):
        if m.group(2) != "Declaration":
            continue
        text = m.group(3)
        base = m.start(3)
        for s, ln, msg in stf.check_names(text, o):
            p = base + s
            line = xml.count("\n", 0, p) + 1
            col = p - (xml.rfind("\n", 0, p) + 1) + 1
            yield line, col, _owner(xml, base), text.count("\n", 0, s) + 1, msg


def collect(paths):
    files = []
    for p in paths:
        p = os.path.abspath(p.strip('"'))
        if os.path.isfile(p) and p.lower().endswith(EXTENSIONS):
            files.append(p)
            continue
        if os.path.isfile(p):                      # .plcproj / .sln / .tsproj -> its folder
            p = os.path.dirname(p)
        for root, dirs, names in os.walk(p):
            dirs[:] = [d for d in dirs if d.lower() not in ("_boot", "_compileinfo", "_libraries", ".git")]
            for n in names:
                if n.lower().endswith(EXTENSIONS):
                    files.append(os.path.join(root, n))
    return files


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    flags = set(a for a in argv[1:] if a.startswith("--"))
    if not args:
        print(__doc__)
        return 2
    o = _opts()
    do_format = "--check" not in flags
    do_check = "--no-check" not in flags and o.get("naming_check", True)
    dry = "--dry-run" in flags
    files = collect(args)
    n_changed = n_warn = n_err = 0
    for path in files:
        try:
            xml, bom = _read(path)
            if do_format:
                new = format_xml(xml, o)
                if new != xml:
                    n_changed += 1
                    if dry:
                        print("would format: %s" % path)
                    else:
                        _write(path, new, bom)
                        print("formatted: %s" % path)
                    xml = new
            if do_check:
                for line, col, owner, dline, msg in check_xml(xml, o):
                    n_warn += 1
                    first, _, rest = msg.partition("\n")
                    print("%s(%d,%d): warning ST001: %s, decl. line %d: %s - %s"
                          % (path, line, col, owner, dline, first, rest.replace("\n", "; ")))
        except Exception as e:
            n_err += 1
            print("%s(1,1): error ST000: %s" % (path, e))
    summary = "ST: %d file(s)" % len(files)
    if do_format:
        summary += ", %d %sformatted" % (n_changed, "would be " if dry else "")
    if do_check:
        summary += ", %d naming problem(s)" % n_warn
    if n_err:
        summary += ", %d error(s)" % n_err
    print(summary)
    return 1 if n_err else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
