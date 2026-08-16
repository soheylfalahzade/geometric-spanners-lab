import os
import sys
import numpy as np
import osmnx as ox
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

# وارد کردن الگوریتم شما
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from greedy_spanner import build_greedy_t_spanner

def run_independent_validation():
    print("=" * 60)
    print("INDEPENDENT STRETCH FACTOR VERIFICATION (Delft, Netherlands)")
    print("=" * 60)

    # 1. بارگذاری نقشه دلفت (شعاع 1500 متر)
    print("[1/3] Downloading Delft network (1500m)...")
    G = ox.graph_from_address("Delft, Netherlands", dist=1500, network_type='drive')
    G_proj = ox.project_graph(G)
    nodes = list(G_proj.nodes(data=True))
    points_dict = {i: np.array([data['x'], data['y']]) for i, (node_id, data) in enumerate(nodes)}
    n = len(points_dict)
    coords = np.array([points_dict[i] for i in range(n)])
    
    # 2. ساخت اسپانر با t = 1.4
    print(f"[2/3] Building Greedy Spanner for {n} nodes...")
    H, runtime = build_greedy_t_spanner(points_dict, t=1.4)
    
    # 3. محاسبه ماتریس کشیدگی واقعی برای تمام جفت‌ها
    print("[3/3] Computing All-Pairs Shortest Paths and Stretch Distribution...")
    dist_mat = distance_matrix(coords, coords)
    
    # ماتریس مجاورت اسپانر
    row, col, data = [], [], []
    for u, v, d in H.edges(data=True):
        w = d['weight']
        row.extend([u, v])
        col.extend([v, u])
        data.extend([w, w])
    spanner_adj = csr_matrix((data, (row, col)), shape=(n, n))
    
    apsp = shortest_path(csgraph=spanner_adj, directed=False)
    
    # استخراج فقط مثلث بالایی ماتریس (همه جفت‌های u < v یکتا)
    upper_tri_indices = np.triu_indices(n, k=1)
    spanner_dists = apsp[upper_tri_indices]
    euclidean_dists = dist_mat[upper_tri_indices]
    
    stretch_ratios = spanner_dists / euclidean_dists
    
    # 4. محاسبه آماره‌های دقیق توزیع (بدون هیچ‌گونه گرد کردن فیک)
    min_val = np.min(stretch_ratios)
    mean_val = np.mean(stretch_ratios)
    median_val = np.median(stretch_ratios)
    p90_val = np.percentile(stretch_ratios, 90)
    p95_val = np.percentile(stretch_ratios, 95)
    p99_val = np.percentile(stretch_ratios, 99)
    raw_max_val = np.max(stretch_ratios)
    
    print("\n" + "=" * 60)
    print("STRETCH FACTOR DISTRIBUTION REPORT:")
    print("=" * 60)
    print(f"Total Unique Pairs Evaluated:  {len(stretch_ratios):,}")
    print(f"Minimum Stretch:               {min_val:.8f}")
    print(f"Mean Stretch:                  {mean_val:.8f}")
    print(f"Median (50th percentile):      {median_val:.8f}")
    print(f"90th Percentile:               {p90_val:.8f}")
    print(f"95th Percentile:               {p95_val:.8f}")
    print(f"99th Percentile:               {p99_val:.8f}")
    print(f"EXACT RAW MAXIMUM STRETCH:     {raw_max_val:.8f}")
    print(f"Theoretical Target (t):        1.40000000")
    print(f"Violates t=1.4?                {'YES (Violation!)' if raw_max_val > 1.4 + 1e-7 else 'NO (Strictly holds)'}")
    print("=" * 60)
    
    # 5. رسم هیستوگرام توزیع
    plt.figure(figsize=(10, 5), dpi=300)
    plt.hist(stretch_ratios, bins=100, color='#1e40af', edgecolor='black', alpha=0.7)
    plt.axvline(1.4, color='red', linestyle='--', linewidth=1.5, label='Theoretical Bound (t=1.4)')
    plt.axvline(raw_max_val, color='orange', linestyle=':', linewidth=1.5, label=f'Max Measured ({raw_max_val:.5f})')
    plt.axvline(mean_val, color='green', linestyle='-', linewidth=1.5, label=f'Mean ({mean_val:.3f})')
    plt.title("Empirical Distribution of Stretch Factors Across All Node Pairs (Delft)", fontsize=13)
    plt.xlabel("Stretch Factor (Spanner Distance / Euclidean Distance)")
    plt.ylabel("Pair Frequency")
    plt.legend()
    plt.tight_layout()
    plt.savefig("stretch_distribution_delft.png")
    print("\n[SUCCESS] Histogram saved to stretch_distribution_delft.png")

if __name__ == '__main__':
    run_independent_validation()

