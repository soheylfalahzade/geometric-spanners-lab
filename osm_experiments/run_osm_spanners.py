import os
import sys
import time
import json
import multiprocessing
import numpy as np
import networkx as nx
import osmnx as ox
import matplotlib.pyplot as plt
from scipy.spatial import distance_matrix
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import shortest_path

# اضافه کردن پوشه والد به مسیر سیستم برای دسترسی به فایل greedy_spanner.py شما
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from greedy_spanner import build_greedy_t_spanner

# ================= Configuration =================
CITIES = [
    "Delft, Netherlands",
    "Eindhoven, Netherlands",
    "Leuven, Belgium",
    "Rome, Italy"
]
#RADIUS_METERS = 2000
#RADIUS_METERS = 500
RADIUS_METERS = 1500
T_VALUE = 1.4
TIMEOUT_SECONDS = 1800  # 30 minutes limit per city
# =================================================

def worker(points_dict, t, return_dict):
    """
    Multiprocessing worker to execute the spanner construction.
    Edges are extracted to avoid Pickling complex NetworkX objects across processes.
    """
    try:
        H, runtime = build_greedy_t_spanner(points_dict, t)
        return_dict['edges'] = list(H.edges(data=True))
        return_dict['runtime'] = runtime
    except Exception as e:
        return_dict['error'] = str(e)

def measure_actual_stretch(points_dict, edges, t_target):
    """
    Calculates the exact maximum stretch factor using All-Pairs Shortest Path.
    """
    n = len(points_dict)
    coords = np.array([points_dict[i] for i in range(n)])
    
    # Base Euclidean distance matrix (Graph G)
    dist_mat = distance_matrix(coords, coords)
    
    # Build Spanner sparse adjacency matrix for fast APSP
    row, col, data = [], [], []
    for u, v, d in edges:
        w = d['weight']
        row.extend([u, v])
        col.extend([v, u])
        data.extend([w, w])
        
    spanner_adj = csr_matrix((data, (row, col)), shape=(n, n))
    
    # Compute shortest paths on the Spanner H
    apsp_spanner = shortest_path(csgraph=spanner_adj, directed=False)
    
    # Calculate stretch (ignore diagonal to avoid 0/0 division)
    np.fill_diagonal(dist_mat, np.inf)
    stretch_matrix = apsp_spanner / dist_mat
    
    max_stretch = np.max(stretch_matrix)
    
    if max_stretch > t_target + 1e-5:
        print(f"\n[FLAG] Measured stretch ({max_stretch:.4f}) VIOLATES the t={t_target} guarantee!")
        print("Likely Cause: OSM point clouds may contain highly collinear points or floating-point ")
        print("precision differences exist between your NetworkX shortest_path check and Scipy's APSP.")
        
    return float(max_stretch)

def generate_visualization(city_name, points_dict, full_edges, spanner_edges, pruned_pct, t_value):
    """
    Matches the style of evaluate_and_export_figure but optimized for large N.
    """
    n = len(points_dict)
    coords = np.array([points_dict[i] for i in range(n)])
    
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), dpi=300)
    fig.suptitle(f"{city_name} — Spanner Evaluation (t={t_value})", fontsize=15, fontweight='bold')
    
    # Left: Complete Graph (Visualized as point cloud due to O(n^2) density causing matplotlib to hang)
    axes[0].scatter(coords[:, 0], coords[:, 1], c='#1f2937', s=1)
    axes[0].set_title(f"Complete Metric Graph $K_{{{n}}}$\n({full_edges} Edges — Dense $O(n^2)$)", fontsize=13, pad=12)
    axes[0].axis('off')
    
    # Right: Greedy t-Spanner
    axes[1].scatter(coords[:, 0], coords[:, 1], c='#dc2626', s=1, zorder=2)
    
    # Fast plotting of line segments using LineCollection would be optimal, 
    # but looping is okay for ~2000-5000 edges.
    for u, v, _ in spanner_edges:
        p1, p2 = points_dict[u], points_dict[v]
        axes[1].plot([p1[0], p2[0]], [p1[1], p2[1]], c='#1e40af', linewidth=0.5, alpha=0.7, zorder=1)
        
    axes[1].set_title(f"Greedy $t$-Spanner Backbone\n({len(spanner_edges)} Edges — {pruned_pct:.2f}% Pruned)", fontsize=13, fontweight='bold', pad=12)
    axes[1].axis('off')
    
    plt.tight_layout()
    safe_name = city_name.split(',')[0].strip().lower().replace(" ", "_")
    output_file = f"spanner_{safe_name}.png"
    plt.savefig(output_file, bbox_inches='tight')
    plt.close()
    print(f"[SUCCESS] Visualization exported: {output_file}")

