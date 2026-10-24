"""Tests for the greedy t-spanner construction. All run in a few seconds."""
import contextlib
import io
import os
import sys

import networkx as nx
import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from greedy_spanner import build_greedy_t_spanner, compute_euclidean_distance, generate_euclidean_points


def build(points, t):
    with contextlib.redirect_stdout(io.StringIO()):
        return build_greedy_t_spanner(points, t)[0]


def exhaustive_max_stretch(points, H):
    n = len(points)
    dist = dict(nx.all_pairs_dijkstra_path_length(H, weight="weight"))
    worst = 0.0
    for i in range(n):
        for j in range(i + 1, n):
            if j not in dist[i]:
                return float("inf")
            worst = max(worst, dist[i][j] / compute_euclidean_distance(points[i], points[j]))
    return worst


def test_points_are_reproducible_and_in_range():
    a, b = generate_euclidean_points(30, 5), generate_euclidean_points(30, 5)
    assert all(np.array_equal(a[i], b[i]) for i in a)
    assert all(0.0 <= c <= 100.0 for p in a.values() for c in p)


@pytest.mark.parametrize("seed", [1, 2, 3, 4, 5])
@pytest.mark.parametrize("t", [1.2, 1.4, 2.0])
def test_stretch_invariant_holds_exhaustively(seed, t):
    pts = generate_euclidean_points(35, seed)
    H = build(pts, t)
    assert nx.is_connected(H)
    assert exhaustive_max_stretch(pts, H) <= t + 1e-9


def test_published_baseline_numbers():
    pts = generate_euclidean_points(45, 42)
    H = build(pts, 1.4)
    assert H.number_of_edges() == 77
    assert 45 * 44 // 2 == 990
    assert round(100 * (1 - 77 / 990), 2) == 92.22


def test_edges_are_a_subset_of_the_complete_graph_with_euclidean_weights():
    pts = generate_euclidean_points(25, 9)
    H = build(pts, 1.5)
    for u, v, d in H.edges(data=True):
        assert u != v
        assert d["weight"] == pytest.approx(compute_euclidean_distance(pts[u], pts[v]))


def test_larger_t_never_needs_more_edges_than_a_much_tighter_t():
    pts = generate_euclidean_points(40, 3)
    assert build(pts, 3.0).number_of_edges() <= build(pts, 1.1).number_of_edges()


def test_construction_is_deterministic():
    pts = generate_euclidean_points(30, 11)
    e1 = sorted(tuple(sorted(e)) for e in build(pts, 1.4).edges())
    e2 = sorted(tuple(sorted(e)) for e in build(pts, 1.4).edges())
    assert e1 == e2
