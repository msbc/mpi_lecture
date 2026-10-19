"""Draw the blocking and non-blocking send/receive diagrams (figures/blocking.png, figures/nonblocking.png).

Run from the repository root:

    uv run --active --group figures figures/src/communication.py

The diagram is laid out in data coordinates: x runs 0-100 and y runs 0-90, top to bottom.
"""

import argparse
import os

import matplotlib.pyplot as plt
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch

HERE = os.path.dirname(os.path.abspath(__file__))
FIG = os.path.join(HERE, "..")

FIGSIZE = (7.6, 6.85)  # inches; matches the 0-100 x 0-90 data box
DPI = 300
FONT = "Graphik"
MONO = "Menlo"
FS = 16  # base font size

TEXT = "#41464D"
MUTED = "#7D858F"
RANK = ["#1F63B5", "#E07B39"]  # rank 0 (sender), rank 1 (receiver)
TINT = ["#EEF3FA", "#FCF2EB"]
SYSBUF = "#8A929C"
PANEL_EDGE = "#C9CED5"

XMID = 50  # divider between your code and the MPI library
XCALL = 26  # center of the "your code" column
XBRK = 56  # the bracket showing time spent inside MPI
XSTEP = 59  # left edge of the step text
XBUF = (26, 76)  # centers of the user and system buffer chips


def box(ax, x0, y0, w, h, fc, ec="none", lw=0, pad=0.0, r=1.6, **kw):
    ax.add_patch(
        FancyBboxPatch((x0, y0), w, h, boxstyle=f"round,pad={pad},rounding_size={r}", fc=fc, ec=ec, lw=lw, **kw)
    )


def arrow(ax, p, q, color=TEXT, lw=1.8, rad=0.0, style="-|>", ms=14, **kw):
    ax.add_patch(
        FancyArrowPatch(
            p,
            q,
            arrowstyle=style,
            mutation_scale=ms,
            color=color,
            lw=lw,
            connectionstyle=f"arc3,rad={rad}",
            shrinkA=0,
            shrinkB=0,
            **kw,
        )
    )


def chip(ax, x, y, label, color, w=19, h=5, mono=True):
    """A filled buffer chip centered at (x, y)."""
    box(ax, x - w / 2, y - h / 2, w, h, fc=color, r=1.2)
    ax.text(x, y, label, ha="center", va="center", color="white", fontsize=FS, family=MONO if mono else FONT)


def call(ax, y, name, color):
    """An MPI call in the user's code: monospace label with an arrow into the library."""
    ax.text(XCALL, y, name, ha="center", va="center", fontsize=FS + 1, family=MONO, color=color, weight="bold")
    arrow(ax, (XCALL + 15, y), (XBRK, y), color=TEXT)


def ret(ax, y, label="returns"):
    arrow(ax, (XBRK, y), (XCALL + 12, y), color=TEXT)
    ax.text(XCALL + 10, y, label, ha="right", va="center", fontsize=FS, color=TEXT)


def steps(ax, y_top, y_bot, lines, color):
    """The time spent inside MPI: a bracket with numbered steps beside it."""
    ax.plot([XBRK, XBRK], [y_top, y_bot], color=color, lw=4, solid_capstyle="round")
    n = len(lines)
    for i, s in enumerate(lines):
        y = y_top - (i + 0.5) * (y_top - y_bot) / n
        ax.text(
            XSTEP,
            y,
            f"{i + 1}",
            ha="center",
            va="center",
            fontsize=FS - 2,
            color="white",
            weight="bold",
            bbox={"boxstyle": "circle,pad=0.25", "fc": color, "ec": "none"},
        )
        ax.text(XSTEP + 3, y, s, ha="left", va="center", fontsize=FS, color=TEXT, linespacing=1.25)


def panel(ax, y0, y1, rank, y_label):
    box(ax, 1, y0, 98, y1 - y0, fc=TINT[rank], ec=PANEL_EDGE, lw=1.2, r=2.5)
    ax.plot([XMID, XMID], [y0 + 1.5, y1 - 1.5], color=PANEL_EDGE, lw=1.2, ls=(0, (4, 3)))
    label = ["rank 0  (sender)", "rank 1  (receiver)"][rank]
    ax.text(4, y_label, label, ha="left", va="center", fontsize=FS, color=RANK[rank], weight="bold")


def draw(nonblocking):
    plt.rcParams.update({"font.family": FONT, "text.color": TEXT})
    fig = plt.figure(figsize=FIGSIZE)
    ax = fig.add_axes((0, 0, 1, 1))
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 90)
    ax.set_axis_off()

    ax.text(XCALL, 87.5, "your code", ha="center", va="center", fontsize=FS + 2, color=MUTED)
    ax.text(75, 87.5, "MPI library", ha="center", va="center", fontsize=FS + 2, color=MUTED)

    send, recv = ("MPI_Isend", "MPI_Irecv") if nonblocking else ("MPI_Send", "MPI_Recv")

    # ---- rank 0: sender (buffers sit at the bottom, next to the network)
    panel(ax, 46, 85, 0, y_label=81.8)
    call(ax, 77, send, RANK[0])
    steps(ax, 77, 60, ["copy sendbuf\nto sysbuf", "send to rank 1"], RANK[0])
    chip(ax, XBUF[0], 51, "sendbuf", RANK[0])
    chip(ax, XBUF[1], 51, "sysbuf", SYSBUF)
    arrow(ax, (XBUF[0] + 10, 51), (XBUF[1] - 10, 51), color=RANK[0], lw=2.2)

    # ---- rank 1: receiver (buffers at the top)
    panel(ax, 1, 40, 1, y_label=4.2)  # label at the bottom, clear of the buffers
    chip(ax, XBUF[0], 34, "recvbuf", RANK[1])
    chip(ax, XBUF[1], 34, "sysbuf", SYSBUF)
    arrow(ax, (XBUF[1] - 10, 34), (XBUF[0] + 10, 34), color=RANK[1], lw=2.2)
    call(ax, 25, recv, RANK[1])
    steps(ax, 25, 8, ["receive into\nsysbuf", "copy sysbuf\nto recvbuf"], RANK[1])

    # ---- the network between the two system buffers
    arrow(ax, (XBUF[1], 48.5), (XBUF[1], 36.5), color=SYSBUF, lw=2.6, ms=18)
    ax.text(XBUF[1] + 3, 43, "network", ha="left", va="center", fontsize=FS, color=MUTED, style="italic")

    if nonblocking:
        # the call returns at once and the steps run in the background; MPI_Wait returns when they are done
        for y_call, y_end in ((77, 60), (25, 8)):
            ret(ax, y_call - 4, "returns at once")
            ax.text(
                XCALL,
                (y_call + y_end) / 2 - 0.5,
                "keeps computing…",
                ha="center",
                va="center",
                fontsize=FS - 1,
                color=MUTED,
                style="italic",
            )
            call(ax, y_end + 4, "MPI_Wait", TEXT)
            ret(ax, y_end, "returns when done")
    else:
        ret(ax, 60)
        ret(ax, 8)
    return fig


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--outdir", default=FIG, help="where to save the PNGs (default: figures/)")
    ap.add_argument("--show", action="store_true", help="open interactive windows instead of saving")
    args = ap.parse_args()

    for name, nonblocking in (("blocking", False), ("nonblocking", True)):
        fig = draw(nonblocking)
        if not args.show:
            path = os.path.join(args.outdir, f"{name}.png")
            fig.savefig(path, dpi=DPI, transparent=True)
            print(f"wrote {os.path.abspath(path)}")
    if args.show:
        plt.show()


if __name__ == "__main__":
    main()
