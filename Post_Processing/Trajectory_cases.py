import pandas as pd
import numpy as np
import os
from numpy_financial import irr
import matplotlib.pyplot as plt

def build_discounted_matrix_from_trajectory(bess_traj, res_traj, revenues_by_res, n_steps, discount_rate):
    lifetime = 20
    n_years = len(bess_traj) + lifetime  # 15 install years + 20 for lifetime
    n_steps = max_len  # Use full available steps from revenue data
    matrix = np.zeros((n_years, n_steps))

    res_levels = np.array([50, 60, 70, 80, 90])
    calendar_years = list(range(2025, 2025 + n_years))
    lifetime_years = list(range(n_years))
    res_full = [None] * n_years
    bess_full = [None] * n_years

    # Fill first 15 years
    for i, (bess, res) in enumerate(zip(bess_traj, res_traj)):
        res_rounded = res_levels[np.abs(res_levels - res).argmin()]
        steps = bess // 100
        value_index = steps - 1

        if value_index < len(revenues_by_res[res_rounded]):
            val = revenues_by_res[res_rounded][value_index]
            discounted_val = val / ((1 + discount_rate) ** (i)) if not np.isnan(val) else 0
            matrix[i, :steps] = int(discounted_val)

        res_full[i] = res
        bess_full[i] = bess

    # Fill extension years: all 70 columns with discounted (7000, 90%) value
    final_years_start = len(bess_traj)
    final_bess = bess_traj[-1]
    final_res = res_traj[-1]
    final_steps = final_bess // 100
    value_index = final_steps - 1
    final_res_rounded = res_levels[np.abs(res_levels - final_res).argmin()]

    if value_index < len(revenues_by_res[final_res_rounded]):
        val = revenues_by_res[final_res_rounded][value_index] 
        for k in range(20):
            i = final_years_start + k
            discounted_val = val / ((1 + discount_rate) ** (i)) if not np.isnan(val) else 0
            matrix[i, :final_steps] = int(discounted_val)  # <-- Limit to actual installed steps
            res_full[i] = final_res
            bess_full[i] = final_bess

    # === Enforce 20-year lifespan per 100 MW increment dynamically ===
    for step in range(n_steps):
        first_year_with_value = next((i for i in range(n_years) if matrix[i, step] > 0), None)
        if first_year_with_value is not None:
            end_year = first_year_with_value + 20
            if end_year < n_years:
                matrix[end_year:, step] = 0
    

    df_matrix = pd.DataFrame(matrix, columns=[f"{i+1}th 100MW" for i in range(n_steps)])
    df_matrix.insert(0, "BESS", bess_full)
    df_matrix.insert(0, "RES", res_full)
    df_matrix.insert(0, "Calendar Year", calendar_years)
    df_matrix.insert(0, "Lifetime Year", lifetime_years)


    # === Add Discounted CAPEX column ===
    capex_nominal = 70_000_000
    discounted_capex = []
    for i in range(n_years):
        if i < len(bess_traj) and bess_full[i] is not None and bess_full[i] > 0:
            capex_val = -capex_nominal / ((1 + discount_rate) ** (i))
        else:
            capex_val = 0
        discounted_capex.append(capex_val)

    df_matrix.insert(4, "Discounted CAPEX", discounted_capex)

    return df_matrix

def build_best_case_matrix(res_best, revenues_by_res, discount_rate, n_steps, years):
    all_res_levels = [50, 60, 70, 80, 90]
    bc_matrix = np.zeros((years, n_steps))
    for i in range(n_steps):
        for t in range(years):
            target_res = res_best[t] if t < len(res_best) else 90
            fallback_sequence = [target_res] + [res for res in all_res_levels if res != target_res]
            for fallback_res in fallback_sequence:
                if i < len(revenues_by_res[fallback_res]):
                    val = revenues_by_res[fallback_res][i]
                    discounted = int(val / ((1 + discount_rate) ** (i))) if not np.isnan(val) else 0
                    bc_matrix[t, i] = discounted
                    break
            else:
                bc_matrix[t, i] = 0
    return bc_matrix

