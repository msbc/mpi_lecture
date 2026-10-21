"""BuildEngine: the slide layouts, written once against drawing primitives that each engine implements."""

import os
import re
import subprocess
import sys
from abc import ABC, abstractmethod

from .assets import FIG, HERE, png_size, render_eq
from .markup import code_height, code_size, highlight
from .style import ACCENT, CAPTION, CW, HEAD, LINE, PAD, SANS, SANS_REGULAR, TEXT, X0, Y0, YMAX


def repo_url():
    """The repository's origin remote as host/path (e.g. github.com/user/repo), or None if it has none."""
    r = subprocess.run(["git", "-C", HERE, "remote", "get-url", "origin"], capture_output=True, text=True)
    if r.returncode:
        return None
    url = r.stdout.strip().removesuffix(".git")
    # https://host/path, ssh://user@host:port/path or user@host:path
    m = re.fullmatch(r"(?:[a-z+]+://)?(?:[^@/]+@)?([^:/]+)(?::\d+)?[:/](.+)", url)
    return f"{m[1]}/{m[2]}" if m else url


class BuildEngine(ABC):
    """Builds a deck from the slide specs in slides.py.

    Each spec's `kind` selects a layout_<kind> method. Layouts place things in Keynote pixel
    coordinates (1920x1080, origin top left) through the primitives below, which subclasses implement.
    Masters are Keynote's master slide names: "Title", "Section", "Statement", "Title & Bullets", "Title Only".
    Any slide with repo=True also shows the repository's URL (from git) at the lower right.
    """

    default_output = None  # file name in the repository root
    protect_existing = True  # refuse to replace an existing output without --overwrite

    def __init__(self, output):
        self.output = output
        self.lang = "c"

    def build(self, slides):
        self.repo = repo_url()
        if self.repo is None and any(spec.get("repo") for spec in slides):
            print("warning: no git remote named origin, so the slides show no repository URL", file=sys.stderr)
        self.begin()
        for spec in slides:
            self.lang = spec.get("lang", "c")  # syntax highlighting for code blocks
            layout = getattr(self, f"layout_{spec['kind']}", None)
            if layout is None:
                raise ValueError(spec["kind"])
            layout(spec)
            if spec.get("repo") and self.repo:
                self.add_repo_url()
            if spec.get("notes"):
                self.notes(spec["notes"])
        self.finish()

    # ------------------------------------------------------------ primitives
    @abstractmethod
    def begin(self):
        """Start the document."""

    @abstractmethod
    def finish(self):
        """End the document."""

    @abstractmethod
    def source(self):
        """The generated program (AppleScript, LaTeX) as a string."""

    @abstractmethod
    def render(self):
        """Run the generated program to write self.output; return an exit status."""

    @abstractmethod
    def start_slide(self, master):
        """Begin a new slide based on a master."""

    @abstractmethod
    def title(self, title, sub=None):
        """Set the slide title, and the subtitle (removed if None)."""

    @abstractmethod
    def title_slide(self, title, sub, footer):
        """Fill the title, subtitle and footer of a "Title" master slide."""

    @abstractmethod
    def statement(self, text):
        """Fill the single text of a "Statement" master slide."""

    @abstractmethod
    def body(self, bullets, x=X0, y=Y0, w=CW, h=None, size=None):
        """Bulleted list in the box (x, y, w, h); h defaults to the rest of the content area."""

    @abstractmethod
    def text(self, s, x, y, w, size=36, font=SANS, color=TEXT, align="left", link=None):
        """Text in a box of width w, aligned "left" or "right"; outside code (font MONO), `backticks` mark
        inline code. With link, an engine that can makes the text a link to that URL."""

    @abstractmethod
    def code_text(self, code, x, y, w, size, spans):
        """Code in MONO; spans are (start, end, color, bold) 1-based inclusive character ranges."""

    @abstractmethod
    def card(self, x, y, w, h, alpha=0.82):
        """White rounded card with a thin border behind code or figures."""

    @abstractmethod
    def image(self, path, x, y, w, h):
        """Image file (PNG or PDF) stretched to the box."""

    @abstractmethod
    def notes(self, s):
        """Presenter notes for the current slide."""

    # ------------------------------------------------------------ composites
    def add_code(self, code, x, y, w, hmax=None, size=None, lang="c", marks=()):
        """Code on a rounded card at (x, y), width w. Each regex in `marks` sets its matches (group 1
        if it has one) in bold ACCENT on top of the syntax colors. Returns card height."""
        hmax = hmax or (YMAX - y)
        size = size or code_size(code, w, hmax)
        ch = code_height(code, size)
        self.card(x, y, w, ch)
        spans = [(a, b, col, False) for a, b, col in highlight(code, lang)]
        for pattern in marks:
            for m in re.finditer(pattern, code):
                g = 1 if m.re.groups else 0
                spans.append((m.start(g) + 1, m.end(g), ACCENT, True))
        self.code_text(code, x + PAD, y + PAD, w - 2 * PAD, size, spans)
        return ch

    def add_repo_url(self):
        """The repository's URL at the lower right, on the line of the title slide's footer."""
        self.text(self.repo, X0, 968, CW, size=30, font=HEAD, color=CAPTION, align="right", link=f"https://{self.repo}")

    def add_figure(self, name, x, y, bw, bh, center=True, card=True):
        """Fit figure into box (bw x bh) on a white card; returns (x, y, w, h) of card."""
        path = os.path.join(FIG, name)
        iw, ih = png_size(path)
        p = 24 if card else 0
        sc = min((bw - 2 * p) / iw, (bh - 2 * p) / ih)
        w, h = int(iw * sc), int(ih * sc)
        cx = x + (bw - (w + 2 * p)) // 2 if center else x
        if card:
            self.card(cx, y, w + 2 * p, h + 2 * p, alpha=0.95)
        self.image(path, cx + p, y + p, w, h)
        return cx, y, w + 2 * p, h + 2 * p

    def add_eq(self, tex, x, y, bw, size=44, center=True):
        """LaTeX display equation at (x, y) in a box of width bw, scaled so its text matches a
        `size`-pt font (shrunk if too wide). Returns its height."""
        path, pw, ph = render_eq(tex)
        sc = min(size / 10, bw / pw)
        w, h = round(pw * sc), round(ph * sc)
        self.image(path, x + (bw - w) // 2 if center else x, y, w, h)
        return h

    # --------------------------------------------------------------- layouts
    def layout_title(self, spec):
        self.start_slide("Title")
        self.title_slide(spec["title"], spec["sub"], spec["footer"])
        if spec.get("credit"):  # small line just under the subtitle
            self.text(spec["credit"], X0, 651, CW, size=24, font=SANS_REGULAR)

    def layout_section(self, spec):
        self.start_slide("Section")
        self.title(spec["title"])

    def layout_statement(self, spec):
        self.start_slide("Statement")
        self.statement(spec["title"])

    def layout_bullets(self, spec):
        self.start_slide("Title & Bullets")
        self.title(spec["title"], spec.get("sub"))
        self.body(spec["bullets"], size=spec.get("size"))

    def layout_split(self, spec):
        """Bullets left, code right (code: a string, or a list of strings / (code, lang) stacked)."""
        self.start_slide("Title & Bullets")
        self.title(spec["title"], spec.get("sub"))
        cw = spec.get("code_w", 900)
        self.body(spec["bullets"], w=CW - cw - 60, size=spec.get("size", 36))
        code = [spec["code"]] if isinstance(spec["code"], str) else spec["code"]
        blocks = [b if isinstance(b, tuple) else (b, self.lang) for b in code]
        gap, y = 30, Y0 + 20
        # one font size for all blocks: each fits the width, and together they fit the height
        nlines = sum(c.count("\n") + 1 for c, _ in blocks)
        room = YMAX - y - gap * (len(blocks) - 1) - len(blocks) * (2 * PAD + 10)
        size = spec.get("code_size") or int(
            min(min(code_size(c, cw, 10**4) for c, _ in blocks), room / (LINE * nlines))
        )
        for c, lg in blocks:
            y += self.add_code(c, X0 + CW - cw, y, cw, size=size, lang=lg, marks=spec.get("marks", ())) + gap

    def layout_code(self, spec):
        """Code card on top, optional bullets below."""
        self.start_slide("Title & Bullets" if spec.get("bullets") else "Title Only")
        self.title(spec["title"], spec.get("sub"))
        hmax = spec.get("code_h", YMAX - Y0)
        ch = self.add_code(
            spec["code"], X0, Y0, spec.get("code_w", CW), hmax=hmax, size=spec.get("code_size"), lang=self.lang
        )
        if spec.get("bullets"):
            self.body(spec["bullets"], y=Y0 + ch + 40, size=spec.get("size", 36))

    def layout_twocode(self, spec):
        self.start_slide("Title Only")
        self.title(spec["title"], spec.get("sub"))
        cw = (CW - 40) // 2
        sz = min(code_size(spec["left"], cw, YMAX - Y0), code_size(spec["right"], cw, YMAX - Y0))
        self.add_code(spec["left"], X0, Y0, cw, size=sz, lang=self.lang)
        self.add_code(spec["right"], X0 + cw + 40, Y0, cw, size=sz, lang=self.lang)

    def layout_figure(self, spec):
        """Optional code, figure, caption, optional trailing text."""
        self.start_slide("Title Only")
        self.title(spec["title"], spec.get("sub"))
        y = Y0
        if spec.get("code"):
            y += self.add_code(spec["code"], X0, y, CW, size=spec.get("code_size", 32), lang=self.lang) + 30
        bottom = YMAX - (50 if spec.get("caption") else 0) - (70 if spec.get("after") else 0)
        cx, cy, cw_, chh = self.add_figure(spec["image"], X0, y, CW, min(bottom - y, spec.get("max_h", 2000)))
        y = cy + chh + 12
        if spec.get("caption"):
            self.text(spec["caption"], cx, y, max(cw_, 900), size=28, color=CAPTION)
            y += 50
        if spec.get("after"):
            self.text(spec["after"], X0, y + 10, CW, size=34)

    def layout_codefig(self, spec):
        """Code (or program output, with lang=None) left, figure right."""
        self.start_slide("Title Only")
        self.title(spec["title"], spec.get("sub"))
        cw = spec.get("code_w", 1000)
        self.add_code(spec["code"], X0, Y0, cw, size=spec.get("code_size"), lang=self.lang, marks=spec.get("marks", ()))
        fx, fw = X0 + cw + 50, CW - cw - 50
        cx, cy, cw_, chh = self.add_figure(spec["image"], fx, Y0, fw, YMAX - Y0 - (60 if spec.get("caption") else 0))
        if spec.get("caption"):
            self.text(spec["caption"], cx, cy + chh + 12, cw_, size=26, color=CAPTION)

    def layout_figbullets(self, spec):
        """Figure left, bullets right."""
        self.start_slide("Title & Bullets")
        self.title(spec["title"], spec.get("sub"))
        fw = spec.get("fig_w", 800)
        cx, cy, cw_, chh = self.add_figure(spec["image"], X0, Y0, fw, YMAX - Y0 - 60)
        if spec.get("caption"):
            self.text(spec["caption"], cx, cy + chh + 12, cw_, size=26, color=CAPTION)
        self.body(spec["bullets"], x=X0 + fw + 60, w=CW - fw - 60, size=spec.get("size", 34))

    def layout_figpair(self, spec):
        self.start_slide("Title Only")
        self.title(spec["title"], spec.get("sub"))
        y = Y0
        for line in spec.get("lines", []):
            self.text(line, X0, y, CW, size=34)
            y += 64
        y += 16
        bw = (CW - 60) // 2
        for i, (img, cap) in enumerate(spec["images"]):
            x = X0 + i * (bw + 60)
            cx, cy, cw_, chh = self.add_figure(img, x, y, bw, YMAX - y - 80)
            self.text(cap, x, cy + chh + 12, bw, size=26, color=CAPTION)

    def layout_columns(self, spec):
        self.start_slide("Title Only")
        self.title(spec["title"], spec.get("sub"))
        n = len(spec["cols"])
        gap = 50
        cw = (CW - gap * (n - 1)) // n
        for i, (head, items) in enumerate(spec["cols"]):
            x = X0 + i * (cw + gap)
            self.card(x, Y0, cw, YMAX - Y0 - 40)
            self.text(head, x + 36, Y0 + 32, cw - 72, size=48, font=HEAD, color=ACCENT)
            self.text("\n".join("•  " + it for it in items), x + 36, Y0 + 190, cw - 72, size=34)

    def layout_flow(self, spec):
        """Vertical stack of text / centered images."""
        self.start_slide("Title Only")
        self.title(spec["title"], spec.get("sub"))
        y = Y0
        for blk in spec["blocks"]:
            if blk[0] == "text":
                self.text(blk[1], X0, y, CW, size=36)
                y += 70
            elif blk[0] == "img":
                cx, cy, cw_, chh = self.add_figure(blk[1], X0, y, CW, blk[2], card=False)
                y += chh + 20
            elif blk[0] == "code":
                y += self.add_code(blk[1], X0, y, CW, size=32, lang=self.lang) + 30
            elif blk[0] == "eq":  # ("eq", r"latex", [font size])
                y += self.add_eq(blk[1], X0, y, CW, *blk[2:]) + 40
            elif blk[0] == "imgtext":  # image left, text right
                _, img, ih, txt = blk
                cx, cy, cw_, chh = self.add_figure(img, X0, y, 600, ih, center=False)
                self.text(txt, X0 + 680, y + 60, CW - 680, size=40)
                y += chh + 20
