# Introduction to MPI: lecture and exercises

Materials for the "Introduction to MPI" lecture at the Fall Break Parallel Programming Bootcamp 2026
(Research Computing, Princeton University). Adapted from slides by Jonathan Gorard (PPPL).

The repository has two parts: a Keynote deck generated from a Python slide spec, and hands-on exercises in C and Fortran.

## Contents

| Path | What it is |
| --- | --- |
| `slides.py` | Slide content and presenter notes: the source of truth for the deck |
| `build_keynote.py` | Builds `Intro_MPI.key` from `slides.py` (macOS and Keynote only) |
| `figures/` | Images used by the slides |
| `figures/src/` | Matplotlib scripts that draw some of those images |
| `Intro_MPI/` | The exercises; see [Intro_MPI/README.md](Intro_MPI/README.md) |
| `ci/check_exercises.py` | Builds and runs every exercise and checks the printed value of π |
| `ci/sync_shared.py` | Copies the code in `Intro_MPI/shared/` into every exercise |
| `ci/check_slides.py` | Checks that the code on the slides matches the exercise files |
| `.github/workflows/exercises.yml` | Runs that check on GitHub Actions with GCC, Clang and Intel compilers |

## Building the slides

Edit `slides.py`, then build the deck:

```
uv run build_keynote.py --output /tmp/Intro_MPI.key
```

- The script drives Keynote through AppleScript, so it needs macOS with Keynote installed.
- Code blocks are syntax-highlighted with [Pygments](https://pygments.org) (installed by `uv run` from `pyproject.toml`).
  Set `lang="bash"`, `"make"` or `"fortran"` on a slide in `slides.py`; the default is C.
- It uses the "Dynamic Waves Light" theme at 16:9.
- It refuses to overwrite an existing file unless you pass `--overwrite`.
  Without `--output` it writes `Intro_MPI.key` in this directory.
- `--export-png DIR` also exports each slide as an image.
- `--print-script` prints the generated AppleScript instead of running it, for debugging a build.
  Nothing is saved, so it skips the overwrite check; it still renders any missing cards and equations under `figures/`.

`Intro_MPI.key` is generated and not tracked by git; change `slides.py`, not the deck.

### Figures

Some figures are drawn by scripts in `figures/src/`, which write PNGs into `figures/`.
Hand-tunable settings (sizes, colors, ticks) are constants at the top of each script.

```
uv run --active --group figures figures/src/riemann_sum.py    # riemann-sum.png
uv run --active --group figures figures/src/communication.py  # blocking.png, nonblocking.png
```

Pass `--show` to open a figure in a window instead of saving it.

## Exercises

The exercises estimate π by numerical integration, first serially and then with MPI, in C and Fortran.
See [Intro_MPI/README.md](Intro_MPI/README.md) for how to build and run them (written for Adroit).

To check all of them locally (needs an MPI installation):

```
python3 ci/check_exercises.py
```

## Development

Linting and formatting run through [pre-commit](https://pre-commit.com):

```
pre-commit install
pre-commit run --all-files
```

| Language | Tools | Config |
| --- | --- | --- |
| Python | ruff (lint and format) | `.ruff.toml` |
| C | clang-format, clang-tidy (as both C and C++) | `.clang-format`, `.clang-tidy` |
| Fortran | fortitude | `fortitude.toml` |

The clang-tidy hooks use `bear` to generate `Intro_MPI/C/compile_commands.json`.

### Shared code in the exercises

Every exercise is a self-contained file, but some code (the exact value of π, and reading the number of slices from the command line) is the same in all of them.
That code lives once in `Intro_MPI/shared/` (for example `parse_nslices.c` and `parse_nslices.f90`), and is copied between `BEGIN shared` and `END shared` comments in each program.
Edit the file in `Intro_MPI/shared/`, never a copy, then run:

```
python3 ci/sync_shared.py
```

A pre-commit hook and the GitHub workflow run `python3 ci/sync_shared.py --check`, which fails if any copy is out of date.

### Code on the slides

A slide that lists an exercise's code names the file in `slides.py`, e.g. `source="C/solutions/cpi_2.c"` (relative to `Intro_MPI/`).
The slide shows that program's main code: everything from `int main(` on in C, or everything but the `contains` section in Fortran.
Add `excerpt=True` for a slide that shows only part of it.
Check them with:

```
python3 ci/check_slides.py
```

The comparison ignores comments, line wrapping and the order of names in a Fortran `use ..., only:` line, so slides can trim and rewrap code for display.
A pre-commit hook and the GitHub workflow (in its own `slides` job) run it too.
A failure gives the line in `slides.py` and the line in the exercise where they first differ:

```
FAIL  slide 33 (Exercise #2 solution in C) doesn't match Intro_MPI/C/solutions/cpi_2.c
  slides.py:519:  printf("Number of intervals = %d.\n",
  Intro_MPI/C/solutions/cpi_2.c:63:  printf("Number of slices = %d.\n", nslices);
```

Fix whichever side is wrong (usually the listing in `slides.py`), then rebuild the deck.
On GitHub the same errors also appear on those lines of a pull request's diff.
