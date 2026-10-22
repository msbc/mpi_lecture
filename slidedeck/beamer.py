"""BeamerEngine: generates a Beamer document styled like the Keynote deck, and compiles it with lualatex.

The page is 1920 x 1080 bp, so one Keynote pixel is one bp and Keynote font sizes carry over unchanged.
Every slide is a TikZ overlay that places things at the same coordinates as in Keynote.
"""

import glob
import os
import shutil
import subprocess
import tempfile

from .engine import BuildEngine
from .markup import inline_code
from .style import (
    ACCENT,
    BODY_SIZE,
    CAPTION,
    CARD_BORDER,
    CODE,
    COMMENT,
    COVER_FOOTER,
    COVER_SUB,
    COVER_TITLE,
    CW,
    HEAD,
    HEAD_TITLE,
    KEYWORD,
    LINE,
    LITERAL,
    MONO,
    MONO_BOLD,
    SANS,
    SANS_REGULAR,
    SECTION_TITLE,
    STATEMENT,
    SUBTITLE,
    TEXT,
    TITLE,
    TYPE,
    H,
    W,
    X0,
    Y0,
    YMAX,
)


SANS_LINE = 1.33  # line height / font size for the theme's sans text
PARA_SKIP = 1.45  # extra space between paragraphs of a Keynote text item, in em
# Keynote sets the first line of a text box lower than TeX does; shift top-aligned text down by this, in em
TOP_INSET = 0.45
CODE_INSET = 0.33
ITEM_SKIP = 1.1  # extra space between the bullets of a body placeholder, in em
# The theme's fonts ship with macOS as downloadable assets; Keynote downloads them on first use
ASSETS = "/System/Library/AssetsV2/com_apple_MobileAsset_Font*/*/AssetData"
SYSTEM_FONTS = "/System/Library/Fonts"
# font role -> (collection, face index); Helvetica Neue stands in if the theme fonts are missing
FACES = {
    SANS: ("Graphik.ttc", 6),  # Graphik-Light
    SANS_REGULAR: ("Graphik.ttc", 0),  # Graphik-Regular
    HEAD: ("Produkt.ttc", 4),  # Produkt-Light
    HEAD_TITLE: ("Produkt.ttc", 6),  # Produkt-Extralight
}
STAND_IN = {SANS: 7, SANS_REGULAR: 0, HEAD: 7, HEAD_TITLE: 12}  # HelveticaNeue Light, Regular, Light, Thin
# Glyphs missing from Graphik and Produkt (π, Δ, ∫, subscripts) come from Helvetica Neue, in a matching weight
# where it has them: font role -> faces of HelveticaNeue.ttc to try in turn
FALLBACKS = {SANS: (7, 0), SANS_REGULAR: (0,), HEAD: (7, 0), HEAD_TITLE: (12, 0), MONO: (0,)}
COLORS = {
    "text": TEXT,
    "code": CODE,
    "accent": ACCENT,
    "comment": COMMENT,
    "caption": CAPTION,
    "keyword": KEYWORD,
    "type": TYPE,
    "literal": LITERAL,
    "cardborder": CARD_BORDER,
}
# lualatex log lines worth reporting after a successful build
WARNINGS = ("Overfull", "Missing character")

# \fitbody{width}{height}{size}{\item ...}: a bulleted list, its font shrunk until the list fits the box,
# as in Keynote's body placeholder
FITBODY = r"""\newsavebox{\bodybox}\newdimen\bodysize
\newcommand{\fitbody}[4]{%
  \bodysize=#3bp\relax
  \loop
    \sbox{\bodybox}{\begin{minipage}[t]{#1bp}%
      \fontsize{\bodysize}{SANS_LINE\bodysize}\fontsans\selectfont\slideleft
      \begin{list}{\textbullet}{\setlength{\leftmargin}{1.1em}\setlength{\labelwidth}{0.6em}%
        \setlength{\labelsep}{0.5em}\setlength{\itemsep}{ITEM_SKIPem}\setlength{\topsep}{0pt}%
        \setlength{\parsep}{0pt}}#4\end{list}\end{minipage}}%
  \ifdim\dimexpr\ht\bodybox+\dp\bodybox\relax>#2bp\bodysize=0.95\bodysize\repeat
  \usebox{\bodybox}}"""

