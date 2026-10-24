import json
import matplotlib.pyplot as plt
import numpy as np

# 1. Load the measured data from the JSON file
with open('stretch_distributions.json', 'r') as f:
    data = json.load(f)

fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

colors = {
    "Delft, Netherlands": "#2563eb",      # blue
    "Eindhoven, Netherlands": "#059669",  # green
    "Leuven, Belgium": "#d97706",         # orange
    "Rome, Italy": "#dc2626"              # red
}

y_positions = np.arange(len(data))

# Draw range lines and percentiles for each city
for i, entry in enumerate(data):
    city = entry['city']
    c = colors.get(city, '#333333')
    y = y_positions[i]
    
    # Overall range line: from Min to Max
    ax.plot([entry['min'], entry['raw_max']], [y, y], color=c, alpha=0.35, linewidth=4, zorder=1)
    
    # Main mass: from Median to P99 (covers 99% of the pairs)
    ax.plot([entry['median'], entry['p99']], [y, y], color=c, alpha=0.8, linewidth=8, zorder=2)
    
    # Marker points
    ax.scatter(entry['median'], y, color='white', edgecolor=c, s=90, linewidth=2, zorder=3, label='Median' if i == 0 else "")
    ax.scatter(entry['mean'], y, color=c, marker='D', s=70, zorder=4, label='Mean' if i == 0 else "")
    ax.scatter(entry['p95'], y, color=c, marker='|', s=120, linewidth=2, zorder=3, label='95th %ile' if i == 0 else "")
    ax.scatter(entry['p99'], y, color=c, marker='s', s=50, zorder=3, label='99th %ile' if i == 0 else "")
    ax.scatter(entry['raw_max'], y, color='black', marker='x', s=60, linewidth=1.5, zorder=3, label='Max (Measured)' if i == 0 else "")

# Dashed line at the theoretical bound t=1.4
ax.axvline(1.4, color='#b91c1c', linestyle='--', linewidth=1.8, label='Theoretical Bound (t=1.4)', zorder=0)

# Axis settings
ax.set_yticks(y_positions)
city_labels = [f"{d['city'].split(',')[0]} (Mean: {d['mean']:.3f})" for d in data]
ax.set_yticklabels(city_labels, fontsize=12, fontweight='bold')
ax.set_xlabel("Stretch Factor ($d_H(u,v) / d_G(u,v)$)", fontsize=12, labelpad=10)
ax.set_xlim(0.98, 1.43)
ax.set_title("Stretch Factor Distribution Across 4 Structurally Different Cities (t=1.4)", fontsize=13, fontweight='bold', pad=15)

# Grid and style
ax.grid(axis='x', linestyle=':', alpha=0.6)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# Legend
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc='lower right', framealpha=0.95, fontsize=10)

plt.tight_layout()
output_file = "city_comparison_distributions.png"
plt.savefig(output_file, bbox_inches='tight')
plt.close()

print(f"[SUCCESS] Honest comparison chart saved strictly from JSON: {output_file}")
