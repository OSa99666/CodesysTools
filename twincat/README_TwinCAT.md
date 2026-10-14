# Using the Structured Text scripts in TwinCAT 3 (XAE)

TwinCAT stores every PLC object as a text file (`.TcPOU`, `.TcDUT`, `.TcGVL`, `.TcIO`):
XML with the ST code inside `<![CDATA[ … ]]>` sections. `st_twincat.py` formats and checks
exactly those sections and leaves the rest of the file untouched (byte for byte, BOM and
line endings kept). It uses the same `StructuredText_Format.py` as Notepad++ and CODESYS.

Requires Python 3 for Windows (standard library only, no extra packages).

## Files (keep them in one folder, e.g. `C:\Tools\ST`)

| File | Purpose |
|---|---|
| `StructuredText_Format.py` | Formatter + naming check (keep identical to the Notepad++ / CODESYS copy) |
| `st_twincat.py` | TwinCAT adapter / command-line tool |

## Integration in TwinCAT XAE: External Tools

### Automatic install (recommended)

Close XAE, then run in this folder:

```
powershell -ExecutionPolicy Bypass -File Install_XAE_Tools.ps1
```

It copies `st_twincat.py` + `StructuredText_Format.py` to `%LOCALAPPDATA%\STTools` and adds the
three tools below (prefix `ST:`) to **Tools** in XAE; other External Tools are kept. Re-run after
updating the scripts; `-Python <path>` selects the interpreter, `-Uninstall` removes the entries.

### Manual install

**Tools → External Tools… → Add**, three times:

| Title | Command | Arguments | Initial directory |
|---|---|---|---|
| ST &Format current object | `C:\…\python.exe` | `"C:\Tools\ST\st_twincat.py" "$(ItemPath)"` | `$(ItemDir)` |
| ST Format &solution | `C:\…\python.exe` | `"C:\Tools\ST\st_twincat.py" "$(SolutionDir)"` | `$(SolutionDir)` |
| ST Check &names | `C:\…\python.exe` | `"C:\Tools\ST\st_twincat.py" --check "$(SolutionDir)"` | `$(SolutionDir)` |

| ST Check &spelling | `C:\…\python.exe` | `"C:\Tools\ST\st_twincat.py" --spell "$(SolutionDir)"` | `$(SolutionDir)` |

Tick **Use Output window** for all of them. Find the Python path with `where python` in a command prompt.

Optional keyboard shortcut: **Tools → Options → Environment → Keyboard**, search for
`Tools.ExternalCommand1` (2, 3 … in the order of the list) and assign e.g. `Ctrl+Alt+F`.

### How to use

1. **Save first** (`Ctrl+Shift+S`) – the tool works on the files on disk.
2. Select the POU in the Solution Explorer (or have its editor active) and run *ST Format current object*.
3. XAE notices the changed file and reloads it (confirm the reload prompt if it appears).
   If an open editor doesn't show the change, close and reopen the object.

Naming problems appear in the **Output** window as
`…\FB_Valve.TcPOU(27,5): warning ST001: FB_Valve.M_Reset, decl. line 3: bForce [VAR_INPUT, BOOL] - expected prefix 'ib' or 'ix' …`.
The object name and *decl. line* tell you where to look in the PLC editor
(double-clicking may open the file without jumping to the line).

Spelling problems in comments appear as `…\FB_Valve.TcPOU(27,5): warning ST002: FB_Valve: wrod [spelling] - suggestions: word`.
By default the **spelling engine of Windows** is used (`spell_languages`, default `en-US` and `nb-NO`; no files
needed). For Hunspell instead, set `spell_dictionaries` (e.g. `["en_GB", "nb_NO"]`) in the copy of
`StructuredText_Format.py` and put the files (`en_GB.dic` + `en_GB.aff`) in
`%LOCALAPPDATA%\STTools\dictionaries\` (or pass `--dict=C:\path\en_GB` on the command line). The automatic install creates the External Tool; the other spell
options are described in the Notepad++ README, section 3b.

## What gets formatted

- The declaration and all ST implementations of one file – POU, methods, properties (Get/Set),
  actions, transitions – are formatted together, so `:` / `:=` / `=>` line up across the whole file.
- Graphical implementations (FBD, LD, CFC, SFC) are not touched; their declarations are.
- `TWINCAT_OPTIONS` at the top of `st_twincat.py` overrides options for TwinCAT only.

## Command line, CI and Git

```
python st_twincat.py C:\Projects\Machine\PLC1                 # format whole PLC project + check
python st_twincat.py --check C:\Projects\Machine               # naming check only
python st_twincat.py --spell --dict=C:\Dict\en_GB C:\Projects\Machine   # spell check comments only
python st_twincat.py --dry-run C:\Projects\Machine             # list files that would change
python st_twincat.py --no-check FB_Valve.TcPOU                 # format one file only
```

Because it works on files, it can also run as a Git pre-commit hook or in a build pipeline.

## Notes and limitations

- Work on a copy or under source control the first time.
- `<LineIds>` (TwinCAT's line map for breakpoints) is not changed. After formatting adds or
  removes lines it may be out of date until the object is saved again in XAE
  (open it, make any change, undo, save); do this before online change / debugging.
- Undo in XAE doesn't cover external changes – use source control or the backup copy.
- **Alternative (not implemented):** the TwinCAT Automation Interface (COM) can read and write
  `DeclarationText` / `ImplementationText` of objects in the running XAE directly – no reload,
  but it needs `pywin32` and is more fragile to set up.
- TwinCAT's own **Static Analysis** (TE1200) also has naming conventions with scope and
  type prefixes, but without the ALL-CAPS terminal / IEC PAS 63131 exception.
