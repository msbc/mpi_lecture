#!/usr/bin/env python3
"""Build Intro_MPI.key (Keynote, "Dynamic Waves Light", 1920x1080) from the slide
spec in slides.py. Generates an AppleScript and runs it with osascript.

Usage:  python3 build_keynote.py [--output PATH] [--overwrite] [--export-png DIR] [--print-script]

Refuses to run if the output file already exists unless --overwrite is given.
--print-script writes the AppleScript to stdout instead of running it.
"""

import argparse
import hashlib
import os
import re
import struct
import subprocess
import sys
import tempfile
import zlib

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "figures")
CARDS = os.path.join(HERE, "figures", "_cards")
EQS = os.path.join(HERE, "figures", "_eq")
OUT = os.path.join(HERE, "Intro_MPI.key")
sys.path.insert(0, HERE)
from slides import SLIDES  # noqa: E402

THEME = "Dynamic Waves Light"
W, H = 1920, 1080
X0, CW = 95, 1730  # left margin, content width
Y0, YMAX = 300, 1020  # content area (below title + subtitle)


# Colors (16-bit RGB for AppleScript)
def rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i : i + 2], 16) * 257 for i in (0, 2, 4))


TEXT = rgb("#41464D")  # theme body text
CODE = rgb("#2B3036")
ACCENT = rgb("#1F63B5")  # MPI identifiers
COMMENT = rgb("#7D858F")
CAPTION = rgb("#6A7079")

MONO = "Menlo-Regular"
MONO_BOLD = "Menlo-Bold"
SANS = "Graphik-Light"
HEAD = "Produkt-Light"
LINE = 1.167  # Menlo line height / font size in Keynote text items
CHAR = 0.602  # Menlo advance / font size
PAD = 28  # card padding around code


# ---------------------------------------------------------------- PNG helpers
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


# ------------------------------------------------------------ LaTeX equations
EQ_PREAMBLE = r"""\pdfobjcompresslevel=0
\documentclass[border=1pt]{standalone}
\usepackage[T1]{fontenc}
\usepackage{amsmath}
\usepackage{sansmathfonts}
\renewcommand{\familydefault}{\sfdefault}
\usepackage{xcolor}
\definecolor{fg}{HTML}{41464D}
"""


def render_eq(tex):
    """Typeset display math with pdflatex (10pt, sans, theme text color); return (pdf path, w, h in pt).
    Cached in figures/_eq by a hash of the source."""
    doc = EQ_PREAMBLE + "\\begin{document}\\color{fg}$\\displaystyle " + tex + "$\\end{document}\n"
    path = os.path.join(EQS, f"eq_{hashlib.sha1(doc.encode()).hexdigest()[:12]}.pdf")
    if not os.path.exists(path):
        os.makedirs(EQS, exist_ok=True)
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "eq.tex"), "w", encoding="utf-8") as f:
                f.write(doc)
            r = subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", "eq.tex"],
                cwd=tmp,
                capture_output=True,
                text=True,
            )
            if r.returncode:
                err = [ln for ln in r.stdout.splitlines() if ln.startswith("!")]
                sys.exit(f"pdflatex failed on equation {tex!r}: {' '.join(err) or r.stdout[-500:]}")
            os.replace(os.path.join(tmp, "eq.pdf"), path)
    with open(path, "rb") as f:
        m = re.search(rb"/MediaBox\s*\[\s*([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)\s+([-\d.]+)", f.read())
    x0, y0, x1, y1 = map(float, m.groups())
    return path, x1 - x0, y1 - y0


