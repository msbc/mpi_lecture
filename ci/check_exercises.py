#!/usr/bin/env python3
"""Build every MPI exercise with its Makefile, run it, and check the output.

Each program is built with "make <name>" (and "make <name>-cxx" for the C
sources), run as "<mpirun> -np <N> ./pi", and its printed value(s) of pi are
checked against what that stage of the exercise is expected to print.
"""

import argparse
import math
import re
import shlex
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent / "Intro_MPI"
TOLERANCE = 1e-8

# A printed value of pi, e.g. "Pi is approximately 3.14...", " Pi=   3.14...",
# "pi is    3.14..."
PI_VALUE = re.compile(r"\bpi(?: is(?: approximately)?)?\s*=?\s*([-+0-9.]+(?:[eE][-+]?\d+)?)", re.I)
JACOBI_DIFF = re.compile(r"diff is ([-+0-9.eE]+)")

# Programs whose ranks each print only their share of the integral, so the
# printed values add up to pi instead of one of them being pi.
PARTIAL_SUMS = {"cpi_3", "fpi_3", "ex4e"}


def check_output(name, output, nproc):
    """Return an error message if the output is not what NAME should print."""
    if name == "jacobi_MPI":
        diffs = [float(d) for d in JACOBI_DIFF.findall(output)]
        if not diffs or diffs[-1] > 1e-2:
            return f"Jacobi did not converge (last diff: {diffs[-1] if diffs else 'none'})"
        return None

    values = [float(v) for v in PI_VALUE.findall(output)]
    if not values:
        return "no value of pi in the output"
    if name in PARTIAL_SUMS:
        if len(values) != nproc:
            return f"expected {nproc} partial sums, got {len(values)}"
        if abs(sum(values) - math.pi) > TOLERANCE:
            return f"partial sums add up to {sum(values)}, not pi"
    elif not any(abs(v - math.pi) <= TOLERANCE for v in values):
        return f"no rank printed pi (got {values})"
    return None


def run(cmd, cwd, timeout):
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, check=False)
    return result.returncode, result.stdout + result.stderr


def exercises(languages):
    """Yield (directory, make target, program name) for every exercise."""
    if "c" in languages or "cxx" in languages:
        for src in sorted((ROOT / "C").rglob("*.c")):
            name = str(src.relative_to(ROOT / "C").with_suffix(""))
            if "c" in languages:
                yield ROOT / "C", name, src.stem
            if "cxx" in languages:
                yield ROOT / "C", f"{name}-cxx", src.stem
    if "fortran" in languages:
        for src in sorted((ROOT / "Fortran").rglob("*.f90")):
            name = str(src.relative_to(ROOT / "Fortran").with_suffix(""))
            yield ROOT / "Fortran", name, src.stem


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--lang",
        nargs="+",
        choices=["c", "cxx", "fortran"],
        default=["c", "cxx", "fortran"],
        help="languages to build and run (default: all)",
    )
    parser.add_argument("-n", "--nproc", type=int, default=4, help="MPI processes (default: 4)")
    parser.add_argument("--mpirun", default="mpirun", help='MPI launcher, e.g. "mpirun --oversubscribe"')
    parser.add_argument("--timeout", type=float, default=300, help="seconds allowed per build or run")
    args = parser.parse_args()

    failures = []
    for directory, target, name in exercises(args.lang):
        label = f"{directory.name}/{target}"
        # A successful silent build prints nothing, so any output is a warning
        code, output = run(["make", "-s", target], directory, args.timeout)
        if code != 0 or output.strip():
            failures.append(label)
            print(f"FAIL  {label}: build\n{output}")
            continue

        launcher = [*shlex.split(args.mpirun), "-np", str(args.nproc), "./pi"]
        code, output = run(launcher, directory, args.timeout)
        problem = f"exit code {code}" if code != 0 else check_output(name, output, args.nproc)
        if problem:
            failures.append(label)
            print(f"FAIL  {label}: {problem}\n{output}")
        else:
            print(f"ok    {label}")

    for directory in ("C", "Fortran"):
        run(["make", "-s", "clean"], ROOT / directory, args.timeout)

    print(f"\n{len(failures)} failure(s)" + (": " + ", ".join(failures) if failures else ""))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
