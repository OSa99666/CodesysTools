# -*- coding: utf-8 -*-
"""
Structured Text (IEC 61131-3) auto-formatter for Notepad++.

Runs inside the Notepad++ "PythonScript" plugin (Python 2.7 or 3.x).
Always formats the whole document.

Can also be used from the command line for testing:
    python StructuredText_Format.py input.st            -> prints result
    python StructuredText_Format.py input.st --inplace  -> rewrites file

Edit OPTIONS below to change the formatting style.
"""
from __future__ import print_function
import os
import re
import sys

# ---------------------------------------------------------------------------
# OPTIONS - edit to taste
# ---------------------------------------------------------------------------
OPTIONS = {
    "indent_size": 4,                # spaces per level (ignored if use_tabs)
    "use_tabs": False,               # indent with tabs instead of spaces
    # --- Keyword / type case: "pascal" | "upper" | "lower" | "preserve" -----
    # pascal = capital first letter and capital after every '_' (End_If, ElsIf)
    "keyword_case": "pascal",        # IF THEN ELSIF END_IF CASE FOR ... AND OR NOT TRUE FALSE
    "decl_keyword_case": "upper",    # VAR_INPUT END_VAR FUNCTION_BLOCK STRUCT ARRAY CONSTANT ...
    "region_case": "upper",          # REGION / END_REGION
    "type_case": "pascal",           # Bool Int LInt LReal LTime DWord ...
    "function_case": "pascal",       # standard functions: Abs Sqrt Sin Cos Limit Int_To_Real ... (see FUNCTIONS)

    "normalize_spacing": True,       # rewrite spaces between tokens
    "space_around_operators": True,  # a := b + c   vs   a:=b+c
    "space_after_comma": True,       # f(a, b)      vs   f(a,b)
    "decl_colon_style": " : ",       # " : " ->  x : Int;    ": " ->  x: Int;  (when not aligned)

    # --- Column alignment ----------------------------------------------------
    # Columns are 1-based, like "Col:" in the Notepad++ status bar. 0 = automatic.
    # "file":  ONE column for the whole file - the ':' of every declaration and
    #          the ':=' of every assignment line up from top to bottom.
    # "block": each run of consecutive declarations/assignments is aligned on its own.
    "align_scope": "file",
    "align_declarations": True,      # declarations as 3 columns: NAME | : TYPE | // COMMENT
    "align_assignments": True,       # code: TARGET | := or => | // COMMENT  (=> = call outputs)
    "align_column": 0,               # column of ':' and ':=' (0 = auto: longest name + gap)
    "decl_min_gap": 1,               # min spaces between a name and ':'
    "assign_min_gap": 1,             # min spaces between a target and ':='
    "align_comments": True,          # line up trailing comments
    "comment_column": 0,             # column of trailing comments (0 = auto)
    "comment_min_gap": 2,            # min spaces between code and comment
    "decl_comment_style": "//",      # "//" converts (* c *) to // c in declarations; "preserve"
    # A line that is too long for a fixed column is pushed right on its own.

    # --- Attributes / pragmas -------------------------------------------------
    "attribute_column0": True,       # {attribute '...'} always starts in column 1
    "attribute_join": True,          # put {attribute ...} on the same line as the declaration
                                     # it belongs to:  {attribute 'hide'} bVar : Bool;

    # --- Hungarian notation check (Notepad++ only: orange underline + hover tip)
    "naming_check": True,            # check declarations against the naming table
    "check_naming_after_format": True,
    "naming_indicator_style": "thick",   # "thick" | "plain" | "squiggle" underline, "box" (filled), "outline"
    "naming_indicator_color": (255, 140, 0),  # orange (R, G, B)
    "naming_ignore": [],             # exact names never flagged, e.g. ["i", "j"]
    # Names that are one of these prefixes, or start with it followed by a capital letter,
    # digit or '_', are never flagged (k, k_1, kMaxSize, vSpeed, m2). Case sensitive;
    # "mode" is NOT exempt by "m".
    "naming_ignore_prefixes": ["k", "v", "m", "sm", "tm", "sv", "tv"],   # k=constant, v=vector, m=matrix, s/t = static/temp
    # Declarations of these data types are never checked (case-insensitive; the element
    # type for ARRAY OF). Standard or own types, e.g. ["TOD", "DT", "ST_Data", "FB_Timer"].
    "naming_ignore_types": [],
    # False = members of TYPE ... STRUCT / UNION declarations are not checked at all.
    "naming_check_type_members": True,
    # UNION members are alternative views of the same memory: a bare type prefix (b, dw, w, ...)
    # or a prefix + capital/digit is accepted whatever the member's type (b : tBits; dw : DWord).
    "naming_union_views": True,
    # A COMMENT containing {attribute 'noprefix'} (e.g.  //{attribute 'noprefix'}  - a real pragma
    # gives compiler warnings) switches the name check off:
    #   before any code            -> for the whole file / CODESYS object
    #   behind STRUCT/UNION/VAR... -> for that block only (same line as the keyword)
    # "" = feature disabled.
    "naming_skip_attribute": "noprefix",
    "naming_report_console": False,  # also list problems in the PythonScript console
    "naming_indicator_id": 13,       # Scintilla indicator number (change if another plugin uses 13)
    # VAR_INPUT / VAR_OUTPUT / VAR_IN_OUT: names in ALL CAPITALS always pass the
    # Hungarian check (terminal names). If True they must also be a valid
    # IEC PAS 63131 terminal code (see TERMINAL_FIRST / TERMINAL_NEXT).
    "terminal_code_check": False,

    # --- Spell check of comments (Hunspell .dic + .aff files) ---------------------------
    # Dictionaries are looked up by name in: spell_folders, the Notepad++/DSpellCheck Hunspell
    # folder, %LOCALAPPDATA%\CODESYS\Script Commands\dictionaries, %LOCALAPPDATA%\STTools\dictionaries
    # and a "dictionaries" folder next to this file. A full path (without .dic) also works.
    # A word is correct if ANY listed dictionary accepts it.
    # Backend: "windows" = the spelling engine built into Windows 8+ (no files; handles Norwegian
    # compounds; also uses your Windows custom words), "hunspell" = the dictionary files below,
    # "auto" = Hunspell if spell_dictionaries is filled in, otherwise Windows.
    "spell_backend": "auto",
    "spell_languages": ["en-US", "nb-NO"],   # Windows backend: a word is OK in ANY of these
    "spell_python": "",              # CODESYS + Windows backend: python.exe for the helper process ("" = find it)
    "spell_dictionaries": [],        # Hunspell backend, e.g. ["en_GB", "nb_NO"]
    "spell_folders": [],             # extra folders to search for the dictionaries
    "spell_user_words": [],          # extra accepted words, e.g. ["PLC", "Hunspell"] (case-insensitive)
    "spell_user_dictionary": "user_words.txt",   # your own words, one per line (# = comment); a plain name is
                                     # looked up in the dictionary folders (every copy found is used)
    "check_spelling_after_format": False,   # Notepad++: also spell check after formatting
    "spell_min_length": 3,           # shorter words are not checked
    "spell_skip_allcaps": True,      # PLC, IEC, HMI ...
    "spell_skip_identifiers": True,  # camelCase words (tMbState, sValve)
    "spell_code_words": True,        # words found in the code's identifiers (Valve, Mb) are accepted
    "spell_skip_code_comments": True,    # skip comment lines that look like code (:=, =>, ends in ;)
    "spell_compounds": True,         # accept words glued from 2-4 valid words (Norwegian: arbeidsbord)
    "spell_suggestions": 5,          # max. suggestions per word (0 = none)
    "spell_indicator_id": 14,        # Scintilla indicator number (Notepad++)
    "spell_indicator_style": "squiggle",
    "spell_indicator_color": (220, 0, 0),
    "spell_report_console": False,

    "indent_pou_body": False,        # indent code inside PROGRAM/FUNCTION_BLOCK/TYPE...
    "indent_case_items": True,       # indent statements under CASE labels

    # --- FB / function calls with named parameters ------------------------------
    # "expanded":  sTimer                "preserve": leave calls as written
    #              (
    #                  IN := sbStart,
    #                  Q  => sbDone
    #              );
    "call_style": "expanded",
    "call_expand_min_params": 1,     # expand only calls with at least this many parameters
    "call_paren_indent": 1,          # indent levels of "(" relative to the call name
    "call_param_offset": 1,          # extra spaces of parameters and ");" relative to "("
    # Declarations with named initialisation, e.g.  sValve : tValve(bOpen := True, iMax := 10);
    # are laid out like calls (needs call_style "expanded"); ':' and ':=' stay column aligned.
    "decl_init_expand": True,
    "max_blank_lines": 1,            # collapse runs of blank lines to this many
    "ensure_final_newline": True,
}

# Exact spellings used in "pascal" mode. Anything not listed gets a capital
# first letter and a capital after every '_', rest lowercase (End_If, Var_Input).
# Add or change entries here to suit your style.
PASCAL_CASE = {
    # keywords
    "ELSIF": "ElsIf",
    # data types
    "BOOL": "Bool", "BYTE": "Byte", "WORD": "Word", "DWORD": "DWord", "LWORD": "LWord",
    "SINT": "SInt", "INT": "Int", "DINT": "DInt", "LINT": "LInt",
    "USINT": "USInt", "UINT": "UInt", "UDINT": "UDInt", "ULINT": "ULInt",
    "REAL": "Real", "LREAL": "LReal",
    "TIME": "Time", "LTIME": "LTime", "DATE": "Date", "LDATE": "LDate",
    "TIME_OF_DAY": "Time_Of_Day", "LTIME_OF_DAY": "LTime_Of_Day",
    "DATE_AND_TIME": "Date_And_Time", "LDATE_AND_TIME": "LDate_And_Time",
    "TOD": "TOD", "LTOD": "LTOD", "DT": "DT", "LDT": "LDT",
    "STRING": "String", "WSTRING": "WString", "CHAR": "Char", "WCHAR": "WChar",
    "ANY": "Any", "ANY_NUM": "Any_Num", "ANY_INT": "Any_Int", "ANY_REAL": "Any_Real",
    "ANY_BIT": "Any_Bit", "ANY_STRING": "Any_String", "ANY_DATE": "Any_Date",
    "XWORD": "XWord", "XINT": "XInt", "UXINT": "UXInt",
}

# ---------------------------------------------------------------------------
# Hungarian notation table:  name = <memory prefix><type prefix><Capital>...
#   e.g. sbReset (static Bool), ibReset (input Bool), trValue (temp Real),
#        sMotor (static FB instance / complex type), gciMaxCount (global const Int)
# ---------------------------------------------------------------------------
MEMORY_PREFIX = {
    "VAR": "s",                  # static section (FB / PROGRAM)
    "VAR_IN_FUNCTION": "t",      # VAR inside FUNCTION / METHOD is temporary
    "VAR_STAT": "s",
    "VAR_INST": "s",
    "VAR_TEMP": "t",
    "VAR_GLOBAL": "g",
    "VAR_GLOBAL_CONSTANT": "gc",
    "VAR_CONSTANT": "c",
    "VAR_INPUT": "i",
    "VAR_OUTPUT": "q",
    "VAR_IN_OUT": "iq",
    "AT_INPUT": "i",             # x AT %I...  (input image)
    "AT_OUTPUT": "q",            # x AT %Q...  (output image)
    "STRUCT_MEMBER": "",         # members of STRUCT / UNION: type prefix only
}