def build_worst_case_matrix(revenues_by_res, discount_rate, n_steps, years):
    all_res_levels = [50, 60, 70, 80, 90]
    wc_matrix = np.zeros((years, n_steps))
    for i in range(n_steps):
        for fallback_res in all_res_levels:
            if i < len(revenues_by_res[fallback_res]):
                val = revenues_by_res[fallback_res][i]
                discounted = int(val / (1 + discount_rate) ** (0)) if not np.isnan(val) else 0
                wc_matrix[0, i] = discounted
                break
        else:
            wc_matrix[0, i] = 0
    return wc_matrix


# === Load marginal revenues ===
raw_revenues_by_res = {
    50: (df := pd.read_excel("results_case_016/revenue_debug.xlsx"))["Marginal_Net_Revenue"].values + df["Marginal_CAPEX_Cost"].values,
    70: (df := pd.read_excel("results_case_017/revenue_debug.xlsx"))["Marginal_Net_Revenue"].values + df["Marginal_CAPEX_Cost"].values,
    90: (df := pd.read_excel("results_case_018/revenue_debug.xlsx"))["Marginal_Net_Revenue"].values + df["Marginal_CAPEX_Cost"].values
}
max_len = max(len(arr) for arr in raw_revenues_by_res.values())
installed_capacities = [f"Installed {cap} MW" for cap in range(100, max_len * 100 + 1, 100)]
res_levels = [50, 60, 70, 80, 90]
res_best = [50]*1 + [90]*19
n_steps = max_len
lifetime = 20
discount_rate = 0.06

# Pad and clean
revenues_by_res = {}
for res, arr in raw_revenues_by_res.items():
    padded = np.concatenate([arr, np.zeros(max_len - len(arr))]) if len(arr) < max_len else arr
    padded[padded < 0] = 0
    revenues_by_res[res] = padded

# Interpolate for 60% and 80%
for res_target in [60, 80]:
    interpolated = []
    for i in range(max_len):
        x = np.array([50, 70, 90])
        y = np.array([revenues_by_res[50][i], revenues_by_res[70][i], revenues_by_res[90][i]])
        interp_value = np.interp(res_target, x, y)
        interpolated.append(interp_value)
    revenues_by_res[res_target] = np.array(interpolated)


res_revenue_matrix = {
    f"{res}% RES": revenues_by_res[res][:len(installed_capacities)]
    for res in res_levels
}
df_res_revenue = pd.DataFrame(res_revenue_matrix, index=installed_capacities).T


# === Define Trajectory A (Slow RES / Fast BESS growth) ===
bess_A = [100, 300, 500, 600, 1000, 1500, 2300, 3000, 3400, 4000, 4600, 4900, 5500, 6500, 7000]
res_A  = [50]*4 + [60]*3 + [70]*4 + [80]*2 + [90]*2

# === Define Trajectory B (Fast RES / Slow BESS growth) ===
bess_B = [100, 200, 300, 500, 600, 700, 800, 900, 1000, 1200, 1500, 2000, 2500, 3000, 3500]
res_B = [50]*0 + [60]*3 + [70]*3 + [80]*4 + [90]*5

# === Define Trajectory C (Fast RES / Fast BESS growth) ===
bess_C = [100, 500, 900, 1500, 2000, 2500, 3000, 3500, 4000, 4500, 5000, 5500, 6000, 6500, 7000]
res_C  = [50]*2 + [60]*2 + [70]*2 + [80]*2 + [90]*7

# === Define Trajectory D (Slow RES / Slow BESS growth) ===
bess_D = [100, 200, 300, 400, 500, 600, 700, 900, 900, 1000, 1000, 2000, 2000, 3000, 3500]
res_D  = [50]*5 + [60]*5 + [70]*2 + [80]*2 + [90]*1


# === Build matrix and export ===
discounted_matrix_A = build_discounted_matrix_from_trajectory(bess_A, res_A, revenues_by_res, max_len, discount_rate)
discounted_matrix_B = build_discounted_matrix_from_trajectory(bess_B, res_B, revenues_by_res, max_len, discount_rate)
discounted_matrix_C = build_discounted_matrix_from_trajectory(bess_C, res_C, revenues_by_res, max_len, discount_rate)
discounted_matrix_D = build_discounted_matrix_from_trajectory(bess_D, res_D, revenues_by_res, max_len, discount_rate)