TEX_SPECIAL = {
    "\\": r"\textbackslash{}",
    "{": r"\{",
    "}": r"\}",
    "$": r"\$",
    "&": r"\&",
    "#": r"\#",
    "^": r"\textasciicircum{}",
    "_": r"\_",
    "%": r"\%",
    "~": r"\textasciitilde{}",
}


def tex_escape(s):
    """Escape LaTeX's special characters; keep runs of spaces."""
    out = "".join(TEX_SPECIAL.get(c, c) for c in s)
    return out.replace("  ", r" \ ").replace("\n", r"\\")


def font_file(role):
    """(directory, file, face index) of the font for a role."""
    name, index = FACES[role]
    found = sorted(glob.glob(os.path.join(ASSETS, name)))
    if found:
        return os.path.dirname(found[0]), name, index
    return SYSTEM_FONTS, "HelveticaNeue.ttc", STAND_IN[role]


def fallback(role):
    """luaotfload fallback list for a role's missing glyphs, and its name."""
    name = "fallback" + role.replace("-", "")
    faces = ", ".join(f'"[{SYSTEM_FONTS}/HelveticaNeue.ttc]({i}):mode=node;"' for i in FALLBACKS[role])
    return f'\\directlua{{luaotfload.add_fallback("{name}", {{{faces}}})}}', name


def font_cs(role):
    """The command that selects a role's font: \\fontsans, \\fonthead, ..., or \\ttfamily for code."""
    return {MONO: r"\ttfamily", MONO_BOLD: r"\ttfamily\bfseries"}.get(role) or "\\font" + role.replace("-", "")


def fontspec_family(role, command=None):
    """Font declaration for a role (\\newfontfamily\\font<role> by default), with its fallback for missing glyphs."""
    d, f, i = font_file(role)
    command = command or rf"\newfontfamily{font_cs(role)}"
    return f"{command}{{{f}}}[Path={d}/, FontIndex={i}, RawFeature={{fallback={fallback(role)[1]}}}]"


