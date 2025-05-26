import os
import numpy_financial as npf 
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import itertools
from run1_extrapolation import load_initial_prices
from run5_Plotting import plot_revenues, plot_aggregate_revenue_contributions
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
from RES_iterations import run_iterations

def main():
    total_demand_current = 125_000_000
    growth_rate = 0.03
    lifetime = 20
    discount_rate = 0.06
    BESS_duration = 4
    H_block = 4

    # Load static coefficients
    coefficients_bess = {
        "Day-Ahead Market": bess_coefficients_DA("bess_price_data.xlsx"),
        "Imbalance Shortage": bess_coefficients_imb_short("bess_price_data.xlsx"),
        "Imbalance Surplus": bess_coefficients_imb_surplus("bess_price_data.xlsx"),
        "aFRR Up Contracted": bess_coefficients_aFRR_up("bess_price_data.xlsx"),
        "aFRR Down Contracted": bess_coefficients_aFRR_down("bess_price_data.xlsx"),
    }

    coefficients_res = {
        "Day-Ahead Market": res_coefficients_DA("bess_price_data.xlsx"),
        "Imbalance Shortage": res_coefficients_imb_short("bess_price_data.xlsx"),
        "Imbalance Surplus": res_coefficients_imb_surplus("bess_price_data.xlsx"),
        "aFRR Up Contracted": res_coefficients_aFRR_up("bess_price_data.xlsx"),
        "aFRR Down Contracted": res_coefficients_aFRR_down("bess_price_data.xlsx"),
    }

    # Define all combinations
    RES_list = [0.7] # 3 cases of RES share
    CAPEX_list = [500_000] # 2 cases of CAPEX 
    OPEX_list = [30_000] # 3 cases of OPEX, current, with grid costs contract, without grid costs

    full_grid = list(itertools.product(CAPEX_list, OPEX_list, RES_list))

    saturation_summary_rows = []

    for idx, (CAPEX, OPEX, RES_share) in enumerate(full_grid, start=1):
        t = {0.5: 0, 0.7: 6, 0.9: 16}[RES_share]  # map RES share to time horizon
        output_dir = f"results_case_{idx:03d}"

        annualized_CAPEX_component = (discount_rate * (1 + discount_rate) ** lifetime) / ((1 + discount_rate) ** lifetime - 1) * CAPEX
        annualized_OPEX_component = OPEX
        annualized_cost_value = annualized_CAPEX_component + annualized_OPEX_component

        total_demand_future = total_demand_current * (1 + growth_rate) ** t
        RES_current = total_demand_current * 0.5
        RES_future = total_demand_future * RES_share

        df = load_initial_prices(
            RES_current, RES_future,
            total_demand_current, total_demand_future,
            coefficients_res["Day-Ahead Market"],
            coefficients_res["Imbalance Shortage"],
            coefficients_res["Imbalance Surplus"],
            coefficients_res["aFRR Up Contracted"],
            coefficients_res["aFRR Down Contracted"]
        )

        print(f"\n🚀 Running case {idx:03d} — CAPEX={CAPEX}, OPEX={OPEX}, RES={RES_share}, t={t} → {output_dir}")
        saturation_point = run_iterations(
            df=df,
            max_capacity=15000,
            step=100,
            output_dir=output_dir,
            BESS_duration=BESS_duration,
            H_block=H_block,
            annualized_cost_value=annualized_cost_value,
            annualized_CAPEX_component=annualized_CAPEX_component,
            annualized_OPEX_component=annualized_OPEX_component,
            coefficients_bess=coefficients_bess
        )

        # Derive symbolic labels
        res_symbol = {0.5: "A1", 0.7: "A2", 0.9: "A3"}[RES_share]
        capex_symbol = {900_000: "B1", 700_000: "B2", 500_000: "B3"}[CAPEX]
        opex_symbol = {130_000: "C1", 80_000: "C2", 30_000: "C3"}[OPEX]
        combo_str = f"{res_symbol} - {capex_symbol} - {opex_symbol}"

        # Store saturation summary
        saturation_summary_rows.append({
            "Case": idx,
            "Combination": combo_str,
            "Saturation_Point_MW": saturation_point
        })

        results_path = os.path.join(output_dir, "final_results1.xlsx")
        label = f"Case {idx:03d} — RES {int(RES_share*100)}%"
        plot_revenues(results_path, label)
        plot_aggregate_revenue_contributions(results_path, label)


    pd.DataFrame(saturation_summary_rows).to_excel("saturation_summary.xlsx", index=False)

    print("\nAll cases completed and saved.")

if __name__ == "__main__":
    main()