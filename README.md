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
| `Intro_MPI/` | The exercises; see [Intro_MPI/README.md](Intro_MPI/README.md) |
| `ci/check_exercises.py` | Builds and runs every exercise and checks the printed value of π |
| `.github/workflows/exercises.yml` | Runs that check on GitHub Actions with GCC, Clang and Intel compilers |

## Building the slides

Edit `slides.py`, then build the deck:

```
python3 build_keynote.py --output /tmp/Intro_MPI.key
```

- The script drives Keynote through AppleScript, so it needs macOS with Keynote installed.
- It uses the "Dynamic Waves Light" theme at 16:9.
- It refuses to overwrite an existing file unless you pass `--overwrite`.
  Without `--output` it writes `Intro_MPI.key` in this directory.
- `--export-png DIR` also exports each slide as an image.

`Intro_MPI.key` is generated and not tracked by git; change `slides.py`, not the deck.

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