# === Generate best and worst case matrices
best_case_matrix = build_best_case_matrix(res_best, revenues_by_res, discount_rate, n_steps, lifetime)
worst_case_matrix = build_worst_case_matrix(revenues_by_res, discount_rate, n_steps, lifetime)

df_best_case = pd.DataFrame(best_case_matrix, columns=[f"Installed {i*100+100} MW" for i in range(n_steps)])
df_best_case.insert(0, "Year", list(range(2025, 2025 + lifetime)))

df_worst_case = pd.DataFrame(worst_case_matrix, columns=[f"Installed {i*100+100} MW" for i in range(n_steps)])
df_worst_case.insert(0, "Year", list(range(2025, 2025 + lifetime)))



# === Compute summed revenues per step (€/100MW) ===
installed_steps = np.arange(100, max_len * 100 + 1, 100)

trajectory_A_array = discounted_matrix_A.iloc[:, 5:].values  
revenue_A_per_step = trajectory_A_array.sum(axis=0)

trajectory_B_array = discounted_matrix_B.iloc[:, 5:].values  
revenue_B_per_step = trajectory_B_array.sum(axis=0)

trajectory_C_array = discounted_matrix_C.iloc[:, 5:].values  
revenue_C_per_step = trajectory_C_array.sum(axis=0)

trajectory_D_array = discounted_matrix_D.iloc[:, 5:].values  
revenue_D_per_step = trajectory_D_array.sum(axis=0)

revenue_best_case = best_case_matrix.sum(axis=0)
revenue_worst_case = worst_case_matrix.sum(axis=0)

# === Plot ===
# === Limit to first 3000 MW ===
max_mw = 4000
max_index = max_mw // 100  # 30 steps

installed_steps_limited = installed_steps[:max_index]
revenue_A_per_step_limited = revenue_A_per_step[:max_index]
revenue_B_per_step_limited = revenue_B_per_step[:max_index]


revenue_best_case_limited = revenue_best_case[:max_index]
revenue_worst_case_limited = revenue_worst_case[:max_index]
revenue_C_per_step_limited = revenue_C_per_step[:max_index]
revenue_D_per_step_limited = revenue_D_per_step[:max_index]

# === Plot ===
plt.figure(figsize=(10, 6))
#plt.plot(installed_steps_limited, revenue_best_case_limited, label="Best Case", linewidth=2, color="blue")
plt.plot(installed_steps_limited, revenue_worst_case_limited, label="Worst Case", linewidth=2, color="orange")
plt.plot(installed_steps_limited, revenue_A_per_step_limited, label="Trajectory A - Slow RES / Fast BESS growth", linewidth=2, color="green")
plt.plot(installed_steps_limited, revenue_B_per_step_limited, label="Trajectory B - Fast RES / Slow BESS growth", linewidth=2, color="purple")
#plt.plot(installed_steps_limited, revenue_C_per_step_limited, label="Trajectory C - Fast RES / Fast BESS", linewidth=2, color="cyan")
#plt.plot(installed_steps_limited, revenue_D_per_step_limited, label="Trajectory D - Slow RES / Slow BESS", linewidth=2, color="brown")

#plt.scatter(installed_steps_limited, revenue_best_case_limited, color="blue", marker="o")
plt.scatter(installed_steps_limited, revenue_worst_case_limited, color="orange", marker="x")
plt.scatter(installed_steps_limited, revenue_A_per_step_limited, color="green", marker="s")
plt.scatter(installed_steps_limited, revenue_B_per_step_limited, color="purple", marker="d")
#plt.scatter(installed_steps_limited, revenue_C_per_step_limited, color="cyan", marker="^")
#plt.scatter(installed_steps_limited, revenue_D_per_step_limited, color="brown", marker="v")


plt.xlabel("Installed BESS Capacity at the moment of investing the next increment")
plt.ylabel("Total Discounted Net Revenue over BESS lifetime (€/100MW)")
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()


