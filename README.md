# ST Tools

Formatter and Hungarian-notation naming checker for IEC 61131-3 Structured Text,
with integrations for Notepad++, CODESYS and TwinCAT 3 XAE.

| Target | Folder | Install guide |
|---|---|---|
| Notepad++ (UDL highlighting + PythonScript) | `notepadpp/` | `notepadpp/README_NotepadPP.md` |
| CODESYS (ScriptEngine toolbar buttons) | `codesys/` | `codesys/README_CODESYS.md` |
| TwinCAT 3 XAE (External Tools / CLI) | `twincat/` | `twincat/README_TwinCAT.md` |

The formatter lives once in `src/StructuredText_Format.py`; `python tools/build_dist.py`
creates ready-to-copy folders and zips in `dist/` with the core copied into each.

Tests: `python tests/run_tests.py`. Developer notes and all design decisions: `CLAUDE.md`.
