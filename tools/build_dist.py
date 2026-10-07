#!/usr/bin/env python3
"""
Build the three deliverables from the single source in src/.

    python tools/build_dist.py

Creates dist/NotepadPP, dist/CODESYS, dist/TwinCAT (each with its own copy of
src/StructuredText_Format.py) and a zip of each. Never edit the copies in dist/.
"""
import os
import shutil
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, "dist")
CORE = os.path.join(ROOT, "src", "StructuredText_Format.py")
TARGETS = {
    "NotepadPP": "notepadpp",
    "CODESYS": "codesys",
    "TwinCAT": "twincat",
}


def main():
    if os.path.isdir(DIST):
        shutil.rmtree(DIST)
    for name, folder in TARGETS.items():
        out = os.path.join(DIST, name)
        shutil.copytree(os.path.join(ROOT, folder), out,
                        ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy(CORE, out)
        zpath = os.path.join(DIST, name + "_scripts.zip")
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
            for fn in sorted(os.listdir(out)):
                z.write(os.path.join(out, fn), os.path.join(name, fn))
        print("built %s" % zpath)


if __name__ == "__main__":
    main()