def main():
    results = []
    
    for city in CITIES:
        print("\n" + "="*60)
        print(f"Processing Real OSM Network: {city}")
        print("="*60)
        
        try:
            # 1. Download and project OSM Graph
            print(f"[1/4] Downloading street network (Radius: {RADIUS_METERS}m)...")
            G = ox.graph_from_address(city, dist=RADIUS_METERS, network_type='drive')
            G_proj = ox.project_graph(G)
            
            # 2. Extract points into the exact format your script expects: dict[int, np.ndarray]
            print("[2/4] Formatting coordinates...")
            nodes = list(G_proj.nodes(data=True))
            points_dict = {i: np.array([data['x'], data['y']]) for i, (node_id, data) in enumerate(nodes)}
            n_nodes = len(points_dict)
            full_edges_count = (n_nodes * (n_nodes - 1)) // 2
            
            print(f"      Extracted {n_nodes} nodes.")
            print(f"      Equivalent Complete Graph Edges: {full_edges_count}")
            
            # 3. Execute Greedy Spanner with strict timeout
            print(f"[3/4] Running Greedy t-Spanner (Timeout: {TIMEOUT_SECONDS}s)...")
            manager = multiprocessing.Manager()
            return_dict = manager.dict()
            
            p = multiprocessing.Process(target=worker, args=(points_dict, T_VALUE, return_dict))
            p.start()
            p.join(TIMEOUT_SECONDS)
            
            if p.is_alive():
                print(f"\n[FAILED] Process timed out for {city}. Graph density too high for O(n^3 log n) worst-case.")
                p.terminate()
                p.join()
                results.append({
                    "city": city, "num_nodes": n_nodes, "num_edges_full": full_edges_count,
                    "num_edges_spanner": None, "pct_pruned": None, "measured_max_stretch": None,
                    "runtime_seconds": TIMEOUT_SECONDS, "status": "TIMEOUT"
                })
                continue
                
            if 'error' in return_dict:
                print(f"\n[FAILED] Script crashed: {return_dict['error']}")
                continue
                
            spanner_edges = return_dict['edges']
            runtime = return_dict['runtime']
            num_spanner_edges = len(spanner_edges)
            pct_pruned = 100.0 * (1.0 - (num_spanner_edges / full_edges_count))
            
            print(f"      Spanner built in {runtime:.2f} seconds.")
            print(f"      Retained Edges: {num_spanner_edges} ({pct_pruned:.4f}% pruned)")
            
            # 4. Measure Stretch & Export
            print("[4/4] Validating actual maximum stretch factor...")
            max_stretch = measure_actual_stretch(points_dict, spanner_edges, T_VALUE)
            print(f"      Measured Max Stretch: {max_stretch:.4f}")
            
            generate_visualization(city, points_dict, full_edges_count, spanner_edges, pct_pruned, T_VALUE)
            
            results.append({
                "city": city,
                "num_nodes": n_nodes,
                "num_edges_full": full_edges_count,
                "num_edges_spanner": num_spanner_edges,
                "pct_pruned": round(pct_pruned, 4),
                "measured_max_stretch": round(max_stretch, 4),
                "runtime_seconds": round(runtime, 2),
                "status": "SUCCESS"
            })
            
        except Exception as e:
            print(f"[ERROR] Could not process {city}: {e}")
            
    print("\n" + "="*60)
    print("All experiments finished. Saving raw metrics to results.json...")
    with open('results.json', 'w') as f:
        json.dump(results, f, indent=4)
    print("Done.")

if __name__ == '__main__':
    main()
