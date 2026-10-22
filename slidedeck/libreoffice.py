"""OdpEngine: the PowerPoint engine's deck, converted to OpenDocument (LibreOffice Impress) with soffice."""

import os
import shutil
import subprocess
import tempfile

from .powerpoint import FONTS, PptxEngine
from .style import HEAD, HEAD_TITLE, SANS

# LibreOffice knows the family "Helvetica Neue" but not the weight-named "Helvetica Neue Light",
# which it would replace with a serif font; the regular weight is a little heavier than the theme's
FONTS_ODP = {**FONTS, SANS: "Helvetica Neue", HEAD: "Helvetica Neue", HEAD_TITLE: "Helvetica Neue"}


def find_soffice():
    path = shutil.which("soffice") or "/Applications/LibreOffice.app/Contents/MacOS/soffice"
    if not os.access(path, os.X_OK):
        raise SystemExit("The LibreOffice engine needs soffice (LibreOffice): brew install --cask libreoffice")
    return path


class OdpEngine(PptxEngine):
    default_output = "Intro_MPI.odp"
    fonts = FONTS_ODP

    def render(self):
        with tempfile.TemporaryDirectory() as tmp:
            stem = os.path.splitext(os.path.basename(self.output))[0]
            pptx = os.path.join(tmp, stem + ".pptx")
            self.prs.save(pptx)
            r = subprocess.run(
                [find_soffice(), "--headless", "--convert-to", "odp", "--outdir", tmp, pptx],
                capture_output=True,
                text=True,
                check=False,
            )
            odp = os.path.join(tmp, stem + ".odp")
            if r.returncode or not os.path.exists(odp):
                print(f"soffice failed: {(r.stderr or r.stdout).strip()[-1000:]}")
                return r.returncode or 1
            shutil.move(odp, self.output)
        print(self.output)
        return 0
