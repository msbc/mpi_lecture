"""Geometry, metrics, colors and font roles shared by every engine.

Coordinates are Keynote pixels on a 1920x1080 canvas, origin top left. Font sizes are in points
on that canvas (Keynote treats 1 px as 1 pt; the Beamer engine sets 1 px = 1 bp).
"""

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
