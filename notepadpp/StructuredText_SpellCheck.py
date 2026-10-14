# -*- coding: utf-8 -*-
"""Notepad++ PythonScript: underline misspelled words in comments (Hunspell dictionaries)
without reformatting. Needs StructuredText_Format.py in the same scripts folder."""
try:
    from importlib import reload as _reload
except ImportError:          # Python 2
    _reload = reload         # noqa: F821
import StructuredText_Format as _stf
_stf = _reload(_stf)         # pick up edits to OPTIONS / tables
try:
    _stf.run_spell_check()
except Exception:
    _stf.show_error("StructuredText_SpellCheck - error")
