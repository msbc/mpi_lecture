"""Geometry, metrics, colors and font roles shared by every engine.

Coordinates are Keynote pixels on a 1920x1080 canvas, origin top left. Font sizes are in points
on that canvas (Keynote treats 1 px as 1 pt; the Beamer engine sets 1 px = 1 bp).
"""

from collections import namedtuple

W, H = 1920, 1080
X0, CW = 95, 1730  # left margin, content width
Y0, YMAX = 300, 1020  # content area (below title + subtitle)

LINE = 1.167  # Menlo line height / font size in Keynote text items
CHAR = 0.602  # Menlo advance / font size
PAD = 28  # card padding around code

# Colors, as hex
TEXT = "#41464D"  # theme body text
CODE = "#2B3036"
ACCENT = "#1F63B5"  # MPI identifiers
COMMENT = "#7D858F"
CAPTION = "#6A7079"
KEYWORD = "#9B3D8F"
TYPE = "#2E7D6B"
LITERAL = "#B35C1E"
CARD_BORDER = "#CDD8E2"

# Font roles: each engine maps these to its own font names
SANS = "sans"  # body text
SANS_REGULAR = "sans-regular"  # a heavier body face (the title slide's credit line)
HEAD = "head"  # headings
MONO = "mono"  # code
MONO_BOLD = "mono-bold"

HEAD_TITLE = "head-title"  # an extra font role: Produkt-Extralight, for the masters' titles

BODY_SIZE = 40  # the "Title & Bullets" master's body size
# Text boxes of the Keynote masters, measured with osascript
# shrink: one line, scaled down to fit the width (Keynote's "shrink text to fit"); otherwise lines wrap
Box = namedtuple("Box", "x y w h font size valign halign shrink", defaults=("left", False))
TITLE = Box(95, 50, 1730, 123, HEAD_TITLE, 100, "bottom", shrink=True)  # "Title & Bullets" and "Title Only"
SUBTITLE = Box(95, 175, 1730, 79, HEAD_TITLE, 55, "top", shrink=True)
SECTION_TITLE = Box(95, 308, 1730, 366, HEAD_TITLE, 120, "middle")
STATEMENT = Box(95, 330, 1730, 322, HEAD_TITLE, 120, "middle", "center")
COVER_TITLE = Box(95, 206, 1730, 338, HEAD_TITLE, 120, "bottom")  # the "Title" master
COVER_SUB = Box(95, 579, 1730, 158, HEAD_TITLE, 55, "top", shrink=True)
COVER_FOOTER = Box(95, 966, 1730, 52, HEAD, 33, "top", shrink=True)
