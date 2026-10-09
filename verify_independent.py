#!/usr/bin/env python3
"""Independent verifier for geometric-spanners-lab.

Deliberately NOT part of the pipeline. It re-derives every headline number
from scratch with its own code path (heapq Dijkstra + scipy all-pairs), and
only then compares against (a) the numbers claimed in the README and (b) the
pipeline's own output (greedy_spanner.build_greedy_t_spanner).

It needs no network access and no OSMnx. Exit code 0 = all checks passed.

Checks
  0. Self-test with analytically known controls (positive and negative).
  1. Independent greedy construction on the n=45, seed=42, t=1.4 point set.
  2. Exhaustive stretch over all pairs: max stretch <= t, graph connected.
  3. Edge counts and pruning percentage match the README (990 / 77 / 92.22%).
  4. Independent edge set == pipeline edge set.
  5. osm_experiments/results.json is internally consistent:
     num_edges_full == n(n-1)/2, pct_pruned recomputed from edge counts,
     measured_max_stretch <= t (within rounding).

Usage:  python verify_independent.py [--results osm_experiments/results.json]
"""
import argparse
import heapq
import json
import math
import os
import sys

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

T = 1.4
N = 45
SEED = 42
README_TOTAL, README_KEPT, README_PCT = 990, 77, 92.22
EPS = 1e-9

FAILS = []


def check(name, ok, detail=""):
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")
    if not ok:
        FAILS.append(name)


def points(n=N, seed=SEED):
    # Legacy global-state RNG on purpose: reproduces the pipeline's point set.
    np.random.seed(seed)
    return np.random.rand(n, 2) * 100.0


def bounded_dijkstra(adj, src, dst, limit):
    """Shortest src->dst distance in adj, abandoning paths longer than limit."""
    dist = {src: 0.0}
    heap = [(0.0, src)]
    while heap:
        d, u = heapq.heappop(heap)
        if d > dist.get(u, math.inf):
            continue
        if u == dst:
            return d
        for v, w in adj[u]:
            nd = d + w
            if nd <= limit and nd < dist.get(v, math.inf):
                dist[v] = nd
                heapq.heappush(heap, (nd, v))
    return math.inf


def independent_greedy(pts, t):
    n = len(pts)
    cand = []
    for i in range(n):
        for j in range(i + 1, n):
            cand.append((float(np.hypot(*(pts[i] - pts[j]))), i, j))
    cand.sort()
    adj = [[] for _ in range(n)]
    kept = set()
    for w, u, v in cand:
        if bounded_dijkstra(adj, u, v, t * w) > t * w:
            adj[u].append((v, w))
            adj[v].append((u, w))
            kept.add((u, v))
    return kept, len(cand)


def all_pairs_stretch(pts, edges):
    """Max stretch and connectivity from exhaustive all-pairs shortest paths."""
    n = len(pts)
    rows, cols, data = [], [], []
    for u, v in edges:
        w = float(np.hypot(*(pts[u] - pts[v])))
        rows += [u, v]
        cols += [v, u]
        data += [w, w]
    adj = csr_matrix((data, (rows, cols)), shape=(n, n))
    apsp = shortest_path(adj, directed=False)
    iu = np.triu_indices(n, k=1)
    euclid = np.sqrt(((pts[:, None, :] - pts[None, :, :]) ** 2).sum(-1))[iu]
    d_h = apsp[iu]
    if not np.all(np.isfinite(d_h)):
        return math.inf, False
    return float(np.max(d_h / euclid)), True


def self_test():
    sq = np.array([[0, 0], [1, 0], [1, 1], [0, 1]], dtype=float)
    # Negative control: path 0-1-2-3, pair (0,3) has d_H = 3, d_G = 1 -> 3.0 exactly.
    s, conn = all_pairs_stretch(sq, {(0, 1), (1, 2), (2, 3)})
    check("self-test: planted shortcut gap gives stretch exactly 3.0", conn and abs(s - 3.0) < EPS, f"(got {s})")
    # Disconnected control must be reported as infinite, never a finite guess.
    s, conn = all_pairs_stretch(sq, {(0, 1), (2, 3)})
    check("self-test: disconnected graph reported as inf", (not conn) and math.isinf(s))
    # Positive control: complete graph has stretch exactly 1.
    full = {(i, j) for i in range(4) for j in range(i + 1, 4)}
    s, conn = all_pairs_stretch(sq, full)
    check("self-test: complete graph has stretch 1.0", conn and abs(s - 1.0) < EPS, f"(got {s})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--results", default="osm_experiments/results.json")
    args = ap.parse_args()

    self_test()

    pts = points()
    kept, total = independent_greedy(pts, T)
    pct = 100.0 * (1.0 - len(kept) / total)
    print(f"\nIndependent re-derivation: total={total} kept={len(kept)} pruned={pct:.4f}%")

    check("total candidate edges == n(n-1)/2", total == N * (N - 1) // 2, f"({total})")
    check("README total edges", total == README_TOTAL)
    check("README kept edges", len(kept) == README_KEPT, f"(derived {len(kept)})")
    check("README pruning percentage", abs(pct - README_PCT) < 0.005, f"(derived {pct:.4f})")

    s, conn = all_pairs_stretch(pts, kept)
    check("spanner connected", conn)
    check("exhaustive max stretch <= t", s <= T + 1e-7, f"(max {s:.8f}, t={T})")

    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    try:
        from greedy_spanner import build_greedy_t_spanner
        H, _ = build_greedy_t_spanner({i: pts[i] for i in range(N)}, t=T)
        theirs = {tuple(sorted(e)) for e in H.edges()}
        check("independent edge set == pipeline edge set", theirs == kept,
              f"(pipeline {len(theirs)} edges, symmetric difference {len(theirs ^ kept)})")
    except ImportError as exc:
        check("pipeline importable for cross-check", False, f"({exc})")

    if os.path.exists(args.results):
        with open(args.results, encoding="utf-8") as fh:
            rows = json.load(fh)
        for r in rows:
            if r.get("status") != "SUCCESS":
                continue
            n = r["num_nodes"]
            full = n * (n - 1) // 2
            pct_r = 100.0 * (1.0 - r["num_edges_spanner"] / r["num_edges_full"])
            tag = r["city"]
            check(f"{tag}: num_edges_full == n(n-1)/2", r["num_edges_full"] == full)
            check(f"{tag}: pct_pruned recomputed", abs(pct_r - r["pct_pruned"]) < 6e-5,
                  f"(recomputed {pct_r:.4f}, reported {r['pct_pruned']})")
            check(f"{tag}: measured_max_stretch <= t (rounding tol)", r["measured_max_stretch"] <= T + 1e-4)
    else:
        print(f"[SKIP] {args.results} not found")

    print()
    if FAILS:
        print(f"{len(FAILS)} CHECK(S) FAILED: {FAILS}")
        sys.exit(1)
    print("ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