# Types not listed here are "complex" (FB, STRUCT, UNION, enum, TOD, DT,
# POINTER ...): they get only the memory prefix, e.g. sMotor, tData.
# ARRAY [..] OF X uses the prefix of X (trValues : ARRAY[1..5] OF Real).
TYPE_PREFIX = {
    "BOOL": ["b", "x"], "BIT": ["b", "x"],     # b is preferred
    "BYTE": ["by"], "WORD": ["w"], "DWORD": ["dw"], "LWORD": ["lw"],
    "SINT": ["si"], "USINT": ["usi"], "INT": ["i"], "UINT": ["ui"],
    "DINT": ["di"], "UDINT": ["udi"], "LINT": ["li"], "ULINT": ["uli"],
    "TIME": ["t"], "LTIME": ["lt"], "REAL": ["r"], "LREAL": ["lr"],
    "DATE": ["d"], "CHAR": ["c"], "STRING": ["s"],
    "WSTRING": ["s"], "WCHAR": ["c"],          # not in the table - assumed
}

# IEC PAS 63131 terminal code identification letters (used when
# "terminal_code_check" is True). Remove letters you don't want to allow.
TERMINAL_FIRST = {
    "A": "Action alarm", "B": "Binary status", "F": "Force command",
    "L": "Lock command", "P": "Parameter", "R": "Reset command",
    "S": "Set command", "W": "Warning alarm", "X": "External input",
    "Y": "Normal function output",
}
TERMINAL_NEXT = {
    "A": "Automatic mode", "B": "Blocked mode", "C": "Confirmed",
    "D": "Disable transition mode", "E": "Enabled status",
    "F": "Fault/Failed/Forward", "G": "Position", "H": "High",
    "I": "Internal (set-point mode)/Information", "L": "Low", "M": "Manual mode",
    "N": "Hold/Negative transition", "O": "Outside mode", "P": "Positive transition",
    "Q": "Quantity", "R": "Reference signal", "S": "Safeguarding mode",
    "T": "Track mode", "U": "Suppressed mode", "V": "Variance/Deviation",
    "W": "Warning alarm",
}
# digits 1-9 are terminal enumerations and allowed after the first letter

# Leading lowercase runs that look like an old prefix; stripped when the
# checker suggests a corrected name (nSpeed -> iiSpeed, aBuf -> srBuf).
_OTHER_PREFIXES = set("n f e a p st fb ar arr str en ref ptr dt tod ldt ltod".split())

# ---------------------------------------------------------------------------
# Language tables
# ---------------------------------------------------------------------------
def _set(s):
    return set(s.split())

KW_CONTROL = _set("IF THEN ELSE ELSIF END_IF CASE OF END_CASE FOR TO BY DO END_FOR "
                  "WHILE END_WHILE REPEAT UNTIL END_REPEAT EXIT CONTINUE RETURN JMP")
KW_DECL = _set("PROGRAM END_PROGRAM FUNCTION END_FUNCTION FUNCTION_BLOCK END_FUNCTION_BLOCK "
               "METHOD END_METHOD PROPERTY END_PROPERTY ACTION END_ACTION INTERFACE END_INTERFACE "
               "TYPE END_TYPE STRUCT END_STRUCT UNION END_UNION NAMESPACE END_NAMESPACE "
               "CONFIGURATION END_CONFIGURATION RESOURCE END_RESOURCE "
               "VAR VAR_INPUT VAR_OUTPUT VAR_IN_OUT VAR_GLOBAL VAR_EXTERNAL VAR_TEMP VAR_STAT "
               "VAR_INST VAR_CONFIG VAR_ACCESS END_VAR CONSTANT RETAIN NON_RETAIN PERSISTENT AT "
               "EXTENDS IMPLEMENTS PUBLIC PRIVATE PROTECTED INTERNAL ABSTRACT FINAL OVERRIDE "
               "THIS SUPER POINTER REFERENCE REF_TO")
KW_OPS = _set("AND OR XOR NOT MOD AND_THEN OR_ELSE")
KW_CONST = _set("TRUE FALSE NULL")
TYPES = _set("BOOL BYTE WORD DWORD LWORD SINT INT DINT LINT USINT UINT UDINT ULINT REAL LREAL "
             "TIME LTIME DATE LDATE TIME_OF_DAY LTIME_OF_DAY TOD LTOD DATE_AND_TIME LDATE_AND_TIME "
             "DT LDT STRING WSTRING CHAR WCHAR ANY ANY_NUM ANY_INT ANY_REAL ANY_BIT ANY_STRING "
             "ANY_DATE XWORD XINT UXINT ARRAY")
KW_REGION = _set("REGION END_REGION")
# Standard IEC functions: re-cased (option function_case) when used as a call, i.e. followed by '('.
# <TYPE>_TO_<TYPE> and TO_<TYPE> conversions are recognised automatically.
FUNCTIONS = _set("ABS SQRT LN LOG EXP EXPT SIN COS TAN ASIN ACOS ATAN ATAN2 TRUNC "
                 "ADD SUB MUL DIV MOVE SHL SHR ROL ROR SEL MAX MIN LIMIT MUX "
                 "GT GE EQ LE LT NE LEN LEFT RIGHT MID CONCAT INSERT DELETE REPLACE FIND "
                 "SIZEOF ADR BITADR")
RE_CONVERSION = re.compile(r"^(?:([A-Z_0-9]+)_TO_|TO_|TRUNC_)([A-Z_0-9]+)$")
KEYWORDS = KW_CONTROL | KW_DECL | KW_OPS | KW_CONST | KW_REGION
RESERVED = KEYWORDS | TYPES

VAR_KINDS = _set("VAR VAR_INPUT VAR_OUTPUT VAR_IN_OUT VAR_GLOBAL VAR_EXTERNAL VAR_TEMP "
                 "VAR_STAT VAR_INST VAR_CONFIG VAR_ACCESS")
POU_KINDS = _set("PROGRAM FUNCTION FUNCTION_BLOCK METHOD PROPERTY ACTION INTERFACE TYPE "
                 "NAMESPACE CONFIGURATION RESOURCE")
BLOCK_KINDS = _set("IF CASE FOR WHILE REPEAT STRUCT UNION")

OPENERS = {}
for _k in POU_KINDS | BLOCK_KINDS:
    OPENERS[_k] = _k
for _k in VAR_KINDS:
    OPENERS[_k] = "VAR"
CLOSERS = dict(("END_" + k, k) for k in POU_KINDS | BLOCK_KINDS)
CLOSERS["END_VAR"] = "VAR"
OPENERS["REGION"] = "REGION"
CLOSERS["END_REGION"] = "REGION"
DECL_CONTEXT = _set("VAR STRUCT UNION")

DATE_PREFIXES = _set("D DATE LDATE DT LDT DATE_AND_TIME LDATE_AND_TIME TOD LTOD "
                     "TIME_OF_DAY LTIME_OF_DAY")

BINOPS = set([":=", "=>", "=", "<>", "<", ">", "<=", ">=", "+", "-", "*", "/", "**", "&"])
MULTI_OPS = [":=", "=>", "<=", ">=", "<>", "..", "**"]
SINGLE_OPS = ":;,()[].^+-*/=<>&@#"
COMMENT_KINDS = ("lcomment", "bcomment")

RE_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
RE_NUMBER = re.compile(r"\d[\d_]*(?:\.\d[\d_]*)?(?:[eE][+-]?\d+)?")
RE_INT = re.compile(r"\d[\d_]*")
RE_ADDR = re.compile(r"%[A-Za-z0-9_.*]+")


class Tok(object):
    __slots__ = ("kind", "v", "pos", "role")

    def __init__(self, kind, v, role=None):
        self.kind = kind
        self.v = v
        self.role = role


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------
def _read_string(text, i, quote):
    n = len(text)
    j = i + 1
    while j < n:
        ch = text[j]
        if ch == "$":
            j += 2
            continue
        if ch == quote:
            return j + 1
        if ch in "\r\n":
            return j
        j += 1
    return n


def _read_literal(text, j, prefix):
    """j points just after '#'. Returns end index of a typed literal."""
    n = len(text)
    if j < n and text[j] in "'\"":
        return _read_string(text, j, text[j])
    allow_date = prefix.upper() in DATE_PREFIXES
    if j < n and text[j] in "+-":
        j += 1
    while j < n:
        ch = text[j]
        if ch.isalnum() or ch in "_.":
            j += 1
        elif allow_date and ch in "-:":
            j += 1
        else:
            break
    return j


def tokenize(text):
    toks = []
    i, n = 0, len(text)
    line_start = True
    while i < n:
        c = text[i]
        if toks and toks[-1].kind not in ("ws", "nl"):
            line_start = False
        if c in "\r\n":
            line_start = True
            j = i + 2 if (c == "\r" and i + 1 < n and text[i + 1] == "\n") else i + 1
            toks.append(Tok("nl", text[i:j]))
            i = j
            continue
        if c in " \t\f\v":
            j = i
            while j < n and text[j] in " \t\f\v":
                j += 1
            toks.append(Tok("ws", text[i:j]))
            i = j
            continue
        if text.startswith("//", i):
            j = i
            while j < n and text[j] not in "\r\n":
                j += 1
            toks.append(Tok("lcomment", text[i:j]))
            i = j
            continue
        if text.startswith("(*", i) or text.startswith("/*", i):
            end = "*)" if c == "(" else "*/"
            j = text.find(end, i + 2)
            j = n if j < 0 else j + 2
            toks.append(Tok("bcomment", text[i:j]))
            i = j
            continue
        if c == "{":
            j = text.find("}", i + 1)
            j = n if j < 0 else j + 1
            toks.append(Tok("pragma", text[i:j]))
            i = j
            continue
        if c in "'\"":
            j = _read_string(text, i, c)
            toks.append(Tok("string", text[i:j]))
            i = j
            continue
        m = RE_IDENT.match(text, i)
        if m:
            j = m.end()
            if j < n and text[j] == "#":
                j = _read_literal(text, j + 1, m.group(0))
                toks.append(Tok("literal", text[i:j]))
            else:
                toks.append(Tok("ident", text[i:j]))
                if line_start and m.group(0).upper() == "REGION":
                    # REGION <free text name> up to end of line
                    k = j
                    while k < n and text[k] not in "\r\n":
                        k += 1
                    seg = text[j:k]
                    name = seg.strip()
                    if name:
                        a = j + seg.index(name)
                        if a > j:
                            toks.append(Tok("ws", text[j:a]))
                        toks.append(Tok("rname", name))
                        if a + len(name) < k:
                            toks.append(Tok("ws", text[a + len(name):k]))
                    elif k > j:
                        toks.append(Tok("ws", seg))
                    j = k
            i = j
            continue
        if c.isdigit():
            m = RE_INT.match(text, i)
            j = m.end()
            if j < n and text[j] == "#":
                j = _read_literal(text, j + 1, "")
                toks.append(Tok("literal", text[i:j]))
            else:
                j = RE_NUMBER.match(text, i).end()
                toks.append(Tok("number", text[i:j]))
            i = j
            continue
        if c == "%":
            m = RE_ADDR.match(text, i)
            if m:
                toks.append(Tok("addr", m.group(0)))
                i = m.end()
                continue
        matched = False
        for op in MULTI_OPS:
            if text.startswith(op, i):
                toks.append(Tok("op", op))
                i += len(op)
                matched = True
                break
        if matched:
            continue
        if c in SINGLE_OPS:
            toks.append(Tok("op", c))
        else:
            toks.append(Tok("other", c))
        i += 1
    return toks


# ---------------------------------------------------------------------------
# Formatter
# ---------------------------------------------------------------------------
class Line(object):
    def __init__(self):
        self.blank = False
        self.extra = 0        # extra spaces after the indent (call parameters)
        self.indent = 0
        self.code = ""
        self.comment = ""
        self.left = None      # declaration name part (for alignment)
        self.right = None     # declaration ': TYPE ...' part
        self.alignable = False
        self.a_left = None    # assignment target (for := alignment)
        self.a_right = None   # ':= expression;'


def _depth(stack):
    return sum(inc for _, inc in stack)


def _pop_to(stack, kind):
    for k in range(len(stack) - 1, -1, -1):
        if stack[k][0] == kind:
            del stack[k:]
            return True
    return False


