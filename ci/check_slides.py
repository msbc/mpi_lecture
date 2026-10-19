#!/usr/bin/env python3
"""Check that the code on the slides matches the exercise files it comes from.

A slide in slides.py with source="C/solutions/cpi_2.c" (relative to Intro_MPI)
shows that program's main code: everything from "int main(" on in C, or
everything except the contains section in Fortran. With excerpt=True, the
slide shows one unbroken stretch of it instead.

The code is compared token by token, so the slides may leave out comments,
wrap lines differently (in Fortran, with & continuations; in C, splitting a
string into adjacent literals) and list the names in a Fortran
"use ..., only:" line in any order. Everything else, including the text
inside strings, must match.
"""

import argparse
import ast
import io
import os
import re
import sys
import tokenize
from pathlib import Path

HERE = Path(__file__).resolve().parent.parent
ROOT = HERE / "Intro_MPI"
SLIDES_PY = HERE / "slides.py"
sys.path.insert(0, str(HERE))
from slides import SLIDES  # noqa: E402

C_TOKEN = re.compile(r'"(?:\\.|[^"\\\n])*"|\'(?:\\.|[^\'\\\n])*\'|/\*.*?\*/|//[^\n]*|\w+|\S', re.S)
F_TOKEN = re.compile(r'"[^"]*"|\'[^\']*\'|!.*|\w+|\S')
END_OF_STATEMENT = "<newline>"
HINT = "Update the listing in slides.py to match the file (or fix the file), then rebuild the deck."


class SourceError(Exception):
    """The source file can't be checked, e.g. it's missing or has no main program."""


# Tokens are (text, line) pairs: the line, counted from 0, of the code they come from


def c_tokens(code):
    tokens = []
    for m in C_TOKEN.finditer(code):
        tok = m.group()
        if tok.startswith(("/*", "//")):
            continue
        # "abc" "def" is one string to the compiler
        if tok.startswith('"') and tokens and tokens[-1][0].startswith('"'):
            tokens[-1] = (tokens[-1][0][:-1] + tok[1:], tokens[-1][1])
        else:
            tokens.append((tok, code.count("\n", 0, m.start())))
    return tokens


def f_tokens(code):
    tokens, statement = [], []
    for number, line in enumerate(code.split("\n")):
        toks = [(t, number) for t in F_TOKEN.findall(line) if not t.startswith("!")]
        continued = bool(toks) and toks[-1][0] == "&"
        statement += [t for t in toks if t[0] != "&"]
        if continued or not statement:
            continue
        texts = [t for t, _ in statement]
        if texts[0] == "use" and "only" in texts:
            start = texts.index("only") + 2
            statement = statement[:start] + sorted(t for t in statement[start:] if t[0] != ",")
        tokens += statement + [(END_OF_STATEMENT, number)]
        statement = []
    return tokens


def main_code(path):
    """The part of a program that a full listing shows.

    Returns (code, lines), where lines maps each line of code (from 0) to its line in the file (from 1).
    """
    text = path.read_text().split("\n")
    if path.suffix == ".c":
        start = next((i for i, ln in enumerate(text) if ln.startswith("int main(")), None)
        if start is None:
            raise SourceError('no line starting "int main(" to mark where the listing begins')
        keep = range(start, len(text))
    else:
        # Drop the contained procedures, but keep "end program"
        contains = next((i for i, ln in enumerate(text) if ln.strip() == "contains"), len(text))
        end = next((i for i, ln in enumerate(text) if ln.startswith("end program")), len(text))
        keep = [*range(contains), *range(end, len(text))]
    return "\n".join(text[i] for i in keep), {n: i + 1 for n, i in enumerate(keep)}


def literal_lines(spec_index, keys):
    """Map each line of a slide's code to the line of slides.py it is written on.

    KEYS are the slide's fields that hold the code (e.g. left and right), joined
    by newlines in that order. Each line of code is written as one or more string
    literals; return {line in the code: line in slides.py of its first literal}.
    """
    source = SLIDES_PY.read_text()
    tree = ast.parse(source)
    slides = next(
        n.value for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "SLIDES"
    )
    call = slides.elts[spec_index]
    values = {kw.arg: kw.value for kw in call.keywords}
    lines, code_line = {}, 0
    for key in keys:
        node = values[key]
        segment = "\n".join(source.split("\n")[node.lineno - 1 : node.end_lineno])
        for tok in tokenize.generate_tokens(io.StringIO(segment).readline):
            if tok.type != tokenize.STRING:
                continue
            lines.setdefault(code_line, node.lineno + tok.start[0] - 1)
            code_line += ast.literal_eval(tok.string).count("\n")
        code_line += 1  # the newline that joins this field to the next
    return lines


