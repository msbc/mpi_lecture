#!/usr/bin/env python3
"""Copy the shared code blocks in Intro_MPI/shared into every exercise.

Each exercise is a self-contained file, so code that several of them need
(such as reading the number of slices from the command line) is kept once in
Intro_MPI/shared/<name>.c or <name>.f90 and copied between marker comments:

    /* BEGIN shared: <name> ... */        ! BEGIN shared: <name> ...
    ...                                   ...
    /* END shared: <name> */              ! END shared: <name>

Edit the file in Intro_MPI/shared, then run this script. With --check it
changes nothing and fails if any copy differs from its source.
"""

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "Intro_MPI"
SHARED = ROOT / "shared"

# One pattern per language: the BEGIN line, the copied block, the END line
BLOCKS = {
    ".c": re.compile(
        r"(?P<begin>^/\* BEGIN shared: (?P<name>\w+)[^\n]*\*/\n)(?P<body>.*?)(?P<end>^/\* END shared: (?P=name) \*/$)",
        re.M | re.S,
    ),
    ".f90": re.compile(
        r"(?P<begin>^ *! BEGIN shared: (?P<name>\w+)[^\n]*\n)(?P<body>.*?)(?P<end>^ *! END shared: (?P=name)$)",
        re.M | re.S,
    ),
}


def synced(path, text):
    """Return TEXT with every shared block replaced by its source."""

    def replace(match):
        source = SHARED / f"{match['name']}{path.suffix}"
        if not source.is_file():
            sys.exit(f"{path}: no shared block {source.relative_to(ROOT.parent)}")
        return match["begin"] + source.read_text() + match["end"]

    return BLOCKS[path.suffix].sub(replace, text)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--check", action="store_true", help="change nothing; fail if any copy is out of date")
    args = parser.parse_args()

    stale = []
    for suffix in BLOCKS:
        for path in sorted(ROOT.rglob(f"*{suffix}")):
            if path.parent == SHARED:
                continue
            text = path.read_text()
            new = synced(path, text)
            if new == text:
                continue
            stale.append(path.relative_to(ROOT.parent))
            if not args.check:
                path.write_text(new)

    verb = "out of date" if args.check else "updated"
    for path in stale:
        print(f"{verb}: {path}")
    if args.check and stale:
        print("Run ci/sync_shared.py to update them.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
