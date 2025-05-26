import pandas as pd
import matplotlib.pyplot as plt
import os

# Load only needed columns
usecols = [
    'Total_Capacity', 'Time', 'DAM_Price',
    'Imbalance_Price_Surplus', 'Imbalance_Price_Shortage',
    'aFRR_Up_Price_reserve', 'aFRR_Down_Price_reserve'
]
df = pd.read_excel('final_results1.xlsx', usecols=usecols)

# Filter to every 1000 MW
fixed_capacities = sorted([c for c in df['Total_Capacity'].unique() if c % 1000 == 0])
df_filtered = df[df['Total_Capacity'].isin(fixed_capacities)]

# Assign fixed colors
capacity_colors = {
    cap: color for cap, color in zip(
        fixed_capacities,
        ['#0072B2', '#D55E00', '#009E73', '#F0E442',
         '#CC79A7', '#56B4E9', '#E69F00', '#9966CC',
         '#999933', '#CC6677']
    )
}

# Define baseline
baseline_capacity = min(fixed_capacities)
df_baseline = df_filtered[df_filtered['Total_Capacity'] == baseline_capacity]

# Merge with baseline prices on time
merged_df = df_filtered.merge(
    df_baseline[['Time', 'DAM_Price', 'Imbalance_Price_Shortage', 'Imbalance_Price_Surplus',
                 'aFRR_Up_Price_reserve', 'aFRR_Down_Price_reserve']],
    on='Time',
    suffixes=('', '_baseline')
)

# Compute price deltas
merged_df['Δ_DAM'] = merged_df['DAM_Price'] - merged_df['DAM_Price_baseline']
merged_df['Δ_Imb_Short'] = merged_df['Imbalance_Price_Shortage'] - merged_df['Imbalance_Price_Shortage_baseline']
merged_df['Δ_Imb_Surplus'] = merged_df['Imbalance_Price_Surplus'] - merged_df['Imbalance_Price_Surplus_baseline']
merged_df['Δ_aFRR_Up'] = merged_df['aFRR_Up_Price_reserve'] - merged_df['aFRR_Up_Price_reserve_baseline']
merged_df['Δ_aFRR_Down'] = merged_df['aFRR_Down_Price_reserve'] - merged_df['aFRR_Down_Price_reserve_baseline']

# Plot setup
price_changes = {
    'Δ_DAM': ('Δ DAM Price [€/MWh]', 'Day-Ahead Market', 'delta_dam.png'),
    'Δ_Imb_Short': ('Δ Imbalance Shortage Price [€/MWh]', 'Imbalance Shortage', 'delta_imb_shortage.png'),
    'Δ_Imb_Surplus': ('Δ Imbalance Surplus Price [€/MWh]', 'Imbalance Surplus', 'delta_imb_surplus.png'),
    'Δ_aFRR_Up': ('Δ aFRR Up Reserve Price [€/MW/h]', 'aFRR Up Reserve', 'delta_afrr_up.png'),
    'Δ_aFRR_Down': ('Δ aFRR Down Reserve Price [€/MW/h]', 'aFRR Down Reserve', 'delta_afrr_down.png')
}

output_folder = "bess_price_deltas"
os.makedirs(output_folder, exist_ok=True)

# Plot and save each Δ price
for col, (ylabel, title, filename) in price_changes.items():
    plt.figure(figsize=(12, 6))
    for capacity in [8000, 2000]:
        if capacity not in fixed_capacities or capacity == baseline_capacity:
            continue
        subset = merged_df[merged_df['Total_Capacity'] == capacity]
        color = capacity_colors[capacity]
        plt.plot(subset['Time'], subset[col], label=f'{capacity} MW', color=color)

    plt.axhline(0, color='black', linestyle='--', linewidth=0.8)
    plt.xlabel('Hour timestep (First half of the year)', fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    #plt.title(f'Change in {title} Relative to Baseline ({baseline_capacity} MW)', fontsize=16)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(title='BESS Capacity', loc='upper left')
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(output_folder, filename), dpi=300)
    plt.close()
    print(f"Saved: {filename}")