def _apply_case(word, mode):
    if mode == "pascal":
        u = word.upper()
        if u in PASCAL_CASE:
            return PASCAL_CASE[u]
        return "_".join(p[:1].upper() + p[1:].lower() for p in word.split("_"))
    if mode == "upper":
        return word.upper()
    if mode == "lower":
        return word.lower()
    return word


def _is_function(name, nxt):
    if nxt is None or nxt.v != "(":
        return False
    u = name.upper()
    if u in FUNCTIONS:
        return True
    m = RE_CONVERSION.match(u)
    return bool(m) and m.group(2) in TYPES and (m.group(1) is None or m.group(1) in TYPES)


def _function_case(name, mode):
    """Conversions follow the type spelling: INT_TO_LREAL -> Int_To_LReal, TO_LTIME -> To_LTime."""
    m = RE_CONVERSION.match(name.upper())
    if mode != "pascal" or not m:
        return _apply_case(name, mode)
    head = name.upper()[:m.start(2)]            # 'INT_TO_' | 'TO_' | 'TRUNC_'
    src = head[:-len("_TO_")] if m.group(1) else None
    pre = "%s_To_" % _apply_case(src, mode) if src else head[:1] + head[1:].lower()
    return pre + _apply_case(m.group(2), mode)


def _display(t, o, nxt=None):
    if t.kind == "ident":
        u = t.v.upper()
        if u in KW_REGION:
            return _apply_case(t.v, o["region_case"])
        if u in KW_DECL:
            return _apply_case(t.v, o["decl_keyword_case"])
        if u in KEYWORDS:
            return _apply_case(t.v, o["keyword_case"])
        if u in TYPES:
            return _apply_case(t.v, o["type_case"])
        if _is_function(t.v, nxt):
            return _function_case(t.v, o["function_case"])
    elif t.kind == "literal":
        # typed literal: only the type prefix before '#' follows type_case (LTIME#1s -> LTime#1s)
        pre, sep, rest = t.v.partition("#")
        if sep and pre.upper() in TYPES:
            return _apply_case(pre, o["type_case"]) + sep + rest
    return t.v


def _is_unary(prev, cur):
    if cur.kind != "op" or cur.v not in ("-", "+"):
        return False
    if prev is None:
        return True
    if prev.kind == "op":
        return prev.v not in (")", "]", "^")
    if prev.kind == "ident":
        u = prev.v.upper()
        return u in KEYWORDS and u not in KW_CONST
    return prev.kind in COMMENT_KINDS


def _sep(prev, cur, prev_unary, o, label_colon):
    pk, pv, ck, cv = prev.kind, prev.v, cur.kind, cur.v
    if ck in COMMENT_KINDS or pk in COMMENT_KINDS or ck == "pragma" or pk == "pragma":
        return " "
    if prev_unary:
        return ""
    if ck == "op" and cv in (";", ","):
        return ""
    if pk == "op" and pv == ",":
        return " " if o["space_after_comma"] else ""
    if pk == "op" and pv in ("(", "["):
        return ""
    if ck == "op" and cv in (")", "]"):
        return ""
    if (ck == "op" and cv in (".", "..", "^")) or (pk == "op" and pv in (".", "..")):
        return ""
    if ck == "op" and cv == "[":
        return "" if (pk == "ident" or pv in (")", "]", "^")) else " "
    if ck == "op" and cv == "(":
        if pk == "ident":
            u = pv.upper()
            if u not in RESERVED or u in TYPES:
                return ""
        if pk == "op" and pv in (")", "]", "^"):
            return ""
        return " "
    if ck == "op" and cv == ":":
        if cur is label_colon:
            return ""
        return " " if o["decl_colon_style"].startswith(" ") else ""
    if pk == "op" and pv == ":":
        return " "
    if (ck == "op" and cv in BINOPS) or (pk == "op" and pv in BINOPS):
        return " " if o["space_around_operators"] else ""
    return " "


def _find_label_colon(code):
    """Return index of the ':' ending a CASE label at the start of a line, else None."""
    for k, t in enumerate(code):
        if t.kind == "op" and t.v == ":":
            return k if k > 0 else None
        if t.kind in ("number", "literal", "string"):
            continue
        if t.kind == "ident":
            u = t.v.upper()
            if u in RESERVED and u not in KW_CONST:
                return None
            continue
        if t.kind == "op" and t.v in (",", "..", "-", "+", "."):
            continue
        return None
    return None


def _build_line(tokens, o, stack, paren):
    """Analyse one physical line. Mutates stack; returns (Line, new_paren)."""
    line = Line()
    sig, pre_ws = [], []
    pending_ws = ""
    for t in tokens:
        if t.kind == "ws":
            pending_ws = t.v
        else:
            sig.append(t)
            pre_ws.append(pending_ws)
            pending_ws = ""
    if not sig:
        line.blank = True
        return line, paren

    in_decl_ctx = bool(stack) and stack[-1][0] in DECL_CONTEXT
    start_paren = list(paren)
    min_d = _depth(stack)
    code_toks = [t for t in sig if t.kind not in COMMENT_KINDS]

    # CASE labels
    label_colon = None
    if stack and stack[-1][0] in ("CASE", "CASE_ITEM") and code_toks:
        idx = _find_label_colon(code_toks)
        if idx is not None:
            label_colon = code_toks[idx]
            if stack[-1][0] == "CASE_ITEM":
                stack.pop()
                min_d = min(min_d, _depth(stack))

    # block structure
    decl_colon = None
    assign_tok = None
    local_paren = 0
    for t in code_toks:
        if t is label_colon:
            stack.append(["CASE_ITEM", 1 if o["indent_case_items"] else 0])
            continue
        if t.kind == "ident":
            u = t.v.upper()
            if u in OPENERS:
                kind = OPENERS[u]
                inc = 0 if (kind in POU_KINDS and not o["indent_pou_body"]) else 1
                stack.append([kind, inc])
            elif u in CLOSERS:
                if _pop_to(stack, CLOSERS[u]):
                    min_d = min(min_d, _depth(stack))
            elif u in ("ELSE", "ELSIF", "UNTIL"):
                if u == "ELSE" and stack and stack[-1][0] == "CASE_ITEM":
                    stack.pop()
                if stack:
                    top = stack[-1]
                    ok = (u == "ELSE" and top[0] in ("IF", "CASE")) or \
                         (u == "ELSIF" and top[0] == "IF") or \
                         (u == "UNTIL" and top[0] == "REPEAT")
                    if ok:
                        min_d = min(min_d, _depth(stack) - top[1])
        elif t.kind == "op":
            if t.v in ("(", "["):
                paren.append((t.role, max(0, min_d)))
                local_paren += 1
            elif t.v in (")", "]"):
                if paren:
                    paren.pop()
                local_paren -= 1
            elif t.v == ":" and decl_colon is None and local_paren == 0:
                decl_colon = t
            elif t.v in (":=", "=>") and assign_tok is None and local_paren == 0:
                assign_tok = t

    indent, extra = max(0, min_d), 0
    first = sig[0]
    if first.role == "call_open":
        indent += int(o.get("call_paren_indent", 1))
    elif start_paren and start_paren[-1][0] == "call_open":
        indent = start_paren[-1][1] + int(o.get("call_paren_indent", 1))
        extra = int(o.get("call_param_offset", 1))
    elif start_paren and not (first.kind == "op" and first.v in (")", "]")):
        indent += 1
    line.indent = indent
    line.extra = extra
    if o["attribute_column0"] and _is_attribute(first):
        line.indent = 0
        line.extra = 0

    # split off trailing comments
    end = len(sig)
    multiline_comment = any(t.kind == "bcomment" and ("\n" in t.v or "\r" in t.v) for t in sig)
    while end > 0 and sig[end - 1].kind in COMMENT_KINDS:
        end -= 1
    if end == 0:
        end = len(sig)          # comment-only line: treat it as "code"

    # render code
    parts, prev, prev_unary, colon_pos, assign_pos = [], None, False, None, None
    for k in range(end):
        t = sig[k]
        if prev is not None:
            if o["normalize_spacing"]:
                sp = _sep(prev, t, prev_unary, o, label_colon)
            else:
                sp = pre_ws[k] or ""
            if t is decl_colon:
                colon_pos = len("".join(parts))
            if t is assign_tok:
                assign_pos = len("".join(parts))
            parts.append(sp)
        parts.append(_display(t, o, sig[k + 1] if k + 1 < len(sig) else None))
        prev_unary = _is_unary(prev, t)
        prev = t
    code = "".join(parts)

    comment = ""
    if end < len(sig):
        cparts = []
        for k in range(end, len(sig)):
            if cparts:
                cparts.append(" " if o["normalize_spacing"] else (pre_ws[k] or " "))
            cparts.append(sig[k].v)
        comment = "".join(cparts)

    line.code = code
    line.comment = comment
    if in_decl_ctx and decl_colon is not None and colon_pos is not None and not multiline_comment:
        line.left = code[:colon_pos].rstrip()
        line.right = code[colon_pos:].lstrip()
        line.alignable = True
        line.decl_gap = int(o["decl_min_gap"])
        if comment and o["decl_comment_style"] == "//":
            line.comment = _to_line_comment(comment)
    elif (assign_pos is not None
          and (not in_decl_ctx or (start_paren and start_paren[-1][0] == "call_open"))
          and label_colon is None
          and decl_colon is None and not multiline_comment and code_toks
          and code_toks[0].kind == "ident"
          and (code_toks[0].v.upper() not in RESERVED or code_toks[0].v.upper() in ("THIS", "SUPER"))):
        line.a_left = code[:assign_pos].rstrip()
        line.a_right = code[assign_pos:].lstrip()
    return line, paren


def _is_attribute(t):
    return t.kind == "pragma" and re.match(r"\{\s*attribute\b", t.v, re.I) is not None


def _to_line_comment(comment):
    """'(* text *)' or '/* text */' -> '// text' (only for a single trailing block comment)."""
    m = re.match(r"^(?:\(\*(.*?)\*\)|/\*(.*?)\*/)$", comment, re.S)
    if not m:
        return comment
    body = (m.group(1) if m.group(1) is not None else m.group(2)).strip()
    return ("// " + body) if body else "//"


def _indent_str(level, o):
    if o["use_tabs"]:
        return "\t" * level
    return " " * (level * int(o["indent_size"]))


def _lw(L, o):
    return _ind_width(L.indent, o) + L.extra


def _ind_width(level, o):
    return level * int(o["indent_size"])


def _groups(lines, is_member):
    """Runs of consecutive member lines with equal indent; comment-only lines are skipped."""
    i, n = 0, len(lines)
    while i < n:
        if not is_member(lines[i]):
            i += 1
            continue
        group, j = [], i
        while j < n:
            L = lines[j]
            if is_member(L) and L.indent == lines[i].indent:
                group.append(L)
            elif L.blank or not L.code.startswith(("//", "(*", "/*")):
                break
            j += 1
        yield group
        i = j


def _col_target(fixed_col, needed_abs):
    """Absolute 0-based column to pad to. fixed_col is 1-based (0 = auto)."""
    if fixed_col and int(fixed_col) > 0:
        return int(fixed_col) - 1
    return needed_abs


