# Geometric Spanners Lab: Greedy $t$-Spanner Benchmark

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](https://www.python.org/)
[![Status: Reproducible](https://img.shields.io/badge/Benchmarks-Reproducible-brightgreen.svg)]()

A clean, reproducible implementation and benchmarking lab for **Greedy $t$-Spanner Algorithms** on 2D metric spaces.

---

## 📌 Mathematical Background

Given a complete geometric graph $G = (V, E)$ with Euclidean edge weights, a subgraph $H = (V, E_H)$ is a **$t$-spanner** if:

$$\forall u, v \in V, \quad d_H(u, v) \le t \cdot d_G(u, v)$$

where $t \ge 1$ is the **stretch factor** (dilation). The classical greedy algorithm sorts all candidate edges and greedily adds an edge $(u, v)$ only if no path of length $\le t \cdot \|u - v\|$ currently exists in $H$.

---

## 📊 Empirical Baseline ($n=45, t=1.4$)

| Metric | Complete Graph ($K_{45}$) | Greedy $t$-Spanner | Reduction |
| :--- | :---: | :---: | :---: |
| **Edge Count ($|E|$)** | **990** | **77** | **92.22% Sparsity** |
| **Stretch Factor ($t$)** | 1.00 | $\le 1.40$ | *Guaranteed Bound* |
| **Graph Density** | $O(n^2)$ | $O(n)$ | Sparse Backbone |

![Spanner Comparison](spanner_comparison.png)

---

## 🚀 Quickstart & Reproducibility

```bash
# Clone the repository
git clone https://github.com/soheylfalahzade/geometric-spanners-lab.git
cd geometric-spanners-lab

# Run the benchmark
python greedy_spanner.py
📄 License
This project is licensed under the MIT License.
