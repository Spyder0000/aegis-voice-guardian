import os
import matplotlib.pyplot as plt
import numpy as np

# Ensure target directory exists
os.makedirs("docs/charts", exist_ok=True)

# Common styling configuration
plt.rcParams['font.sans-serif'] = 'DejaVu Sans'
plt.rcParams['axes.edgecolor'] = '#CCCCCC'
plt.rcParams['axes.linewidth'] = 0.8

# Colors
COLOR_SAHARA = '#2563EB'   # Royal Blue
COLOR_WHISPER = '#10B981'  # Emerald Green

COLOR_FP = '#EF4444'       # Coral Red
COLOR_FN = '#F59E0B'       # Amber
COLOR_ACC = '#10B981'      # Emerald Green

# ---------------------------------------------------------
# Chart 1: WER Comparison (Grouped Bar Chart)
# ---------------------------------------------------------
labels = ['Corrected Avg WER', 'Final Avg Numeric WER']
sahara_vals = [61.01, 68.07]
whisper_vals = [51.02, 26.71]

x = np.arange(len(labels))
width = 0.35

fig, ax = plt.subplots(figsize=(8, 5.5), dpi=300)

rects1 = ax.bar(x - width/2, sahara_vals, width, label='Sahara v2', color=COLOR_SAHARA, edgecolor='none', zorder=3)
rects2 = ax.bar(x + width/2, whisper_vals, width, label='Whisper large-v3', color=COLOR_WHISPER, edgecolor='none', zorder=3)

# Title & Axis formatting
ax.set_ylabel('Error Rate (%)', fontsize=12, fontweight='bold', labelpad=10)
ax.set_title('Word Error Rate (WER) Comparison', fontsize=14, fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=11, fontweight='bold')
ax.set_ylim(0, 85)

# Clean clutter
ax.grid(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#888888')
ax.spines['bottom'].set_color('#888888')

# Legend
ax.legend(frameon=False, fontsize=11, loc='upper right')

# Value labels on top of bars
def autolabel_grouped(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 5),  # 5 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold', color='#1E293B')

autolabel_grouped(rects1)
autolabel_grouped(rects2)

plt.tight_layout()
wer_chart_path = "docs/charts/wer_comparison.png"
plt.savefig(wer_chart_path, format='png', dpi=300)
plt.close()
print(f"Saved {wer_chart_path}")


# ---------------------------------------------------------
# Chart 2: Downstream Risk Scorer Accuracy (Simple Bar Chart)
# ---------------------------------------------------------
metrics = ['False Positive Rate', 'False Negative Rate', 'Overall Accuracy']
accuracy_vals = [15.0, 15.0, 85.0]
bar_colors = [COLOR_FP, COLOR_FN, COLOR_ACC]

fig, ax = plt.subplots(figsize=(7.5, 5.5), dpi=300)

rects = ax.bar(metrics, accuracy_vals, width=0.45, color=bar_colors, edgecolor='none', zorder=3)

# Title & Axis formatting
ax.set_ylabel('Percentage (%)', fontsize=12, fontweight='bold', labelpad=10)
ax.set_title('Downstream Risk Scorer Accuracy (Rule-Based Baseline)', fontsize=13, fontweight='bold', pad=15)
ax.set_ylim(0, 100)

# Clean clutter
ax.grid(False)
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('#888888')
ax.spines['bottom'].set_color('#888888')

ax.set_xticks(range(len(metrics)))
ax.set_xticklabels(metrics, fontsize=10.5, fontweight='bold')

# Value labels on top of bars
for rect in rects:
    height = rect.get_height()
    ax.annotate(f'{height:.1f}%',
                xy=(rect.get_x() + rect.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha='center', va='bottom', fontsize=10.5, fontweight='bold', color='#1E293B')

plt.tight_layout()
risk_chart_path = "docs/charts/risk_scorer_accuracy.png"
plt.savefig(risk_chart_path, format='png', dpi=300)
plt.close()
print(f"Saved {risk_chart_path}")
