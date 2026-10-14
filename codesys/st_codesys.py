# -*- coding: utf-8 -*-
"""
CODESYS adapter for StructuredText_Format.py (CODESYS ScriptEngine, IronPython 2.7).

Formats and/or checks every Structured Text object in the open project:
POUs, methods, properties (Get/Set), actions, transitions, DUTs and GVLs.
Declaration and implementation of one object are formatted together, so the
':' / ':=' columns line up across both parts (the CODESYS equivalent of
"the entire file").

Called by ST_Format.py and ST_CheckNames.py (toolbar buttons).
"""
from __future__ import print_function
import os
import re
import sys

_HERE = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
for _p in (_HERE,
           os.path.join(os.environ.get("LOCALAPPDATA", ""), "CODESYS", "Script Commands")):
    if _p and _p not in sys.path:
        sys.path.insert(0, _p)

import StructuredText_Format as stf   # the same file used in Notepad++

# ---------------------------------------------------------------------------
# CODESYS-specific overrides of StructuredText_Format.OPTIONS
# ---------------------------------------------------------------------------
CODESYS_OPTIONS = {
    "ensure_final_newline": False,   # CODESYS texts have no trailing newline
}

SPLIT_MARK = "//@@ST_FORMAT_SPLIT@@"


def _opts():
    o = dict(stf.OPTIONS)
    o.update(CODESYS_OPTIONS)
    return o


def _eol(text):
    m = re.search(r"\r\n|\n|\r", text or "")
    return m.group(0) if m else "\r\n"


def _path(obj):
    names = []
    o = obj
    while o is not None:
        try:
            if getattr(o, "is_root", False):
                break
            names.append(o.get_name())
            o = o.parent
        except Exception:
            break
    return ".".join(reversed(names))


def iter_st_objects(project):
    """Yield (obj, has_decl, has_impl) for every object with ST text."""
    for obj in project.get_children(recursive=True):
        try:
            has_decl = bool(obj.has_textual_declaration)
        except Exception:
            has_decl = False
        try:
            has_impl = bool(obj.has_textual_implementation)
        except Exception:
            has_impl = False
        if has_decl or has_impl:
            yield obj, has_decl, has_impl


def format_object(obj, has_decl, has_impl, o):
    """Format one object. Returns True if something was changed."""
    decl = obj.textual_declaration.text if has_decl else None
    impl = obj.textual_implementation.text if has_impl else None
    if decl is not None and impl is not None:
        eol = _eol(decl + impl)
        combined = decl + eol + SPLIT_MARK + eol + impl
        res = stf.format_st(combined, o)
        parts = re.split(r"[ \t]*" + re.escape(SPLIT_MARK) + r"[ \t]*(?:\r\n|\n|\r)?", res, 1)
        if len(parts) != 2:
            return False                          # should never happen - leave untouched
        new_decl = parts[0].rstrip("\r\n")
        new_impl = parts[1]
    else:
        new_decl = stf.format_st(decl, o) if decl is not None else None
        new_impl = stf.format_st(impl, o) if impl is not None else None
    changed = False
    if decl is not None and new_decl != decl:
        obj.textual_declaration.replace(new_decl)
        changed = True
    if impl is not None and new_impl != impl:
        obj.textual_implementation.replace(new_impl)
        changed = True
    return changed


def check_object(obj, has_decl, o):
    """Return list of (line, message) for one object's declaration."""
    if not has_decl:
        return []
    text = obj.textual_declaration.text
    out = []
    for s, ln, msg in stf.check_names(text, o):
        out.append((text.count("\n", 0, s) + 1, msg))
    return out


def spell_object(obj, has_decl, has_impl, o):
    """Return list of (part, line, message) for misspelled comment words in one object."""
    decl = obj.textual_declaration.text if has_decl else None
    impl = obj.textual_implementation.text if has_impl else None
    out = []
    for part, text, other in (("decl.", decl, impl), ("impl.", impl, decl)):
        if text:
            for s, ln, msg in stf.check_spelling(text, o, other):
                out.append((part, text.count("\n", 0, s) + 1, msg))
    return out


