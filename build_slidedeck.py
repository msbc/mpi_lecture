#!/usr/bin/env python3
"""Build the lecture deck from the slide spec in slides.py, with one of four engines:

  keynote  Intro_MPI.key (Keynote, "Dynamic Waves Light", 1920x1080), via a generated AppleScript run by osascript
  beamer   Intro_MPI.pdf (Beamer, styled to match the Keynote deck), via generated LaTeX compiled by lualatex
  pptx     Intro_MPI.pptx (PowerPoint, styled to match the Keynote deck), via python-pptx
  odp      Intro_MPI.odp (LibreOffice Impress), the pptx deck converted by soffice

Usage:  python3 build_slidedeck.py [--engine {keynote,beamer,pptx,odp}] [--output PATH] [--overwrite]
                                   [--export-png DIR] [--print-script]

The Keynote engine refuses to run if the output file already exists unless --overwrite is given.
--print-script writes the generated AppleScript or LaTeX to stdout instead of running it.
"""

import argparse
import os
import sys

from slidedeck.assets import HERE
from slidedeck.beamer import BeamerEngine
from slidedeck.keynote import KeynoteEngine
from slidedeck.libreoffice import OdpEngine
from slidedeck.powerpoint import PptxEngine

sys.path.insert(0, HERE)
from slides import SLIDES  # noqa: E402

ENGINES = {"keynote": KeynoteEngine, "beamer": BeamerEngine, "pptx": PptxEngine, "odp": OdpEngine}


def main():
    ap = argparse.ArgumentParser(description="Build the lecture deck from slides.py.")
    ap.add_argument("--engine", choices=ENGINES, default="keynote", help="output format (default: keynote)")
    ap.add_argument(
        "--overwrite", action="store_true", help="replace an existing Intro_MPI.key (Keynote edits are lost)"
    )
    ap.add_argument("--export-png", metavar="DIR", help="also export each slide as a PNG into DIR (Keynote only)")
    ap.add_argument("--output", help="where to save the deck (default: Intro_MPI.key, .pdf, .pptx or .odp)")
    ap.add_argument(
        "--print-script", action="store_true", help="print the generated AppleScript or LaTeX instead of running it"
    )
    args = ap.parse_args()
    cls = ENGINES[args.engine]
    out_path = os.path.abspath(args.output or os.path.join(HERE, cls.default_output))
    if cls.protect_existing and os.path.exists(out_path) and not args.overwrite and not args.print_script:
        ap.error(f"{out_path} already exists (Keynote edits would be lost); pass --overwrite to replace it")
    if args.print_script and issubclass(cls, PptxEngine):
        ap.error("--print-script works only with --engine keynote or beamer")
    if args.export_png:
        if cls is not KeynoteEngine:
            ap.error("--export-png works only with --engine keynote")
        engine = cls(out_path, export_png=os.path.abspath(args.export_png))
    else:
        engine = cls(out_path)
    engine.build(SLIDES)
    if args.print_script:
        print(engine.source())
        return
    sys.exit(engine.render())


if __name__ == "__main__":
    main()
