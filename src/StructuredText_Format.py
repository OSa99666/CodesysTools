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
    "naming_ignore_prefixes": ["k", "v", "m"],
    # Declarations of these data types are never checked (case-insensitive; the element
    # type for ARRAY OF). Standard or own types, e.g. ["TOD", "DT", "ST_Data", "FB_Timer"].
    "naming_ignore_types": [],
    # False = members of TYPE ... STRUCT / UNION declarations are not checked at all.
    "naming_check_type_members": True,
    "naming_report_console": False,  # also list problems in the PythonScript console
    "naming_indicator_id": 13,       # Scintilla indicator number (change if another plugin uses 13)
    # VAR_INPUT / VAR_OUTPUT / VAR_IN_OUT: names in ALL CAPITALS always pass the
    # Hungarian check (terminal names). If True they must also be a valid
    # IEC PAS 63131 terminal code (see TERMINAL_FIRST / TERMINAL_NEXT).
    "terminal_code_check": False,

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
            return _apply_case(t.v, o["function_case"])
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
    sig = [t for t in toks if t.kind not in ("ws", "nl", "lcomment", "bcomment", "pragma")]
    issues = []
    pou, section, flags, struct = [], None, set(), 0
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
            i += 1
            while i < n and sig[i].kind == "ident" and sig[i].v.upper() in (
                    "CONSTANT", "RETAIN", "PERSISTENT", "NON_RETAIN"):
                flags.add(sig[i].v.upper())
                i += 1
            continue
        if u == "END_VAR":
            section = None
            i += 1
            continue
        if u in ("STRUCT", "UNION"):
            struct += 1
            i += 1
            continue
        if u in ("END_STRUCT", "END_UNION"):
            struct = max(0, struct - 1)
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
                if base in ign_types or (struct > 0 and not check_members):
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


def _state():
    import types
    st = sys.modules.get("_st_naming_state")
    if st is None:
        st = types.ModuleType("_st_naming_state")
        st.msgs = {}
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
        if p < 0 or not editor.indicatorValueAt(INDICATOR_ID, p):
            return
        a, b = editor.wordStartPosition(p, True), editor.wordEndPosition(p, True)
        word = editor.getTextRange(a, b)
        if isinstance(word, bytes):
            word = word.decode("utf-8", "replace")
        msg = _state().msgs.get(notepad.getCurrentBufferID(), {}).get(word)
        if msg:
            editor.callTipShow(p, msg)
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


def _fill(ranges):
    """Fill our indicator. Notepad++ changes the *current* indicator itself
    (smart highlighting runs on the GUI thread while this script runs), so the
    current indicator is set again right before every call, and the result is
    verified and repeated if Notepad++ got in between."""
    for _attempt in range(5):
        for a, b in ranges:
            editor.setIndicatorCurrent(INDICATOR_ID)
            editor.indicatorFillRange(a, b - a)
        missing = [(a, b) for a, b in ranges if b > a and not editor.indicatorValueAt(INDICATOR_ID, a)]
        if not missing:
            return True
        ranges = missing
    return False


def _clear():
    for _attempt in range(3):
        editor.setIndicatorCurrent(INDICATOR_ID)
        editor.indicatorClearRange(0, editor.getLength())
        if editor.indicatorEnd(INDICATOR_ID, 0) in (0, editor.getLength()) and \
                not editor.indicatorValueAt(INDICATOR_ID, 0):
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


def _cli(argv):
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
        except Exception:
            show_error("StructuredText_Format - error")
    else:
        _cli(sys.argv)
