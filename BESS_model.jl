using JuMP
using Gurobi  # Gurobi solver

# Parameters
π = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1]  # Equal probabilities for 10 scenarios
P_DA_t = rand(50:100, 96)  # Random day-ahead prices between 50 and 100
P_imb_t_ω = [rand(40:110, 96) for _ in 1:10]  # Random imbalance prices for 10 scenarios
η_c = 0.95      # Charging efficiency
η_d = 0.95      # Discharging efficiency
Δt = 1.0        # Time step
SoC_init = 50.0 # Initial state of charge (in kWh)
SoC_min = 0.0   # Minimum state of charge (in kWh)
SoC_max = 100.0 # Maximum state of charge (in kWh)
Pd_max = 50.0   # Maximum discharge power (kW)
Pc_max = 50.0   # Maximum charge power (kW)

# Sets
T = 1:96  # Time steps (15-min intervals for a day)
Ω = 1:10  # Scenarios

# Model
model = Model(Gurobi.Optimizer)

# Decision variables
@variable(model, e_DA_t_plus[t in T] >= 0)  # Day-ahead energy bought
@variable(model, e_DA_t_minus[t in T] >= 0) # Day-ahead energy sold
@variable(model, e_imb_plus[t in T, ω in Ω] >= 0) # Imbalance energy bought
@variable(model, e_imb_minus[t in T, ω in Ω] >= 0) # Imbalance energy sold
@variable(model, z_DA_t[t in T], Bin)  # Binary for charging/discharging in DA
@variable(model, z_t[t in T], Bin)     # Binary for charging/discharging in imbalance
@variable(model, SoC[t in T] >= SoC_min, SoC <= SoC_max)  # State of charge (kWh)

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
println("Objective value: ", objective_value(model))
println("Day-ahead energy bought (e_DA_t_plus): ", value.(e_DA_t_plus))
println("Day-ahead energy sold (e_DA_t_minus): ", value.(e_DA_t_minus))
println("State of charge (SoC): ", value.(SoC))