# ---------------------------------------------------------- AppleScript emit
def q(s):
    """AppleScript string literal; line separator U+2028 -> LS variable."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    parts = s.split(" ")
    return " & LS & ".join(f'"{p}"' for p in parts)


def inline_code(s):
    """Strip `backtick` markup; return (plain text, 1-based inclusive character ranges to set in MONO)."""
    plain, ranges, pos = [], [], 0
    for i, part in enumerate(s.split("`")):
        if i % 2 and part:
            ranges.append((pos + 1, pos + len(part)))
        plain.append(part)
        pos += len(part)
    return "".join(plain), ranges


class Slide:
    def __init__(self, out, master):
        self.o = out
        self.o.append(
            f'set s to make new slide at end of slides of d with properties {{base slide:master slide "{master}" of d}}'
        )

    def cmd(self, line):
        self.o.append(line)

    def mono(self, ranges, item, indent=""):
        """Set the inline-code character ranges of `item`'s text in MONO."""
        for a, b in ranges:
            self.cmd(f'{indent}set font of characters {a} thru {b} of object text of {item} to "{MONO}"')

    def placeholder_text(self, y, text, font=None, size=None):
        """Set text of the master placeholder shape whose top edge is at y (or delete it if text is None)."""
        text, ranges = inline_code(text) if text is not None else (None, [])
        self.cmd(
            f"set shs to {{}}\n"
            f"try\n  set shs to (every shape of s)\nend try\n"
            f"repeat with i from 1 to count of shs\n"
            f"  set sh to item i of shs\n"
            f"  if item 2 of (position of sh as list) = {y} then\n"
            + (
                "    delete sh\n"
                if text is None
                else f"    set object text of sh to {q(text)}\n"
                + (f'    set font of object text of sh to "{font}"\n' if font else "")
                + (f"    set size of object text of sh to {size}\n" if size else "")
                + "".join(
                    f'    set font of characters {a} thru {b} of object text of sh to "{MONO}"\n' for a, b in ranges
                )
            )
            + "    exit repeat\n  end if\nend repeat"
        )

    def title(self, title, sub=None, item="default title item of s"):
        self.cmd(f"set object text of {item} to {q(title)}")
        # the theme's title font has no π glyph; use a thin face that matches the title weight
        for i, ch in enumerate(title):
            if ch == "π":
                self.cmd(
                    f'try\n  set font of character {i + 1} of object text of {item} to "HelveticaNeue-Thin"\nend try'
                )
        if item.startswith("default title"):
            self.placeholder_text(183, sub)

    def body(self, bullets, x=X0, y=Y0, w=CW, h=None, size=None):
        h = h or (YMAX - y)
        text, ranges = inline_code(chr(10).join(bullets))
        self.cmd(f"set object text of default body item of s to {q(text)}")
        self.cmd(f"set position of default body item of s to {{{x}, {y}}}")
        self.cmd(f"set width of default body item of s to {w}")
        self.cmd(f"set height of default body item of s to {h}")
        if size:
            self.cmd(f"set size of object text of default body item of s to {size}")
        self.mono(ranges, "default body item of s")

    def image(self, path, x, y, w, h):
        self.cmd(f'tell s to set im to make new image with properties {{file:POSIX file "{path}"}}')
        self.cmd(f"set width of im to {w}")
        self.cmd(f"set height of im to {h}")
        self.cmd(f"set position of im to {{{x}, {y}}}")

    def text(self, s, x, y, w, size=36, font=SANS, color=TEXT):
        """Text item; outside code blocks (font MONO), `backticks` mark inline code."""
        s, ranges = inline_code(s) if font != MONO else (s, [])
        self.cmd("tell s to set ti to make new text item")
        self.cmd(f"set object text of ti to {q(s)}")
        self.cmd(f'set font of object text of ti to "{font}"')
        self.cmd(f"set size of object text of ti to {size}")
        self.cmd(f"set color of object text of ti to {{{color[0]}, {color[1]}, {color[2]}}}")
        self.cmd(f"set width of ti to {w}")
        self.cmd(f"set position of ti to {{{x}, {y}}}")
        self.mono(ranges, "ti")

    def notes(self, s):
        self.cmd(f"set presenter notes of s to {q(s)}")


def code_size(code, w, hmax, maxsize=34):
    lines = code.split("\n")
    n, m = len(lines), max(len(ln.expandtabs(8)) for ln in lines)
    sz = min(maxsize, (w - 2 * PAD - 10) / (CHAR * m), (hmax - 2 * PAD - 10) / (LINE * n))
    return int(sz)


def code_height(code, size):
    return int(LINE * size * len(code.split("\n")) + 8 + 2 * PAD)


KEYWORD = rgb("#9B3D8F")
# pygments token type -> color; anything not listed stays the default code color
TOKEN_COLORS = [
    (("Comment",), COMMENT),
    (("Keyword",), KEYWORD),
    (("Keyword.Type", "Name.Builtin.Type"), rgb("#2E7D6B")),
    (("Literal.String", "Literal.Number"), rgb("#B35C1E")),
]


def token_color(ttype):
    """Color for the most specific matching entry of TOKEN_COLORS (None: default)."""
    best, color = -1, None
    for names, col in TOKEN_COLORS:
        for name in names:
            if str(ttype).removeprefix("Token.").startswith(name) and len(name) > best:
                best, color = len(name), col
    return color


