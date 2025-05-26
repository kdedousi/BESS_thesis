import os
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_revenues(results_path, res_label):
    results_df = pd.read_excel(results_path)
    output_dir = os.path.dirname(results_path)

    grouped = results_df.groupby('Total_Capacity').agg({
        'Marginal_DA_Revenue': 'max',
        'Marginal_Imbalance_Revenue': 'max',
        'Marginal_aFRR_Reserve_Revenue': 'max',
        'Marginal_Net_Revenue': 'max',
        'Marginal_CAPEX_Cost': 'max',
        'Marginal_OPEX_Cost': 'max'     
    }).reset_index()

    fig, ax1 = plt.subplots(figsize=(10, 5))
    bar_width = 20
    capacities = grouped['Total_Capacity']
    
    bottom_imbalance = grouped['Marginal_DA_Revenue']
    bottom_aFRR_res = bottom_imbalance + grouped['Marginal_Imbalance_Revenue']

    ax1.bar(capacities, grouped['Marginal_DA_Revenue'], bar_width, color='blue', label="DAM Revenue")
    ax1.bar(capacities, grouped['Marginal_Imbalance_Revenue'], bar_width, color='purple', bottom=bottom_imbalance, label="Imbalance Revenue")
    ax1.bar(capacities, grouped['Marginal_aFRR_Reserve_Revenue'], bar_width, color='red', bottom=bottom_aFRR_res, label="aFRR Reserve Revenue")
    ax1.bar(capacities, -grouped['Marginal_CAPEX_Cost'], bar_width, color='orange', label="Marginal CAPEX Cost")
    ax1.bar(capacities, -grouped['Marginal_OPEX_Cost'], bar_width, bottom=-grouped['Marginal_CAPEX_Cost'], color='brown', label="Marginal OPEX Cost")

    ax2 = ax1.twinx()
    ax2.plot(capacities, grouped['Marginal_Net_Revenue'], marker='^', color='green', label="Marginal Net Revenue")

    ax1.axhline(0, color='black', linewidth=1)

    ax1.set_xlabel('Marginal Capacity of the BESS (MW)', fontsize=12)
    ax1.set_ylabel('Marginal Revenue and Cost (€/100MW)', fontsize=12)
    ax2.set_ylabel('Marginal Net Revenue (€/100MW)', fontsize=12)
    ax1.tick_params(axis='both', labelsize=10)
    ax2.tick_params(axis='y', labelsize=10)

    ax1.set_ylim(min(ax1.get_ylim()[0], ax2.get_ylim()[0]), max(ax1.get_ylim()[1], ax2.get_ylim()[1]))
    ax2.set_ylim(ax1.get_ylim())

    # Adjust spacing to make room for the legend below
    plt.tight_layout(rect=[0, 0.15, 1, 0.95])

    lines_labels = [ax.get_legend_handles_labels() for ax in [ax1, ax2]]
    lines, labels = [sum(lol, []) for lol in zip(*lines_labels)]
    fig.legend(lines, labels, loc='lower center', bbox_to_anchor=(0.5, 0.0), ncol=2, frameon=True)

    safe_label = res_label.replace(' ', '_').replace('%', 'pct')
    plt.savefig(os.path.join(output_dir, f"marginal_revenue_plot_{safe_label}.png"), dpi=300)
    plt.close()

def plot_aggregate_revenue_contributions(results_path, res_label):
    results_df = pd.read_excel(results_path)
    output_dir = os.path.dirname(results_path)
    grouped_capacity = results_df.groupby("Total_Capacity").agg({
        "Marginal_DA_Revenue": "sum",
        "Marginal_Imbalance_Revenue": "sum",
        "Marginal_aFRR_Reserve_Revenue": "sum",
    }).reset_index()

    grouped_capacity["Total_Revenue"] = (
        grouped_capacity["Marginal_DA_Revenue"] +
        grouped_capacity["Marginal_Imbalance_Revenue"] +
        grouped_capacity["Marginal_aFRR_Reserve_Revenue"]
    ).replace(0, 1)

    grouped_capacity["DA_Share"] = grouped_capacity["Marginal_DA_Revenue"] / grouped_capacity["Total_Revenue"] * 100
    grouped_capacity["Imbalance_Share"] = grouped_capacity["Marginal_Imbalance_Revenue"] / grouped_capacity["Total_Revenue"] * 100
    grouped_capacity["aFRR_Reserve_Share"] = grouped_capacity["Marginal_aFRR_Reserve_Revenue"] / grouped_capacity["Total_Revenue"] * 100

    fig, ax = plt.subplots(figsize=(8, 4))
    bar_width = 20
    bottom = np.zeros(len(grouped_capacity))

    for share, color, label in zip(
        ["DA_Share", "Imbalance_Share", "aFRR_Reserve_Share"],
        ["blue", "purple", "red"],
        ["DA Market", "Imbalance Market", "aFRR Reserve"]
    ):
        bars = ax.bar(
            grouped_capacity["Total_Capacity"],
            grouped_capacity[share],
            width=bar_width,
            bottom=bottom,
            label=label,
            color=color
        )

        show_every = 1 if grouped_capacity["Total_Capacity"].max() <= 3000 else 5

        for i, (bar, pct) in enumerate(zip(bars, grouped_capacity[share])):
            if i % show_every == 0 and pct > 1:
                height = bar.get_height()
                ax.text(
                    bar.get_x() - 1,
                    bar.get_y() + height / 2,
                    rf"$\mathbf{{{pct:.0f}\%}}$",
                    ha='right',
                    va='center',
                    fontsize=8,
                    color='black'
                )

        bottom += grouped_capacity[share]

    ax.set_xlabel("Total Installed BESS Capacity (MW)")
    ax.set_ylabel("Revenue Share (%)")
    #ax.set_title(f'Share of Revenue Streams for Incremental Capacity ({res_label})')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    ax.grid(True)
    plt.tight_layout()
    safe_label = res_label.replace(' ', '_').replace('%', 'pct')
    plt.savefig(os.path.join(output_dir, f"revenue_share_plot_{safe_label}.png"), dpi=300)
    plt.close()


