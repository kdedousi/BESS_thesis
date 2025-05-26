import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

# Load the Excel file
file_path = "saturation_summary.xlsx"
df = pd.read_excel(file_path)

# Ensure correct column names
df.columns = ["Case", "Combination", "Saturation Point"]
df.dropna(inplace=True)
df["Case"] = df["Case"].astype(int)
df["Saturation Point"] = pd.to_numeric(df["Saturation Point"], errors='coerce')

# Identify max and min points
max_idx = df["Saturation Point"].idxmax()
min_idx = df["Saturation Point"].idxmin()
max_point = df.loc[max_idx]
min_point = df.loc[min_idx]

# Create the plot
plt.figure(figsize=(12, 6))
plt.plot(df["Case"], df["Saturation Point"], marker='o', linestyle='-', color='steelblue', label='Saturation Point')

# Highlight max point
plt.scatter(max_point["Case"], max_point["Saturation Point"], color='crimson', label=f"Max (Case {max_point['Case']})", zorder=5)
plt.text(
    max_point["Case"] - 0.7, max_point["Saturation Point"] + 100,
    f"Max: {max_point['Saturation Point']:.0f} MW",
    color='crimson', ha='center', fontsize=14
)

# Highlight min point
plt.scatter(min_point["Case"], min_point["Saturation Point"], color='forestgreen', label=f"Min (Case {min_point['Case']})", zorder=5)
plt.text(
    min_point["Case"] - 0.5, min_point["Saturation Point"] + 400,
    f"Min: {min_point['Saturation Point']:.0f} MW",
    color='forestgreen', ha='left', fontsize=14
)

# Highlight first peak (case 9)
peak_case = 9
peak_point = df[df["Case"] == peak_case].iloc[0]
plt.scatter(peak_point["Case"], peak_point["Saturation Point"], color='orange', label=f"High CAPEX/Low OPEX (Case {peak_case})", zorder=5)
plt.text(
    peak_point["Case"] - 0.5, peak_point["Saturation Point"] + 200,
    f"Peak 1: {peak_point['Saturation Point']:.0f} MW",
    color='darkorange', ha='center', fontsize=14
)

# Highlight second peak (case 18)
peak_case_2 = 18
peak_point_2 = df[df["Case"] == peak_case_2].iloc[0]
plt.scatter(peak_point_2["Case"], peak_point_2["Saturation Point"], color='darkviolet', label=f"Medium CAPEX/Low OPEX (Case {peak_case_2})", zorder=5)
plt.text(
    peak_point_2["Case"] - 0.5, peak_point_2["Saturation Point"] + 200,
    f"Peak 2: {peak_point_2['Saturation Point']:.0f} MW",
    color='darkviolet', ha='center', fontsize=14
)

# Plot styling
plt.xlabel("Case Number", fontsize=16)
plt.ylabel("Saturation Point (MW)", fontsize=16)
plt.xticks(df["Case"])  # force integer ticks only
plt.grid(True, linestyle=':', linewidth=0.5)
plt.legend(fontsize=12)
plt.tight_layout()

# Show plot
plt.show()