def highlight(code, lang="c"):
    """(start, end, color) 1-based inclusive character ranges: pygments syntax colors for `lang`
    (None to skip), then MPI names and comments on top."""
    spans, pos = [], 0
    if lang:
        try:
            from pygments.lexers import get_lexer_by_name
        except ImportError:
            sys.exit("Syntax highlighting needs pygments: pip install pygments")
        for ttype, text in get_lexer_by_name(lang, ensurenl=False, stripnl=False).get_tokens(code):
            col = token_color(ttype)
            if col == COMMENT and text.startswith("#SBATCH"):  # a directive, not a comment
                spans.append((pos + 1, pos + 7, KEYWORD))
                pos, text = pos + 7, text[7:]
                col = None
            if col and text.strip():
                if spans and spans[-1][1] == pos and spans[-1][2] == col:  # merge neighbours
                    spans[-1] = (spans[-1][0], pos + len(text), col)
                else:
                    spans.append((pos + 1, pos + len(text), col))
            pos += len(text)
    pos = 0
    for line in code.split("\n"):
        for m in re.finditer(r"\bMPI_[A-Za-z_]+", line):
            spans.append((pos + m.start() + 1, pos + m.end(), ACCENT))
        m = re.search(r"(^|\s)(# |//|! |/\*)", line)
        if m:
            st = m.start(2)
            spans.append((pos + st + 1, pos + len(line), COMMENT))
        pos += len(line) + 1
    return spans


def add_code(sl, code, x, y, w, hmax=None, size=None, lang="c", marks=()):
    """Code on a rounded card at (x, y), width w. Each regex in `marks` sets its matches (group 1
    if it has one) in bold ACCENT on top of the syntax colors. Returns card height."""
    hmax = hmax or (YMAX - y)
    size = size or code_size(code, w, hmax)
    ch = code_height(code, size)
    sl.image(write_card(w, ch), x, y, w, ch)
    sl.text(code.replace("\n", " "), x + PAD, y + PAD, w - 2 * PAD, size=size, font=MONO, color=CODE)
    for a, b, col in highlight(code, lang):
        sl.cmd(f"set color of characters {a} thru {b} of object text of ti to {{{col[0]}, {col[1]}, {col[2]}}}")
    for pattern in marks:
        for m in re.finditer(pattern, code):
            g = 1 if m.re.groups else 0
            a, b = m.start(g) + 1, m.end(g)
            sl.cmd(f'set font of characters {a} thru {b} of object text of ti to "{MONO_BOLD}"')
            col = ACCENT
            sl.cmd(f"set color of characters {a} thru {b} of object text of ti to {{{col[0]}, {col[1]}, {col[2]}}}")
    return ch


def add_figure(sl, name, x, y, bw, bh, center=True, card=True):
    """Fit figure into box (bw x bh) on a white card; returns (x, y, w, h) of card."""
    path = os.path.join(FIG, name)
    iw, ih = png_size(path)
    p = 24 if card else 0
    sc = min((bw - 2 * p) / iw, (bh - 2 * p) / ih)
    w, h = int(iw * sc), int(ih * sc)
    cx = x + (bw - (w + 2 * p)) // 2 if center else x
    if card:
        sl.image(write_card(w + 2 * p, h + 2 * p, alpha=0.95), cx, y, w + 2 * p, h + 2 * p)
    sl.image(path, cx + p, y + p, w, h)
    return cx, y, w + 2 * p, h + 2 * p


