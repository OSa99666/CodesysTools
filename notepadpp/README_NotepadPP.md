# Structured Text (IEC 61131-3) for Notepad++

Two parts:

| File | What it does |
|---|---|
| `StructuredText_UDL.xml` | Syntax highlighting + code folding (IF/CASE/FOR/VAR/FUNCTION_BLOCK…); REGION/END_REGION highlighted in their own colour |
| `StructuredText_Format.py` | Auto-formatter (indentation, keyword case, alignment) + Hungarian-notation naming check |
| `StructuredText_CheckNames.py` | Runs only the naming check (no reformatting) |

## 1. Syntax highlighting

Remove any older version first, otherwise Notepad++ keeps using it:

1. Close Notepad++.
2. In `%APPDATA%\Notepad++\userDefineLangs\` delete any older Structured Text XML file.
   Also open `%APPDATA%\Notepad++\userDefineLang.xml` (if it exists) and delete the
   `<UserLang name="Structured Text" …> … </UserLang>` block.
3. Copy the new `StructuredText_UDL.xml` into `%APPDATA%\Notepad++\userDefineLangs\`.
4. Start Notepad++, open a `.st` file and select **Language → IEC Structured Text**.

All declaration keywords (VAR_INPUT, VAR_OUTPUT, VAR_IN_OUT, END_VAR, FUNCTION_BLOCK, STRUCT…)
are in a normal keyword list (purple), which always matches whole words.
IF / CASE / FOR / WHILE / REPEAT blocks fold; REGION / END_REGION have their own colour.
Using a dark theme? Change colours in **Language → User Defined Language → Define your language…**.

## 2. Formatter

1. **Plugins → Plugins Admin** → install **PythonScript**.
2. Copy `StructuredText_Format.py` and `StructuredText_CheckNames.py` to
   `%APPDATA%\Notepad++\plugins\config\PythonScript\scripts\`
3. Run it: **Plugins → Python Script → Scripts → StructuredText_Format**
   - always formats the entire file (alignment is file-wide)
   - one **Ctrl+Z** undoes the whole format
4. Add a shortcut (optional):
   **Plugins → Python Script → Configuration** → select the script → **Add** (to Menu items) → restart →
   **Settings → Shortcut Mapper → Plugin commands** → find `StructuredText_Format` → assign e.g. `Ctrl+Alt+Shift+F`.

### Options

Edit the `OPTIONS` dictionary at the top of the script. Columns are 1-based, the same as **Col:** in the Notepad++ status bar; `0` means automatic.

| Option | Default | Effect |
|---|---|---|
| `indent_size` / `use_tabs` | `4` / `False` | Indent width or tabs |
| `keyword_case` | `"pascal"` | IF, ELSIF, END_IF, AND, TRUE… → `If`, `ElsIf`, `End_If`, `And`, `True` |
| `decl_keyword_case` | `"upper"` | VAR_INPUT, END_VAR, FUNCTION_BLOCK, STRUCT, ARRAY… |
| `region_case` | `"upper"` | REGION / END_REGION |
| `type_case` | `"pascal"` | `Bool`, `Int`, `LInt`, `LReal`, `LTime`, `DWord`… |
| `function_case` | `"pascal"` | standard functions when called: `Abs`, `Sqrt`, `Sin`, `Limit`, `Int_To_Real`… (list: `FUNCTIONS`) |
| `normalize_spacing` | `True` | Rewrite spaces between tokens (off = only re-indent) |
| `space_around_operators` | `True` | `a := b + c` vs `a:=b+c` |
| `space_after_comma` | `True` | `f(a, b)` vs `f(a,b)` |
| `align_scope` | `"file"` | `file`: one column for `:` and `:=` across the whole file; `block`: per run of lines |
| `align_declarations` | `True` | Declarations in 3 columns: name, `: type`, `// comment` |
| `align_assignments` | `True` | Align `:=` and `=>` (call outputs) in code |
| `align_column` | `0` | Column of `:` and `:=` |
| `decl_min_gap` / `assign_min_gap` | `1` / `1` | Min spaces before `:` / `:=` |
| `align_comments` | `True` | Align trailing comments |
| `comment_column` | `0` | Column of trailing comments |
| `comment_min_gap` | `2` | Min spaces between code and comment |
| `decl_comment_style` | `"//"` | Convert `(* c *)` to `// c` in declarations, or `"preserve"` |
| `attribute_column0` | `True` | `{attribute ...}` always starts in column 1 |
| `attribute_join` | `True` | Put the attribute on the declaration line: `{attribute 'hide'} bVar : Bool;` |
| `indent_pou_body` | `False` | Indent everything inside PROGRAM / FUNCTION_BLOCK / TYPE |
| `indent_case_items` | `True` | Indent statements under CASE labels |
| `call_style` | `"expanded"` | Calls with named parameters: name, `(` and `);` on their own lines, one parameter per line (`"preserve"` = leave as written) |
| `call_expand_min_params` | `1` | Expand only calls with at least this many parameters |
| `call_paren_indent` | `1` | Indent levels of `(` relative to the call name |
| `call_param_offset` | `1` | Extra spaces of the parameters and `);` relative to `(` |
| `decl_init_expand` | `True` | Declarations with named initialisation (`sV : tValve(bOpen := TRUE, ...);` or `: tT := (a := 1, ...)`) are laid out like calls, `:` and `:=` aligned |
| `max_blank_lines` | `1` | Collapse multiple blank lines |
| `ensure_final_newline` | `True` | Newline at end of file |