class BeamerEngine(BuildEngine):
    default_output = "Intro_MPI.pdf"
    protect_existing = False  # a generated PDF has no hand edits to lose

    def __init__(self, output):
        super().__init__(output)
        self.out = []
        self.colors = {}  # hex -> color name in the LaTeX
        self.master = None
        self.slide_notes = None

    def cmd(self, line):
        self.out.append(line)

    def color(self, hexcolor):
        """Name of the LaTeX color for a hex color, defining it if needed."""
        if hexcolor not in self.colors:
            self.colors[hexcolor] = f"c{hexcolor.lstrip('#')}"
        return self.colors[hexcolor]

    def inline(self, s):
        """Escaped text with `backticks` as inline code, in the current font."""
        plain, ranges = inline_code(s)
        parts, pos = [], 0
        for a, b in ranges:
            parts.append(tex_escape(plain[pos : a - 1]))
            parts.append(r"{\ttfamily " + tex_escape(plain[a - 1 : b]) + "}")
            pos = b
        parts.append(tex_escape(plain[pos:]))
        return "".join(parts)

    def styled(self, s, size, font):
        """Font switch + text, with `backticks` as inline code."""
        paragraphs = f"\\par\\vspace{{{PARA_SKIP}em}}".join(self.inline(p) for p in s.split("\n"))
        return f"\\fontsize{{{size}}}{{{size * SANS_LINE:.1f}}}{font_cs(font)}\\selectfont " + paragraphs

    def node(self, x, y, w, content, h=None, valign="top", halign="left", color=TEXT, inset=0):
        """Text node with its box at (x, y), width w; with h, aligned vertically in a box of that height.
        Top-aligned text starts `inset` px below y."""
        anchor, ny = {
            "top": ("north west", round(y + inset)),
            "middle": ("west", y + (h or 0) / 2),
            "bottom": ("south west", y + (h or 0)),
        }[valign]
        self.cmd(
            f"\\node[anchor={anchor}, inner sep=0pt, text width={w}bp, text={self.color(color)}] "
            f"at ({x},{ny}) {{\\slide{halign} {content}\\par}};"  # \\par inside: break lines with these settings
        )

    def box_text(self, box, s):
        content = self.styled(s, box.size, box.font)
        if box.valign == "bottom":  # the same depth with or without descenders, so baselines line up
            content += r"\vphantom{gp}"
        if box.shrink:
            content = f"\\fitline{{{box.w}}}{{{content}}}"
        self.node(box.x, box.y, box.w, content, box.h, box.valign, box.halign, inset=TOP_INSET * box.size)

    # ------------------------------------------------------------- document
    def begin(self):
        self.out = []
        self.colors = {v: k for k, v in COLORS.items()}

    def finish(self):
        self.end_slide()

    def preamble(self):
        return "\n".join(
            [
                r"\documentclass{beamer}",
                f"\\geometry{{paperwidth={W}bp, paperheight={H}bp}}",
                r"\usepackage{fontspec}",
                r"\usepackage{tikz}",
                r"\hypersetup{hidelinks}  % links are underlined by the slide, not boxed or colored by hyperref",
                r"\setbeamertemplate{navigation symbols}{}",
                r"\setbeamertemplate{background canvas}[default]",
                r"\setbeamercolor{background canvas}{bg=white}",
                *(fallback(role)[0] for role in FALLBACKS),
                *(fontspec_family(role) for role in FACES),
                f"\\setmonofont{{Menlo.ttc}}[Path={SYSTEM_FONTS}/, FontIndex=0, BoldFont=Menlo.ttc, "
                "BoldFeatures={FontIndex=1}, RawFeature={fallback=fallbackmono}]",
                fontspec_family(SANS, command=r"\setsansfont"),
                r"\renewcommand{\familydefault}{\sfdefault}",
                *(f"\\definecolor{{{name}}}{{HTML}}{{{h.lstrip('#')}}}" for h, name in self.colors.items()),
                r"\hyphenpenalty=10000 \exhyphenpenalty=10000 \frenchspacing",
                # beamer's \raggedright fixes \spaceskip and a finite \rightskip at the 11pt size, which would
                # stretch the words at slide sizes; reset them to the font's own spaces and a ragged margin
                r"\newcommand{\slidespaces}{\spaceskip=0pt\relax\xspaceskip=0pt\relax}",
                r"\newcommand{\slideleft}{\raggedright\rightskip=0pt plus 1fil\relax\slidespaces}",
                r"\newcommand{\slideright}{\raggedleft\leftskip=0pt plus 1fil\relax\parfillskip=0pt\relax\slidespaces}",
                r"\newcommand{\slidecenter}{\centering\leftskip=0pt plus 1fil\relax\rightskip=0pt plus 1fil\relax"
                r"\parfillskip=0pt\relax\slidespaces}",
                r"\setlength{\parskip}{0pt}",
                r"\newsavebox{\linebox}",
                r"\newcommand{\fitline}[2]{\sbox{\linebox}{#2}\ifdim\wd\linebox>#1bp"
                r"\resizebox{#1bp}{!}{\usebox{\linebox}}\else\usebox{\linebox}\fi}",
                FITBODY.replace("SANS_LINE", str(SANS_LINE)).replace("ITEM_SKIP", str(ITEM_SKIP)),
                r"\begin{document}",
            ]
        )

    def source(self):
        return self.preamble() + "\n" + "\n".join(self.out) + "\n\\end{document}\n"

    def render(self):
        with tempfile.TemporaryDirectory() as tmp:
            with open(os.path.join(tmp, "deck.tex"), "w", encoding="utf-8") as f:
                f.write(self.source())
            for _ in range(2):  # the second pass places the overlays (remember picture)
                r = subprocess.run(
                    ["lualatex", "-interaction=nonstopmode", "-halt-on-error", "deck.tex"],
                    cwd=tmp,
                    capture_output=True,
                    text=True,
                )
                if r.returncode:
                    log = os.path.splitext(self.output)[0] + ".log"
                    shutil.move(os.path.join(tmp, "deck.log"), log)
                    err = [ln for ln in r.stdout.splitlines() if ln.startswith("!")]
                    print(f"lualatex failed: {' '.join(err) or r.stdout[-1000:]}\n(full log: {log})")
                    return r.returncode
            with open(os.path.join(tmp, "deck.log"), encoding="utf-8", errors="replace") as f:
                log = f.read()
            shutil.move(os.path.join(tmp, "deck.pdf"), self.output)
        print(self.output)
        for w in WARNINGS:
            if n := log.count(w):
                print(f"warning: {n} x {w!r} in the lualatex log")
        return 0

    # ------------------------------------------------------------ primitives
    def end_slide(self):
        if self.master is None:
            return
        self.cmd(r"\end{tikzpicture}")
        if self.slide_notes:
            self.cmd(f"\\note{{{tex_escape(self.slide_notes)}}}")
        self.cmd(r"\end{frame}")

    def start_slide(self, master):
        self.end_slide()
        self.master, self.slide_notes = master, None
        self.cmd(r"\begin{frame}[plain]")
        self.cmd(r"\begin{tikzpicture}[remember picture, overlay, x=1bp, y=-1bp, shift={(current page.north west)}]")

    def title(self, title, sub=None):
        if self.master == "Section":
            self.box_text(SECTION_TITLE, title)
            return
        self.box_text(TITLE, title)
        if sub is not None:
            self.box_text(SUBTITLE, sub)

    def title_slide(self, title, sub, footer):
        self.box_text(COVER_TITLE, title)
        self.box_text(COVER_SUB, sub)
        self.box_text(COVER_FOOTER, footer)

    def statement(self, text):
        self.box_text(STATEMENT, text)

    def body(self, bullets, x=X0, y=Y0, w=CW, h=None, size=None):
        h = h or (YMAX - y)
        items = "".join(r"\item " + self.inline(b) for b in bullets)
        size = size or BODY_SIZE
        self.node(x, y, w, f"\\fitbody{{{w}}}{{{h}}}{{{size}}}{{{items}}}", inset=TOP_INSET * size)

    def text(self, s, x, y, w, size=36, font=SANS, color=TEXT, align="left", link=None):
        if font in (MONO, MONO_BOLD):
            content = f"\\fontsize{{{size}}}{{{size * LINE:.1f}}}{font_cs(font)}\\selectfont " + tex_escape(s)
        else:
            content = self.styled(s, size, font)
        if link:  # a link, underlined and otherwise styled like the text around it
            switch, text = content.split("\\selectfont ", 1)
            content = f"{switch}\\selectfont \\href{{{link}}}{{\\underline{{{text}}}}}"
        self.node(x, y, w, content, halign=align, color=color, inset=TOP_INSET * size)

    def code_text(self, code, x, y, w, size, spans):
        colors, bold = [CODE] * len(code), [False] * len(code)
        for a, b, col, bf in spans:  # later spans win, as in Keynote
            for i in range(a - 1, b):
                colors[i] = col
                bold[i] = bold[i] or bf
        lines, line, run, key, col = [], [], [], None, 0

        def flush():
            if run:
                c, bf = key
                body = "".join(run)
                weight = r"\bfseries " if bf else ""
                line.append(f"\\textcolor{{{self.color(c)}}}{{{weight}{body}}}")
                run.clear()

        for i, ch in enumerate(code):
            if ch == "\n":
                flush()
                lines.append("".join(line))
                line.clear()
                key, col = None, 0
                continue
            k = (colors[i], bold[i])
            if k != key:
                flush()
                key = k
            if ch == "\t":
                n = 8 - col % 8
                run.append(r"\ " * n)
                col += n
            else:
                run.append(r"\ " if ch == " " else TEX_SPECIAL.get(ch, ch))
                col += 1
        flush()
        lines.append("".join(line))
        body = "\\\\\n".join(r"\mbox{" + ln + "}" for ln in lines)
        content = f"\\fontsize{{{size}}}{{{size * LINE:.2f}}}\\ttfamily\\selectfont {body}"
        self.node(x, y, w, content, color=CODE, inset=CODE_INSET * size)

    def card(self, x, y, w, h, alpha=0.82):
        self.cmd(f"\\fill[white, fill opacity={alpha}, rounded corners=22bp] ({x},{y}) rectangle ++({w},{h});")
        self.cmd(
            f"\\draw[cardborder, draw opacity=0.9, line width=2bp, rounded corners=21bp] "
            f"({x + 1},{y + 1}) rectangle ++({w - 2},{h - 2});"
        )

    def image(self, path, x, y, w, h):
        self.cmd(
            f"\\node[anchor=north west, inner sep=0pt] at ({x},{y}) "
            f"{{\\includegraphics[width={w}bp, height={h}bp]{{{path}}}}};"
        )

    def notes(self, s):
        self.slide_notes = s
