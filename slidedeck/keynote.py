"""KeynoteEngine: generates an AppleScript that builds the deck in Keynote, and runs it with osascript."""

import os
import subprocess

from .assets import CARDS, write_card
from .engine import BuildEngine
from .markup import inline_code
from .style import CODE, CW, H, MONO, MONO_BOLD, SANS, SANS_REGULAR, HEAD, TEXT, W, X0, Y0, YMAX

THEME = "Dynamic Waves Light"
FONTS = {
    SANS: "Graphik-Light",
    SANS_REGULAR: "Graphik-Regular",
    HEAD: "Produkt-Light",
    MONO: "Menlo-Regular",
    MONO_BOLD: "Menlo-Bold",
}


def rgb(h):
    """AppleScript color literal (16-bit RGB) for a hex color."""
    h = h.lstrip("#")
    r, g, b = (int(h[i : i + 2], 16) * 257 for i in (0, 2, 4))
    return f"{{{r}, {g}, {b}}}"


def q(s):
    """AppleScript string literal; line separator U+2028 -> LS variable."""
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    parts = s.split(" ")
    return " & LS & ".join(f'"{p}"' for p in parts)


class KeynoteEngine(BuildEngine):
    default_output = "Intro_MPI.key"
    protect_existing = True  # the deck may have been edited by hand in Keynote

    def __init__(self, output, export_png=None):
        super().__init__(output)
        self.export_png = export_png
        self.out = []

    def cmd(self, line):
        self.out.append(line)

    def mono(self, ranges, item, indent=""):
        """Set the inline-code character ranges of `item`'s text in MONO."""
        for a, b in ranges:
            self.cmd(f'{indent}set font of characters {a} thru {b} of object text of {item} to "{FONTS[MONO]}"')

    # ------------------------------------------------------------- document
    def begin(self):
        self.out = [
            "set LS to character id 8232",
            'tell application "Keynote"',
            f'set d to make new document with properties {{document theme:theme "{THEME}", width:{W}, height:{H}}}',
        ]

    def finish(self):
        self.out += ["delete slide 1 of d", f'save d in POSIX file "{self.output}"']
        if self.export_png:
            self.out.append(
                f'export d to POSIX file "{self.export_png}" as slide images with properties {{image format:PNG}}'
            )
        # close the saved deck so builds don't pile up open windows in Keynote
        self.out += ["set n to count of slides of d", "close d saving no", "return n", "end tell"]

    def source(self):
        return "\n".join(self.out)

    def render(self):
        if self.export_png:
            os.makedirs(self.export_png, exist_ok=True)
        path = os.path.join(CARDS, "build.applescript")
        os.makedirs(CARDS, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.source())
        r = subprocess.run(["osascript", path], capture_output=True, text=True)
        print(r.stdout.strip(), r.stderr.strip())
        return r.returncode

    # ------------------------------------------------------------ primitives
    def start_slide(self, master):
        self.cmd(
            f'set s to make new slide at end of slides of d with properties {{base slide:master slide "{master}" of d}}'
        )

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
                    f'    set font of characters {a} thru {b} of object text of sh to "{FONTS[MONO]}"\n'
                    for a, b in ranges
                )
            )
            + "    exit repeat\n  end if\nend repeat"
        )

    def title(self, title, sub=None):
        item = "default title item of s"
        self.cmd(f"set object text of {item} to {q(title)}")
        # the theme's title font has no π glyph; use a thin face that matches the title weight
        for i, ch in enumerate(title):
            if ch == "π":
                self.cmd(
                    f'try\n  set font of character {i + 1} of object text of {item} to "HelveticaNeue-Thin"\nend try'
                )
        self.placeholder_text(183, sub)

    def title_slide(self, title, sub, footer):
        self.cmd(f"set object text of default title item of s to {q(title)}")
        self.cmd(f"set object text of default body item of s to {q(sub)}")
        self.placeholder_text(966, footer)

    def statement(self, text):
        self.cmd("try\n  set object text of default body item of s to " + q(text) + "\nend try")
        self.cmd("try\n  set object text of default title item of s to " + q(text) + "\nend try")

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

    def card(self, x, y, w, h, alpha=0.82):
        self.image(write_card(w, h, alpha=alpha), x, y, w, h)

    def text(self, s, x, y, w, size=36, font=SANS, color=TEXT):
        s, ranges = inline_code(s) if font != MONO else (s, [])
        self.cmd("tell s to set ti to make new text item")
        self.cmd(f"set object text of ti to {q(s)}")
        self.cmd(f'set font of object text of ti to "{FONTS[font]}"')
        self.cmd(f"set size of object text of ti to {size}")
        self.cmd(f"set color of object text of ti to {rgb(color)}")
        self.cmd(f"set width of ti to {w}")
        self.cmd(f"set position of ti to {{{x}, {y}}}")
        self.mono(ranges, "ti")

    def code_text(self, code, x, y, w, size, spans):
        self.text(code.replace("\n", " "), x, y, w, size=size, font=MONO, color=CODE)
        for a, b, col, bold in spans:
            if bold:
                self.cmd(f'set font of characters {a} thru {b} of object text of ti to "{FONTS[MONO_BOLD]}"')
            self.cmd(f"set color of characters {a} thru {b} of object text of ti to {rgb(col)}")

    def notes(self, s):
        self.cmd(f"set presenter notes of s to {q(s)}")
