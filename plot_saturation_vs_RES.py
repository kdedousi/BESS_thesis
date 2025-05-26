import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib.colors import BoundaryNorm

# Load and clean data
file_path = "Saturation_summary.xlsx"
sheet_name = "Sheet1"
df = pd.read_excel(file_path, sheet_name=sheet_name)
df_filtered = df[df["Saturation_Point_MW"].notna()].copy()

# Extract RES %
def extract_res_percent(combo):
    if isinstance(combo, str):
        if combo.startswith("A1"): return 50
        elif combo.startswith("A2"): return 70
        elif combo.startswith("A3"): return 90
    return None

df_filtered["RES %"] = df_filtered["Combination"].apply(extract_res_percent)

# Extract B and C values from combination
df_filtered[["A", "B", "C"]] = df_filtered["Combination"].str.extract(r"(A\d) - (B\d) - (C\d)")

# Plot bounds
x_min, x_max = 100, 8000
y_min, y_max = 50, 100

# Start plot
plt.figure(figsize=(12, 8))

# Color and style palette (optional)
colors = ['blue', 'green', 'orange', 'red', 'purple', 'brown']
linestyles = ['-', '--', '-.', ':', (0, (5, 1)), (0, (3, 5, 1, 5))]

# Group by CAPEX-OPEX (B-C)
for i, ((b_val, c_val), group) in enumerate(df_filtered.groupby(["B", "C"])):
    group = group[["Saturation_Point_MW", "RES %"]].dropna().sort_values("Saturation_Point_MW")
    if len(group) > 1:
        x = group["Saturation_Point_MW"]
        y = group["RES %"]
        
        # Shaded positive (left) and negative (right) regions
        plt.fill_betweenx(y, x1=x_min, x2=x, color='lightblue', alpha=0.15)
        plt.fill_betweenx(y, x1=x, x2=x_max, color='lightcoral', alpha=0.15)

        # Optional: hatching
        plt.fill_betweenx(y, x1=x_min, x2=x, facecolor='none', edgecolor='lightblue', linewidth=0.3, hatch='---')
        plt.fill_betweenx(y, x1=x, x2=x_max, facecolor='none', edgecolor='lightcoral', linewidth=0.3, hatch='///')

        # Line plot
        plt.plot(x, y,
                 color=colors[i % len(colors)],
                 linestyle=linestyles[i % len(linestyles)],
                 linewidth=2,
                 marker='o',
                 label=f"Saturation Line ({b_val}-{c_val})")

# Labels and formatting
#plt.title("Saturation Point vs RES Share for All B-C Combinations", fontsize=14)
plt.xlabel("BESS Capacity in the System (MW)", fontsize=16)
plt.ylabel("RES Share (%)", fontsize=16)
plt.xlim(x_min, x_max)
plt.ylim(y_min, y_max)
plt.grid(True, linestyle=':', linewidth=0.7)

# Create proxy artists for legend
pos_patch = mpatches.Patch(color='lightblue', alpha=0.3, label='Positive Net Revenues')
neg_patch = mpatches.Patch(color='lightcoral', alpha=0.3, label='Negative Net Revenues')

# Add to existing legend handles
handles, labels = plt.gca().get_legend_handles_labels()
handles = [pos_patch, neg_patch] + handles
labels = [patch.get_label() for patch in handles]
plt.xticks(fontsize=14)
plt.yticks(fontsize=14)

plt.legend(handles=handles, loc='lower center', bbox_to_anchor=(0.5, -0.3), ncol=3, fontsize=12, frameon=True)
plt.tight_layout()
plt.show()

# Map strings to numeric values
res_map = {'A1': 1, 'A2': 2, 'A3': 3}
capex_map = {'B1': 1, 'B2': 2}
opex_codes = ['C1', 'C2', 'C3']
opex_labels = ['High OPEX', 'Mid OPEX', 'Low OPEX']

# Extract components
df[['RES', 'CAPEX', 'OPEX']] = df['Combination'].str.extract(r'(A\d)\s*-\s*(B\d)\s*-\s*(C\d)')
df['RES_num'] = df['RES'].map(res_map)
df['CAPEX_num'] = df['CAPEX'].map(capex_map)

# Create vertically stacked subplots
fig, axes = plt.subplots(3, 1, figsize=(7, 12), sharex=True)

# Colormaps for each plot
colormaps = ['viridis', 'plasma', 'inferno']

for idx in range(3):
    opex_code = opex_codes[idx]
    subset = df[df['OPEX'] == opex_code]

    Z = np.full((3, 2), np.nan)
    for _, row in subset.iterrows():
        y = row['RES_num'] - 1
        x = row['CAPEX_num'] - 1
        Z[y, x] = row['Saturation_Point_MW']

    # Axis and meshgrid
    X, Y = np.meshgrid([1, 2], [1, 2, 3])
    ax = axes[idx]

    # Plot-specific min/max for full colormap use
    local_vmin = np.nanmin(Z)
    local_vmax = np.nanmax(Z)

    contour = ax.contourf(X, Y, Z, cmap=colormaps[idx], levels=15, vmin=local_vmin, vmax=local_vmax)
    cbar = fig.colorbar(contour, ax=ax)
    cbar.set_label("Saturation Point (MW)", fontsize=12)
    cbar.ax.tick_params(labelsize=10)

    # Titles and labels
    ax.set_title(opex_labels[idx], fontsize=14)
    if idx == 2:
        ax.set_xlabel("CAPEX", fontsize=14)
        ax.set_xticks([1, 2])
        ax.set_xticklabels(['High', 'Low'], fontsize=12)
    else:
        ax.set_xticks([1, 2])
        ax.set_xticklabels([])

    ax.set_ylabel("RES Share", fontsize=14)
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(['50%', '70%', '90%'], fontsize=12)

plt.tight_layout()
plt.show()