using JuMP
using Gurobi
using Plots 
using Pkg
using XLSX

# Load the Excel file
xf = XLSX.readxlsx("extrapolated_prices_stable_res.xlsx")
sh = xf["Sheet1"]
sheet_data = sh[:]
P_DA_t = sheet_data[2:end, 3]

# Parameters
T = 1:length(P_DA_t)  # Daily time steps for one year
Ω = 1:3  # Scenarios
π = [0.1 for _ in Ω]  # Equal probabilities for 10 scenarios

#P_DA_t = rand(50:100, 365)  # Random daily prices between 50 and 100 for a year
P_imb_t_ω = [rand(40:110, 365) for _ in Ω]  # Imbalance prices for each scenario
η_c = 0.95      # Charging efficiency
η_d = 0.95      # Discharging efficiency
Δt = 1.0        # Time step (1 day)
SoC_init = 50.0 # Initial state of charge (in kWh)
SoC_min = 10.0   # Minimum state of charge (in kWh)
SoC_max = 90.0 # Maximum state of charge (in kWh)
Pd_max = 50.0   # Maximum discharge power (kW)
Pc_max = 50.0   # Maximum charge power (kW)

# Model
model = Model(optimizer_with_attributes(Gurobi.Optimizer, "OutputFlag" => 0)) 

# Decision variables
@variable(model, e_DA_t_plus[t in T] >= 0)  # Day-ahead energy bought
@variable(model, e_DA_t_minus[t in T] >= 0) # Day-ahead energy sold
@variable(model, e_imb_plus[t in T, ω in Ω] >= 0) # Imbalance energy bought
@variable(model, e_imb_minus[t in T, ω in Ω] >= 0) # Imbalance energy sold
@variable(model, z_DA_t[t in T], Bin)  # Binary for charging/discharging in DA
@variable(model, z_t[t in T], Bin)     # Binary for charging/discharging in imbalance
@variable(model, SoC_min <= SoC[t in T] <= SoC_max)  # State of charge (kWh)

# Objective function: Maximize expected revenues
@objective(model, Max,
    sum(π[ω] * sum(P_DA_t[t] * (e_DA_t_plus[t] - e_DA_t_minus[t]) +
    P_imb_t_ω[ω][t] * (e_imb_plus[t, ω] - e_imb_minus[t, ω]) for t in T) for ω in Ω)
)

# Constraints
@constraint(model, [t in T[1:end-1]],
    SoC[t+1] == SoC[t] + e_DA_t_plus[t] * η_c - e_DA_t_minus[t] / η_d)

@constraint(model, SoC[1] == SoC_init)  # Initial state of charge

@constraint(model, [t in T], e_DA_t_plus[t] <= Pd_max * z_DA_t[t] * Δt)  # Max DA charge
@constraint(model, [t in T], e_DA_t_minus[t] <= Pc_max * (1 - z_DA_t[t]) * Δt)  # Max DA discharge
@constraint(model, [t in T, ω in Ω], e_imb_plus[t, ω] <= Pd_max * z_t[t] * Δt)  # Max imbalance charge
@constraint(model, [t in T, ω in Ω], e_imb_minus[t, ω] <= Pc_max * (1 - z_t[t]) * Δt)  # Max imbalance discharge

# Solve the model
optimize!(model)

# Display results
using Printf

@printf("Objective value: %.2f\n", objective_value(model))

e_DA_t_plus_array = collect(round.(value.(e_DA_t_plus), digits=2))
println("e_DA_t_plus: ", e_DA_t_plus_array)

e_DA_t_minus_array = collect(round.(value.(e_DA_t_minus), digits=2))
println("e_DA_t_minus: ", e_DA_t_minus_array)

SoC_array = collect(round.(value.(SoC), digits=2))
println("SoC: ", SoC_array)

# Plot results
p1 = plot(T, e_DA_t_plus_array, label="Day-Ahead Energy Bought", xlabel="Days", ylabel="Energy (kWh)", title="Energy Bought Over a Year", lw=2)
display(p1)

p2 = plot(T, e_DA_t_minus_array, label="Day-Ahead Energy Sold", xlabel="Days", ylabel="Energy (kWh)", title="Energy Sold Over a Year", lw=2, color=:orange)
display(p2)

p3 = plot(T, SoC_array, label="State of Charge", xlabel="Days", ylabel="Energy (kWh)", title="State of Charge Over a Year", lw=2, color=:green)
display(p3)