# ---------------------------------------------------------------------------
# Entry points (need the ScriptEngine globals: projects, system, Severity...)
# ---------------------------------------------------------------------------
def _write(system, severity, text, obj=None):
    try:
        if obj is not None:
            system.write_message(severity, text, obj)
            return
    except Exception:
        pass
    system.write_message(severity, text)


def _traceback_tail(lines=8):
    """Last lines of the current traceback on one line (shown in the Messages view)."""
    import traceback
    return " / ".join(x.strip() for x in traceback.format_exc().splitlines()[-lines:])


def _confirm(system, text):
    try:
        from scriptengine import PromptChoice, PromptResult
        return system.ui.prompt(text, PromptChoice.YesNo, PromptResult.No) == PromptResult.Yes
    except Exception:
        return True


def run_format(projects, system, Severity, check_after=False):
    proj = projects.primary
    if proj is None:
        _write(system, Severity.Error, "ST Format: no project is open.")
        return
    if not _confirm(system, "Format ALL Structured Text objects in '%s'?\n\n"
                            "Tip: save or commit the project first." % proj.path):
        return
    o = _opts()
    items = list(iter_st_objects(proj))
    total = len(items)
    _write(system, Severity.Information, "ST Format: started, %d ST objects found..." % total)
    n_obj = n_changed = 0
    for obj, has_decl, has_impl in items:
        n_obj += 1
        try:
            if format_object(obj, has_decl, has_impl, o):
                n_changed += 1
                _write(system, Severity.Information,
                       "ST Format: [%d/%d] formatted %s" % (n_obj, total, _path(obj)), obj)
            elif n_obj % 25 == 0:
                _write(system, Severity.Information,
                       "ST Format: [%d/%d] ..." % (n_obj, total))
        except Exception as e:
            _write(system, Severity.Error, "ST Format: %s: %s" % (_path(obj), e), obj)
    _write(system, Severity.Information,
           "ST Format: %d of %d ST objects reformatted." % (n_changed, n_obj))
    if check_after:
        run_check(projects, system, Severity)


def run_spell(projects, system, Severity, options=None):
    try:
        _run_spell(projects, system, Severity, options)
    finally:
        stf.close_spellers()                      # stop the Windows spelling helper process, if any


def _run_spell(projects, system, Severity, options=None):
    proj = projects.primary
    if proj is None:
        _write(system, Severity.Error, "ST spelling: no project is open.")
        return
    o = _opts()
    if options:
        o.update(options)
    items = list(iter_st_objects(proj))
    _write(system, Severity.Information,
           "ST spelling: started, %d ST objects found..." % len(items))
    total = 0
    for k, (obj, has_decl, has_impl) in enumerate(items, 1):
        try:
            for part, line, msg in spell_object(obj, has_decl, has_impl, o):
                total += 1
                first, _, rest = msg.partition("\n")
                _write(system, Severity.Warning,
                       "Spelling: %s, %s line %d: %s - %s"
                       % (_path(obj), part, line, first, rest.replace("\n", "; ")), obj)
        except stf.SpellError as e:
            _write(system, Severity.Error, "ST spelling: %s" % str(e).replace("\n", " "))
            return
        except Exception as e:
            _write(system, Severity.Error, "ST spelling: %s: %s  [%s]" % (_path(obj), e, _traceback_tail()), obj)
        if k % 25 == 0:
            _write(system, Severity.Information, "ST spelling: [%d/%d] ..." % (k, len(items)))
    _write(system, Severity.Information,
           "ST spelling: %s" % ("OK" if not total else "%d misspelled word(s)" % total))


def run_check(projects, system, Severity):
    proj = projects.primary
    if proj is None:
        _write(system, Severity.Error, "ST naming: no project is open.")
        return
    o = _opts()
    total = 0
    for obj, has_decl, has_impl in iter_st_objects(proj):
        try:
            for line, msg in check_object(obj, has_decl, o):
                total += 1
                first, _, rest = msg.partition("\n")
                _write(system, Severity.Warning,
                       "Naming: %s, decl. line %d: %s - %s"
                       % (_path(obj), line, first, rest.replace("\n", "; ")), obj)
        except Exception as e:
            _write(system, Severity.Error, "ST naming: %s: %s" % (_path(obj), e), obj)
    _write(system, Severity.Information,
           "ST naming: %s" % ("OK" if not total else "%d problem(s)" % total))
