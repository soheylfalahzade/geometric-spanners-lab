"""
Geometric Spanners Lab: Greedy t-Spanner Construction & Visualization
Author: Soheil Fallahzadeh (M.Sc. in Algorithms & Theory of Computation)
"""

import numpy as np
import networkx as nx
import matplotlib.pyplot as plt
import time

def generate_euclidean_points(n_points: int = 45, seed: int = 42) -> dict:
    """Generates synthetic 2D Euclidean point coordinates in a bounded metric space."""
    np.random.seed(seed)
    coords = np.random.rand(n_points, 2) * 100.0
    return {i: coords[i] for i in range(n_points)}

def compute_euclidean_distance(p1: np.ndarray, p2: np.ndarray) -> float:
    return float(np.linalg.norm(p1 - p2))

def build_greedy_t_spanner(points: dict, t: float = 1.4) -> tuple[nx.Graph, float]:
    """
    Constructs a classical Greedy t-Spanner for a given metric point set.
    Invariant: For all u, v in V, shortest_path_dist_H(u, v) <= t * dist_G(u, v)
    """
    n = len(points)
    all_edges = []
    
    # 1. Compute and sort all pairwise candidate edges by weight ascending: O(n^2 log n)
    for i in range(n):
        for j in range(i + 1, n):
            weight = compute_euclidean_distance(points[i], points[j])
            all_edges.append((weight, i, j))
    all_edges.sort()

    # 2. Iteratively construct the spanner subgraph
    H = nx.Graph()
    for i in range(n):
        H.add_node(i, pos=points[i])

    print(f"\n[INFO] Initializing Greedy t-Spanner Construction (t = {t}, |V| = {n})...")
    start_time = time.time()

    for weight, u, v in all_edges:
        if nx.has_path(H, u, v):
            shortest_dist = nx.shortest_path_length(H, source=u, target=v, weight='weight')
            if shortest_dist <= t * weight:
                continue
        H.add_edge(u, v, weight=weight)

    elapsed_time = time.time() - start_time
    return H, elapsed_time

def evaluate_and_export_figure(points: dict, H: nx.Graph, t: float = 1.4, output_file: str = "spanner_comparison.png"):
    """Evaluates spanner sparsity metrics and exports a publication-grade comparison figure."""
    n = len(points)
    total_complete_edges = n * (n - 1) // 2
    spanner_edges = H.number_of_edges()
    sparsity_ratio = (1.0 - (spanner_edges / total_complete_edges)) * 100.0

    print("=" * 60)
    print(f"Total Complete Graph Edges (K_{n}): {total_complete_edges}")
    print(f"Retained Spanner Edges (|E_H|):     {spanner_edges}")
    print(f"Edge Pruning / Sparsity Ratio:       {sparsity_ratio:.2f}%")
    print(f"Theoretical Stretch Factor Bound:    t = {t}")
    print("=" * 60)

    # Visualization styling
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=300)
    pos = {i: points[i] for i in points}

    # Left: Complete Dense Graph (K_n)
    G_complete = nx.complete_graph(n)
    nx.draw_networkx_nodes(G_complete, pos, ax=axes[0], node_size=40, node_color='#1f2937')
    nx.draw_networkx_edges(G_complete, pos, ax=axes[0], alpha=0.06, edge_color='#6b7280')
    axes[0].set_title(f"Complete Metric Graph $K_{{{n}}}$\n({total_complete_edges} Edges — Dense $O(n^2)$)", fontsize=13, pad=12)
    axes[0].axis('off')

    # Right: Greedy t-Spanner Backbone
    nx.draw_networkx_nodes(H, pos, ax=axes[1], node_size=55, node_color='#dc2626')
    nx.draw_networkx_edges(H, pos, ax=axes[1], edge_color='#1e40af', width=1.4, alpha=0.85)
    axes[1].set_title(f"Greedy $t$-Spanner Backbone ($t = {t}$)\n({spanner_edges} Edges — {sparsity_ratio:.1f}% Pruned)", fontsize=13, fontweight='bold', pad=12)
    axes[1].axis('off')

    plt.tight_layout()
    plt.savefig(output_file, bbox_inches='tight')
    print(f"[SUCCESS] High-resolution visualization exported: {output_file}\n")

if __name__ == "__main__":
    point_set = generate_euclidean_points(n_points=45, seed=42)
    spanner_h, runtime = build_greedy_t_spanner(point_set, t=1.4)
    evaluate_and_export_figure(point_set, spanner_h, t=1.4)