def _align(lines, o):
    joiner = " " if o["decl_colon_style"].startswith(" ") else ""
    gap_c = int(o["comment_min_gap"])

    def is_decl(L):
        return L.alignable and o["align_declarations"]

    def is_asg(L):
        return L.a_left is not None and o["align_assignments"]

    def parts(L):
        if L.alignable:
            return L.left, L.right, int(o["decl_min_gap"])
        return L.a_left, L.a_right, int(o["assign_min_gap"])

    # unaligned declarations still need their joiner
    for L in lines:
        if L.alignable and not o["align_declarations"]:
            L.code = L.left + joiner + L.right

    # ':' / ':=' column
    if o["align_scope"] == "file":
        members = [L for L in lines if is_decl(L) or is_asg(L)]
        groups = [members] if members else []
    else:
        groups = list(_groups(lines, is_decl)) + list(_groups(lines, is_asg))
    for g in groups:
        need = max(_lw(L, o) + len(parts(L)[0]) + parts(L)[2] for L in g)
        target = _col_target(o["align_column"], need)
        for L in g:
            left, right, gap = parts(L)
            iw = _lw(L, o)
            width = max(target, iw + len(left) + gap) - iw
            L.code = left.ljust(width) + right
            L.aligned = True

    # comment column
    if not o["align_comments"]:
        return

    def has_tail_comment(L):
        return (not L.blank and L.comment and "\n" not in L.comment and "\r" not in L.comment
                and "\n" not in L.code and "\r" not in L.code)

    def end_col(L):
        return _lw(L, o) + len(L.code)

    if o["align_scope"] == "file":
        cgroups = [[L for L in lines if has_tail_comment(L)]]
    else:
        cgroups = [[L for L in g if has_tail_comment(L)] for g in groups]
    for g in cgroups:
        if not g:
            continue
        basis = [L for L in g if getattr(L, "aligned", False)] or g
        target = _col_target(o["comment_column"], max(end_col(L) for L in basis) + gap_c)
        for L in g:
            iw = _lw(L, o)
            width = max(target, end_col(L) + gap_c) - iw
            L.code = L.code.ljust(width)
            L.comment_attached = True


_STMT_KEYWORDS = set("THEN ELSE DO OF REPEAT END_VAR END_IF END_CASE END_FOR END_WHILE "
                     "END_REPEAT REGION END_REGION".split())
_NON_CODE = ("ws", "nl", "lcomment", "bcomment", "pragma")


def _stmt_boundary(prev):
    """True if a new statement may start after code token `prev`."""
    if prev is None:
        return True
    if prev.kind == "op" and prev.v in (";", ":"):
        return True
    if prev.kind == "rname":
        return True
    return prev.kind == "ident" and prev.v.upper() in _STMT_KEYWORDS


def _match_call(toks, i, o):
    """At toks[i] (an identifier at the start of a statement) try to match
    name(...)[;] with named parameters. Returns (new_tokens, next_index, last_token) or None."""
    n = len(toks)
    k = i + 1
    # name: a.b.c, a[i].b ...
    while k < n:
        t = toks[k]
        if t.kind == "op" and t.v == "." and k + 1 < n and toks[k + 1].kind == "ident":
            k += 2
        elif t.kind == "op" and t.v == "[":
            depth = 0
            while k < n:
                if toks[k].kind == "op" and toks[k].v == "[":
                    depth += 1
                elif toks[k].kind == "op" and toks[k].v == "]":
                    depth -= 1
                    if depth == 0:
                        k += 1
                        break
                elif toks[k].kind == "nl":
                    return None
                k += 1
        else:
            break
    name = [t for t in toks[i:k] if t.kind != "ws"]
    while k < n and toks[k].kind in ("ws", "nl"):
        k += 1
    if k >= n or not (toks[k].kind == "op" and toks[k].v == "("):
        return None
    r = _expand_paren(toks, k, o)
    if r is None:
        return None
    body, j = r
    return _finish_expanded(toks, list(name) + body, j)


def _match_decl(toks, i, o):
    """At toks[i] (first identifier of a declaration) try to match
    name : Type(a := 1, ...)[;]  or  name : Type := (a := 1, ...)[;].
    Returns (new_tokens, next_index, last_token) or None."""
    n, k, colon, depth = len(toks), i, False, 0
    while k < n:
        t = toks[k]
        if t.kind in ("lcomment", "bcomment", "pragma", "rname"):
            return None
        if t.kind == "op":
            if t.v == ";":
                return None
            if t.v == ":" and depth == 0:
                colon = True
            elif t.v == "[":
                depth += 1
            elif t.v == "]":
                depth -= 1
            elif t.v == "(" and depth == 0:
                break
        k += 1
    if k >= n or not colon:
        return None
    r = _expand_paren(toks, k, o)
    if r is None:
        return None
    body, j = r
    head = [t for t in toks[i:k] if t.kind != "nl"]
    while head and head[-1].kind == "ws":
        head.pop()
    return _finish_expanded(toks, head + body, j)


def _expand_paren(toks, k, o):
    """toks[k] is '('. If its content has named parameters return
    ([nl, '(', nl, params..., ')'], index_of_closing_paren), else None."""
    n = len(toks)
    # matching ')'
    depth, j = 0, k
    while j < n:
        t = toks[j]
        if t.kind == "op" and t.v == "(":
            depth += 1
        elif t.kind == "op" and t.v == ")":
            depth -= 1
            if depth == 0:
                break
        j += 1
    if j >= n:
        return None
    inner = toks[k + 1:j]
    # named parameters at depth 1?
    depth, named = 0, False
    for t in inner:
        if t.kind == "op" and t.v in ("(", "["):
            depth += 1
        elif t.kind == "op" and t.v in (")", "]"):
            depth -= 1
        elif depth == 0 and t.kind == "op" and t.v in (":=", "=>"):
            named = True
    if not named:
        return None
    # split into parameters; a comment right after ',' stays with that parameter
    segs, cur, depth, attach = [], [], 0, False
    for t in inner:
        if attach:
            if t.kind == "ws":
                continue
            if t.kind in ("lcomment", "bcomment"):
                segs[-1].append(Tok("ws", " "))
                segs[-1].append(t)
                continue
            attach = False
            if t.kind == "nl":
                continue
        if t.kind == "op" and t.v in ("(", "["):
            depth += 1
        elif t.kind == "op" and t.v in (")", "]"):
            depth -= 1
        if depth == 0 and t.kind == "op" and t.v == ",":
            cur.append(t)
            segs.append(cur)
            cur, attach = [], True
            continue
        cur.append(t)
    segs.append(cur)

    def strip(seg):
        a, b = 0, len(seg)
        while a < b and seg[a].kind in ("ws", "nl"):
            a += 1
        while b > a and seg[b - 1].kind in ("ws", "nl"):
            b -= 1
        return seg[a:b]

    segs = [strip(sg) for sg in segs]
    segs = [sg for sg in segs if sg]
    if len(segs) < int(o.get("call_expand_min_params", 1)):
        return None
    nl = Tok("nl", "\n")
    out = [nl, Tok("op", "(", "call_open"), nl]
    for sg in segs:
        out.extend(sg)
        out.append(nl)
    out.append(Tok("op", ")", "call_close"))
    return out, j


def _finish_expanded(toks, out, j):
    """Append an optional ';' after the closing paren at toks[j]; returns (out, next_index, last)."""
    n = len(toks)
    last = toks[j]
    j += 1
    m = j
    while m < n and toks[m].kind == "ws":
        m += 1
    if m < n and toks[m].kind == "op" and toks[m].v == ";":
        out.append(toks[m])
        last = toks[m]
        j = m + 1
    return out, j, last


def _expand_calls(toks, o):
    out, i, n = [], 0, len(toks)
    prev, line_start, decl_start = None, True, True
    var_depth = 0          # > 0 inside VAR ... END_VAR / STRUCT ... END_STRUCT
    while i < n:
        t = toks[i]
        if t.kind == "nl":
            out.append(t)
            line_start = decl_start = True
            i += 1
            continue
        if t.kind in _NON_CODE:
            out.append(t)
            if t.kind != "ws":
                line_start = False
            if t.kind not in ("ws", "pragma"):
                decl_start = False
            i += 1
            continue
        if t.kind == "ident":
            u = t.v.upper()
            if u in VAR_KINDS or u in ("STRUCT", "UNION"):
                var_depth += 1
            elif u in ("END_VAR", "END_STRUCT", "END_UNION"):
                var_depth = max(0, var_depth - 1)
        if (var_depth and o.get("decl_init_expand", True) and decl_start
                and t.kind == "ident" and t.v.upper() not in RESERVED):
            m = _match_decl(toks, i, o)
            if m:
                new, i, prev = m
                out.extend(new)
                line_start = decl_start = False
                continue
        decl_start = False
        if (line_start and t.kind == "ident" and t.v.upper() not in RESERVED
                and _stmt_boundary(prev)):
            m = _match_call(toks, i, o)
            if m:
                new, i, prev = m
                out.extend(new)
                line_start = False
                continue
        out.append(t)
        prev = t
        line_start = False
        i += 1
    return out


def format_st(text, options=None):
    o = dict(OPTIONS)
    if options:
        o.update(options)
    m = re.search(r"\r\n|\n|\r", text)
    eol = m.group(0) if m else "\r\n"

    toks = tokenize(text)
    if o.get("call_style", "expanded") == "expanded":
        toks = _expand_calls(toks, o)
    physical = [[]]
    for t in toks:
        if t.kind == "nl":
            physical.append([])
        else:
            physical[-1].append(t)

    stack, paren, lines = [], [], []
    k = 0
    while k < len(physical):
        toks = physical[k]
        sig = [t for t in toks if t.kind != "ws"]
        if (o["attribute_join"] and sig and all(_is_attribute(t) for t in sig)
                and stack and stack[-1][0] in DECL_CONTEXT and k + 1 < len(physical)):
            nxt = [t for t in physical[k + 1] if t.kind != "ws"]
            if nxt and nxt[0].kind == "ident" and nxt[0].v.upper() not in RESERVED:
                toks = sig + [Tok("ws", " ")] + physical[k + 1]
                k += 1
        line, paren = _build_line(toks, o, stack, paren)
        lines.append(line)
        k += 1

    _align(lines, o)

    out, blanks = [], 0
    for L in lines:
        if L.blank:
            blanks += 1
            if blanks <= int(o["max_blank_lines"]) and out:
                out.append("")
            continue
        blanks = 0
        s = _indent_str(L.indent, o) + " " * L.extra + L.code
        if L.comment:
            s += L.comment if getattr(L, "comment_attached", False) else " " + L.comment
        out.append(s.rstrip(" \t"))
    while out and out[-1] == "":
        out.pop()
    result = eol.join(out)
    if o["ensure_final_newline"] and result:
        result += eol
    return result


# ---------------------------------------------------------------------------
# Hungarian notation checker
# ---------------------------------------------------------------------------
def _known_prefixes():
    mem = set(MEMORY_PREFIX.values())
    typ = set(p for v in TYPE_PREFIX.values() for p in v)
    known = set(m + t for m in mem for t in (typ | _OTHER_PREFIXES)) | mem | typ | _OTHER_PREFIXES
    known.discard("")
    return known


def _suggest(name, prefix):
    if _ALLCAPS.match(name):
        return prefix + "".join(w.capitalize() for w in name.split("_") if w)
    m = re.match(r"^([a-z]+)([A-Z0-9].*)$", name)
    if m and m.group(1) in _known_prefixes():
        core = m.group(2)
    else:
        core = name[:1].upper() + name[1:]
    return prefix + core


_ALLCAPS = re.compile(r"^[A-Z][A-Z0-9_]*$")
_INTERFACE = ("VAR_INPUT", "VAR_OUTPUT", "VAR_IN_OUT")


def _terminal_code_error(name):
    """None if name is a valid IEC PAS 63131 terminal code, else an explanation."""
    first = name[0]
    if first not in TERMINAL_FIRST:
        return ("'%s' is not a valid first letter\nvalid first letters: %s"
                % (first, " ".join(sorted(TERMINAL_FIRST))))
    for ch in name[1:]:
        if ch in "123456789":
            continue
        if ch not in TERMINAL_NEXT:
            return ("'%s' is not a valid succeeding character\nvalid: %s and digits 1-9"
                    % (ch, " ".join(sorted(TERMINAL_NEXT))))
    return None


def describe_terminal_code(name):
    parts = ["%s = %s" % (name[0], TERMINAL_FIRST.get(name[0], "?"))]
    for ch in name[1:]:
        parts.append("%s = %s" % (ch, "terminal no." if ch.isdigit() else TERMINAL_NEXT.get(ch, "?")))
    return ", ".join(parts)


