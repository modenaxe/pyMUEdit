import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

# Load your comparison summary
df = pd.read_csv("fastICA_comparison_summary2.csv")

# Clean up variable naming (optional)
df['variable'] = df['variable'].astype(str)

# ---- Choose one electrode to inspect ----
electrode_to_plot = 0   # change to 1 if you want electrode 1
df = df[df['electrode'] == electrode_to_plot]

# ---- Aggregate by iteration or sub_iteration ----
# e.g. take mean correlation per iteration
corr_by_iter = df.groupby(['iteration'])['correlation'].mean()
angle_by_iter = df.groupby(['iteration'])['angle_deg'].mean()
norm_ratio_by_iter = df.groupby(['iteration'])['norm_ratio'].mean()

# ---- Plot trends ----
plt.figure(figsize=(10, 6))
plt.plot(corr_by_iter.index, corr_by_iter.values, 'o-', label='Mean Correlation')
plt.plot(angle_by_iter.index, angle_by_iter.values, 's-', label='Mean Angle (deg)')
plt.xlabel('Iteration')
plt.ylabel('Value')
plt.title(f'FastICA Debug Comparison Trends (Electrode {electrode_to_plot})')
plt.grid(True, alpha=0.3)
plt.legend()
plt.tight_layout()
plt.show()

# ---- Optional: deeper zoom on sub-iterations ----
fig, ax = plt.subplots(figsize=(10,6))
for it in sorted(df['iteration'].unique()):
    subset = df[df['iteration'] == it]
    ax.plot(subset['sub_iteration'], subset['correlation'], 'o-', alpha=0.5, label=f'Iter {it}')
ax.set_xlabel('Sub-iteration')
ax.set_ylabel('Correlation')
ax.set_title(f'Per-subiteration Correlation (Electrode {electrode_to_plot})')
ax.legend(ncol=4, fontsize=8)
ax.grid(True, alpha=0.3)
plt.tight_layout()
plt.show()
