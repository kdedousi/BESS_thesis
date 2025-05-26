import pandas as pd
import matplotlib.pyplot as plt
import os
from matplotlib.patches import ConnectionPatch, Rectangle

# Load only needed columns
usecols = [
    'Total_Capacity', 'Time', 'DAM_Price',
    'Imbalance_Price_Surplus', 'Imbalance_Price_Shortage',
    'aFRR_Up_Price_reserve', 'aFRR_Down_Price_reserve'
]
df = pd.read_excel('final_results1.xlsx', usecols=usecols)

# Filter to every 1000 MW
fixed_capacities = sorted([c for c in df['Total_Capacity'].unique() if c % 1000 == 0])

# Assign fixed colors
capacity_colors = {
    cap: color for cap, color in zip(
        fixed_capacities,
        ['#0072B2', '#D55E00', '#009E73', '#F0E442',
         '#CC79A7', '#56B4E9', '#E69F00', '#9966CC',
         '#999933', '#CC6677']
    )
}

# Output folder
output_folder = "bess_price_plots"
os.makedirs(output_folder, exist_ok=True)

def plot_price_by_capacity(df, price_column, ylabel, filename):
    plt.figure(figsize=(12, 6))

    # Filter for first half of the year (0 to 4379)
    df_half_year = df[df['Time'] < 4380]

    for capacity in fixed_capacities:
        subset = df_half_year[df_half_year['Total_Capacity'] == capacity]
        color = capacity_colors[capacity]
        plt.plot(subset['Time'], subset[price_column], label=f'{capacity} MW', color=color)

    plt.xlabel('Hour timestep (First half of the year)', fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(title='BESS Capacity', loc='upper left')
    plt.grid(True)
    plt.tight_layout()

    plot_path = os.path.join(output_folder, filename)
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved: {plot_path}")


def plot_price_with_zoom(df, price_column, ylabel, filename, zoom_range, inset_loc):
    from mpl_toolkits.axes_grid1.inset_locator import inset_axes, mark_inset

    plt.figure(figsize=(12, 6))

    df_half_year = df[df['Time'] < 4380]

    for capacity in fixed_capacities:
        subset = df_half_year[df_half_year['Total_Capacity'] == capacity]
        color = capacity_colors[capacity]
        plt.plot(subset['Time'], subset[price_column], label=f'{capacity} MW', color=color)

    plt.xlabel('Hour timestep (First half of the year)', fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    plt.xticks(fontsize=12)
    plt.yticks(fontsize=12)
    plt.legend(title='BESS Capacity', loc='upper left')
    plt.grid(True)

    # Add zoom-in inset at desired location
    ax = plt.gca()
    axins = inset_axes(ax, width="30%", height="30%", loc=inset_loc, borderpad=2)

    for capacity in fixed_capacities:
        subset = df_half_year[df_half_year['Total_Capacity'] == capacity]
        color = capacity_colors[capacity]
        zoom_subset = subset[(subset['Time'] >= zoom_range[0]) & (subset['Time'] <= zoom_range[1])]
        axins.plot(zoom_subset['Time'], zoom_subset[price_column], color=color)

    axins.set_xlim(zoom_range[0], zoom_range[1])
    axins.set_xticks([])
    axins.set_yticks([])
    axins.set_title('Zoom-in', fontsize=11, fontweight='bold')

    # Compute zoom rectangle to include full height of all curves
    zoom_data = df_half_year[df_half_year['Time'].between(zoom_range[0], zoom_range[1])]
    y_vals = []

    for capacity in fixed_capacities:
        subset = zoom_data[zoom_data['Total_Capacity'] == capacity]
        y_vals.extend(subset[price_column].dropna().values)

    if y_vals:
        y_min, y_max = min(y_vals), max(y_vals)
    else:
        y_min, y_max = 0, 1  # Default fallback in case no data
    zoom_box_bottom = y_min
    zoom_height = y_max - y_min

    # Draw the zoom indicator box on main plot
    zoom_box = Rectangle(
        (zoom_range[0], zoom_box_bottom),
        zoom_range[1] - zoom_range[0],
        zoom_height,
        linewidth=1.5, edgecolor='black', facecolor='none'
    )
    ax.add_patch(zoom_box)

    # Decide connection corners based on price type
    if 'aFRR' in price_column:
        # From top-right of main box to bottom-left of inset
        x_main = zoom_range[1]
        y_main = zoom_box_bottom + zoom_height
        x_inset = zoom_range[0]
        y_inset = zoom_box_bottom
    else:
        # From bottom-right of main box to top-left of inset
        x_main = zoom_range[1]
        y_main = zoom_box_bottom
        x_inset = zoom_range[0]
        y_inset = zoom_box_bottom + zoom_height

    # Draw the connector line
    con = ConnectionPatch(
        xyA=(x_main, y_main), coordsA=ax.transData,
        xyB=(x_inset, y_inset), coordsB=axins.transData,
        arrowstyle='-', linewidth=1.5, color='black'
    )
    con.set_zorder(5)
    ax.add_artist(con)

    # Bring inset border to front
    for spine in axins.spines.values():
        spine.set_zorder(10)


    plt.tight_layout()
    plot_path = os.path.join(output_folder, filename)
    plt.savefig(plot_path, dpi=300)
    plt.close()
    print(f"Saved: {plot_path}")

# Generate and save plots
plot_price_with_zoom(df, 'DAM_Price', 'DA - Price [€/MWh]', 'DA_prices.png', zoom_range=(500, 700), inset_loc='lower center')
plot_price_with_zoom(df, 'aFRR_Up_Price_reserve', 'aFRR Up - Price [€/MW/h]', 'aFRR_up_prices.png', zoom_range=(500, 700), inset_loc='upper center')
plot_price_with_zoom(df, 'aFRR_Down_Price_reserve', 'aFRR down - Price [€/MW/h]', 'aFRR_down_prices.png', zoom_range=(500, 700), inset_loc='upper center')
plot_price_by_capacity(df, 'Imbalance_Price_Shortage', 'Imbalance shortage - Price [€/MWh]', 'Imbalance_shortage_prices.png')
plot_price_by_capacity(df, 'Imbalance_Price_Surplus', 'Imbalance surplus - Price [€/MWh]', 'Imbalance_surplus_prices.png')