def _base_type(ttoks):
    """Return upper-case base type name, following ARRAY ... OF; None = complex."""
    idents = [t for t in ttoks if t.kind == "ident"]
    if not idents:
        return None
    u = idents[0].v.upper()
    if u == "ARRAY":
        for k, t in enumerate(ttoks):
            if t.kind == "ident" and t.v.upper() == "OF":
                return _base_type(ttoks[k + 1:])
        return None
    if u in ("POINTER", "REFERENCE", "REF_TO"):
        return None
    if len(ttoks) > 1 and ttoks[1].kind == "op" and ttoks[1].v == ".":
        return None                      # Library.Type
    return u


def _memory_prefixes(section, flags, pou, addr, in_struct):
    M = MEMORY_PREFIX
    if in_struct:
        return [M["STRUCT_MEMBER"]], "STRUCT member"
    a = (addr or "").upper()
    if a.startswith("%I"):
        return [M["AT_INPUT"]], "AT %I"
    if a.startswith("%Q"):
        return [M["AT_OUTPUT"]], "AT %Q"
    const = "CONSTANT" in flags
    if section in ("VAR_GLOBAL", "VAR_EXTERNAL"):
        if const:
            return [M["VAR_GLOBAL_CONSTANT"]], section + " CONSTANT"
        if section == "VAR_EXTERNAL":
            return [M["VAR_GLOBAL"], M["AT_INPUT"], M["AT_OUTPUT"]], section
        return [M["VAR_GLOBAL"]], section
    if section in ("VAR_INPUT", "VAR_OUTPUT", "VAR_IN_OUT"):
        return [M[section]], section
    if const:
        return [M["VAR_CONSTANT"]], section + " CONSTANT"
    if section == "VAR":
        if pou and pou[-1] in ("FUNCTION", "METHOD"):
            return [M["VAR_IN_FUNCTION"]], "VAR in " + pou[-1]
        return [M["VAR"]], "VAR"
    if section in M:
        return [M[section]], section
    return None, section


def _has_ignored_prefix(name, prefix):
    """name is the prefix alone, or the prefix followed by a capital, digit or '_'."""
    if not name.startswith(prefix):
        return False
    rest = name[len(prefix):]
    return not rest or rest[0].isupper() or rest[0].isdigit() or rest[0] == "_"


def _union_view_ok(name):
    for lst in TYPE_PREFIX.values():
        for p in lst:
            if p and name.startswith(p) and (len(name) == len(p) or name[len(p)].isupper()
                                             or name[len(p)].isdigit()):
                return True
    return False


def _is_skip_marker(t, attr):
    if t.kind not in ("lcomment", "bcomment"):
        return False
    body = " ".join(t.v.replace("/", " ").replace("(*", " ").replace("*)", " ").split()).lower()
    return ("{attribute '%s'}" % attr).lower() in body


def _skip_attribute_present(toks, attr):
    """True if a skip marker comment appears before the first real code token."""
    for t in toks:
        if _is_skip_marker(t, attr):
            return True
        if t.kind not in ("ws", "nl", "lcomment", "bcomment", "pragma"):
            return False
    return False


def check_names(text, options=None):
    """Return a list of (char_start, char_length, message) for badly named declarations."""
    o = dict(OPTIONS)
    if options:
        o.update(options)
    ignore = set(o.get("naming_ignore") or [])
    ign_prefixes = tuple(o.get("naming_ignore_prefixes") or ())
    check_members = o.get("naming_check_type_members", True)
    ign_types = set(x.upper() for x in (o.get("naming_ignore_types") or []))
    toks = tokenize(text)
    pos = 0
    for t in toks:
        t.pos = pos
        pos += len(t.v)
    if o.get("naming_skip_attribute") and _skip_attribute_present(toks, o["naming_skip_attribute"]):
        return []
    marker_lines = set()
    if o.get("naming_skip_attribute"):
        marker_lines = set(text.count("\n", 0, t.pos) for t in toks
                           if _is_skip_marker(t, o["naming_skip_attribute"]))

    def _marked(tok):
        return bool(marker_lines) and text.count("\n", 0, tok.pos) in marker_lines
    sig = [t for t in toks if t.kind not in ("ws", "nl", "lcomment", "bcomment", "pragma")]
    issues = []
    pou, section, flags, struct, aggr = [], None, set(), 0, []
    var_skip, aggr_skip = False, []
    stop_words = set(["END_VAR", "END_STRUCT", "END_UNION"])
    i, n = 0, len(sig)
    while i < n:
        t = sig[i]
        u = t.v.upper() if t.kind == "ident" else None
        if u in POU_KINDS:
            pou.append(u)
            i += 1
            continue
        if u and u.startswith("END_") and u[4:] in POU_KINDS:
            _k = u[4:]
            while pou:
                if pou.pop() == _k:
                    break
            i += 1
            continue
        if u in VAR_KINDS:
            section, flags = u, set()
            var_skip = _marked(t)
            i += 1
            while i < n and sig[i].kind == "ident" and sig[i].v.upper() in (
                    "CONSTANT", "RETAIN", "PERSISTENT", "NON_RETAIN"):
                flags.add(sig[i].v.upper())
                i += 1
            continue
        if u == "END_VAR":
            section = None
            var_skip = False
            i += 1
            continue
        if u in ("STRUCT", "UNION"):
            struct += 1
            aggr.append(u)
            aggr_skip.append(_marked(t))
            i += 1
            continue
        if u in ("END_STRUCT", "END_UNION"):
            struct = max(0, struct - 1)
            if aggr:
                aggr.pop()
                aggr_skip.pop()
            i += 1
            continue
        if (section or struct) and t.kind == "ident" and u not in RESERVED:
            names, addr, j = [], None, i
            while j < n:
                tj = sig[j]
                if tj.kind == "ident" and tj.v.upper() == "AT":
                    addr = sig[j + 1].v if j + 1 < n else ""
                    j += 2
                elif tj.kind == "ident" and tj.v.upper() not in RESERVED:
                    names.append(tj)
                    j += 1
                elif tj.kind == "op" and tj.v == ",":
                    j += 1
                else:
                    break
            if j < n and sig[j].kind == "op" and sig[j].v == ":":
                k, depth, ttoks = j + 1, 0, []
                while k < n:
                    tk = sig[k]
                    if tk.kind == "ident" and tk.v.upper() in stop_words:
                        break
                    if tk.kind == "op":
                        if tk.v in ("(", "["):
                            depth += 1
                        elif tk.v in (")", "]"):
                            depth -= 1
                        elif depth == 0 and tk.v in (";", ":="):
                            break
                    ttoks.append(tk)
                    k += 1
                base = _base_type(ttoks)
                mems, where = _memory_prefixes(section, flags, pou, addr, struct > 0)
                if base in ign_types or (struct > 0 and not check_members) or var_skip or any(aggr_skip):
                    mems = None
                if mems is not None:
                    tps = TYPE_PREFIX.get(base, [""]) if base else [""]
                    tname = base if (base and base in TYPE_PREFIX) else "complex type"
                    allowed = [m + tp for m in mems for tp in tps]
                    for nm in names:
                        name = nm.v
                        if name in ignore:
                            continue
                        if ign_prefixes and any(_has_ignored_prefix(name, x) for x in ign_prefixes):
                            continue
                        if o["naming_union_views"] and aggr and aggr[-1] == "UNION" and _union_view_ok(name):
                            continue
                        if section in _INTERFACE and not struct and _ALLCAPS.match(name):
                            if o["terminal_code_check"]:
                                err = _terminal_code_error(name)
                                if err:
                                    msg = ("%s  [%s]\nnot a valid IEC PAS 63131 terminal code: %s"
                                           % (name, section, err))
                                    issues.append((nm.pos, len(name), msg))
                            continue
                        ok = any(name.startswith(p) and len(name) > len(p) and (name[len(p)].isupper() or name[len(p)].isdigit())
                                 for p in allowed)
                        if not ok:
                            shown = " or ".join("'%s'" % p if p else "a capital letter" for p in allowed)
                            msg = ("%s  [%s, %s]\nexpected prefix %s followed by a capital letter or digit"
                                   "\nsuggestion: %s") % (name, where, tname, shown, _suggest(name, allowed[0]))
                            issues.append((nm.pos, len(name), msg))
                depth = 0
                while k < n:
                    tk = sig[k]
                    if tk.kind == "ident" and tk.v.upper() in stop_words:
                        break
                    if tk.kind == "op":
                        if tk.v in ("(", "["):
                            depth += 1
                        elif tk.v in (")", "]"):
                            depth -= 1
                        elif depth == 0 and tk.v == ";":
                            k += 1
                            break
                    k += 1
                i = k
                continue
            i = j if j > i else i + 1
            continue
        i += 1
    return issues


# ---------------------------------------------------------------------------
# Spell checker for comments (Hunspell .dic/.aff files, standard library only)
# ---------------------------------------------------------------------------
class SpellError(Exception):
    """Dictionary missing / unreadable - the message explains what to do."""


def _spell_codec(name):
    import codecs
    n = (name or "UTF-8").strip()
    for cand in (n, n.replace("ISO8859-", "iso-8859-"), n.replace("microsoft-", "")):
        try:
            codecs.lookup(cand)
            return cand
        except LookupError:
            pass
    return "latin-1"


def _read_bytes(path):
    with open(path, "rb") as f:
        raw = f.read()
    return raw[3:] if raw.startswith(b"\xef\xbb\xbf") else raw


