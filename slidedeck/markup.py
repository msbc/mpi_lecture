"""Engine-independent text handling: inline-code markup, syntax highlighting and code sizing."""

import re
import sys

from .style import ACCENT, CHAR, COMMENT, KEYWORD, LINE, LITERAL, PAD, TYPE


def inline_code(s):
    """Strip `backtick` markup; return (plain text, 1-based inclusive character ranges of inline code)."""
    plain, ranges, pos = [], [], 0
    for i, part in enumerate(s.split("`")):
        if i % 2 and part:
            ranges.append((pos + 1, pos + len(part)))
        plain.append(part)
        pos += len(part)
    return "".join(plain), ranges


def code_size(code, w, hmax, maxsize=34):
    lines = code.split("\n")
    n, m = len(lines), max(len(ln.expandtabs(8)) for ln in lines)
    sz = min(maxsize, (w - 2 * PAD - 10) / (CHAR * m), (hmax - 2 * PAD - 10) / (LINE * n))
    return int(sz)


def code_height(code, size):
    return int(LINE * size * len(code.split("\n")) + 8 + 2 * PAD)


# pygments token type -> color; anything not listed stays the default code color
TOKEN_COLORS = [
    (("Comment",), COMMENT),
    (("Keyword",), KEYWORD),
    (("Keyword.Type", "Name.Builtin.Type"), TYPE),
    (("Literal.String", "Literal.Number"), LITERAL),
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
