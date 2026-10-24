"""Animated GIF of the greedy t-spanner construction (n = 45, t = 1.4, seed 42).

Candidate edges are examined in ascending length. A candidate is added when the
current shortest path between its endpoints exceeds t times its length; otherwise
it is skipped. The trace below mirrors greedy_spanner.build_greedy_t_spanner and
asserts at the end that it reproduces exactly the same edge set.

Run from the repository root:  python make_animation.py
"""
import contextlib
import io

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np
from matplotlib.animation import FuncAnimation, PillowWriter

from greedy_spanner import build_greedy_t_spanner, compute_euclidean_distance, generate_euclidean_points

N, T, SEED = 45, 1.4, 42
STEP = 9            # candidates examined per frame
HOLD = 14           # extra frames at the end
BLUE, RED, GREY, ORANGE = "#1e40af", "#dc2626", "#9ca3af", "#f59e0b"


def trace(points, t):
    n = len(points)
    cand = sorted((compute_euclidean_distance(points[i], points[j]), i, j)
                  for i in range(n) for j in range(i + 1, n))
    H = nx.Graph()
    H.add_nodes_from(range(n))
    steps = []
    for w, u, v in cand:
        keep = True
        if nx.has_path(H, u, v) and nx.shortest_path_length(H, u, v, weight="weight") <= t * w:
            keep = False
        if keep:
            H.add_edge(u, v, weight=w)
        steps.append((u, v, keep))
    return H, steps


def main():
    pts = generate_euclidean_points(N, SEED)
    H, steps = trace(pts, T)
    with contextlib.redirect_stdout(io.StringIO()):
        ref, _ = build_greedy_t_spanner(pts, T)
    assert {tuple(sorted(e)) for e in H.edges()} == {tuple(sorted(e)) for e in ref.edges()}, "trace differs from pipeline"
    total = len(steps)
    P = np.array([pts[i] for i in range(N)])

    kept_after = np.cumsum([k for _, _, k in steps])
    frames = list(range(STEP, total + 1, STEP))
    if frames[-1] != total:
        frames.append(total)
    frames += [total] * HOLD

    fig = plt.figure(figsize=(10, 5), dpi=80)
    ax = fig.add_axes([0.02, 0.04, 0.46, 0.84])
    ax2 = fig.add_axes([0.58, 0.16, 0.38, 0.66])

    def draw(k):
        ax.clear()
        ax2.clear()
        ax.set_xlim(-4, 104)
        ax.set_ylim(-4, 104)
        ax.axis("off")
        ax.set_aspect("equal")
        for u, v, keep in steps[:k]:
            if keep:
                ax.plot(P[[u, v], 0], P[[u, v], 1], color=BLUE, lw=1.6, alpha=0.9, zorder=2)
        if k < total:
            u, v, keep = steps[k - 1]
            ax.plot(P[[u, v], 0], P[[u, v], 1], color=ORANGE if keep else RED, lw=2.4, alpha=0.95, zorder=3)
        ax.scatter(P[:, 0], P[:, 1], s=34, color="#111827", zorder=4)
        kept = int(kept_after[k - 1])
        ax.set_title(f"examined {k} / {total} candidate edges   |   kept {kept}", fontsize=12, loc="left")
        xs = np.arange(1, total + 1)
        ax2.plot(xs, kept_after, color=GREY, lw=1, alpha=0.5)
        ax2.plot(xs[:k], kept_after[:k], color=BLUE, lw=2.4)
        ax2.axhline(H.number_of_edges(), color=RED, lw=1, ls="--")
        ax2.text(total * 0.40, H.number_of_edges() + 5, f"final: {H.number_of_edges()} edges\n"
                 f"{100 * (1 - H.number_of_edges() / total):.2f}% of $K_{{{N}}}$ pruned", color=RED, fontsize=10)
        ax2.set_xlim(0, total)
        ax2.set_ylim(0, 95)
        ax2.set_xlabel("candidate edges examined (ascending length)")
        ax2.set_ylabel("edges kept in the spanner")
        ax2.spines[["top", "right"]].set_visible(False)
        ax2.grid(alpha=0.25)
        ax2.set_title(f"Greedy t-spanner, t = {T}", fontsize=12, loc="left")

    anim = FuncAnimation(fig, lambda i: draw(frames[i]), frames=len(frames), interval=90)
    anim.save("figures/greedy_construction.gif", writer=PillowWriter(fps=11))
    print("saved figures/greedy_construction.gif;", len(frames), "frames; final edges", H.number_of_edges())


if __name__ == "__main__":
    main()
