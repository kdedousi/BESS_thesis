using JuMP
using Gurobi

function bess_optimization(P_DA_t, P_imb_t_ω, P_anc_t, SoC_init, capacity, annualized_cost_value)
    # Define time periods
    T = 1:length(P_DA_t)
    @show size(T)

    # Define efficiency and timestep
    n_c = 0.95  # Charging efficiency
    n_d = 0.95  # Discharging efficiency
    Δt = 1.0  # One-hour timestep
    SoC_min = 0  # Minimum SoC

    # Define BESS parameters
    SoC_max = capacity * 4
    Pd_max = capacity   # Max power proportional to capacity (4-hour battery)
    Pc_max = capacity 

    # Initialize model
    model = Model(Gurobi.Optimizer)
    set_optimizer_attribute(model, "Threads", 8)  # Use multiple CPU cores
    set_optimizer_attribute(model, "MIPFocus", 1)  # Focus on feasibility

    # Decision variables
    @variable(model, e_DA_t_plus[t in T] >= 0)  
    @variable(model, e_DA_t_minus[t in T] >= 0)  
    @variable(model, e_imb_plus[t in T] >= 0)   
    @variable(model, e_imb_minus[t in T] >= 0)  
    @variable(model, e_anc_t[t in T] >= 0)      
    @variable(model, 0 <= z_DA_t[t in T] <= 1)
    @variable(model, 0 <= z_t[t in T] <= 1)
    @variable(model, 0 <= z_anc_t[t in T] <= 1)     
    @variable(model, SoC_min <= SoC[t in T] <= SoC_max)  

    # Objective: Maximize revenue
    @objective(model, Max,
        sum(P_DA_t[t] * (e_DA_t_plus[t] - e_DA_t_minus[t]) for t in T) +
        sum(P_imb_t_ω[t] * (e_imb_plus[t] - e_imb_minus[t]) for t in T) +
        sum(P_anc_t[t] * e_anc_t[t] for t in T)
    )

    # State of Charge Constraints
    @constraint(model, SoC[1] == SoC_init)
    @constraint(model, [t in T[1:end-1]], 
        SoC[t+1] == SoC[t] + (e_DA_t_plus[t] + e_imb_plus[t]) * n_c - (e_DA_t_minus[t] + e_imb_minus[t]) / n_d
    )

    # Charging and discharging limits
    @constraint(model, [t in T], e_DA_t_plus[t] <= Pd_max * z_DA_t[t] * Δt * n_d)  
    @constraint(model, [t in T], e_DA_t_minus[t] <= Pc_max * (1 - z_DA_t[t]) * Δt / n_c)  
    @constraint(model, [t in T], e_imb_plus[t] <= Pd_max * z_t[t] * Δt * n_d)  
    @constraint(model, [t in T], e_imb_minus[t] <= Pc_max * (1 - z_t[t]) * Δt / n_c)  
    @constraint(model, [t in T], e_anc_t[t] <= Pd_max * z_anc_t[t] * Δt)  

   # Solve optimization problem
    optimize!(model)

    # Extract results
    ancillary_revenue = sum(value.(e_anc_t) .* P_anc_t)  
    electricity_revenue = objective_value(model)  

    # Compute total and net revenue
    total_revenue = electricity_revenue + ancillary_revenue
    net_revenue = total_revenue - (capacity * annualized_cost_value)

    # Store results in dictionaries
    charging_DA = Dict(capacity => value.(e_DA_t_plus))
    discharging_DA = Dict(capacity => value.(e_DA_t_minus))
    charging_imb = Dict(capacity => value.(e_imb_plus))
    discharging_imb = Dict(capacity => value.(e_imb_minus))
    ancillary_output = Dict(capacity => value.(e_anc_t))

    return charging_DA, discharging_DA, charging_imb, discharging_imb, ancillary_output, electricity_revenue, total_revenue, net_revenue
end