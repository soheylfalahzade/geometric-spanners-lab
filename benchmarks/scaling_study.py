"""Scaling and stretch-trade-off study for the greedy t-spanner.

Replaces single-instance claims with distributions over random instances:
  * edge count, edges per vertex, pruned fraction and runtime versus n (t = 1.4)
  * edge count and exhaustively measured stretch versus t (n = 100)
Stretch is measured with scipy all-pairs shortest paths, independently of the
construction code. Raw rows go to results/*.csv, figures to figures/*.png.

Run from the repository root:  python benchmarks/scaling_study.py
"""
import contextlib
import csv
import io
import json
import os
import sys
import time

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from greedy_spanner import build_greedy_t_spanner, generate_euclidean_points  # noqa: E402

BLUE, RED, GREY = "#1e40af", "#dc2626", "#6b7280"
SIZES = {25: 30, 50: 30, 100: 30, 150: 20, 200: 20, 300: 8}     # n -> number of random instances
T_VALUES = [1.1, 1.2, 1.4, 1.6, 2.0, 3.0]
N_TRADEOFF, SEEDS_TRADEOFF = 100, 20


def build(points, t):
    with contextlib.redirect_stdout(io.StringIO()):
        t0 = time.perf_counter()
        H, _ = build_greedy_t_spanner(points, t)
        return H, time.perf_counter() - t0


def stretch_stats(points, H):
    n = len(points)
    P = np.array([points[i] for i in range(n)])
    rows, cols, w = [], [], []
    for u, v in H.edges():
        d = float(np.linalg.norm(P[u] - P[v]))
        rows += [u, v]
        cols += [v, u]
        w += [d, d]
    apsp = shortest_path(csr_matrix((w, (rows, cols)), shape=(n, n)), directed=False)
    iu = np.triu_indices(n, 1)
    euclid = np.sqrt(((P[:, None] - P[None]) ** 2).sum(-1))[iu]
    s = apsp[iu] / euclid
    return float(s.max()), float(s.mean()), bool(np.isfinite(s).all())


def boot_ci(x, rng, n_boot=2000):
    x = np.asarray(x, float)
    means = rng.choice(x, (n_boot, len(x))).mean(axis=1)
    return float(np.percentile(means, 2.5)), float(np.percentile(means, 97.5))


