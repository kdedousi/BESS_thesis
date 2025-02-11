import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from run1_extrapolation import load_initial_prices
from run2_BESS_optimization import bess_optimization
from run3_updatePrices import update_prices

# Function to run multiple capacity iterations
def run_iterations(df, max_capacity, step, SoC_init, annualized_cost_value, bess_optimization, price_per_mwh_bess):
    results = pd.DataFrame()
    capacity = 50  # Initial capacity

    # Create results directory
    output_dir = os.path.join(os.getcwd(), "results")
    os.makedirs(output_dir, exist_ok=True)

    # Save initial prices
    initial_prices_path = os.path.join(output_dir, "initial_extrapolated_prices.xlsx")
    df.to_excel(initial_prices_path, index=False)

    num_days = len(df) // 24  # Total number of days
    
    while capacity <= max_capacity:
        SoC_day = SoC_init  # Reset SoC for each capacity iteration
        
        for day in range(num_days):
            start_idx = day * 24
            end_idx = start_idx + 24

        # Get updated prices
        P_DA_t = df["Extrapolated_DAM_Price"]
        P_imb_t_ω = df["Extrapolated_Imbalance_Price"]

        # Run BESS optimization
        charging_DA, discharging_DA, charging_imb, discharging_imb, ancillary_output, electricity_revenue, total_revenue, net_revenue = bess_optimization(
            P_DA_t, P_imb_t_ω, np.full(len(P_DA_t), 50), SoC_init, capacity, annualized_cost_value
        )

        # Convert JuMP variables to lists (assuming bess_optimization returns lists/arrays)
        charging_DA_vec = np.array(charging_DA[capacity])
        discharging_DA_vec = np.array(discharging_DA[capacity])
        charging_imb_vec = np.array(charging_imb[capacity])
        discharging_imb_vec = np.array(discharging_imb[capacity])

        # Update prices
        update_prices(df, charging_DA_vec, discharging_DA_vec, charging_imb_vec, discharging_imb_vec, price_per_mwh_bess)

        # Save updated prices
        filename = os.path.join(output_dir, f"updated_prices_capacity_{capacity}.xlsx")
        df.to_excel(filename, index=False)

        # Append results
        new_results = pd.DataFrame({
            "Capacity": [capacity] * len(P_DA_t),
            "Time": np.arange(1, len(P_DA_t) + 1),
            "Charging_DA": charging_DA_vec,
            "Discharging_DA": discharging_DA_vec,
            "Charging_Imb": charging_imb_vec,
            "Discharging_Imb": discharging_imb_vec,
            "Electricity_Revenue": [electricity_revenue] * len(P_DA_t),
            "Total_Revenue": [total_revenue] * len(P_DA_t),
            "Net_Revenue": [net_revenue] * len(P_DA_t),
            "DAM_Price": P_DA_t.values,
            "Imbalance_Price": P_imb_t_ω.values
        })

        results = pd.concat([results, new_results], ignore_index=True)

        # Update SoC_init (assuming max is based on constraints)
        SoC_min = 0  # Define SoC_min if applicable
        SoC_init = max(SoC_min, charging_DA_vec[-1] - discharging_DA_vec[-1])

        df["Historical_DAM_Price"] = df["Extrapolated_DAM_Price"]
        df["Historical_Imbalance_Price"] = df["Extrapolated_Imbalance_Price"]

        capacity += step

    # Plotting
    grouped = results.groupby('Capacity').agg({
        'Electricity_Revenue': 'mean',
        'Total_Revenue': 'mean',
        'Net_Revenue': 'mean'
    }).reset_index()

    # Calculate ancillary revenue and annual cost
    grouped['Ancillary_Revenue'] = grouped['Total_Revenue'] - grouped['Electricity_Revenue']
    grouped['Annual_Cost'] = grouped['Total_Revenue'] - grouped['Net_Revenue']

    # Plotting
    fig, ax1 = plt.subplots(figsize=(8, 4))

    # Bar chart for revenues and costs
    bar_width = 10.0
    capacities = grouped['Capacity']

    p1 = ax1.bar(capacities, grouped['Electricity_Revenue'], bar_width, label='Annual revenue from electricity', color='blue')
    p2 = ax1.bar(capacities, grouped['Ancillary_Revenue'], bar_width, bottom=grouped['Electricity_Revenue'], label='Annual revenue from ancillary', color='red')
    p3 = ax1.bar(capacities, -grouped['Annual_Cost'], bar_width, label='Annual cost of the BESS', color='orange')

    # Line plot for net revenue
    ax2 = ax1.twinx()
    ax2.plot(capacities, grouped['Net_Revenue'], marker='^', color='green', label='Annual net revenue of the BESS')

    # Labels and legend
    ax1.set_xlabel('Capacity of the BESS (MW)')
    ax1.set_ylabel('Annual revenue and annual cost (€)')
    ax2.set_ylabel('Annual net revenue (€)')

    # Legends
    bars = [p1, p2, p3]
    labels = [bar.get_label() for bar in bars]
    lines, line_labels = ax2.get_legend_handles_labels()

    ax1.legend(bars + lines, labels + line_labels, loc='upper center', bbox_to_anchor=(0.5, -0.1), ncol=2)

    # Grid and layout
    ax1.grid(True)
    plt.tight_layout()

    # Show plot
    plt.show()

    # Save final results
    final_results_path = os.path.join(output_dir, "final_results.xlsx")
    results.to_excel(final_results_path, index=False)
    print(f"Final results saved to '{final_results_path}'")


# Function to compute annualized cost
def annualized_cost(capex, opex, lifetime, discount_rate):
    annuity_factor = (discount_rate * (1 + discount_rate) ** lifetime) / ((1 + discount_rate) ** lifetime - 1)
    return capex * annuity_factor + opex

# Define cost parameters
CAPEX = 375_000  # € per MWh (1.5M €/MW for 4-hour battery -> 1.5M/4)
OPEX = 7_500     # € per MWh/year
lifetime = 30    # years
discount_rate = 0.05  

# Compute annualized cost
annualized_cost_value = annualized_cost(CAPEX, OPEX, lifetime, discount_rate)

# Print the annualized cost value
print(f"Annualized Cost Value: {annualized_cost_value}")

RES_current = 50_000_000 # Current renewable energy sources (MWh)
RES_future = 60_000_000 # Future renewable energy sources (MWh)
price_per_mwh_res = -0.00075 / 1000 # Price per MWh of RES change
price_per_mwh_bess = 0.02 # Price per MWh of BESS

# Load initial prices (you need to define load_initial_prices)
df = load_initial_prices(RES_current, RES_future, price_per_mwh_res)

# Run iterations (you need to define bess_optimization)
run_iterations(df, 50.0, 50.0, 50.0, annualized_cost_value, bess_optimization, price_per_mwh_bess)

print("Results saved to 'final_results.xlsx'")
