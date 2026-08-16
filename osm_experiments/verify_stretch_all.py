import os
import sys
import json
import numpy as np
import osmnx as ox
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

# وارد کردن الگوریتم اصلی شما
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from greedy_spanner import build_greedy_t_spanner

CITIES = [
    "Delft, Netherlands",
    "Eindhoven, Netherlands",
    "Leuven, Belgium",
    "Rome, Italy"
]
RADIUS_METERS = 1500
T_VALUE = 1.4

def verify_city(city_name):
    print("\n" + "=" * 65)
    print(f"VERIFYING STRETCH DISTRIBUTION: {city_name}")
    print("=" * 65)
    
    # 1. دانلود نقشه
    print("[1/3] Downloading road network (1500m)...")
    G = ox.graph_from_address(city_name, dist=RADIUS_METERS, network_type='drive')
    G_proj = ox.project_graph(G)
    nodes = list(G_proj.nodes(data=True))
    points_dict = {i: np.array([data['x'], data['y']]) for i, (node_id, data) in enumerate(nodes)}
    n = len(points_dict)
    coords = np.array([points_dict[i] for i in range(n)])
    
    # 2. ساخت اسپانر
    print(f"[2/3] Constructing Greedy Spanner for {n} nodes...")
    H, runtime = build_greedy_t_spanner(points_dict, t=T_VALUE)
    
    # 3. محاسبه ماتریس فاصله‌ها و نسبت کشیدگی
    print("[3/3] Calculating full distribution across all pairs...")
    dist_mat = distance_matrix(coords, coords)
    
    row, col, data = [], [], []
    for u, v, d in H.edges(data=True):
        w = d['weight']
        row.extend([u, v])
        col.extend([v, u])
        data.extend([w, w])
    spanner_adj = csr_matrix((data, (row, col)), shape=(n, n))
    
    apsp = shortest_path(csgraph=spanner_adj, directed=False)
    
    upper_tri = np.triu_indices(n, k=1)
    spanner_dists = apsp[upper_tri]
    euclidean_dists = dist_mat[upper_tri]
    stretch_ratios = spanner_dists / euclidean_dists
    
    # آماره‌ها
    metrics = {
        "city": city_name,
        "num_nodes": n,
        "total_pairs": len(stretch_ratios),
        "min": float(np.min(stretch_ratios)),
        "mean": float(np.mean(stretch_ratios)),
        "median": float(np.median(stretch_ratios)),
        "p90": float(np.percentile(stretch_ratios, 90)),
        "p95": float(np.percentile(stretch_ratios, 95)),
        "p99": float(np.percentile(stretch_ratios, 99)),
        "raw_max": float(np.max(stretch_ratios)),
        "runtime_seconds": round(runtime, 2)
    }
    
    # چاپ نتایج در ترمینال
    print("-" * 65)
    print(f"Total Evaluated Pairs: {metrics['total_pairs']:,}")
    print(f"Min Stretch:           {metrics['min']:.6f}")
    print(f"Mean Stretch:          {metrics['mean']:.6f}")
    print(f"Median:                {metrics['median']:.6f}")
    print(f"90th Percentile:       {metrics['p90']:.6f}")
    print(f"95th Percentile:       {metrics['p95']:.6f}")
    print(f"99th Percentile:       {metrics['p99']:.6f}")
    print(f"RAW MAX STRETCH:       {metrics['raw_max']:.8f}")
    print(f"Violates t={T_VALUE}?        {'YES' if metrics['raw_max'] > T_VALUE + 1e-7 else 'NO'}")
    print("-" * 65)
    
    # رسم هیستوگرام
    safe_name = city_name.split(',')[0].strip().lower().replace(" ", "_")
    plt.figure(figsize=(9, 4.5), dpi=300)
    plt.hist(stretch_ratios, bins=100, color='#1e40af', edgecolor='black', alpha=0.7)
    plt.axvline(T_VALUE, color='red', linestyle='--', linewidth=1.5, label=f'Target (t={T_VALUE})')
    plt.axvline(metrics['raw_max'], color='orange', linestyle=':', linewidth=1.5, label=f"Max ({metrics['raw_max']:.4f})")
    plt.axvline(metrics['mean'], color='green', linestyle='-', linewidth=1.5, label=f"Mean ({metrics['mean']:.3f})")
    plt.title(f"Stretch Factor Distribution — {city_name}", fontsize=12)
    plt.xlabel("Stretch Factor")
    plt.ylabel("Pair Count")
    plt.legend()
    plt.tight_layout()
    hist_file = f"stretch_distribution_{safe_name}.png"
    plt.savefig(hist_file)
    plt.close()
    print(f"[SUCCESS] Histogram saved: {hist_file}")
    
    return metrics

def main():
    all_results = []
    for city in CITIES:
        res = verify_city(city)
        all_results.append(res)
        
    with open('stretch_distributions.json', 'w') as f:
        json.dump(all_results, f, indent=4)
        
    print("\n" + "=" * 65)
    print("ALL 4 CITIES VERIFIED SUCCESSFULLY. Saved to stretch_distributions.json")
    print("=" * 65)

if __name__ == '__main__':
    main()
