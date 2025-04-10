import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def plot_revenues(results_path):
    results_df = pd.read_excel(results_path)
    grouped = results_df.groupby('Total_Capacity').agg({
        'Marginal_DA_Revenue': 'max',
        'Marginal_Imbalance_Revenue': 'max',
        'Marginal_aFRR_Reserve_Revenue': 'max',
        #'Marginal_aFRR_Activation_Revenue': 'max',
        'Marginal_Total_Revenue': 'max',
        'Marginal_Net_Revenue': 'max'
    }).reset_index()

    fig, ax1 = plt.subplots(figsize=(8, 4))
    bar_width = 10
    capacities = grouped['Total_Capacity']
    
    bottom_imbalance = grouped['Marginal_DA_Revenue']
    bottom_aFRR_res = bottom_imbalance + grouped['Marginal_Imbalance_Revenue']
    #bottom_aFRR_act = bottom_aFRR_res + grouped['Marginal_aFRR_Reserve_Revenue']

    # Stacked bar plot for revenues
    bars_DA = ax1.bar(capacities, grouped['Marginal_DA_Revenue'], bar_width, color='blue')
    bars_Imb = ax1.bar(capacities, grouped['Marginal_Imbalance_Revenue'], bar_width, color='purple', bottom=bottom_imbalance)
    bars_aFRR_res = ax1.bar(capacities, grouped['Marginal_aFRR_Reserve_Revenue'], bar_width, color='red', bottom=bottom_aFRR_res)
    #bars_aFRR_act = ax1.bar(capacities, grouped['Marginal_aFRR_Activation_Revenue'], bar_width, color='brown', bottom=bottom_aFRR_act)
    
    # Bar for cost
    bars_Cost = ax1.bar(capacities, -grouped['Marginal_Total_Revenue'] + grouped['Marginal_Net_Revenue'], bar_width, color='orange')

    # Secondary y-axis for net revenue
    ax2 = ax1.twinx()
    net_revenue_line, = ax2.plot(capacities, grouped['Marginal_Net_Revenue'], marker='^', color='green')

    ax1.set_xlabel('Marginal Capacity of the BESS (MW)')
    ax1.set_ylabel('Marginal revenue and total cost (€)')
    ax2.set_ylabel('Marginal net revenue (€)')

    # Find the minimum and maximum y-limits needed
    min_y1, max_y1 = ax1.get_ylim()
    min_y2, max_y2 = ax2.get_ylim()

    common_min = min(min_y1, min_y2)  # Allow negatives
    common_max = max(max_y1, max_y2)  

    ax1.set_ylim(common_min, common_max)
    ax2.set_ylim(common_min, common_max)

    ax1.axhline(0, color='black', linewidth=1)  # Draw a horizontal line at y=0 for reference

    ax1.grid(True)

    # Custom legend formatting with separated revenue streams and colors
    legend_handles = [bars_DA, bars_Imb, bars_aFRR_res, bars_Cost, net_revenue_line]
    legend_labels = [
        "Revenue from DAM",
        "Revenue from Imbalance Market",
        "Revenue from aFRR Reserve",
        #"Revenue from aFRR Activation",
        "Annual Cost of BESS",
        "Marginal net revenue of the BESS"
    ]

    ax1.legend(legend_handles, legend_labels, loc='upper center', bbox_to_anchor=(0.5, -0.25), ncol=2, frameon=True)
    
    plt.tight_layout()
    plt.show()


def plot_aggregate_revenue_contributions(results_path):
    results_df = pd.read_excel(results_path)
    grouped_capacity = results_df.groupby("Total_Capacity").agg({
        "Marginal_DA_Revenue": "sum",
        "Marginal_Imbalance_Revenue": "sum",
        "Marginal_aFRR_Reserve_Revenue": "sum",
        #"Marginal_aFRR_Activation_Revenue": "sum"
    }).reset_index()

    grouped_capacity["Total_Revenue"] = (
        grouped_capacity["Marginal_DA_Revenue"] +
        grouped_capacity["Marginal_Imbalance_Revenue"] +
        grouped_capacity["Marginal_aFRR_Reserve_Revenue"]
        #grouped_capacity["Marginal_aFRR_Activation_Revenue"]
    )
    grouped_capacity["Total_Revenue"] = grouped_capacity["Total_Revenue"].replace(0, 1)

    grouped_capacity["DA_Share"] = grouped_capacity["Marginal_DA_Revenue"] / grouped_capacity["Total_Revenue"] * 100
    grouped_capacity["Imbalance_Share"] = grouped_capacity["Marginal_Imbalance_Revenue"] / grouped_capacity["Total_Revenue"] * 100
    grouped_capacity["aFRR_Reserve_Share"] = grouped_capacity["Marginal_aFRR_Reserve_Revenue"] / grouped_capacity["Total_Revenue"] * 100
    #grouped_capacity["aFRR_Activation_Share"] = grouped_capacity["Marginal_aFRR_Activation_Revenue"] / grouped_capacity["Total_Revenue"] * 100

    bar_width = 10
    fig, ax = plt.subplots(figsize=(8, 4))
    
    bottom = [0] * len(grouped_capacity["Total_Capacity"])  # Keeps track of stacking
    colors = ["blue", "purple", "red", "brown"]
    labels = ["DA Market", "Imbalance Market", "aFRR Reserve"]
    revenue_shares = ["DA_Share", "Imbalance_Share", "aFRR_Reserve_Share"]
    
    for share, color, label in zip(revenue_shares, colors, labels):
        bars = ax.bar(grouped_capacity["Total_Capacity"], grouped_capacity[share], width=bar_width, bottom=bottom, label=label, color=color)
        
        # Add text labels to the left of the bars
        for bar, value in zip(bars, grouped_capacity[share]):
            if value > 0:
                ax.text(bar.get_x(), bar.get_y() + bar.get_height() / 2, f"{value:.1f}%", ha='right', va='center', color='black', fontsize=10)

        bottom += grouped_capacity[share]  # Update stacking position

    ax.set_xlabel("Total Installed BESS Capacity (MW)")
    ax.set_ylabel("Revenue Share (%)")
    ax.set_title("Share of Revenue Streams for Incremental Capacity")

    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.15), ncol=3)
    ax.grid(True)
    
    plt.tight_layout()
    plt.show()


def plot_irr_and_payback():
    revenue_debug_path = os.path.join("results1", "revenue_debug.xlsx")
    
    # Load the data with IRR and Payback info
    df = pd.read_excel(revenue_debug_path)

    # Plot IRR and Payback Period vs BESS Capacity
    fig, ax1 = plt.subplots(figsize=(8, 4))

    # IRR plot on primary axis
    ax1.set_xlabel("Total BESS Capacity (MW)")
    ax1.set_ylabel("IRR (%)", color='tab:blue')
    ax1.plot(df["Total_Capacity"], df["IRR"], marker='o', color='tab:blue', label="IRR (%)")
    ax1.tick_params(axis='y', labelcolor='tab:blue')
    ax1.grid(True)

    # Payback plot on secondary axis
    ax2 = ax1.twinx()
    ax2.set_ylabel("Payback Period (Years)", color='tab:red')
    ax2.plot(df["Total_Capacity"], df["Payback_Period"], marker='s', linestyle='--', color='tab:red', label="Payback Period")
    ax2.tick_params(axis='y', labelcolor='tab:red')

    # Title and layout
    plt.title("IRR and Payback Period vs BESS Capacity")
    fig.tight_layout()
    plt.show()
