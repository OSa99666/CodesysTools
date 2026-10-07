# ST Tools – Structured Text formatter, naming checker and editor integrations

Tooling for IEC 61131-3 Structured Text (ST): one formatter + Hungarian-notation naming
checker (`src/StructuredText_Format.py`) used from three environments:
**Notepad++** (PythonScript plugin + UDL highlighting), **CODESYS** (ScriptEngine toolbar
buttons) and **TwinCAT 3 XAE** (External Tools working on .TcPOU/.TcDUT/.TcGVL/.TcIO files).

Originally developed in a claude.ai chat; this file captures every decision made there.

## Status (confirmed by the user)

- Notepad++: highlighting, formatting, naming underlines + hover tips all work.
- CODESYS: works on a copy of a real project.
- TwinCAT: built and tested only against a hand-written sample .TcPOU – **not yet confirmed
  in a real XAE installation**.

## Commands

```
python tests/run_tests.py            # run all regression tests (must pass before finishing any change)
python tests/run_tests.py --update   # regenerate tests/expected/* – ONLY after the user approved the new output
python tools/build_dist.py           # build dist/NotepadPP, dist/CODESYS, dist/TwinCAT (+ zips)
python src/StructuredText_Format.py FILE.st            # print formatted file
python src/StructuredText_Format.py FILE.st --check    # list naming problems
python twincat/st_twincat.py [--check|--no-check|--dry-run] PATH...
```

## Repository layout

```
src/StructuredText_Format.py   THE single source of formatter + checker + Notepad++ glue
notepadpp/                     UDL XML, StructuredText_CheckNames.py, README_NotepadPP.md
codesys/                       st_codesys.py adapter, ST_Format.py / ST_CheckNames.py buttons,
                               config.json + .ico for "Script Commands", README_CODESYS.md
twincat/                       st_twincat.py (file-based adapter, CLI), README_TwinCAT.md
tests/samples/                 input files;  tests/expected/  golden outputs
tools/build_dist.py            copies src/ core into each target folder in dist/
```

