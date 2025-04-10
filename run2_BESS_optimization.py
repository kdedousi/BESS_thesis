from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np
from math import sqrt

def bess_optimization(P_DA_t, P_imb_t_sur, P_imb_t_short,
                      P_aFRR_up_reserve, P_aFRR_down_reserve, 
                      aFRR_volume_up_reserve, aFRR_volume_down_reserve, 
                      imb_volume_surplus, imb_volume_shortage,
                      capacity, annualized_cost_value, BESS_duration, first_run, 
                      SoC_previous, imbalance_used_surplus, imbalance_used_shortage, aFRR_used_down, aFRR_used_up, H_block):

    model = ConcreteModel()

    T = range(len(P_DA_t))
    n = 0.85  # Charging efficiency
    SoC_min = 0.1 * capacity * BESS_duration  # Minimum SoC
    SoC_max = 0.9 * capacity * BESS_duration # Max SoC (4-hour battery)
    Pd_max = capacity
    Pc_max = capacity
    M = capacity  # Big-M parameter for exclusivity constraints

    if first_run:
        SoC_init = SoC_max / 2  # Start at 50% capacity for first iteration
    else:
        SoC_init = SoC_previous  # Carry over from previous iteration
    
    # Decision variables
    model.e_DA_t_plus = Var(T, domain=NonNegativeReals)  # DA Discharging
    model.e_DA_t_minus = Var(T, domain=NonNegativeReals)  # DA Charging
    model.e_imb_plus = Var(T, domain=NonNegativeReals)  # Imbalance Discharging
    model.e_imb_minus = Var(T, domain=NonNegativeReals)  # Imbalance Charging
    model.e_aFRR_up = Var(T, domain=NonNegativeReals)  # aFRR Up Reserve
    model.e_aFRR_down = Var(T, domain=NonNegativeReals)  # aFRR Down Reserve
    model.SoC = Var(T, bounds=(SoC_min, SoC_max))

    # Binary variables to enforce mutual exclusivity of charging/discharging
    model.z_DA = Var(T, domain=Binary)
    model.z_imb = Var(T, domain=Binary)
    model.z_aFRR = Var(T, domain=Binary)

    # Revenue contributions
    revenue_DA = sum(P_DA_t[t] * (model.e_DA_t_plus[t] - model.e_DA_t_minus[t]) for t in T)
    revenue_Imbalance = sum((P_imb_t_short[t] * model.e_imb_plus[t] - P_imb_t_sur[t] * model.e_imb_minus[t]) for t in T)
    revenue_aFRR_reserve = sum((P_aFRR_up_reserve[t] * model.e_aFRR_up[t] + P_aFRR_down_reserve[t] * model.e_aFRR_down[t]) for t in T)
    
    # Objective function: maximize total revenue
    model.objective = Objective(
        expr=revenue_DA + revenue_Imbalance + revenue_aFRR_reserve,
        sense=maximize
    )
    
    # SoC Constraints
    model.soc_init = Constraint(expr=model.SoC[0] == SoC_init)

    def soc_rule(model, t):
        if t < len(T) - 1:
            return model.SoC[t+1] == (
                model.SoC[t] 
                + (model.e_DA_t_minus[t] + model.e_imb_minus[t]) * sqrt(n) 
                - (model.e_DA_t_plus[t] + model.e_imb_plus[t]) / sqrt(n)
            )
        return Constraint.Skip
    
    model.soc_constraints = Constraint(T, rule=soc_rule)

    # Adjusted SoC constraints for every 4-hour interval - limit the SoC variation over rolling 4-hour periods when the battery participates in aFRR services
    def soc_max_rule(model, t):
        if t < len(T) - H_block:
            return model.SoC[t] + sqrt(n) * sum(model.e_aFRR_down[tau] for tau in range(t, min(t+H_block, len(T)))) <= SoC_max
        return Constraint.Skip

    def soc_min_rule(model, t):
        if t < len(T) - H_block:
            return model.SoC[t] - sqrt(n) * sum(model.e_aFRR_up[tau] for tau in range(t, min(t+H_block, len(T)))) >= SoC_min
        return Constraint.Skip

    model.SoC_max = Constraint(T, rule=soc_max_rule)
    model.SoC_min = Constraint(T, rule=soc_min_rule)

    # Charging/discharging mutual exclusivity (per market)
    #model.DA_exclusivity = Constraint(T, rule=lambda model, t: model.e_DA_t_plus[t] <= model.z_DA[t] * M)
    #model.DA_exclusivity2 = Constraint(T, rule=lambda model, t: model.e_DA_t_minus[t] <= (1 - model.z_DA[t]) * M)

    #model.imb_exclusivity = Constraint(T, rule=lambda model, t: model.e_imb_plus[t] <= model.z_imb[t] * M)
    #model.imb_exclusivity2 = Constraint(T, rule=lambda model, t: model.e_imb_minus[t] <= (1 - model.z_imb[t]) * M)

    #model.aFRR_exclusivity = Constraint(T, rule=lambda model, t: model.e_aFRR_up[t] <= model.z_aFRR[t] * M)
    #model.aFRR_exclusivity2 = Constraint(T, rule=lambda model, t: model.e_aFRR_down[t] <= (1 - model.z_aFRR[t]) * M)

    # Ensuring DA, Imbalance, and aFRR activations sum to max capacity
    model.sum_to_max_capacity_plus = Constraint(T, rule=lambda model, t: model.e_DA_t_plus[t] + model.e_imb_plus[t] + model.e_aFRR_up[t] <= Pd_max)
    model.sum_to_max_capacity_minus = Constraint(T, rule=lambda model, t: model.e_DA_t_minus[t] + model.e_imb_minus[t] + model.e_aFRR_down[t] <= Pc_max)

    # aFRR capacity (explicit balance) constraints
    model.aFRR_capacity_up = Constraint(T, rule=lambda model, t: model.e_aFRR_up[t] <= max(aFRR_volume_up_reserve[t] - aFRR_used_up[t], 0))  # Volume in MW, no need for BESS duration multiplication
    model.aFRR_capacity_down = Constraint(T, rule=lambda model, t: model.e_aFRR_down[t] <= max(aFRR_volume_down_reserve[t] - aFRR_used_down[t], 0)) # Volume in MW, no need for BESS duration multiplication

    # settled imbalance volumes (implicit balance) constraints
    model.settled_imb_short = Constraint(T, rule=lambda model, t: model.e_imb_plus[t] <= max(imb_volume_shortage[t] - imbalance_used_shortage[t], 0)) # Volume in MWh
    model.settled_imb_sur = Constraint(T, rule=lambda model, t: model.e_imb_minus[t] <= max(imb_volume_surplus[t] - imbalance_used_surplus[t], 0)) # Volume in MWh

    # Solve model
    opt = SolverFactory('gurobi')
    opt.solve(model, tee=False)

    # Extract SoC values
    SoC_values = [model.SoC[t].value for t in T]

    # Extract results
    charging_DA = {capacity: [model.e_DA_t_minus[t].value for t in T]}
    discharging_DA = {capacity: [model.e_DA_t_plus[t].value for t in T]}
    charging_imb = {capacity: [model.e_imb_minus[t].value for t in T]}
    discharging_imb = {capacity: [model.e_imb_plus[t].value for t in T]}
    charging_aFRR = {capacity: [model.e_aFRR_down[t].value for t in T]}
    discharging_aFRR = {capacity: [model.e_aFRR_up[t].value for t in T]}

    SoC_final = SoC_values[-1]
    
    objective_value = model.objective()
    marginal_DA_revenue = revenue_DA()
    marginal_Imbalance_revenue = revenue_Imbalance()
    marginal_aFRR_reserve_revenue = revenue_aFRR_reserve()
    total_revenue = objective_value
    net_revenue = total_revenue - (capacity * annualized_cost_value)

    print(f"Total Objective Revenue: {objective_value}")
    print(f"Revenue from DA: {value(revenue_DA)}")
    print(f"Revenue from Imbalance: {value(revenue_Imbalance)}")
    print(f"Revenue from aFRR reserve: {value(revenue_aFRR_reserve)}")


    return (charging_DA, discharging_DA, charging_imb, discharging_imb, charging_aFRR, discharging_aFRR, 
        marginal_DA_revenue, marginal_Imbalance_revenue, marginal_aFRR_reserve_revenue, 
        total_revenue, net_revenue, SoC_final)