def slide_code(spec):
    """The code on a slide and the fields of the slide it comes from."""
    if spec["kind"] == "twocode":
        return spec["left"] + "\n" + spec["right"], ["left", "right"]
    if isinstance(spec.get("code"), str):
        return spec["code"], ["code"]
    raise SourceError('source= works only on "twocode" slides and slides with a single code block')


def first_difference(a, b):
    return next((i for i, (x, y) in enumerate(zip(a, b)) if x[0] != y[0]), min(len(a), len(b)))


def best_alignment(got, want):
    """Where an excerpt most likely starts in the source: the start that matches it longest."""
    starts = [i for i, t in enumerate(want) if t[0] == got[0][0]] or [0]
    return max(starts, key=lambda s: first_difference(got, want[s:]))


def line_at(tokens, i, code):
    """The line of CODE holding token I (or the last token), and its number in CODE."""
    if not tokens:
        return None, "(empty)"
    number = tokens[min(i, len(tokens) - 1)][1]
    return number, code.split("\n")[number].strip() + ("" if i < len(tokens) else "   <- ends here")


class Mismatch(Exception):
    def __init__(self, slide_line, file_line, slide_text, file_text):
        super().__init__()
        self.slide_line, self.file_line = slide_line, file_line
        self.slide_text, self.file_text = slide_text, file_text


def check(index, spec):
    """Raise Mismatch if slide INDEX doesn't match its source, or SourceError if it can't be checked."""
    path = ROOT / spec["source"]
    if not path.is_file():
        raise SourceError(f"no such file {path.relative_to(HERE)}")
    tokenizer = c_tokens if path.suffix == ".c" else f_tokens
    code, keys = slide_code(spec)
    source, file_lines = main_code(path)
    got, want = tokenizer(code), tokenizer(source)
    start = best_alignment(got, want) if spec.get("excerpt") and got else 0
    candidate = want[start : start + len(got)] if spec.get("excerpt") else want
    i = first_difference(got, candidate)
    if i == len(got) == len(candidate):
        return
    slide_number, slide_text = line_at(got, i, code)
    file_number, file_text = line_at(want, start + i, source)
    slide_lines = literal_lines(index, keys)
    raise Mismatch(slide_lines.get(slide_number, slide_lines[0]), file_lines.get(file_number, 1), slide_text, file_text)


def annotate(path, line, title, message):
    """Show an error on that line of the file in GitHub's pull request view."""
    message = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error file={path},line={line},title={title}::{message}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.parse_args()
    github = os.environ.get("GITHUB_ACTIONS") == "true"

    checked = failures = 0
    for index, spec in enumerate(SLIDES):
        if "source" not in spec:
            continue
        checked += 1
        label = f"slide {index + 1} ({spec['title']})"
        source = f"Intro_MPI/{spec['source']}"
        try:
            check(index, spec)
        except SourceError as e:
            failures += 1
            print(f"FAIL  {label}: can't check {source}: {e}")
            continue
        except Mismatch as m:
            failures += 1
            what = "isn't in" if spec.get("excerpt") else "doesn't match"
            print(f"FAIL  {label} {what} {source}")
            print(f"  slides.py:{m.slide_line}:  {m.slide_text}")
            print(f"  {source}:{m.file_line}:  {m.file_text}")
            print(f"  {HINT}")
            if github:
                body = f"The code on {label} {what} {source}:{m.file_line}.\n{HINT}"
                annotate("slides.py", m.slide_line, "Slide code doesn't match the exercise", body)
                annotate(source, m.file_line, "Slide code doesn't match the exercise", body)
            continue
        print(f"ok    {label}")

    print(f"\n{checked} listing(s) checked, {failures} failure(s)")
    print('(Slides without source="..." are not checked.)')
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