Each deployed folder needs its own copy of `StructuredText_Format.py` (the user keeps three
copies: Notepad++ scripts dir, `%LOCALAPPDATA%\CODESYS\Script Commands\`, TwinCAT tools dir).
Edit only `src/`; produce copies with `tools/build_dist.py`. Tell the user to replace all three.

## Hard constraints

- **Python 2.7 compatible** everywhere in `src/` and `codesys/`: Notepad++ PythonScript 2.x is
  Python 2.7, CODESYS ScriptEngine is **IronPython 2.7**. No f-strings, no type hints, no
  `nonlocal`, no keyword-only args, keep `from __future__ import print_function`.
  `twincat/st_twincat.py` runs under normal CPython 3 but must stay standard-library only.
- **No third-party packages** in any deliverable.
- **Formatting must be idempotent** (format(format(x)) == format(x)); tests enforce it.
- **Never touch strings, comments or pragmas** except the documented cases
  (`(* c *)` → `// c` for trailing declaration comments; `{attribute …}` placement).
- TwinCAT: only the content of `<Declaration><![CDATA[…]]>` and `<ST><![CDATA[…]]>` may change;
  everything else byte-identical (BOM, CRLF). Tests check this.
- Everything the user can tune lives in the `OPTIONS` dict / tables at the top of
  `src/StructuredText_Format.py`. When adding an option: add it there with a comment, document
  it in `notepadpp/README_NotepadPP.md` (options table) and add a test.

## Formatting spec (all decided by the user – don't change without asking)

Case
- `KW_CONTROL` (IF THEN ELSIF END_IF CASE FOR …), operators (AND OR NOT MOD) and TRUE/FALSE:
  **pascal with a capital after every `_`**: `If`, `ElsIf`, `End_If`, `End_Case`, `True`.
- `KW_DECL`, VAR kinds, POU kinds: **UPPER** (`VAR_INPUT`, `END_VAR`, `FUNCTION_BLOCK`, `STRUCT`).
- Data types (`TYPES`): pascal with explicit spellings from `PASCAL_CASE`:
  `Bool Int LInt LReal LTime Time DWord UDInt WString …`; `TOD LTOD DT LDT` stay upper.
  `ARRAY` was moved from KW_DECL to TYPES → `Array` (user request). `OF` is control → `Of`.
- `REGION` / `END_REGION` (Siemens style): UPPER, own colour in the UDL, indents its body,
  rest of the REGION line is a free-text name (token kind `rname`).

Layout
- Whole file is always formatted (selection formatting was removed on purpose).
- Indent 4 spaces; POU bodies not indented (`indent_pou_body` False); CASE items indented.
- **File-wide alignment** (`align_scope = "file"`): the `:` of every declaration, the `:=` of
  every assignment and the `=>` of call outputs share ONE column for the whole file
  (CODESYS: per object = declaration + implementation together; TwinCAT: per .TcXXX file).
  `align_column` 0 = auto, else fixed 1-based column (user mentioned 40 as an example; default
  left at 0). Lines too long for a fixed column overflow individually.
- Declarations are 3 columns: name | `: type [:= init]` | `// comment`. Comment column
  `comment_column` 0 = flexible (after longest aligned line + `comment_min_gap`).
- `{attribute '…'}` always in column 1, one space, then the declaration on the same line
  (a pragma-only line is joined with the following declaration).
- Calls with named parameters (`:=`/`=>`) that are statements of their own are expanded:
  ```
  sTimer
      (
       IN          := sbStart,
       Q           => sbDone
       );
  ```
  `(` one level in from the name (`call_paren_indent`), parameters and `);` one extra space
  (`call_param_offset`). Positional-only calls and calls inside expressions stay inline.
- Typed declarations with named init (`sV : tT(a := 1, b := 2);` / `: tT := (a := 1);`) in VAR/STRUCT
  use the same expanded layout (`decl_init_expand`); their `:=` join the file-wide alignment.

## Naming check spec (Hungarian notation)

Name = `<memory prefix><type prefix><Capital letter>…` (tables `MEMORY_PREFIX`, `TYPE_PREFIX`).
- Memory: VAR in PROGRAM/FB `s`; VAR in FUNCTION/METHOD and VAR_TEMP `t`; VAR_STAT/VAR_INST `s`;
  VAR_GLOBAL `g`; VAR_GLOBAL CONSTANT `gc`; VAR CONSTANT `c`; VAR_INPUT / `AT %I` `i`;
  VAR_OUTPUT / `AT %Q` `q`; VAR_IN_OUT `iq`; VAR_EXTERNAL accepts g/i/q (gc if constant);
  STRUCT/UNION members: no memory prefix.
- Type: BOOL `b` or `x`; BYTE `by`; WORD `w`; DWORD `dw`; LWORD `lw`; (U)SINT `(u)si`;
  (U)INT `(u)i`; (U)DINT `(u)di`; (U)LINT `(u)li`; TIME `t`; LTIME `lt`; REAL `r`; LREAL `lr`;
  DATE `d`; CHAR `c`; STRING `s`; assumed: WSTRING `s`, WCHAR `c`.
  Anything else (FB, STRUCT, enum, TOD, DT, POINTER…) = complex → memory prefix only.
  `ARRAY[..] OF X` uses X's prefix.
- **ALL-CAPS names in VAR_INPUT / VAR_OUTPUT / VAR_IN_OUT always pass** (terminal names).
  Optional `terminal_code_check`: must then be a valid IEC PAS 63131 terminal code
  (`TERMINAL_FIRST`: A B F L P R S W X Y; `TERMINAL_NEXT` letters; digits 1-9). All table
  entries are standard (the italics in the user's source table were only the header).
- Derived-name principle (ibReset → sbReset/tbReset) is a guideline, not checked.
- Notepad++ marks problems with Scintilla indicator 13 (orange thick underline) + calltip on
  mouse dwell; status bar shows count and line numbers. CODESYS: warnings in the Messages
  view. TwinCAT: `file(line,col): warning ST001: …` lines in the Output window.

## Hard-won lessons (don't regress)

- **Notepad++ UDL**: "Folding in code 1" matches *without* word separators – it broke
  colouring of `VAR_INPUT` (`VAR` matched, `_INPUT` not). Declaration keywords now live in the
  normal Keywords2 list (no folding – user said VAR folding is not needed). Only
  IF/CASE/FOR/WHILE/REPEAT fold (code 2). REGION/END_REGION in Keywords8 (white on orange),
  not folding (a fold keyword can't have its own colour). Language name: "IEC Structured Text".
- **Notepad++ indicators**: PythonScript runs on a worker thread; Notepad++ (smart
  highlighting) and **DSpellCheck** (indicator 19, uses PostMessage) change the *current
  indicator* in between. Fix in `_fill()`: call `setIndicatorCurrent` before every
  `indicatorFillRange`, verify with `indicatorValueAt`, retry. Confirmed working with DSpellCheck.
- PythonScript: scripts run with `__name__ == "__main__"`; positions are bytes (UTF-8) →
  `_char_to_byte_positions`. Errors are shown in a message box (`show_error`).
- CODESYS: `textual_declaration.text` / `.replace(text)`; `system.write_message(sev, text, obj)`
  (falls back without obj); toolbar via `config.json` in Script Commands. No editor API for
  underlines; script changes are not one undo step; no "active editor" → whole project.
  SmartCoding uppercase-keyword option would fight pascal case.
- TwinCAT: decl/impl of POU, methods, properties, actions are combined with marker comments
  `//@@ST_SPLIT_n@@`, formatted once, split again. `<LineIds>` are not updated (user should
  re-save objects in XAE before debugging). `indent_pou_body` forced False in adapters because
  TwinCAT/CODESYS objects have no END_FUNCTION_BLOCK.

## Known limitations / ideas not done

- Statement continuation lines without parentheses (`x := a +` ⏎ `b;`) are not indented.
- In compact calls only the first `:=`/`=>` per line is aligned (calls are expanded by default).
- TwinCAT Automation Interface (COM, `pywin32`, `DeclarationText`/`ImplementationText`) would
  allow editing inside the running XAE without reload – offered, not built.
- CODESYS Static Analysis / TwinCAT TE1200 naming conventions cover most of the Hungarian
  rules but not the ALL-CAPS terminal exception.
- User-facing replies: the user is a PLC engineer, writes short messages, prefers concise
  answers with a small before/after example and exact edit locations when he can edit himself.