class _Hunspell(object):
    """One Hunspell dictionary: suffix/prefix rules (also two-level suffixes and
    prefix+suffix cross products). Compounding is handled by _Speller."""

    def __init__(self, base):
        self.words = {}
        self.flagmode = "char"
        self.try_chars = u""
        self.needaffix = self.onlyic = self.forbidden = None
        self.sfx_last, self.sfx_empty = {}, []
        self.pfx_first, self.pfx_empty = {}, []
        self._fs = {}
        enc = "utf-8"
        aff = base + ".aff"
        if os.path.exists(aff):
            raw = _read_bytes(aff)
            m = re.search(br"^SET[ \t]+(\S+)", raw, re.M)
            enc = _spell_codec(m.group(1).decode("ascii", "replace")) if m else "latin-1"
            self._parse_aff(raw.decode(enc, "replace"))
        self._parse_dic(_read_bytes(base + ".dic").decode(enc, "replace"))

    def _flags(self, s):
        r = self._fs.get(s)
        if r is None:
            if self.flagmode == "long":
                r = frozenset(s[i:i + 2] for i in range(0, len(s), 2))
            elif self.flagmode == "num":
                r = frozenset(x for x in s.split(",") if x)
            else:
                r = frozenset(s)
            self._fs[s] = r
        return r

    def _parse_aff(self, text):
        cross = {}
        for line in text.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            p = line.split()
            key = p[0]
            if key == "FLAG" and len(p) > 1:
                self.flagmode = "long" if p[1] == "long" else ("num" if p[1] == "num" else "char")
            elif key == "TRY" and len(p) > 1:
                self.try_chars = p[1]
            elif key in ("NEEDAFFIX", "PSEUDOROOT") and len(p) > 1:
                self.needaffix = p[1]
            elif key == "ONLYINCOMPOUND" and len(p) > 1:
                self.onlyic = p[1]
            elif key == "FORBIDDENWORD" and len(p) > 1:
                self.forbidden = p[1]
            elif key in ("PFX", "SFX") and len(p) >= 4:
                if len(p) == 4 and p[2] in ("Y", "N") and p[3].isdigit():
                    cross[(key, p[1])] = (p[2] == "Y")        # rule group header
                    continue
                flag, strip, add = p[1], p[2], p[3]
                cond = p[4] if len(p) > 4 else "."
                strip = "" if strip == "0" else strip
                cont = ""
                if "/" in add:
                    add, cont = add.split("/", 1)
                add = "" if add == "0" else add
                rx = None
                if cond != ".":
                    try:
                        rx = re.compile(cond + "$" if key == "SFX" else "^" + cond, re.UNICODE)
                    except re.error:
                        continue
                rule = (flag, cross.get((key, flag), True), strip, add, rx, self._flags(cont))
                if key == "SFX":
                    if add:
                        self.sfx_last.setdefault(add[-1], []).append(rule)
                    else:
                        self.sfx_empty.append(rule)
                else:
                    if add:
                        self.pfx_first.setdefault(add[0], []).append(rule)
                    else:
                        self.pfx_empty.append(rule)

    def _parse_dic(self, text):
        lines = text.splitlines()
        start = 1 if lines and lines[0].strip().isdigit() else 0
        join = "," if self.flagmode == "num" else ""
        words = self.words
        split_flags = re.compile(r"(?<!\\)/")
        for line in lines[start:]:
            if not line.strip() or line[0] == "\t":
                continue
            parts = split_flags.split(line.split()[0], 1)
            w = parts[0].replace("\\/", "/")
            f = parts[1] if len(parts) > 1 else ""
            old = words.get(w)
            words[w] = f if old is None else old + join + f

    def _sfx(self, w):
        out = []
        for flag, cross, strip, add, rx, cont in list(self.sfx_last.get(w[-1:], ())) + self.sfx_empty:
            if add and not w.endswith(add):
                continue
            base = (w[:len(w) - len(add)] if add else w) + strip
            if base and (rx is None or rx.search(base)):
                out.append((flag, cross, base, cont))
        return out

    def _pfx(self, w):
        out = []
        for flag, cross, strip, add, rx, cont in list(self.pfx_first.get(w[:1], ())) + self.pfx_empty:
            if add and not w.startswith(add):
                continue
            base = strip + w[len(add):]
            if base and (rx is None or rx.search(base)):
                out.append((flag, cross, base, cont))
        return out

    def _has(self, stem, flag):
        f = self.words.get(stem)
        return f is not None and flag in self._flags(f)

    def _affix_check(self, w):
        f = self.words.get(w)
        if f is not None:
            s = self._flags(f)
            if self.forbidden is not None and self.forbidden in s:
                return False
            if not ((self.needaffix is not None and self.needaffix in s) or
                    (self.onlyic is not None and self.onlyic in s)):
                return True
        for flag, cross, base, cont in self._sfx(w):
            if self._has(base, flag):
                return True
            for flag2, cross2, base2, cont2 in self._sfx(base):      # two-level suffix
                if flag in cont2 and self._has(base2, flag2):
                    return True
        for pflag, pcross, pbase, pcont in self._pfx(w):
            if self._has(pbase, pflag):
                return True
            if pcross:                                              # prefix + suffix
                for flag, cross, base, cont in self._sfx(pbase):
                    f = self.words.get(base)
                    if cross and f is not None:
                        s = self._flags(f)
                        if pflag in s and flag in s:
                            return True
        return False

    def check(self, w):
        if self._affix_check(w):
            return True
        low = w.lower()
        if w == low:
            return False
        if w.isupper():
            return self._affix_check(low) or self._affix_check(low[:1].upper() + low[1:])
        if w[:1].isupper() and w[1:] == low[1:]:
            return self._affix_check(low)
        return False


class _Speller(object):
    def __init__(self, dicts, compounds=True):
        self.dicts = dicts
        self.compounds = compounds
        self._memo = {}

    def plain(self, w):
        r = self._memo.get(w)
        if r is None:
            r = any(d.check(w) for d in self.dicts)
            self._memo[w] = r
        return r

    def _compound(self, w, parts):
        """Words glued from 2-4 valid words, optionally with a linking s/e (Norwegian)."""
        if parts < 2:
            return False
        for i in range(3, len(w) - 2):
            head, tail = w[:i], w[i:]
            if not (self.plain(head) or (head[-1] in u"se" and len(head) > 3 and self.plain(head[:-1]))):
                continue
            if self.plain(tail) or self._compound(tail, parts - 1):
                return True
        return False

    def check(self, w):
        if self.plain(w):
            return True
        if w.endswith(u"'s") and self.plain(w[:-2]):
            return True
        return self.compounds and 7 <= len(w) <= 40 and self._compound(w.lower(), 4)

    def suggest(self, w, limit):
        low = w.lower()
        letters = u"".join(d.try_chars for d in self.dicts)
        letters = u"".join(sorted(set(letters.lower()))) or u"abcdefghijklmnopqrstuvwxyz"
        splits = [(low[:i], low[i:]) for i in range(len(low) + 1)]
        cands = [a + b[1] + b[0] + b[2:] for a, b in splits if len(b) > 1]          # transposed
        cands += [a + b[1:] for a, b in splits if b]                                  # deleted
        cands += [a + c + b[1:] for a, b in splits if b for c in letters]            # replaced
        cands += [a + c + b for a, b in splits for c in letters]                      # inserted
        cands += [low[:i] + u" " + low[i:] for i in range(2, len(low) - 1)           # two words
                  if self.plain(low[:i]) and self.plain(low[i:])]
        out, seen = [], set([low])
        for c in cands:
            if c in seen:
                continue
            seen.add(c)
            if u" " in c or self.plain(c):
                out.append(c)
                if len(out) >= limit:
                    break
        if w[:1].isupper():
            out = [x[:1].upper() + x[1:] for x in out]
        return out


class _ComPtr(object):
    """Minimal COM interface pointer driven through ctypes (vtable calls, no packages)."""

    def __init__(self, address):
        self.addr = address

    def call(self, index, argtypes, *args):
        import ctypes
        vtbl = ctypes.cast(self.addr, ctypes.POINTER(ctypes.c_void_p))[0]
        fn = ctypes.cast(vtbl, ctypes.POINTER(ctypes.c_void_p))[index]
        proto = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, *argtypes)
        return proto(fn)(self.addr, *args)

    def release(self):
        if self.addr:
            self.call(2, [])
            self.addr = None


class _WinSpeller(object):
    """The spelling engine of Windows (ISpellChecker, Windows 8+): the same dictionaries as
    Word/Edge/Notepad, including the Windows custom word list. Norwegian compounds are handled
    by Windows itself.

    Text is handed to Windows either as c_wchar_p (mode 1) or as UTF-16 buffers (mode 2); some
    hosts (an interactive CODESYS session) fail on the first, so mode 2 is tried as a fallback."""
    CLSID_FACTORY = "{7AB36653-1796-484B-BDFA-E74F1DB7C1DC}"
    IID_FACTORY = "{8E018A9D-2415-4677-BF08-794EA61F94BB}"
    MODES = (False, True)                       # string args first, UTF-16 buffers as fallback

    def __init__(self, languages):
        import ctypes
        self.ct = ctypes
        self.factory, self.checkers, self._memo = None, [], {}
        self.step, errors = "start", []
        if not hasattr(ctypes, "windll"):
            raise SpellError("The Windows spelling backend only works on Windows.")
        for use_buf in self.MODES:
            self.use_buf = use_buf
            self.wt = ctypes.c_void_p if use_buf else ctypes.c_wchar_p
            try:
                self._open(languages)
                return
            except SpellError:
                raise
            except Exception as e:
                errors.append("%s mode: step '%s': %s: %s"
                              % ("buffer" if use_buf else "string", self.step, e.__class__.__name__, e))
                try:
                    self.close()
                except Exception:
                    pass
        raise SpellError("The Windows spelling backend failed.\n" + "\n".join(errors))

    def _w(self, text):
        if not isinstance(text, type(u"")):
            try:
                text = text.decode("utf-8")
            except Exception:
                text = type(u"")(text)
        return self.ct.create_unicode_buffer(text) if self.use_buf else self.ct.c_wchar_p(text)

    def _guid(self, text):
        import struct
        h = text.strip("{}").replace("-", "")
        tail = bytes(bytearray(int(h[i:i + 2], 16) for i in range(16, 32, 2)))
        return self.ct.create_string_buffer(struct.pack("<IHH", int(h[:8], 16), int(h[8:12], 16),
                                                        int(h[12:16], 16)) + tail, 16)

    def _open(self, languages):
        ct = self.ct
        self.step = "load ole32"
        self.ole = ct.windll.ole32
        self.step = "CoInitializeEx"
        self.ole.CoInitializeEx(None, 2)           # per thread; harmless if already initialised
        self.step = "build GUIDs"
        clsid, iid = self._guid(self.CLSID_FACTORY), self._guid(self.IID_FACTORY)
        ptr = ct.c_void_p()
        self.step = "CoCreateInstance"
        hr = self.ole.CoCreateInstance(clsid, None, 1, iid, ct.byref(ptr))
        if hr != 0 or not ptr.value:
            raise SpellError("The Windows spelling service is not available (needs Windows 8 or later)."
                             " HRESULT %s" % hex(hr & 0xffffffff))
        self.factory = _ComPtr(ptr.value)
        missing = []
        for lang in languages:
            self.step = "language " + lang
            ok = ct.c_int(0)
            self.factory.call(4, [self.wt, ct.POINTER(ct.c_int)], self._w(lang), ct.byref(ok))
            if not ok.value:
                missing.append(lang)
                continue
            chk = ct.c_void_p()
            self.factory.call(5, [self.wt, ct.POINTER(ct.c_void_p)], self._w(lang), ct.byref(chk))
            if chk.value:
                self.checkers.append(_ComPtr(chk.value))
        self.step = "check languages"
        if missing or not self.checkers:
            have = ", ".join(self.supported())
            self.close()
            raise SpellError("Windows has no spelling dictionary for: %s\n\nInstalled: %s\n\n"
                             "Add the language in Windows Settings > Time & language > Language & region."
                             % (", ".join(missing) or "(no language configured)", have or "none"))

    def _strings(self, enum_ptr, limit):
        ct, out = self.ct, []
        enum = _ComPtr(enum_ptr)
        try:
            while len(out) < limit:
                s, got = ct.c_void_p(), ct.c_ulong(0)
                hr = enum.call(3, [ct.c_ulong, ct.POINTER(ct.c_void_p), ct.POINTER(ct.c_ulong)],
                               1, ct.byref(s), ct.byref(got))
                if hr != 0 or not got.value:
                    break
                out.append(ct.wstring_at(s.value))
                self.ole.CoTaskMemFree(ct.c_void_p(s.value))
        finally:
            enum.release()
        return out

    def supported(self):
        ct = self.ct
        enum = ct.c_void_p()
        self.factory.call(3, [ct.POINTER(ct.c_void_p)], ct.byref(enum))
        return self._strings(enum.value, 200) if enum.value else []

    def plain(self, w):
        r = self._memo.get(w)
        if r is None:
            r = False
            for chk in self.checkers:
                errs = self.ct.c_void_p()
                chk.call(4, [self.wt, self.ct.POINTER(self.ct.c_void_p)], self._w(w), self.ct.byref(errs))
                if not errs.value:
                    r = True
                    break
                enum = _ComPtr(errs.value)
                err = self.ct.c_void_p()
                hr = enum.call(3, [self.ct.POINTER(self.ct.c_void_p)], self.ct.byref(err))   # IEnumSpellingError::Next
                if hr == 0 and err.value:
                    _ComPtr(err.value).release()
                else:                                   # S_FALSE: no spelling error in this language
                    r = True
                enum.release()
                if r:
                    break
            self._memo[w] = r
        return r

    check = plain

    def suggest(self, w, limit):
        out = []
        for chk in self.checkers:
            enum = self.ct.c_void_p()
            chk.call(5, [self.wt, self.ct.POINTER(self.ct.c_void_p)], self._w(w), self.ct.byref(enum))
            if enum.value:
                for x in self._strings(enum.value, limit):
                    if x not in out:
                        out.append(x)
            if len(out) >= limit:
                break
        return out[:limit]

    def close(self):
        for chk in self.checkers:
            chk.release()
        self.checkers = []
        if getattr(self, "factory", None):
            self.factory.release()
            self.factory = None


