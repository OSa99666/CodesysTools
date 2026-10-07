#!/usr/bin/env python3
"""
Regression tests for the Structured Text tools. No external packages needed.

    python tests/run_tests.py            run all tests
    python tests/run_tests.py --update   regenerate golden files in tests/expected/
                                         (only after reviewing that the new output is wanted!)
"""
from __future__ import print_function
import io
import os
import re
import shutil
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SAMPLES = os.path.join(ROOT, "tests", "samples")
EXPECTED = os.path.join(ROOT, "tests", "expected")
sys.path[:0] = [os.path.join(ROOT, "src"), os.path.join(ROOT, "codesys"), os.path.join(ROOT, "twincat")]

import StructuredText_Format as stf  # noqa: E402

UPDATE = "--update" in sys.argv
failures = []


def read(p):
    with io.open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()


def write(p, s):
    with io.open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)


def golden(name, actual):
    p = os.path.join(EXPECTED, name)
    if UPDATE or not os.path.exists(p):
        write(p, actual)
        print("  wrote golden %s" % name)
        return
    if read(p) != actual:
        failures.append("%s differs from golden file" % name)


def check(cond, msg):
    if not cond:
        failures.append(msg)


# 1. formatter: golden output + idempotency
print("formatter")
for fn in sorted(os.listdir(SAMPLES)):
    if not fn.endswith(".st"):
        continue
    src = read(os.path.join(SAMPLES, fn))
    out = stf.format_st(src)
    golden(fn, out)
    check(stf.format_st(out) == out, "%s: formatting is not idempotent" % fn)
    print("  ok %s" % fn)

# 2. option variants
print("options")
calls = read(os.path.join(SAMPLES, "calls.st"))
golden("calls.align40.st", stf.format_st(calls, {"align_column": 40}))
golden("calls.preserve.st", stf.format_st(calls, {"call_style": "preserve"}))
golden("general.upper.st", stf.format_st(read(os.path.join(SAMPLES, "general.st")),
                                         {"keyword_case": "upper", "type_case": "upper"}))
o40 = stf.format_st(calls, {"align_column": 40})
for line in o40.splitlines():
    m = re.match(r"^\s*[A-Za-z_][\w.\[\]]*\s+(:=|=>|:)\s", line)
    if m and len(line[:m.start(1)]) != 39:
        failures.append("align_column 40 not respected: %r" % line)

# 3. naming check
print("naming")
for fn, opts in (("naming.st", None), ("terminal_codes.st", None),
                 ("terminal_codes.st", {"terminal_code_check": True})):
    text = read(os.path.join(SAMPLES, fn))
    lines = ["%d: %s" % (text.count("\n", 0, s) + 1, m.replace("\n", " | "))
             for s, ln, m in stf.check_names(text, opts)]
    golden(fn.replace(".st", ".strict" if opts else "") + ".naming.txt", "\n".join(lines) + "\n")

# 4. TwinCAT adapter
print("twincat")
import st_twincat  # noqa: E402
tmp = tempfile.mkdtemp()
try:
    p = os.path.join(tmp, "FB_Valve.TcPOU")
    shutil.copy(os.path.join(SAMPLES, "FB_Valve.TcPOU"), p)
    before = open(p, "rb").read()
    xml, bom = st_twincat._read(p)
    new = st_twincat.format_xml(xml, st_twincat._opts())
    st_twincat._write(p, new, bom)
    after = open(p, "rb").read()
    strip = lambda b: re.sub(rb"<!\[CDATA\[.*?\]\]>", b"", b, flags=re.S)
    check(strip(before) == strip(after), "TwinCAT: XML outside CDATA changed")
    check(after.startswith(b"\xef\xbb\xbf"), "TwinCAT: BOM lost")
    check(after.count(b"\n") == after.count(b"\r\n"), "TwinCAT: line endings changed")
    check(st_twincat.format_xml(new, st_twincat._opts()) == new, "TwinCAT: not idempotent")
    golden("FB_Valve.TcPOU", new)
finally:
    shutil.rmtree(tmp)

# 5. CODESYS adapter against a mock of the ScriptEngine API
print("codesys (mock)")
import st_codesys  # noqa: E402


class Doc(object):
    def __init__(self, t):
        self.text = t

    def replace(self, t):
        self.text = t


class Obj(object):
    def __init__(self, name, decl=None, impl=None, parent=None):
        self.name, self.parent, self.is_root = name, parent, False
        self.has_textual_declaration = decl is not None
        self.has_textual_implementation = impl is not None
        if decl is not None:
            self.textual_declaration = Doc(decl)
        if impl is not None:
            self.textual_implementation = Doc(impl)

    def get_name(self):
        return self.name


class Proj(object):
    path = "mock.project"

    def __init__(self, ch):
        self.ch = ch

    def get_children(self, recursive=False):
        return self.ch


class Sev(object):
    Error, Warning, Information = "E", "W", "I"


messages = []


class Sys(object):
    def write_message(self, sev, text, obj=None):
        messages.append((sev, text))


class Projects(object):
    pass


root = Obj("App")
root.is_root = True
fb = Obj("FB_Valve",
         "FUNCTION_BLOCK FB_Valve\r\nvar_input\r\nR:bool;\r\nnSpeed:int; // speed\r\nend_var\r\n"
         "VAR\r\nsrTemperatureActual:LREAL;\r\nEND_VAR",
         "if R then\r\nsrTemperatureActual:=0.0;\r\nend_if\r\nx:=1;", root)
gvl = Obj("GVL", "VAR_GLOBAL\r\ngbAlarm:BOOL;\r\nbBad:BOOL;\r\nEND_VAR", None, root)
P = Projects()
P.primary = Proj([fb, gvl])
st_codesys._confirm = lambda *a: True
st_codesys.run_format(P, Sys(), Sev)
golden("codesys_mock.txt",
       fb.textual_declaration.text + "\n----\n" + fb.textual_implementation.text + "\n----\n"
       + gvl.textual_declaration.text + "\n----\n" + "\n".join("%s %s" % m for m in messages) + "\n")
check(not any(s == "E" for s, _ in messages), "CODESYS mock reported errors: %r" % messages)

# 6. Python 2.7 / IronPython 2.7 compatibility (no f-strings etc.)
print("py2 compatibility")
for rel in ("src/StructuredText_Format.py", "codesys/st_codesys.py",
            "notepadpp/StructuredText_CheckNames.py"):
    import tokenize
    with io.open(os.path.join(ROOT, rel), "r", encoding="utf-8") as fh:
        for tok in tokenize.generate_tokens(fh.readline):
            if tok.type == tokenize.STRING or getattr(tokenize, "FSTRING_START", -1) == tok.type:
                prefix = re.match(r"[A-Za-z]*", tok.string).group(0).lower()
                if "f" in prefix:
                    failures.append("%s:%d: f-string (must stay Python 2.7 compatible)" % (rel, tok.start[0]))

print()
if failures:
    print("FAILED:")
    for f in failures:
        print("  - " + f)
    sys.exit(1)
print("ALL TESTS PASSED")
