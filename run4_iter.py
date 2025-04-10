import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import numpy_financial as npf
from run1_extrapolation import load_initial_prices
from run2_BESS_optimization import bess_optimization
from run3_updatePrices import update_prices
from run5_Plotting import plot_revenues, plot_aggregate_revenue_contributions, plot_irr_and_payback
from coef_DA import bess_coefficients_DA
from coef_imb_short import bess_coefficients_imb_short
from coef_imb_surplus import bess_coefficients_imb_surplus
from coef_aFRR_up import bess_coefficients_aFRR_up
from coef_aFRR_down import bess_coefficients_aFRR_down
from res_coeff_DA import res_coefficients_DA
from res_coeff_imb_short import res_coefficients_imb_short
from res_coeff_imb_sur import res_coefficients_imb_surplus
from res_coef_aFRR_up import res_coefficients_aFRR_up
from res_coef_aFRR_down import res_coefficients_aFRR_down


def main():
    # Define cost parameters
    CAPEX = 1_000_000  # € per MW
    OPEX = 32_000    # € per MW/year (add grid costs around 60k, which accounts for 60-70% of the total OPEX, loan interest rate, how long would the loan take to repay)
    lifetime = 20    # years
    discount_rate = 0.06  

    # Compute annualized cost
    annualized_cost_value = (discount_rate * (1 + discount_rate) ** lifetime) / ((1 + discount_rate) ** lifetime - 1) * CAPEX + OPEX

    # Renewable energy and price parameters
    RES_share_current = 0.5  # Current share of renewable energy sources
    RES_share_future = 0.7  # Future share of renewable energy sources
    total_demand_current =  125_000_000 # Total demand (MWh/year)
    growth_rate = 0.05  # 5% growth rate
    total_demand_future = total_demand_current * (1 + growth_rate)
    RES_current = total_demand_current * RES_share_current # Current renewable energy sources (MWh/year)
    RES_future =  total_demand_future * RES_share_future # Future renewable energy sources (MWh)
    BESS_duration = 1  # hours
    H_block = 4  # Hour block for aFRR reserve


    # Extract BESS capacity coefficients - €/MWh per MW of installed BESS
    coefficients_bess = {
        "Day-Ahead Market": bess_coefficients_DA("bess_price_data.xlsx"),
        "Imbalance Shortage": bess_coefficients_imb_short("bess_price_data.xlsx"),
        "Imbalance Surplus": bess_coefficients_imb_surplus("bess_price_data.xlsx"),
        "aFRR Up Contracted": bess_coefficients_aFRR_up("bess_price_data.xlsx"),
        "aFRR Down Contracted": bess_coefficients_aFRR_down("bess_price_data.xlsx"),
    }

    # Extract RES coefficients - €/MWh per 1 % RES share
    coefficients_res = {
        "Day-Ahead Market": res_coefficients_DA("bess_price_data.xlsx"),
        "Imbalance Shortage": res_coefficients_imb_short("bess_price_data.xlsx"),
        "Imbalance Surplus": res_coefficients_imb_surplus("bess_price_data.xlsx"),
        "aFRR Up Contracted": res_coefficients_aFRR_up("bess_price_data.xlsx"),
        "aFRR Down Contracted": res_coefficients_aFRR_down("bess_price_data.xlsx"),
    }

    # Assign coefficients to appropriate variables
    coef_DAM = coefficients_bess.get("Day-Ahead Market", 0)
    coef_imb_short = coefficients_bess.get("Imbalance Shortage", 0)
    coef_imb_sur = coefficients_bess.get("Imbalance Surplus", 0)
    coef_aFRR_up_reserve = coefficients_bess.get("aFRR Up Contracted", 0)
    coef_aFRR_down_reserve = coefficients_bess.get("aFRR Down Contracted", 0)

    res_DAM = coefficients_res.get("Day-Ahead Market", 0)
    res_imb_short = coefficients_res.get("Imbalance Shortage", 0)
    res_imb_sur = coefficients_res.get("Imbalance Surplus", 0)
    res_aFRR_up_reserve = coefficients_res.get("aFRR Up Contracted", 0)
    res_aFRR_down_reserve = coefficients_res.get("aFRR Down Contracted", 0)

    df = load_initial_prices(RES_current, RES_future, total_demand_current, total_demand_future, res_DAM, res_imb_short, res_imb_sur, res_aFRR_up_reserve, res_aFRR_down_reserve)

    def run_iterations(df, max_capacity, step):
        results = pd.DataFrame()
        revenue_debug = []  # Store debug information for Excel
        total_capacity = 0  # Initial total capacity by step
        total_DA_revenue = 0
        total_Imbalance_revenue = 0
        total_aFRR_reserve_revenue = 0
        total_total_revenue = 0
        total_net_revenue = 0
        imbalance_used_surplus = np.zeros(len(df))
        imbalance_used_shortage = np.zeros(len(df))
        aFRR_used_down = np.zeros(len(df))
        aFRR_used_up = np.zeros(len(df))

        # Excel initial prices
        output_dir = os.path.join(os.getcwd(), "results1")
        os.makedirs(output_dir, exist_ok=True)
        initial_prices_path = os.path.join(output_dir, "initial_extrapolated_prices.xlsx")
        df.to_excel(initial_prices_path, index=False)

        # Initialize historical prices
        df["Historical_DAM_Price"] = df["Extrapolated_DAM_Price"]
        df["Historical_Imbalance_Surplus_Price"] = df["Extrapolated_Imbalance_Surplus_Price"]
        df["Historical_Imbalance_Shortage_Price"] = df["Extrapolated_Imbalance_Shortage_Price"]
        df["Historical_aFRR_Up_Price_reserve"] = df["Extrapolated_aFRR_Up_Price_reserve"]
        df["Historical_aFRR_Down_Price_reserve"] = df["Extrapolated_aFRR_Down_Price_reserve"]

        # Load the aFRR volume up and down reserve
        aFRR_up_reserve = pd.read_excel("aFRR_hourly_prices_Up.xlsx", sheet_name="Sheet1")  # Load aFRR Up volume reserve
        aFRR_down_reserve = pd.read_excel("aFRR_hourly_prices_Down.xlsx", sheet_name="Sheet1")  # Load aFRR Down volume reserve
        volume_aFRR_up_reserve = aFRR_up_reserve["Volume Reserve (MW)"].values
        volume_aFRR_down_reserve = aFRR_down_reserve["Volume Reserve (MW)"].values

        # Load the implicit balance volume surplus and shortage
        settled_imbalance_surplus = pd.read_excel("settled_imbalance_volumes.xlsx", sheet_name="MWh")  # Load imbalance volume surplus
        settled_imbalance_shortage = pd.read_excel("settled_imbalance_volumes.xlsx", sheet_name="MWh")  # Load imbalance volume shortage
        volume_imb_surplus = settled_imbalance_surplus["Surplus (MWh)"].values
        volume_imb_shortage = settled_imbalance_shortage["Shortage (MWh)"].values

        # Global variable to track if it's the first iteration
        first_run_flag = True  
        SoC_previous = None

        while total_capacity + step <= max_capacity:
            total_capacity += step
            print(f"Iteration {total_capacity}MW")

            # Extract current prices
            P_DA_t = df["Extrapolated_DAM_Price"]
            P_imb_t_sur = df["Extrapolated_Imbalance_Surplus_Price"]
            P_imb_t_short = df["Extrapolated_Imbalance_Shortage_Price"]
            P_aFRR_up_reserve = df["Extrapolated_aFRR_Up_Price_reserve"]
            P_aFRR_down_reserve = df["Extrapolated_aFRR_Down_Price_reserve"]


            # Run BESS optimization
            charging_DA, discharging_DA, charging_imb, discharging_imb, charging_aFRR, discharging_aFRR, marginal_DA_revenue, marginal_Imbalance_revenue, marginal_aFRR_reserve_revenue, marginal_total_revenue, marginal_net_revenue, SoC_final = bess_optimization(
                P_DA_t, P_imb_t_sur, P_imb_t_short, P_aFRR_up_reserve, P_aFRR_down_reserve,
                volume_aFRR_up_reserve, volume_aFRR_down_reserve, volume_imb_surplus, volume_imb_shortage, 
                step, annualized_cost_value, BESS_duration, first_run_flag, SoC_previous, 
                imbalance_used_surplus, imbalance_used_shortage, aFRR_used_down, aFRR_used_up, H_block
            )

            # After the first iteration, update the flag so it's False for future iterations
            first_run_flag = False
            SoC_previous = SoC_final

            # Extract the **actual** imbalance and AFRR participation
            imbalance_used_shortage[:] = np.array(discharging_imb[step])  # Energy discharged into the surplus market
            imbalance_used_surplus[:] = np.array(charging_imb[step])  # Energy charged from the shortage market
            aFRR_used_down[:] = np.array(charging_aFRR[step])  # Energy charged from the aFRR
            aFRR_used_up[:] = np.array(discharging_aFRR[step])  # Energy discharged into the aFRR

            # Reduce imbalance/aFRR volumes for the next iteration based on actual BESS participation
            volume_imb_surplus[:] = np.maximum(volume_imb_surplus - imbalance_used_surplus, 0)
            volume_imb_shortage[:] = np.maximum(volume_imb_shortage - imbalance_used_shortage, 0)
            volume_aFRR_up_reserve[:] = np.maximum(volume_aFRR_up_reserve - aFRR_used_up, 0)
            volume_aFRR_down_reserve[:] = np.maximum(volume_aFRR_down_reserve - aFRR_used_down, 0)

            total_DA_revenue += marginal_DA_revenue
            total_Imbalance_revenue += marginal_Imbalance_revenue
            total_aFRR_reserve_revenue += marginal_aFRR_reserve_revenue
            total_total_revenue += marginal_total_revenue
            total_net_revenue += marginal_net_revenue

            # Store debug values in a list (to convert to a DataFrame later)
            revenue_debug.append({
                "Step_Size": step,
                "Total_Capacity": total_capacity,
                "Marginal_DA_Revenue": marginal_DA_revenue,
                "Marginal_Imbalance_Revenue": marginal_Imbalance_revenue,
                "Marginal_aFRR_Reserve_Revenue": marginal_aFRR_reserve_revenue,
                "Marginal_Total_Revenue": marginal_total_revenue,
                "Marginal_Net_Revenue": marginal_net_revenue,
                "Cumulative_DA_Revenue": total_DA_revenue,
                "Cumulative_Imbalance_Revenue": total_Imbalance_revenue,
                "Cumulative_aFRR_Reserve_Revenue": total_aFRR_reserve_revenue,
                "Cumulative_Total_Revenue": total_total_revenue,
                "Cumulative_Net_Revenue": total_net_revenue
            })
            
            # Compute IRR and Payback for each iteration
            initial_investment_iter = CAPEX * total_capacity
            cash_flows_iter = [-initial_investment_iter] + [total_net_revenue] * lifetime
            irr_iter = npf.irr(cash_flows_iter)
            payback_iter = initial_investment_iter / total_net_revenue if total_net_revenue > 0 else None

            # Add to the last entry in revenue_debug
            revenue_debug[-1]["IRR"] = irr_iter * 100
            revenue_debug[-1]["Payback_Period"] = payback_iter

            # Convert optimization results to arrays
            charging_DA_vec = np.array(charging_DA[step])
            discharging_DA_vec = np.array(discharging_DA[step])
            charging_imb_vec = np.array(charging_imb[step])
            discharging_imb_vec = np.array(discharging_imb[step])
            charging_aFRR_vec = np.array(charging_aFRR[step])
            discharging_aFRR_vec = np.array(discharging_aFRR[step])

            # Update prices
            update_prices(df, charging_DA_vec, discharging_DA_vec, charging_imb_vec, discharging_imb_vec, charging_aFRR_vec, discharging_aFRR_vec, 
                          coef_DAM, coef_imb_short, coef_imb_sur, coef_aFRR_up_reserve, coef_aFRR_down_reserve, step)

            # Save updated prices
            filename = os.path.join(output_dir, f"updated_prices_capacity_{total_capacity}.xlsx")
            df.to_excel(filename, index=False)
            
            # Append results
            new_results = pd.DataFrame({
                "Total_Capacity": [total_capacity] * len(P_DA_t),
                "Time": np.arange(1, len(P_DA_t) + 1),
                "Charging_DA": charging_DA_vec,
                "Discharging_DA": discharging_DA_vec,
                "Charging_Imb": charging_imb_vec,
                "Discharging_Imb": discharging_imb_vec,
                "Charging_aFRR": charging_aFRR_vec,
                "Discharging_aFRR": discharging_aFRR_vec,
                "Marginal_DA_Revenue": [marginal_DA_revenue] * len(P_DA_t),
                "Marginal_Imbalance_Revenue": [marginal_Imbalance_revenue] * len(P_DA_t),
                "Marginal_aFRR_Reserve_Revenue": [marginal_aFRR_reserve_revenue] * len(P_DA_t),
                "Marginal_Total_Revenue": [marginal_total_revenue] * len(P_DA_t),
                "Marginal_Net_Revenue": [marginal_net_revenue] * len(P_DA_t),
                "Cumulative_Total_Revenue": [total_total_revenue] * len(P_DA_t),
                "Cumulative_Net_Revenue": [total_net_revenue] * len(P_DA_t),
                "DAM_Price": P_DA_t.values,
                "Imbalance_Price_Surplus": P_imb_t_sur.values,
                "Imbalance_Price_Shortage": P_imb_t_short.values,
                "aFRR_Up_Price_reserve": P_aFRR_up_reserve.values,
                "aFRR_Down_Price_reserve": P_aFRR_down_reserve.values
            })

            results = pd.concat([results, new_results], ignore_index=True)

            # Save revenue debugging information to Excel
            revenue_debug_df = pd.DataFrame(revenue_debug)
            revenue_debug_path = os.path.join(output_dir, "revenue_debug.xlsx")
            revenue_debug_df.to_excel(revenue_debug_path, index=False)

            # Update historical prices
            df["Historical_DAM_Price"] = df["Extrapolated_DAM_Price"]
            df["Historical_Imbalance_Surplus_Price"] = df["Extrapolated_Imbalance_Surplus_Price"]
            df["Historical_Imbalance_Shortage_Price"] = df["Extrapolated_Imbalance_Shortage_Price"]
            df["Historical_aFRR_Up_Price_reserve"] = df["Extrapolated_aFRR_Up_Price_reserve"]
            df["Historical_aFRR_Down_Price_reserve"] = df["Extrapolated_aFRR_Down_Price_reserve"]

        # Find financial saturation point
        saturation_point = None
        for i in range(1, len(revenue_debug)):
            prev = revenue_debug[i - 1]
            curr = revenue_debug[i]
            if prev["Marginal_Net_Revenue"] > 0 and curr["Marginal_Net_Revenue"] <= 0:
                cap1, rev1 = prev["Total_Capacity"], prev["Marginal_Net_Revenue"]
                cap2, rev2 = curr["Total_Capacity"], curr["Marginal_Net_Revenue"]
                # Linear interpolation
                saturation_point = cap1 + (0 - rev1) * (cap2 - cap1) / (rev2 - rev1)
                print(f"\n Financial saturation point reached at: {saturation_point:.2f} MW\n")
                break


        final_results_path = os.path.join(output_dir, "final_results1.xlsx")
        results.to_excel(final_results_path, index=False)

        # Final investment and financial metrics
        initial_investment = CAPEX * total_capacity
        cash_flows = [-initial_investment] + [total_net_revenue] * lifetime
        irr = npf.irr(cash_flows)
        payback_period = initial_investment / total_net_revenue if total_net_revenue > 0 else None

        # 4b. Discounted Payback Period
        discount_rate = 0.06
        discounted_cash_flows = [total_net_revenue / (1 + discount_rate) ** t for t in range(1, lifetime + 1)]
        cumulative_discounted = np.cumsum(discounted_cash_flows)
        discounted_payback = next((i + 1 for i, total in enumerate(cumulative_discounted) if total >= initial_investment), None)

        # Print metrics
        print(f"\nInternal Rate of Return (IRR): {irr * 100:.2f}%")
        print(f"Payback Period: {payback_period:.2f} years")
        print(f"Discounted Payback Period: {discounted_payback} years")

        # Save metrics to Excel
        financial_metrics = pd.DataFrame({
            "Total_Capacity_MW": [total_capacity],
            "Initial_Investment_€": [initial_investment],
            "Net_Annual_Revenue_€": [total_net_revenue],
            "IRR": [irr],
            "Payback_Period_years": [payback_period],
            "Discounted_Payback_Period_years": [discounted_payback]
        })

        financial_metrics_path = os.path.join(output_dir, "financial_metrics.xlsx")
        financial_metrics.to_excel(financial_metrics_path, index=False)

        return step

    # Run full process
    run_iterations(df, 3000, 100)

    # Define results file path
    results_path = "results1/final_results1.xlsx"

    # Call the plotting functions
    plot_revenues(results_path)
    plot_aggregate_revenue_contributions(results_path)
    plot_irr_and_payback()

if __name__ == "__main__":
    main()

