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
for fn, opts in (("naming.st", None), ("terminal_codes.st", None), ("naming_prefixes.st", None), ("naming_union.st", None), ("naming_noprefix.st", None), ("naming_block_skip.st", None),
                 ("naming_types.st", {"naming_ignore_types": ["tod", "ST_Data"]}),
                 ("naming.st", {"naming_check_type_members": False}),
                 ("terminal_codes.st", {"terminal_code_check": True})):
    text = read(os.path.join(SAMPLES, fn))
    lines = ["%d: %s" % (text.count("\n", 0, s) + 1, m.replace("\n", " | "))
             for s, ln, m in stf.check_names(text, opts)]
    golden(fn.replace(".st", ".strict" if opts else "") + ".naming.txt", "\n".join(lines) + "\n")

# 3b. spell check (Hunspell fixtures in tests/dict: English test dictionary + latin-1 "Norwegian")
print("spelling")
DICT = os.path.join(ROOT, "tests", "dict")
SPELL_OPTS = {"spell_dictionaries": [os.path.join(DICT, "test_en"), os.path.join(DICT, "test_nb")]}
text = read(os.path.join(SAMPLES, "spelling.st"))
lines = []
for s_, ln, m in stf.check_spelling(text, SPELL_OPTS):
    line = text.count("\n", 0, s_) + 1
    col = s_ - (text.rfind("\n", 0, s_) + 1) + 1
    check(text[s_:s_ + ln] == m.split("  ")[0], "spell: wrong range for %r" % m)
    lines.append("%d:%d  %s" % (line, col, m.replace("\n", " | ")))
golden("spelling.spell.txt", "\n".join(lines) + "\n")
try:
    stf.check_spelling(text, {"spell_dictionaries": ["no_such_dictionary"]})
    failures.append("spell: missing dictionary not reported")
except stf.SpellError:
    pass
only_en = stf.check_spelling("// arbeidsbord og feilstavet\n", {"spell_dictionaries": [os.path.join(DICT, "test_en")]})
check(len(only_en) == 2, "spell: Norwegian words should fail with the English dictionary only")
check(not stf.check_spelling("// arbeidsbord\n", SPELL_OPTS), "spell: compound/two dictionaries failed")
check(not stf.check_spelling("// worker valve\n", dict(SPELL_OPTS, spell_user_words=["Worker"])), "spell: user words")
if sys.platform == "win32":      # Windows spelling engine (en-US is installed on Windows 8+)
    WIN_OPTS = {"spell_backend": "windows", "spell_languages": ["en-US"], "spell_dictionaries": []}
    try:
        res = stf.check_spelling("// the valve is wrong, the wrod is spelled right\n", WIN_OPTS)
        check(len(res) == 1 and res[0][2].startswith("wrod"), "spell (Windows): expected only 'wrod', got %r" % (res,))
        check("word" in res[0][2], "spell (Windows): no suggestion 'word'")
    except stf.SpellError as e:
        print("  (Windows spelling engine not available - skipped: %s)" % str(e).split("\n")[0])
    try:                         # the helper-process variant that CODESYS uses (IronPython)
        helper = stf._WinProcSpeller(["en-US"], stf._find_python({}))
        try:
            check(helper.check("valve") and not helper.check("wrod") and "word" in helper.suggest("wrod", 5),
                  "spell (Windows helper process): wrong answers")
            check(helper.check(u"café"), "spell (Windows helper process): non-ASCII word")
        finally:
            helper.shutdown()
    except stf.SpellError as e:
        print("  (Windows helper process not available - skipped: %s)" % str(e).split("\n")[0])
    try:
        stf.check_spelling("// x\n", dict(WIN_OPTS, spell_languages=["xx-ZZ"]))
        failures.append("spell (Windows): unsupported language not reported")
    except stf.SpellError:
        pass
check(len(stf.check_spelling("// ventilbrod\n", dict(SPELL_OPTS, spell_dictionaries=[os.path.join(DICT, "test_en")]))) == 1,
      "spell: word must be flagged without user dictionary")
check(not stf.check_spelling("// ventilbrod\n", dict(SPELL_OPTS, spell_dictionaries=["test_en"], spell_folders=[DICT])),
      "spell: user_words.txt in the dictionaries folder not used")

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

# 4b. TwinCAT spell check
xml_sp = ('<TcPlcObject><POU Name="FB_X"><Declaration><![CDATA[FUNCTION_BLOCK FB_X\r\nVAR\r\n'
          '    sbOpen : BOOL; // the valvs\r\nEND_VAR]]></Declaration><Implementation><ST><![CDATA[// wrod\r\n'
          'sbOpen := TRUE;]]></ST></Implementation></POU></TcPlcObject>')
SPELL_OPTS = {"spell_dictionaries": [os.path.join(ROOT, "tests", "dict", "test_en"),
                                     os.path.join(ROOT, "tests", "dict", "test_nb")]}
found = list(st_twincat.spell_xml(xml_sp, dict(st_twincat._opts(), **SPELL_OPTS)))
check(len(found) == 2, "TwinCAT spell: expected 2 findings, got %r" % (found,))
golden("twincat_spell.txt", "\n".join("%d:%d %s %s" % (f[0], f[1], f[2], f[3].replace("\n", " | "))
                                      for f in found) + "\n")

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

del messages[:]
fb.textual_declaration.text = "FUNCTION_BLOCK FB_Valve\r\nVAR\r\n    sbOpen : BOOL;  // the valvs\r\nEND_VAR"
fb.textual_implementation.text = "// wrod here\r\nsbOpen := TRUE;"
st_codesys.run_spell(P, Sys(), Sev, SPELL_OPTS)
golden("codesys_spell_mock.txt", "\n".join("%s %s" % m for m in messages) + "\n")
del messages[:]
st_codesys.run_spell(P, Sys(), Sev, {"spell_dictionaries": [], "spell_backend": "hunspell"})
check(any(sv == "E" and "No spelling dictionary" in t for sv, t in messages), "CODESYS spell: missing dictionary not reported")

# 6. Python 2.7 / IronPython 2.7 compatibility (no f-strings etc.)
print("py2 compatibility")
for rel in ("src/StructuredText_Format.py", "codesys/st_codesys.py",
            "notepadpp/StructuredText_CheckNames.py", "notepadpp/StructuredText_SpellCheck.py",
            "codesys/ST_SpellCheck.py"):
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