With a fixed column, a line whose name is too long is pushed right on its own; the rest stay on the column.
Exact pascal spellings (ElsIf, LReal, UDInt…) come from the `PASCAL_CASE` table below `OPTIONS`.

## 3. Naming check (Hungarian notation)

Every declaration is checked against `<memory prefix><type prefix><Capital letter>…`.
Names that don't match get an **orange underline**; hover the mouse over one to see why and a suggested name.

| Section | Memory prefix | | Type | Prefix |
|---|---|---|---|---|
| `VAR` in PROGRAM / FB | `s` | | BOOL | `b` (or `x`) |
| `VAR` in FUNCTION / METHOD, `VAR_TEMP` | `t` | | BYTE / WORD / DWORD / LWORD | `by` `w` `dw` `lw` |
| `VAR_STAT`, `VAR_INST` | `s` | | (U)SINT / (U)INT / (U)DINT / (U)LINT | `(u)si` `(u)i` `(u)di` `(u)li` |
| `VAR_GLOBAL` | `g` | | TIME / LTIME | `t` `lt` |
| `VAR_GLOBAL CONSTANT` | `gc` | | REAL / LREAL | `r` `lr` |
| `VAR CONSTANT` | `c` | | DATE / CHAR / STRING | `d` `c` `s` |
| `VAR_INPUT`, `AT %I…` | `i` | | FB, STRUCT, UNION, enum, other | *(none)* |
| `VAR_OUTPUT`, `AT %Q…` | `q` | | `ARRAY[..] OF X` | prefix of X |
| `VAR_IN_OUT` | `iq` | | | |
| STRUCT / UNION members | *(none)* | | | |

Examples: `sbReset`, `ibReset`, `tbReset`, `trValue`, `gciMaxCount`, `sMotor` (FB instance), `tData` (struct), `srValues : ARRAY[1..5] OF Real`.

- Runs automatically after **StructuredText_Format**; run **StructuredText_CheckNames** to check without formatting.
- `MEMORY_PREFIX` and `TYPE_PREFIX` near the top of `StructuredText_Format.py` hold the table – edit them to change the rules.
- `WSTRING` → `s` and `WCHAR` → `c` are assumptions (not in the table). TOD, DT, POINTER etc. are treated as complex (memory prefix only).
- Options: `naming_check`, `check_naming_after_format`, `naming_indicator_style` (`thick` / `plain` / `squiggle` underline, `box` filled, `outline`), `naming_indicator_color`, `naming_ignore` (names never flagged), `naming_report_console` (also list problems in the PythonScript console).
- **Terminal names:** in `VAR_INPUT`, `VAR_OUTPUT` and `VAR_IN_OUT` a name in ALL CAPITALS (e.g. `R`, `BA1`, `START`) always passes.
  Set `terminal_code_check` to `True` to also require a valid IEC PAS 63131 terminal code: first letter from
  `TERMINAL_FIRST` (A B F L P R S W X Y), then letters from `TERMINAL_NEXT` and digits 1-9 (e.g. `BA1`, `RS`, `XE`).
  Remove letters from those two tables to disallow them.
- The derived-name principle (ibReset → sbReset, tbReset) is a design guideline and is not checked automatically.

### Automatic: format on save, check on open (optional)

Add this to `%APPDATA%\Notepad++\plugins\config\PythonScript\scripts\startup.py`
and set **Plugins → Python Script → Configuration → Initialisation** to **ATSTARTUP**:

```python
import os
import StructuredText_Format as stfmt

ST_EXT = (".st", ".scl", ".iecst")

def _is_st(buffer_id):
    return os.path.splitext(notepad.getBufferFilename(buffer_id))[1].lower() in ST_EXT

def _st_before_save(args):
    if _is_st(args["bufferID"]):
        notepad.activateBufferID(args["bufferID"])
        stfmt.format_current_document()

def _st_check(args):
    if _is_st(notepad.getCurrentBufferID()):
        stfmt.check_current_document()

notepad.callback(_st_before_save, [NOTIFICATION.FILEBEFORESAVE])
notepad.callback(_st_check, [NOTIFICATION.FILESAVED, NOTIFICATION.BUFFERACTIVATED])
```

Remove the `_st_before_save` line if you only want the check, not formatting on save.

### If no underlines appear

- Check that **Plugins → Python Script** exists (install *PythonScript* from Plugins Admin).
- Run **Plugins → Python Script → Scripts → StructuredText_CheckNames**. The status bar should show
  *Structured Text - naming: OK* or *… N problem(s)*. If it shows nothing, the script didn't run.
- Any error opens a message box with the details (also in **Plugins → Python Script → Show Console**).
- If another plugin uses the same underline slot, change `naming_indicator_id` (e.g. to 9 or 10).

## Command line

The formatter also runs without Notepad++ (Python 3):

```
python StructuredText_Format.py MyPou.st            # print result
python StructuredText_Format.py MyPou.st --inplace  # rewrite file
python StructuredText_Format.py MyPou.st --check    # list naming problems
```

## Notes

- Strings (`'...'`, `"..."` with `$` escapes), `//`, `(* *)`, `/* */` comments and `{pragmas}` are never modified.
