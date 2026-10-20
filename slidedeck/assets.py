"""Generated and measured image files: PNG sizes, rounded-card PNGs and LaTeX equations."""

import hashlib
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIG = os.path.join(HERE, "figures")
CARDS = os.path.join(HERE, "figures", "_cards")
EQS = os.path.join(HERE, "figures", "_eq")


def png_size(path):
    with open(path, "rb") as f:
        f.read(16)
        return struct.unpack(">II", f.read(8))


def write_card(w, h, r=22, alpha=0.82, border=(205, 216, 226)):
    """White rounded rectangle with a 2px border, as an RGBA PNG of exactly w x h."""
    os.makedirs(CARDS, exist_ok=True)
    path = os.path.join(CARDS, f"card_{w}x{h}.png")
    if os.path.exists(path):
        return path
    rows = []
    for y in range(h):
        row = bytearray([0])
        py = y + 0.5
        for x in range(w):
            px = x + 0.5
            # signed distance to the rounded-rect outline (negative inside)
            dx = max(r - px, px - (w - r), 0.0)
            dy = max(r - py, py - (h - r), 0.0)
            if dx or dy:
                sd = (dx * dx + dy * dy) ** 0.5 - r
            else:
                sd = -min(px, py, w - px, h - py)
            cov = max(0.0, min(1.0, 0.5 - sd))  # anti-aliased outer edge
            inner = max(0.0, min(1.0, -sd - 2.0))  # 0 on the 2px border, 1 inside
            c = tuple(int(255 * inner + b * (1 - inner)) for b in border)
            al = int(255 * cov * (alpha * inner + 0.9 * (1 - inner)))
            row += bytes((*c, al))
        rows.append(bytes(row))
    raw = b"".join(rows)

    def chunk(t, d):
        return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xFFFFFFFF)

    data = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as f:
        f.write(data)
    return path


EQ_PREAMBLE = r"""\pdfvariable objcompresslevel=0
\documentclass[border=1pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{sansmathfonts}
\renewcommand{\familydefault}{\sfdefault}
\usepackage{xcolor}
\definecolor{fg}{HTML}{41464D}
"""


def render_eq(tex):
    """Typeset display math with lualatex (10pt, sans, theme text color); return (pdf path, w, h in pt).
    Cached in figures/_eq by a hash of the source."""
    doc = EQ_PREAMBLE + "\\begin{document}\\color{fg}$\\displaystyle " + tex + "$\\end{document}\n"
    path = os.path.join(EQS, f"eq_{hashlib.sha1(doc.encode()).hexdigest()[:12]}.pdf")
    if not os.path.exists(path):
        os.makedirs(EQS, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "eq.tex"), "w", encoding="utf-8") as f:
                f.write(doc)
            r = subprocess.run(
                ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "eq.tex"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            if r.returncode:
                err = [ln for ln in r.stdout.splitlines() if ln.startswith("!")]
                sys.exit(f"lualatex failed on equation {tex!r}: {' '.join(err) or r.stdout[-500:]}")
            os.replace(os.path.join(tmp, "eq.pdf"), path)
    with open(path, "rb") as f:
        m = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", f.read())
    x0, y0, x1, y1 = map(float, m.groups())
    return path, x1 - x0, y1 - y0
