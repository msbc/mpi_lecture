"""Plot the midpoint-rule Riemann sum for 4 / (1 + x^2) on [0, 1] (figures/riemann-sum.png).

Run from the repository root:

    uv run --active --group figures figures/src/riemann_sum.py

Everything worth hand-tuning is in the constants below.
"""

import argparse
import os

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.ticker import AutoMinorLocator, FuncFormatter, MultipleLocator

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "riemann-sum.png")

# --- figure
FIGSIZE = (5.0, 4.5)  # inches; the slide box is about 600 x 540
DPI = 300
FONT = "Graphik"  # the deck's body font
FONTSIZE = 19

# --- data
NSLICES = 8
XLIM = (0.0, 1.0)
YLIM = (0.0, 4.4)

# --- colors (deck palette)
TEXT = "#41464D"
ACCENT = "#1F63B5"
BAR_FILL = "#1F63B5"
BAR_ALPHA = 0.18
BAR_EDGE = "#1F63B5"
CURVE = "#41464D"
MIDPOINT = "#000000"  # "#E07B39"

# --- ticks
X_MAJOR, Y_MAJOR = 0.25, 1.0
N_MINOR = 5  # minor intervals per major interval
MAJOR_LEN, MINOR_LEN = 7, 3.5
TICK_WIDTH = 1.0
FRAME_WIDTH = 1.2


def f(x):
    return 4.0 / (1.0 + x**2)


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--output", default=OUT, help="where to save the PNG (default: figures/riemann-sum.png)")
    ap.add_argument("--show", action="store_true", help="open an interactive window instead of saving")
    args = ap.parse_args()

    plt.rcParams.update(
        {
            "font.family": FONT,
            "font.size": FONTSIZE,
            "text.color": TEXT,
            "axes.labelcolor": TEXT,
            "axes.edgecolor": TEXT,
            "xtick.color": TEXT,
            "ytick.color": TEXT,
            "mathtext.fontset": "custom",
            "mathtext.rm": FONT,
            "mathtext.it": f"{FONT}:italic",
            "mathtext.bf": f"{FONT}:bold",
            "mathtext.cal": FONT,
        }
    )

    fig, ax = plt.subplots(figsize=FIGSIZE, layout="constrained")

    # compute error for the midpoint rule (for display only)
    dx = (XLIM[1] - XLIM[0]) / NSLICES
    xm = XLIM[0] + (np.arange(NSLICES) + 0.5) * dx
    midpoint_sum = np.sum(f(xm)) * dx
    err = np.abs(midpoint_sum - np.pi)
    e_exp = int(np.floor(np.log10(err)))
    e_mant = err / 10**e_exp

    # midpoint rectangles
    dx = (XLIM[1] - XLIM[0]) / NSLICES
    xm = XLIM[0] + (np.arange(NSLICES) + 0.5) * dx
    ax.bar(xm, f(xm), width=dx, color=BAR_FILL, alpha=BAR_ALPHA, zorder=1)
    ax.bar(xm, f(xm), width=dx, fill=False, edgecolor=BAR_EDGE, linewidth=1.2, zorder=2)
    ax.plot(xm, f(xm), "x", color=MIDPOINT, markersize=8, zorder=4, markeredgewidth=1.5)

    # the integrand
    x = np.linspace(XLIM[0], XLIM[1], 400)
    ax.plot(x, f(x), color=CURVE, linewidth=2.5, zorder=3)
    lbl = r"$\varepsilon_n = " + f"{e_mant:.1f}" + r" \times 10^{" + f"{e_exp}" + r"}$"
    lbl += "\n" + r"$f(x) = \frac{4}{1 + x^2}$" + f"\n$n = {NSLICES}$"
    ax.text(0.95, 0.98, lbl, transform=ax.transAxes, ha="right", va="top", fontsize=FONTSIZE + 3)

    ax.set_xlim(XLIM)
    ax.set_ylim(YLIM)
    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$f(x)$")

    # full frame, inward major and minor ticks on all four sides
    for side in ax.spines.values():
        side.set_linewidth(FRAME_WIDTH)
    ax.xaxis.set_major_locator(MultipleLocator(X_MAJOR))
    ax.yaxis.set_major_locator(MultipleLocator(Y_MAJOR))
    ax.xaxis.set_minor_locator(AutoMinorLocator(N_MINOR))
    ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:g}"))
    ax.yaxis.set_major_formatter(FuncFormatter(lambda v, _: "" if v == 0 else f"{v:g}"))  # 0 is on the x axis
    ax.yaxis.set_minor_locator(AutoMinorLocator(N_MINOR))
    ax.tick_params(which="both", direction="in", top=True, right=True, width=TICK_WIDTH)
    ax.tick_params(which="major", length=MAJOR_LEN)
    ax.tick_params(which="minor", length=MINOR_LEN)

    if args.show:
        plt.show()
    else:
        fig.savefig(args.output, dpi=DPI, transparent=True)
        print(f"wrote {os.path.abspath(args.output)}")


if __name__ == "__main__":
    main()
