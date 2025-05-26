from run2_BESS_optimization import bess_optimization
from run3_updatePrices import update_prices

import numpy as np
import pandas as pd
import os
import numpy_financial as npf

def run_iterations(df, max_capacity, step, output_dir,
                    BESS_duration, H_block, annualized_cost_value, annualized_CAPEX_component,
                    annualized_OPEX_component, coefficients_bess):


            coef_DAM = coefficients_bess["Day-Ahead Market"]
            coef_imb_short = coefficients_bess["Imbalance Shortage"]
            coef_imb_sur = coefficients_bess["Imbalance Surplus"]
            coef_aFRR_up_reserve = coefficients_bess["aFRR Up Contracted"]
            coef_aFRR_down_reserve = coefficients_bess["aFRR Down Contracted"]

            results = pd.DataFrame()
            revenue_debug = []
            total_capacity = 0
            total_DA_revenue = 0
            total_Imbalance_revenue = 0
            total_aFRR_reserve_revenue = 0
            total_total_revenue = 0
            total_net_revenue = 0
            imbalance_used_surplus = np.zeros(len(df))
            imbalance_used_shortage = np.zeros(len(df))
            aFRR_used_down = np.zeros(len(df))
            aFRR_used_up = np.zeros(len(df))

            os.makedirs(output_dir, exist_ok=True)
            initial_prices_path = os.path.join(output_dir, "initial_extrapolated_prices.xlsx")
            df.to_excel(initial_prices_path, index=False)

            df["Historical_DAM_Price"] = df["Extrapolated_DAM_Price"]
            df["Historical_Imbalance_Surplus_Price"] = df["Extrapolated_Imbalance_Surplus_Price"]
            df["Historical_Imbalance_Shortage_Price"] = df["Extrapolated_Imbalance_Shortage_Price"]
            df["Historical_aFRR_Up_Price_reserve"] = df["Extrapolated_aFRR_Up_Price_reserve"]
            df["Historical_aFRR_Down_Price_reserve"] = df["Extrapolated_aFRR_Down_Price_reserve"]

            # Load market volumes
            volume_aFRR_up_reserve = pd.read_excel("aFRR_hourly_prices_Up.xlsx")["Volume Reserve (MW)"].values
            volume_aFRR_down_reserve = pd.read_excel("aFRR_hourly_prices_Down.xlsx")["Volume Reserve (MW)"].values
            volume_imb_surplus = pd.read_excel("settled_imbalance_volumes.xlsx", sheet_name="MWh")["Surplus (MWh)"].values
            volume_imb_shortage = pd.read_excel("settled_imbalance_volumes.xlsx", sheet_name="MWh")["Shortage (MWh)"].values

             # Load the implicit balance volume surplus and shortage
            settled_imbalance_surplus = pd.read_excel("settled_imbalance_volumes.xlsx", sheet_name="MWh")  # Load imbalance volume surplus
            settled_imbalance_shortage = pd.read_excel("settled_imbalance_volumes.xlsx", sheet_name="MWh")  # Load imbalance volume shortage
            volume_imb_surplus = settled_imbalance_surplus["Surplus (MWh)"].values
            volume_imb_shortage = settled_imbalance_shortage["Shortage (MWh)"].values

            first_run_flag = True
            SoC_previous = None

            # Initialize holder variables
            saturation_point = None
            saturation_investment = None
            saturation_net_revenue = None

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
                    "Marginal_CAPEX_Cost": annualized_CAPEX_component * step, 
                    "Marginal_OPEX_Cost": annualized_OPEX_component * step,
                    "Cumulative_DA_Revenue": total_DA_revenue,
                    "Cumulative_Imbalance_Revenue": total_Imbalance_revenue,
                    "Cumulative_aFRR_Reserve_Revenue": total_aFRR_reserve_revenue,
                    "Cumulative_Total_Revenue": total_total_revenue,
                    "Cumulative_Net_Revenue": total_net_revenue
                })
                
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
                    "aFRR_Down_Price_reserve": P_aFRR_down_reserve.values,
                    "Marginal_CAPEX_Cost": annualized_CAPEX_component * step, 
                    "Marginal_OPEX_Cost": annualized_OPEX_component * step,
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

                if saturation_point is None and marginal_net_revenue <= 0:
                    saturation_point = total_capacity
                    print(f"\n📌 Saturation point found at {saturation_point} MW")

                if saturation_point is not None and total_capacity >= saturation_point + 400:
                    print(f"⛔ Reached limit after saturation: {total_capacity} MW")
                    break

            for i in range(1, len(revenue_debug)):
                prev = revenue_debug[i - 1]
                curr = revenue_debug[i]
                if prev["Marginal_Net_Revenue"] > 0 and curr["Marginal_Net_Revenue"] <= 0:
                    cap1, rev1 = prev["Total_Capacity"], prev["Marginal_Net_Revenue"]
                    cap2, rev2 = curr["Total_Capacity"], curr["Marginal_Net_Revenue"]
                    # Linear interpolation
                    saturation_point = cap1 + (0 - rev1) * (cap2 - cap1) / (rev2 - rev1)

                    print(f"\n📌 Financial saturation point (marginal net revenue = 0) reached at: {saturation_point:.2f} MW")
                    break


            final_results_path = os.path.join(output_dir, "final_results1.xlsx")
            results.to_excel(final_results_path, index=False)


            return saturation_point