def _find_python(o):
    """python.exe used for the Windows spelling helper process (CODESYS/IronPython only)."""
    cfg = o.get("spell_python")
    if cfg:
        if os.path.exists(cfg):
            return cfg
        raise SpellError("spell_python does not exist: %s" % cfg)
    env = os.environ.get
    cands = [os.path.join(d.strip('"'), "python.exe") for d in (env("PATH") or "").split(os.pathsep) if d.strip()]
    for root in (env("LOCALAPPDATA"), env("ProgramFiles"), "C:\\"):
        if root:
            base = os.path.join(root, "Programs", "Python") if root == env("LOCALAPPDATA") else root
            try:
                names = sorted(os.listdir(base), reverse=True)
            except OSError:
                names = []
            cands += [os.path.join(base, n, "python.exe") for n in names if n.lower().startswith("python")]
    for c in cands:
        if "WindowsApps" not in c and os.path.isfile(c):
            return c
    raise SpellError("The Windows spelling check inside CODESYS needs Python 3 (python.exe) installed.\n"
                     "Install it, set 'spell_python' to its full path, or use the Hunspell backend.")


class _WinProcSpeller(object):
    """The Windows speller in a separate Python process. Used inside CODESYS (IronPython), where
    calling the COM interfaces in-process crashes the host. Talks a line protocol with
    'python StructuredText_Format.py --winspell LANGS'."""

    def __init__(self, languages, python):
        self.langs = ",".join(languages)
        self._memo = {}
        script = os.path.abspath(__file__)
        if script.lower().endswith((".pyc", ".pyo")):
            script = script[:-1]
        self.net = (sys.platform == "cli")
        if self.net:
            import clr  # noqa: F401
            from System.Diagnostics import Process, ProcessStartInfo
            from System.Text import UTF8Encoding
            psi = ProcessStartInfo()
            psi.FileName = python
            psi.Arguments = '"%s" --winspell %s' % (script, self.langs)
            psi.UseShellExecute = False
            psi.CreateNoWindow = True
            psi.RedirectStandardInput = True
            psi.RedirectStandardOutput = True
            enc = UTF8Encoding(False)
            psi.StandardOutputEncoding = enc
            self.p = Process.Start(psi)
            self.sin, self.sout = self.p.StandardInput, self.p.StandardOutput
        else:
            import subprocess
            self.p = subprocess.Popen([python, script, "--winspell", self.langs],
                                      stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        first = self._ask(None)
        self._send("N")                              # no-op: absorbs a byte-order mark on the first line
        if first != "READY":
            self.shutdown()
            raise SpellError(first[4:] if (first or "").startswith("ERR\t") else
                             "The Windows spelling helper process did not start: %s" % first)

    def _send(self, line):
        if self.net:
            self.sin.Write(line + "\n")
            self.sin.Flush()
        else:
            self.p.stdin.write((line + "\n").encode("ascii"))
            self.p.stdin.flush()

    def _ask(self, line):
        """Send one line (None = nothing) and return the reply line, or '' if the helper died."""
        try:
            if line is not None:
                self._send(line)
            if self.net:
                reply = self.sout.ReadLine()
                return reply if reply is not None else ""
            return self.p.stdout.readline().decode("utf-8").rstrip("\r\n")
        except Exception:
            return ""

    @staticmethod
    def _hex(word):
        import binascii
        if not isinstance(word, type(u"")):
            try:
                word = word.decode("utf-8")
            except Exception:
                word = type(u"")(word)
        return binascii.hexlify(word.encode("utf-8")).decode("ascii")      # the pipe only carries ASCII

    def plain(self, w):
        r = self._memo.get(w)
        if r is None:
            reply = self._ask("C\t" + self._hex(w))
            if reply not in ("OK", "BAD"):
                raise SpellError("The Windows spelling helper process stopped unexpectedly.")
            r = self._memo[w] = (reply == "OK")
        return r

    check = plain

    def suggest(self, w, limit):
        reply = self._ask("S\t%s\t%d" % (self._hex(w), limit))
        return [x for x in reply.split("\t") if x][:limit]

    def close(self):
        pass                                        # stays alive for the next call; see close_spellers()

    def shutdown(self):
        try:
            self._ask("Q")
            if self.net:
                self.sin.Close()
            else:
                self.p.stdin.close()
        except Exception:
            pass


def _spell_state():
    import types
    st = sys.modules.get("_st_spell_state")
    if st is None:
        st = types.ModuleType("_st_spell_state")
        st.cache = {}
        sys.modules["_st_spell_state"] = st
    if not hasattr(st, "procs"):
        st.procs = {}
    return st


def close_spellers():
    """Stop helper processes (CODESYS). Call when a run is finished."""
    st = _spell_state()
    for sp in list(st.procs.values()):
        sp.shutdown()
    st.procs.clear()


def _winspell_server(langs):
    """Helper process: answers spelling requests from the CODESYS adapter (see _WinProcSpeller)."""
    import io
    if getattr(sys.stdin, "buffer", None) is not None:       # Python 3
        inp = io.TextIOWrapper(sys.stdin.buffer, encoding="utf-8", newline="\n")
        outw = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", newline="\n", write_through=True)

        def out(text):
            outw.write(text + "\n")
            outw.flush()
    else:                                                    # Python 2
        inp = (ln.decode("utf-8") for ln in sys.stdin)

        def out(text):
            sys.stdout.write(text.encode("utf-8") + "\n")
            sys.stdout.flush()
    try:
        sp = _WinSpeller([x for x in langs.split(",") if x])
    except SpellError as e:
        out("ERR\t" + str(e).replace("\n", " "))
        return
    out("READY")
    import binascii
    for line in inp:
        parts = line.lstrip(u"\ufeff").rstrip("\r\n").split("\t")
        if parts[0] == "C" and len(parts) > 1:
            out("OK" if sp.plain(binascii.unhexlify(parts[1]).decode("utf-8")) else "BAD")
        elif parts[0] == "S" and len(parts) > 2:
            out("\t".join(sp.suggest(binascii.unhexlify(parts[1]).decode("utf-8"), int(parts[2]))))
        elif parts[0] == "Q":
            break
    sp.close()


def _spell_folders(o):
    env = os.environ.get
    folders = list(o.get("spell_folders") or [])
    for root, parts in ((env("APPDATA"), ("Notepad++", "plugins", "config", "Hunspell")),
                        (env("ProgramFiles"), ("Notepad++", "plugins", "config", "Hunspell")),
                        (env("LOCALAPPDATA"), ("CODESYS", "Script Commands", "dictionaries")),
                        (env("LOCALAPPDATA"), ("STTools", "dictionaries"))):
        if root:
            folders.append(os.path.join(root, *parts))
    here = os.path.dirname(os.path.abspath(__file__)) if "__file__" in globals() else os.getcwd()
    folders.append(os.path.join(here, "dictionaries"))
    return folders


def get_speller(o):
    backend = o.get("spell_backend", "auto")
    names = list(o.get("spell_dictionaries") or [])
    if backend == "windows" or (backend == "auto" and not names):
        langs = list(o.get("spell_languages") or [])
        if sys.platform == "cli":                    # CODESYS/IronPython: COM in-process crashes the host
            st = _spell_state()
            key = ",".join(langs)
            sp = st.procs.get(key)
            if sp is None:
                sp = st.procs[key] = _WinProcSpeller(langs, _find_python(o))
            return sp
        return _WinSpeller(langs)
    if not names:
        raise SpellError("No spelling dictionary configured (spell_backend is \"hunspell\").\n\n"
                         "Set 'spell_dictionaries' in OPTIONS (top of StructuredText_Format.py), e.g.\n"
                         "    \"spell_dictionaries\": [\"en_GB\", \"nb_NO\"],\n"
                         "and put the matching Hunspell files (en_GB.dic + en_GB.aff ...) in one of\n"
                         "the folders listed in 'spell_folders'.")
    folders = _spell_folders(o)
    bases, missing = [], []
    for name in names:
        n = name[:-4] if name.lower().endswith((".dic", ".aff")) else name
        cands = [n] if (os.path.isabs(n) or "/" in n or os.sep in n) else [os.path.join(f, n) for f in folders]
        for c in cands:
            if os.path.exists(c + ".dic"):
                bases.append(c)
                break
        else:
            missing.append(name)
    if missing:
        raise SpellError("Spelling dictionary not found: %s\n\nSearched in:\n  %s\n\n"
                         "Each dictionary is a pair NAME.dic + NAME.aff (Hunspell format)."
                         % (", ".join(missing), "\n  ".join(folders)))
    st = _spell_state()
    key = (tuple(bases), bool(o.get("spell_compounds", True)))
    sp = st.cache.get(key)
    if sp is None:
        try:
            sp = _Speller([_Hunspell(b) for b in bases], key[1])
        except (IOError, OSError) as e:
            raise SpellError("Cannot read spelling dictionary: %s" % e)
        st.cache[key] = sp
    return sp


RE_SPELL_WORD = re.compile(u"[\\w'’]+", re.UNICODE)
RE_SPELL_MASK = re.compile(u"\\{[^}]*\\}|\\w+://\\S+|\\S+@\\S+\\.\\S+|\\b\\w+(?:\\.\\w+)+\\b|[A-Za-z]:\\\\\\S+",
                           re.UNICODE)
RE_CODEISH = re.compile(r":=|=>|;\s*(?:\*\)|\*/)?\s*$")
RE_IDENT_PART = re.compile(r"[A-Z]+(?![a-z])|[A-Z]?[a-z]+")


def _identifier_words(toks, into):
    for t in toks:
        if t.kind == "ident":
            into.add(t.v.lower())
            for part in RE_IDENT_PART.findall(t.v):
                into.add(part.lower())


def check_spelling(text, options=None, extra_code=None):
    """Return a list of (char_start, char_length, message) for misspelled words in
    comments. extra_code: more ST text whose identifiers count as known words.
    Raises SpellError if the dictionaries cannot be loaded."""
    o = dict(OPTIONS)
    if options:
        o.update(options)
    speller = get_speller(o)
    try:
        return _check_spelling(text, o, extra_code, speller)
    finally:
        if hasattr(speller, "close"):
            speller.close()


def _check_spelling(text, o, extra_code, speller):
    toks = tokenize(text)
    pos = 0
    for t in toks:
        t.pos = pos
        pos += len(t.v)
    known = set(w.lower() for w in (o.get("spell_user_words") or []))
    uname = o.get("spell_user_dictionary")
    if uname:
        paths = [uname] if os.path.isabs(uname) else [os.path.join(f, uname) for f in _spell_folders(o)]
        for path in paths:
            if os.path.isfile(path):
                with open(path, "rb") as f:
                    for ln in f.read().decode("utf-8", "replace").lstrip(u"\ufeff").splitlines():
                        if ln.strip() and not ln.startswith("#"):
                            known.add(ln.strip().lower())
    if o["spell_code_words"]:
        _identifier_words(toks, known)
        if extra_code:
            _identifier_words(tokenize(extra_code), known)
    min_len = int(o["spell_min_length"])
    cache, issues = {}, []
    for t in toks:
        if t.kind not in ("lcomment", "bcomment"):
            continue
        for lm in re.finditer(r"[^\r\n]+", t.v):
            line, base = lm.group(0), t.pos + lm.start()
            if o["spell_skip_code_comments"] and RE_CODEISH.search(line):
                continue
            masks = [(m.start(), m.end()) for m in RE_SPELL_MASK.finditer(line)]
            for wm in RE_SPELL_WORD.finditer(line):
                a = wm.start()
                if any(x <= a < y for x, y in masks):
                    continue
                raw = wm.group(0).replace(u"’", u"'")
                word = raw.strip(u"'")
                a += len(raw) - len(raw.lstrip(u"'"))
                if len(word) < min_len or re.search(u"[\\d_]", word, re.UNICODE):
                    continue
                if o["spell_skip_identifiers"] and re.search(u"[a-z][A-Z]", word):
                    continue
                if o["spell_skip_allcaps"] and word.isupper():
                    continue
                if word.lower() in known:
                    continue
                ok = cache.get(word)
                if ok is None:
                    ok = cache[word] = speller.check(word)
                if ok:
                    continue
                sugg = speller.suggest(word, int(o["spell_suggestions"])) if o["spell_suggestions"] else []
                msg = "%s  [spelling]\nsuggestions: %s" % (word, ", ".join(sugg) if sugg else "none")
                issues.append((base + a, len(word), msg))
    return issues


# ---------------------------------------------------------------------------
# Notepad++ integration (PythonScript plugin)
# ---------------------------------------------------------------------------
try:
    from Npp import editor, notepad  # noqa: F401
    _IN_NPP = True
except ImportError:
    _IN_NPP = False


def _decode(raw):
    if isinstance(raw, bytes):
        enc = "utf-8" if editor.getCodePage() == 65001 else "latin-1"
        return raw.decode(enc, "replace"), enc
    return raw, None


def _encode(text, enc):
    return text.encode(enc) if enc else text


def format_current_document(options=None):
    """Format the entire document (one undo step), keeping the view position."""
    o = dict(OPTIONS)
    if options:
        o.update(options)
    first_visible = editor.getFirstVisibleLine()
    cur_line = editor.lineFromPosition(editor.getCurrentPos())
    text, enc = _decode(editor.getText())
    new = format_st(text, o)
    if new != text:
        editor.beginUndoAction()
        editor.setText(_encode(new, enc))
        editor.endUndoAction()
    editor.gotoLine(min(cur_line, editor.getLineCount() - 1))
    editor.setFirstVisibleLine(first_visible)


# ---- naming indicator ------------------------------------------------------
INDICATOR_ID = int(OPTIONS.get("naming_indicator_id", 13))
SPELL_INDICATOR_ID = int(OPTIONS.get("spell_indicator_id", 14))


def _state():
    import types
    st = sys.modules.get("_st_naming_state")
    if st is None:
        st = types.ModuleType("_st_naming_state")
        st.msgs = {}
        st.spell_msgs = {}
        st.hover = False
        sys.modules["_st_naming_state"] = st
    return st


def _char_to_byte_positions(text, enc, char_positions):
    if enc is None:
        enc = "utf-8" if editor.getCodePage() == 65001 else "latin-1"
    out, last_c, last_b = {}, 0, 0
    for c in sorted(set(char_positions)):
        last_b += len(text[last_c:c].encode(enc, "replace"))
        last_c = c
        out[c] = last_b
    return out


def _indicator_style(name):
    from Npp import INDICATORSTYLE
    wanted = {"thick": ["COMPOSITIONTHICK", "PLAIN"], "plain": ["PLAIN"],
              "squiggle": ["SQUIGGLE"], "box": ["STRAIGHTBOX", "ROUNDBOX"],
              "outline": ["BOX"]}.get(name, ["COMPOSITIONTHICK"])
    for w in wanted:
        if hasattr(INDICATORSTYLE, w):
            return getattr(INDICATORSTYLE, w)
    return INDICATORSTYLE.PLAIN


def _on_dwell_start(args):
    try:
        p = args.get("position", -1)
        if p < 0:
            return
        for ind, attr in ((INDICATOR_ID, "msgs"), (SPELL_INDICATOR_ID, "spell_msgs")):
            if not editor.indicatorValueAt(ind, p):
                continue
            a, b = editor.wordStartPosition(p, True), editor.wordEndPosition(p, True)
            word = editor.getTextRange(a, b)
            if isinstance(word, bytes):
                word = word.decode("utf-8", "replace")
            msg = getattr(_state(), attr, {}).get(notepad.getCurrentBufferID(), {}).get(word)
            if msg:
                editor.callTipShow(p, msg)
                return
    except Exception:
        pass


def _on_dwell_end(args):
    editor.callTipCancel()


def _install_hover():
    st = _state()
    if st.hover:
        return
    from Npp import SCINTILLANOTIFICATION
    editor.setMouseDwellTime(500)
    editor.callback(_on_dwell_start, [SCINTILLANOTIFICATION.DWELLSTART])
    editor.callback(_on_dwell_end, [SCINTILLANOTIFICATION.DWELLEND])
    st.hover = True


def _fill(ranges, ind=None):
    """Fill our indicator. Notepad++ changes the *current* indicator itself
    (smart highlighting runs on the GUI thread while this script runs), so the
    current indicator is set again right before every call, and the result is
    verified and repeated if Notepad++ got in between."""
    ind = INDICATOR_ID if ind is None else ind
    for _attempt in range(5):
        for a, b in ranges:
            editor.setIndicatorCurrent(ind)
            editor.indicatorFillRange(a, b - a)
        missing = [(a, b) for a, b in ranges if b > a and not editor.indicatorValueAt(ind, a)]
        if not missing:
            return True
        ranges = missing
    return False


def _clear(ind=None):
    ind = INDICATOR_ID if ind is None else ind
    for _attempt in range(3):
        editor.setIndicatorCurrent(ind)
        editor.indicatorClearRange(0, editor.getLength())
        if editor.indicatorEnd(ind, 0) in (0, editor.getLength()) and \
                not editor.indicatorValueAt(ind, 0):
            return


def check_current_document(options=None):
    """Underline badly named declarations in the current document.
    Returns the list of 1-based line numbers with a problem."""
    o = dict(OPTIONS)
    if options:
        o.update(options)
    text, enc = _decode(editor.getText())
    issues = check_names(text, o) if o["naming_check"] else []
    bpos = _char_to_byte_positions(text, enc, [s for s, _, _ in issues] +
                                   [s + ln for s, ln, _ in issues])

    editor.indicSetStyle(INDICATOR_ID, _indicator_style(o["naming_indicator_style"]))
    editor.indicSetFore(INDICATOR_ID, tuple(o["naming_indicator_color"]))
    try:
        editor.indicSetAlpha(INDICATOR_ID, 70)
        editor.indicSetOutlineAlpha(INDICATOR_ID, 255)
        editor.indicSetUnder(INDICATOR_ID, True)
    except Exception:
        pass
    _clear()
    ranges, msgs, lines = [], {}, []
    for s, ln, msg in issues:
        ranges.append((bpos[s], bpos[s + ln]))
        msgs[text[s:s + ln]] = msg
        lines.append(text.count("\n", 0, s) + 1)
    if ranges:
        _fill(ranges)
    _state().msgs[notepad.getCurrentBufferID()] = msgs
    if issues:
        _install_hover()
    if o["naming_report_console"]:
        from Npp import console
        console.write("Naming check: %d problem(s)\n" % len(issues))
        for (s, ln, msg), line in zip(issues, lines):
            console.write("  line %d: %s\n" % (line, msg.replace("\n", " | ")))
    return lines


def check_spelling_current_document(options=None):
    """Underline misspelled words in comments (red squiggle). Returns 1-based line numbers.
    Raises SpellError if no usable dictionary is configured."""
    o = dict(OPTIONS)
    if options:
        o.update(options)
    text, enc = _decode(editor.getText())
    issues = check_spelling(text, o)
    bpos = _char_to_byte_positions(text, enc, [s for s, _, _ in issues] +
                                   [s + ln for s, ln, _ in issues])
    editor.indicSetStyle(SPELL_INDICATOR_ID, _indicator_style(o["spell_indicator_style"]))
    editor.indicSetFore(SPELL_INDICATOR_ID, tuple(o["spell_indicator_color"]))
    try:
        editor.indicSetAlpha(SPELL_INDICATOR_ID, 70)
        editor.indicSetOutlineAlpha(SPELL_INDICATOR_ID, 255)
        editor.indicSetUnder(SPELL_INDICATOR_ID, True)
    except Exception:
        pass
    _clear(SPELL_INDICATOR_ID)
    ranges, msgs, lines = [], {}, []
    for s, ln, msg in issues:
        ranges.append((bpos[s], bpos[s + ln]))
        msgs[text[s:s + ln]] = msg
        lines.append(text.count("\n", 0, s) + 1)
    if ranges:
        _fill(ranges, SPELL_INDICATOR_ID)
    _state().spell_msgs[notepad.getCurrentBufferID()] = msgs
    if issues:
        _install_hover()
    if o["spell_report_console"]:
        from Npp import console
        console.write("Spell check: %d misspelled word(s)\n" % len(issues))
        for (s, ln, msg), line in zip(issues, lines):
            console.write("  line %d: %s\n" % (line, msg.replace("\n", " | ")))
    return lines


def _cli(argv):
    if "--winspell" in argv:
        k = argv.index("--winspell")
        _winspell_server(argv[k + 1] if k + 1 < len(argv) else "")
        return
    if "--spell" in argv:
        import io
        files = [a for a in argv[1:] if not a.startswith("--")]
        o = dict(OPTIONS)
        dicts = [a[7:] for a in argv if a.startswith("--dict=")]
        if dicts:
            o["spell_dictionaries"] = dicts
        data = io.open(files[0], "r", encoding="utf-8", newline="").read() if files else sys.stdin.read()
        try:
            found = check_spelling(data, o)
        except SpellError as e:
            print("spell check: %s" % e)
            return
        for s, ln, msg in found:
            line = data.count("\n", 0, s) + 1
            col = s - (data.rfind("\n", 0, s) + 1) + 1
            print("%d:%d  %s" % (line, col, msg.replace("\n", "  |  ")))
        return
    if "--check" in argv:
        import io
        files = [a for a in argv[1:] if not a.startswith("--")]
        data = io.open(files[0], "r", encoding="utf-8", newline="").read() if files else sys.stdin.read()
        for s, ln, msg in check_names(data):
            line = data.count("\n", 0, s) + 1
            col = s - (data.rfind("\n", 0, s) + 1) + 1
            print("%d:%d  %s" % (line, col, msg.replace("\n", "  |  ")))
        return
    if len(argv) < 2:
        data = sys.stdin.read()
        sys.stdout.write(format_st(data))
        return
    import io
    with io.open(argv[1], "r", encoding="utf-8", newline="") as f:
        data = f.read()
    res = format_st(data)
    if "--inplace" in argv:
        with io.open(argv[1], "w", encoding="utf-8", newline="") as f:
            f.write(res)
    else:
        sys.stdout.write(res)


def set_status(text):
    try:
        from Npp import STATUSBARSECTION
        notepad.setStatusBar(STATUSBARSECTION.DOCTYPE, text)
    except Exception:
        pass


def show_error(title):
    import traceback
    msg = traceback.format_exc()
    try:
        from Npp import console
        console.write(msg)
    except Exception:
        pass
    notepad.messageBox(msg, title)


def run_spell_check():
    """Underline misspelled comment words; report in the status bar. Returns the count."""
    try:
        lines = check_spelling_current_document()
    except SpellError as e:
        notepad.messageBox(str(e), "Structured Text - spell check")
        return 0
    if not lines:
        set_status("Structured Text - spelling: OK")
    else:
        shown = ", ".join(str(x) for x in lines[:10]) + (" ..." if len(lines) > 10 else "")
        set_status("Structured Text - spelling: %d misspelled word(s) on line %s - hover the underlined words"
                   % (len(lines), shown))
    return len(lines)


def run_naming_check():
    lines = check_current_document()
    if OPTIONS["naming_check"]:
        if not lines:
            set_status("Structured Text - naming: OK")
        else:
            shown = ", ".join(str(x) for x in lines[:10]) + (" ..." if len(lines) > 10 else "")
            set_status("Structured Text - naming: %d problem(s) on line %s - hover the underlined names"
                       % (len(lines), shown))
    return len(lines)


if __name__ == "__main__":
    if _IN_NPP:
        try:
            format_current_document()
            if OPTIONS["check_naming_after_format"]:
                run_naming_check()
            if OPTIONS["check_spelling_after_format"]:
                run_spell_check()
        except Exception:
            show_error("StructuredText_Format - error")
    else:
        _cli(sys.argv)
