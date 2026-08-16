import json
import matplotlib.pyplot as plt
import numpy as np

# ۱. بارگذاری داده‌های واقعی از فایل JSON
with open('stretch_distributions.json', 'r') as f:
    data = json.load(f)

fig, ax = plt.subplots(figsize=(11, 6), dpi=300)

colors = {
    "Delft, Netherlands": "#2563eb",      # آبی
    "Eindhoven, Netherlands": "#059669",  # سبز
    "Leuven, Belgium": "#d97706",         # نارنجی
    "Rome, Italy": "#dc2626"              # قرمز
}

y_positions = np.arange(len(data))

# رسم خطوط دامنه و صدک‌ها برای هر شهر
for i, entry in enumerate(data):
    city = entry['city']
    c = colors.get(city, '#333333')
    y = y_positions[i]
    
    # خط دامنه کلی: از Min تا Max
    ax.plot([entry['min'], entry['raw_max']], [y, y], color=c, alpha=0.35, linewidth=4, zorder=1)
    
    # بازه تمرکز اصلی: از Median تا P99 (پوشش ۹۹٪ جفت‌ها)
    ax.plot([entry['median'], entry['p99']], [y, y], color=c, alpha=0.8, linewidth=8, zorder=2)
    
    # نقاط شاخص
    ax.scatter(entry['median'], y, color='white', edgecolor=c, s=90, linewidth=2, zorder=3, label='Median' if i == 0 else "")
    ax.scatter(entry['mean'], y, color=c, marker='D', s=70, zorder=4, label='Mean' if i == 0 else "")
    ax.scatter(entry['p95'], y, color=c, marker='|', s=120, linewidth=2, zorder=3, label='95th %ile' if i == 0 else "")
    ax.scatter(entry['p99'], y, color=c, marker='s', s=50, zorder=3, label='99th %ile' if i == 0 else "")
    ax.scatter(entry['raw_max'], y, color='black', marker='x', s=60, linewidth=1.5, zorder=3, label='Max (Measured)' if i == 0 else "")

# خط چین مرز نظری t=1.4
ax.axvline(1.4, color='#b91c1c', linestyle='--', linewidth=1.8, label='Theoretical Bound (t=1.4)', zorder=0)

# تنظیمات محورها
ax.set_yticks(y_positions)
city_labels = [f"{d['city'].split(',')[0]} (Mean: {d['mean']:.3f})" for d in data]
ax.set_yticklabels(city_labels, fontsize=12, fontweight='bold')
ax.set_xlabel("Stretch Factor ($d_H(u,v) / d_G(u,v)$)", fontsize=12, labelpad=10)
ax.set_xlim(0.98, 1.43)
ax.set_title("Stretch Factor Distribution Across 4 Structurally Different Cities (t=1.4)", fontsize=13, fontweight='bold', pad=15)

# شبکه کمکی و استایل
ax.grid(axis='x', linestyle=':', alpha=0.6)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)

# راهنمای نمودار (Legend)
handles, labels = ax.get_legend_handles_labels()
ax.legend(handles, labels, loc='lower right', framealpha=0.95, fontsize=10)

plt.tight_layout()
output_file = "city_comparison_distributions.png"
plt.savefig(output_file, bbox_inches='tight')
plt.close()

print(f"[SUCCESS] Honest comparison chart saved strictly from JSON: {output_file}")