def calculate_irr_and_payback(discounted_matrix):
    n_years, n_steps = discounted_matrix.shape[0], discounted_matrix.shape[1] - 5 
    irr_list = []
    payback_list = []
    
    for step in range(n_steps):
        col_name = f"{step+1}th 100MW"
        revenue_col = discounted_matrix[col_name].values
        
        # Find year of investment
        start_idx = next((i for i, val in enumerate(revenue_col) if val > 0), None)
        if start_idx is None or start_idx + 20 > n_years:
            irr_list.append(np.nan)
            payback_list.append(np.nan)
            continue
        
        # Get the discounted CAPEX at time of investment
        capex_discounted = -discounted_matrix.iloc[start_idx]["Discounted CAPEX"]

        # Get the discounted revenue for that year
        flat_revenue = revenue_col[start_idx]

        # Construct flat revenue stream (same value for 20 years)
        cashflow = [-capex_discounted] + [flat_revenue] * 20

        # IRR
        irr_val = irr(cashflow)
        irr_list.append(round(irr_val * 100) if irr_val is not None else np.nan)

        # Payback: find when cumulative revenue >= CAPEX
        cum_revenue = np.cumsum([flat_revenue] * 20)
        payback_year = next((i + 1 for i, total in enumerate(cum_revenue) if total >= capex_discounted), np.nan)
        payback_list.append(payback_year)

    return irr_list, payback_list


irr_A, payback_A = calculate_irr_and_payback(discounted_matrix_A)
irr_B, payback_B = calculate_irr_and_payback(discounted_matrix_B)
irr_C, payback_C = calculate_irr_and_payback(discounted_matrix_C)
irr_D, payback_D = calculate_irr_and_payback(discounted_matrix_D)


# Save to Excel
df_metrics_A = pd.DataFrame({
    "Installed Capacity (100MW step)": [f"{(i+1)*100} MW" for i in range(len(irr_A))],
    "IRR": irr_A,
    "Payback Period (years)": payback_A
})

df_metrics_B = pd.DataFrame({
    "Installed Capacity (100MW step)": [f"{(i+1)*100} MW" for i in range(len(irr_B))],
    "IRR": irr_B,
    "Payback Period (years)": payback_B
})

df_metrics_C = pd.DataFrame({
    "Installed Capacity (100MW step)": [f"{(i+1)*100} MW" for i in range(len(irr_C))],
    "IRR": irr_C,
    "Payback Period (years)": payback_C
})

df_metrics_D = pd.DataFrame({
    "Installed Capacity (100MW step)": [f"{(i+1)*100} MW" for i in range(len(irr_D))],
    "IRR": irr_D,
    "Payback Period (years)": payback_D
})



output_path = "all_revenue_scenarios.xlsx"
with pd.ExcelWriter(output_path, mode="w") as writer:
    df_res_revenue.to_excel(writer, sheet_name="RES_Revenues")
    df_best_case.to_excel(writer, sheet_name="Best_Case", index=False)
    df_worst_case.to_excel(writer, sheet_name="Worst_Case", index=False)
    discounted_matrix_A.to_excel(writer, sheet_name="Trajectory_A_Discounted_Matrix", index=False)
    df_metrics_A.to_excel(writer, sheet_name="IRR_Payback_TrajectoryA", index=False)
    discounted_matrix_B.to_excel(writer, sheet_name="Trajectory_B_Discounted_Matrix", index=False)
    df_metrics_B.to_excel(writer, sheet_name="IRR_Payback_TrajectoryB", index=False)
    discounted_matrix_C.to_excel(writer, sheet_name="Trajectory_C_Discounted_Matrix", index=False)
    df_metrics_C.to_excel(writer, sheet_name="IRR_Payback_TrajectoryC", index=False)
    discounted_matrix_D.to_excel(writer, sheet_name="Trajectory_D_Discounted_Matrix", index=False)
    df_metrics_D.to_excel(writer, sheet_name="IRR_Payback_TrajectoryD", index=False)



print(f"Matrix saved to: {output_path}")