def write_csv(path, rows):
    with open(path, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def style(axes):
    for a in axes:
        a.spines[["top", "right"]].set_visible(False)
        a.grid(alpha=0.25)


def main():
    os.makedirs("results", exist_ok=True)
    os.makedirs("figures", exist_ok=True)
    rng = np.random.default_rng(0)

    cache_path = "results/_cache.json"
    cache = json.load(open(cache_path)) if os.path.exists(cache_path) else {}

    def save_cache():
        with open(cache_path, "w") as fh:
            json.dump(cache, fh)

    rows = []
    for n, k in SIZES.items():
        if f"n{n}" in cache:
            rows += cache[f"n{n}"]
            continue
        part = []
        for seed in range(1, k + 1):
            pts = generate_euclidean_points(n, seed)
            H, sec = build(pts, 1.4)
            ms, mean_s, conn = stretch_stats(pts, H)
            total = n * (n - 1) // 2
            part.append(dict(n=n, seed=seed, t=1.4, edges=H.number_of_edges(),
                             edges_per_vertex=H.number_of_edges() / n,
                             pruned_pct=100 * (1 - H.number_of_edges() / total), seconds=sec,
                             max_stretch=ms, mean_stretch=mean_s, connected=conn))
        rows += part
        cache[f"n{n}"] = part
        save_cache()
        print(f"n={n}: done", flush=True)
    write_csv("results/scaling_study.csv", rows)

    trade = []
    for t in T_VALUES:
        if f"t{t}" in cache:
            trade += cache[f"t{t}"]
            continue
        part = []
        for seed in range(1, SEEDS_TRADEOFF + 1):
            pts = generate_euclidean_points(N_TRADEOFF, seed)
            H, sec = build(pts, t)
            ms, mean_s, conn = stretch_stats(pts, H)
            part.append(dict(n=N_TRADEOFF, seed=seed, t=t, edges=H.number_of_edges(),
                             max_stretch=ms, mean_stretch=mean_s, connected=conn))
        trade += part
        cache[f"t{t}"] = part
        save_cache()
        print(f"t={t}: done", flush=True)
    write_csv("results/t_tradeoff.csv", trade)

    assert all(r["connected"] for r in rows + trade), "a spanner was disconnected"
    assert all(r["max_stretch"] <= r["t"] + 1e-9 for r in rows + trade), "stretch invariant violated"

    ns = sorted(SIZES)

    def agg(key):
        m, lo, hi = [], [], []
        for n in ns:
            v = [r[key] for r in rows if r["n"] == n]
            m.append(np.mean(v))
            a, b = boot_ci(v, rng)
            lo.append(a)
            hi.append(b)
        return np.array(m), np.array(lo), np.array(hi)

    fig, ax = plt.subplots(1, 3, figsize=(15, 4.4), dpi=200)
    style(ax)
    m, lo, hi = agg("edges_per_vertex")
    ax[0].plot(ns, m, "o-", color=BLUE, lw=2)
    ax[0].fill_between(ns, lo, hi, color=BLUE, alpha=0.2)
    ax[0].set_ylim(0, max(2.4, hi.max() * 1.15))
    ax[0].set_xlabel("number of points n")
    ax[0].set_ylabel("spanner edges per vertex")
    ax[0].set_title(f"Edges per vertex: {m[0]:.2f} at n = {ns[0]}, {m[-1]:.2f} at n = {ns[-1]}", fontsize=11)
    m, lo, hi = agg("pruned_pct")
    ax[1].plot(ns, m, "o-", color=RED, lw=2)
    ax[1].fill_between(ns, lo, hi, color=RED, alpha=0.2)
    ax[1].set_xlabel("number of points n")
    ax[1].set_ylabel("edges pruned from $K_n$ (%)")
    ax[1].set_title("Pruned fraction versus the complete graph", fontsize=11)
    m, lo, hi = agg("seconds")
    ax[2].loglog(ns, m, "o-", color=GREY, lw=2)
    ax[2].fill_between(ns, lo, hi, color=GREY, alpha=0.25)
    slope = np.polyfit(np.log(ns), np.log(m), 1)[0]
    ax[2].set_xlabel("number of points n")
    ax[2].set_ylabel("construction time (s)")
    ax[2].set_title(f"Runtime (log-log), fitted exponent {slope:.2f}", fontsize=11)
    fig.suptitle("Greedy t-spanner, t = 1.4: mean over random instances with bootstrap 95% CI",
                 fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig("figures/scaling_study.png", bbox_inches="tight")
    plt.close(fig)

    fig, ax = plt.subplots(1, 2, figsize=(11, 4.4), dpi=200)
    style(ax)
    em, elo, ehi, sm, smax = [], [], [], [], []
    for t in T_VALUES:
        v = [r["edges"] for r in trade if r["t"] == t]
        em.append(np.mean(v))
        a, b = boot_ci(v, rng)
        elo.append(a)
        ehi.append(b)
        s = [r["max_stretch"] for r in trade if r["t"] == t]
        sm.append(np.mean(s))
        smax.append(np.max(s))
    ax[0].plot(T_VALUES, em, "o-", color=BLUE, lw=2)
    ax[0].fill_between(T_VALUES, elo, ehi, color=BLUE, alpha=0.2)
    ax[0].set_xlabel("target stretch t")
    ax[0].set_ylabel("spanner edges (n = 100)")
    ax[0].set_title("Sparsity bought by a looser bound", fontsize=11)
    ax[1].plot(T_VALUES, T_VALUES, "--", color=GREY, label="bound  y = t")
    ax[1].plot(T_VALUES, smax, "s-", color=RED, label="largest observed stretch (20 instances)")
    ax[1].plot(T_VALUES, sm, "o-", color=BLUE, label="mean of per-instance maxima")
    ax[1].set_xlabel("target stretch t")
    ax[1].set_ylabel("exhaustively measured stretch")
    ax[1].legend(frameon=False, fontsize=9)
    ax[1].set_title("The bound holds on every instance", fontsize=11)
    fig.tight_layout()
    fig.savefig("figures/t_tradeoff.png", bbox_inches="tight")
    plt.close(fig)
    print(f"runtime exponent {slope:.2f}; all {len(rows) + len(trade)} instances connected and within bound")


if __name__ == "__main__":
    main()
