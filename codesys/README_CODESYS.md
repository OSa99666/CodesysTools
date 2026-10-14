# Using the Structured Text scripts in CODESYS

CODESYS has a built-in Python script engine (IronPython 2.7, CODESYS V3.5).
The same `StructuredText_Format.py` used in Notepad++ runs inside CODESYS through a
small adapter, `st_codesys.py`, and two toolbar buttons.

## Files (all go in one folder)

| File | Purpose |
|---|---|
| `StructuredText_Format.py` | Formatter + naming check (same file as in Notepad++; keep the copies identical) |
| `st_codesys.py` | Adapter: walks the project, reads/writes declaration + implementation |
| `ST_Format.py` / `ST_Format.ico` | Toolbar button: format all ST objects (no naming check; use ST_CheckNames) |
| `ST_CheckNames.py` / `ST_CheckNames.ico` | Toolbar button: naming check only |
| `ST_SpellCheck.py` / `ST_SpellCheck.ico` | Toolbar button: spell check of all comments (Hunspell dictionaries) |
| `dictionaries\` | Your Hunspell files `NAME.dic` + `NAME.aff` and your own words in `user_words.txt` (one word per line) |
| `config.json` | Toolbar button definitions |

## Installation

1. Copy all files to `%LOCALAPPDATA%\CODESYS\Script Commands\`
   (create the folder if it doesn't exist).
2. Start CODESYS.
3. **Tools → Customize → Toolbars** → **Add Toolbar**, name it e.g. *Structured Text*.
4. **Tools → Customize → Command Icons**, category **ScriptEngine Commands**:
   add *ST Format* and *ST Check names* to the new toolbar.

Without a toolbar you can also run a script with **Tools → Scripting → Execute Script File…**.

## What it does

- **ST Format** asks for confirmation, then formats every object that has Structured Text:
  POUs, methods, properties (Get/Set), actions, transitions, DUTs and GVLs.
  Declaration and implementation of one object are formatted together, so `:` and `:=`
  line up across both editors. Graphical implementations (FBD/LD/SFC) are left alone,
  only their declaration is formatted. A summary appears in the **Messages** view.
- **ST Check names** writes one warning per badly named variable to the **Messages** view,
  e.g. `Naming: FB_Valve, decl. line 4: nSpeed [VAR_INPUT, INT] - expected prefix 'ii' … suggestion: iiSpeed`.
  Double-clicking the message opens the object (not the exact line).

- **ST Spell check** writes one warning per misspelled word in a comment (declaration and implementation)
  to the **Messages** view, e.g. `Spelling: FB_Valve, impl. line 1: wrod [spelling] - suggestions: word`.
  By default it uses the **spelling engine of Windows** (`spell_languages`, default `en-US` and `nb-NO`;
  no dictionary files needed). Because calling Windows COM directly from CODESYS' IronPython crashes
  CODESYS, the Windows engine runs in a small separate **Python 3 process** (hidden, started by the button,
  stopped when it finishes). So **Python 3 must be installed** (the same one used for TwinCAT); it is found
  automatically, or set `spell_python` to the full path of `python.exe`. The Hunspell backend needs no Python. For Hunspell dictionaries instead, set `spell_dictionaries` (e.g. `["en_GB", "nb_NO"]`) in
  `StructuredText_Format.py` and put the files in `%LOCALAPPDATA%\CODESYS\Script Commands\dictionaries\`
  (your own words go in `user_words.txt` there). All spell options (ignored words,
  identifiers, ALL-CAPS, compounds …) are described in the Notepad++ README, section 3b. Without a
  configured dictionary the button reports an error telling you what to do.

All options and tables (`OPTIONS`, `PASCAL_CASE`, `MEMORY_PREFIX`, `TYPE_PREFIX`,
`TERMINAL_FIRST/NEXT`) are read from `StructuredText_Format.py`; `CODESYS_OPTIONS` at the top of
`st_codesys.py` overrides individual options for CODESYS only.

## Limitations

- **No underlines in the CODESYS editor.** The script engine has no access to editor
  decorations, so naming problems are reported in the Messages view instead.
- **Undo:** script changes are not one undo step. Save or commit the project before formatting.
- **Whole project:** the script engine has no "currently open editor", so the whole project is processed.
- **SmartCoding:** if CODESYS converts keywords to upper case while you type
  (**Tools → Options → SmartCoding**), it will undo the pascal case (`If`, `End_If`).
  Turn that option off, or set `keyword_case` to `"upper"`.
- **Tabular declaration editor:** alignment only matters in the textual declaration view.
- Tested against a simulation of the script API, not in a live CODESYS installation.

## Built-in alternative for the naming check

The add-on **CODESYS Static Analysis** (full version, licensed) has configurable naming
conventions with prefixes per scope *and* data type ("Combine scope prefix with data type
prefix"), which covers most of the Hungarian table and reports violations as NCxxxx
messages during build. It does not know the "ALL CAPS terminal name" exception or the
IEC PAS 63131 terminal codes; for those the script is still needed.