def add_eq(sl, tex, x, y, bw, size=44, center=True):
    """LaTeX display equation at (x, y) in a box of width bw, scaled so its text matches a
    `size`-pt font (shrunk if too wide). Returns its height."""
    path, pw, ph = render_eq(tex)
    sc = min(size / 10, bw / pw)
    w, h = round(pw * sc), round(ph * sc)
    sl.image(path, x + (bw - w) // 2 if center else x, y, w, h)
    return h


# ------------------------------------------------------------------- layouts
def build(spec, out):
    k = spec["kind"]
    lang = spec.get("lang", "c")  # syntax highlighting for code blocks
    if k == "title":
        sl = Slide(out, "Title")
        sl.cmd(f"set object text of default title item of s to {q(spec['title'])}")
        sl.cmd(f"set object text of default body item of s to {q(spec['sub'])}")
        sl.placeholder_text(966, spec["footer"])
        if spec.get("credit"):  # small line just under the subtitle
            sl.text(spec["credit"], X0, 651, CW, size=24, font="Graphik-Regular")
    elif k == "section":
        sl = Slide(out, "Section")
        sl.title(spec["title"], item="default title item of s")
    elif k == "statement":
        sl = Slide(out, "Statement")
        sl.cmd("try\n  set object text of default body item of s to " + q(spec["title"]) + "\nend try")
        sl.cmd("try\n  set object text of default title item of s to " + q(spec["title"]) + "\nend try")
    elif k == "bullets":
        sl = Slide(out, "Title & Bullets")
        sl.title(spec["title"], spec.get("sub"))
        sl.body(spec["bullets"], size=spec.get("size"))
    elif k == "split":  # bullets left, code right (code: a string, or a list of strings / (code, lang) stacked)
        sl = Slide(out, "Title & Bullets")
        sl.title(spec["title"], spec.get("sub"))
        cw = spec.get("code_w", 900)
        sl.body(spec["bullets"], w=CW - cw - 60, size=spec.get("size", 36))
        code = [spec["code"]] if isinstance(spec["code"], str) else spec["code"]
        blocks = [b if isinstance(b, tuple) else (b, lang) for b in code]
        gap, y = 30, Y0 + 20
        # one font size for all blocks: each fits the width, and together they fit the height
        nlines = sum(c.count("\n") + 1 for c, _ in blocks)
        room = YMAX - y - gap * (len(blocks) - 1) - len(blocks) * (2 * PAD + 10)
        size = spec.get("code_size") or int(
            min(min(code_size(c, cw, 10**4) for c, _ in blocks), room / (LINE * nlines))
        )
        for c, lg in blocks:
            y += add_code(sl, c, X0 + CW - cw, y, cw, size=size, lang=lg) + gap
    elif k == "code":  # code card on top, optional bullets below
        sl = Slide(out, "Title & Bullets" if spec.get("bullets") else "Title Only")
        sl.title(spec["title"], spec.get("sub"))
        hmax = spec.get("code_h", YMAX - Y0)
        ch = add_code(
            sl, spec["code"], X0, Y0, spec.get("code_w", CW), hmax=hmax, size=spec.get("code_size"), lang=lang
        )
        if spec.get("bullets"):
            sl.body(spec["bullets"], y=Y0 + ch + 40, size=spec.get("size", 36))
    elif k == "twocode":
        sl = Slide(out, "Title Only")
        sl.title(spec["title"], spec.get("sub"))
        cw = (CW - 40) // 2
        sz = min(code_size(spec["left"], cw, YMAX - Y0), code_size(spec["right"], cw, YMAX - Y0))
        add_code(sl, spec["left"], X0, Y0, cw, size=sz, lang=lang)
        add_code(sl, spec["right"], X0 + cw + 40, Y0, cw, size=sz, lang=lang)
    elif k == "figure":  # optional code, figure, caption, optional trailing text
        sl = Slide(out, "Title Only")
        sl.title(spec["title"], spec.get("sub"))
        y = Y0
        if spec.get("code"):
            y += add_code(sl, spec["code"], X0, y, CW, size=spec.get("code_size", 32), lang=lang) + 30
        bottom = YMAX - (50 if spec.get("caption") else 0) - (70 if spec.get("after") else 0)
        cx, cy, cw_, chh = add_figure(sl, spec["image"], X0, y, CW, min(bottom - y, spec.get("max_h", 2000)))
        y = cy + chh + 12
        if spec.get("caption"):
            sl.text(spec["caption"], cx, y, max(cw_, 900), size=28, color=CAPTION)
            y += 50
        if spec.get("after"):
            sl.text(spec["after"], X0, y + 10, CW, size=34)
    elif k == "codefig":  # code (or program output, with lang=None) left, figure right
        sl = Slide(out, "Title Only")
        sl.title(spec["title"], spec.get("sub"))
        cw = spec.get("code_w", 1000)
        lg = spec["lang"] if "lang" in spec else lang
        add_code(sl, spec["code"], X0, Y0, cw, size=spec.get("code_size"), lang=lg, marks=spec.get("marks", ()))
        fx, fw = X0 + cw + 50, CW - cw - 50
        cx, cy, cw_, chh = add_figure(sl, spec["image"], fx, Y0, fw, YMAX - Y0 - (60 if spec.get("caption") else 0))
        if spec.get("caption"):
            sl.text(spec["caption"], cx, cy + chh + 12, cw_, size=26, color=CAPTION)
    elif k == "figbullets":  # figure left, bullets right
        sl = Slide(out, "Title & Bullets")
        sl.title(spec["title"], spec.get("sub"))
        fw = spec.get("fig_w", 800)
        cx, cy, cw_, chh = add_figure(sl, spec["image"], X0, Y0, fw, YMAX - Y0 - 60)
        if spec.get("caption"):
            sl.text(spec["caption"], cx, cy + chh + 12, cw_, size=26, color=CAPTION)
        sl.body(spec["bullets"], x=X0 + fw + 60, w=CW - fw - 60, size=spec.get("size", 34))
    elif k == "figpair":
        sl = Slide(out, "Title Only")
        sl.title(spec["title"], spec.get("sub"))
        y = Y0
        for line in spec.get("lines", []):
            sl.text(line, X0, y, CW, size=34)
            y += 64
        y += 16
        bw = (CW - 60) // 2
        for i, (img, cap) in enumerate(spec["images"]):
            x = X0 + i * (bw + 60)
            cx, cy, cw_, chh = add_figure(sl, img, x, y, bw, YMAX - y - 80)
            sl.text(cap, x, cy + chh + 12, bw, size=26, color=CAPTION)
    elif k == "columns":
        sl = Slide(out, "Title Only")
        sl.title(spec["title"], spec.get("sub"))
        n = len(spec["cols"])
        gap = 50
        cw = (CW - gap * (n - 1)) // n
        for i, (head, items) in enumerate(spec["cols"]):
            x = X0 + i * (cw + gap)
            sl.image(write_card(cw, YMAX - Y0 - 40), x, Y0, cw, YMAX - Y0 - 40)
            sl.text(head, x + 36, Y0 + 32, cw - 72, size=48, font=HEAD, color=ACCENT)
            sl.text("\n".join("•  " + it for it in items), x + 36, Y0 + 190, cw - 72, size=34)
    elif k == "flow":  # vertical stack of text / centered images
        sl = Slide(out, "Title Only")
        sl.title(spec["title"], spec.get("sub"))
        y = Y0
        for blk in spec["blocks"]:
            if blk[0] == "text":
                sl.text(blk[1], X0, y, CW, size=36)
                y += 70
            elif blk[0] == "img":
                cx, cy, cw_, chh = add_figure(sl, blk[1], X0, y, CW, blk[2], card=False)
                y += chh + 20
            elif blk[0] == "code":
                y += add_code(sl, blk[1], X0, y, CW, size=32, lang=lang) + 30
            elif blk[0] == "eq":  # ("eq", r"latex", [font size])
                y += add_eq(sl, blk[1], X0, y, CW, *blk[2:]) + 40
            elif blk[0] == "imgtext":  # image left, text right
                _, img, ih, txt = blk
                cx, cy, cw_, chh = add_figure(sl, img, X0, y, 600, ih, center=False)
                sl.text(txt, X0 + 680, y + 60, CW - 680, size=40)
                y += chh + 20
    else:
        raise ValueError(k)
    if spec.get("notes"):
        sl.notes(spec["notes"])


def main():
    ap = argparse.ArgumentParser(description="Build Intro_MPI.key from slides.py.")
    ap.add_argument(
        "--overwrite", action="store_true", help="replace an existing Intro_MPI.key (Keynote edits are lost)"
    )
    ap.add_argument("--export-png", metavar="DIR", help="also export each slide as a PNG into DIR")
    ap.add_argument("--output", default=OUT, help="where to save the deck (default: Intro_MPI.key)")
    ap.add_argument(
        "--print-script", action="store_true", help="print the AppleScript to stdout instead of running osascript"
    )
    args = ap.parse_args()
    out_path = os.path.abspath(args.output)
    if os.path.exists(out_path) and not args.overwrite and not args.print_script:
        ap.error(f"{out_path} already exists (Keynote edits would be lost); pass --overwrite to replace it")
    out = [
        "set LS to character id 8232",
        'tell application "Keynote"',
        f'set d to make new document with properties {{document theme:theme "{THEME}", width:{W}, height:{H}}}',
    ]
    for sp in SLIDES:
        build(sp, out)
    out += ["delete slide 1 of d", f'save d in POSIX file "{out_path}"']
    if args.export_png:
        dest = os.path.abspath(args.export_png)
        if not args.print_script:
            os.makedirs(dest, exist_ok=True)
        out.append(f'export d to POSIX file "{dest}" as slide images with properties {{image format:PNG}}')
    # close the saved deck so builds don't pile up open windows in Keynote
    out += ["set n to count of slides of d", "close d saving no", "return n", "end tell"]
    script = "\n".join(out)
    if args.print_script:
        print(script)
        return
    path = os.path.join(CARDS, "build.applescript")
    os.makedirs(CARDS, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(script)
    r = subprocess.run(["osascript", path], capture_output=True, text=True)
    print(r.stdout.strip(), r.stderr.strip())
    sys.exit(r.returncode)


if __name__ == "__main__":
    main()
