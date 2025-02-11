from pyomo.environ import *
from pyomo.opt import SolverFactory
import numpy as np

def bess_optimization(P_DA_t, P_imb_t_omega, P_anc_t, SoC_init, capacity, annualized_cost_value):
    # Define model
    model = ConcreteModel()
    
    # Define time periods
    T = range(len(P_DA_t))
    
    # Define efficiency and timestep
    n_c = 0.95  # Charging efficiency
    n_d = 0.95  # Discharging efficiency
    delta_t = 1.0  # One-hour timestep
    SoC_min = 0  # Minimum SoC
    
    # Define BESS parameters
    SoC_max = capacity * 4  # Max power proportional to capacity (4-hour battery)
    Pd_max = capacity  
    Pc_max = capacity
    
    # Decision variables
    model.e_DA_t_plus = Var(T, domain=NonNegativeReals)
    model.e_DA_t_minus = Var(T, domain=NonNegativeReals)
    model.e_imb_plus = Var(T, domain=NonNegativeReals)
    model.e_imb_minus = Var(T, domain=NonNegativeReals)
    model.e_anc_t = Var(T, domain=NonNegativeReals)
    model.z_DA_t = Var(T, domain=Binary)
    model.z_t = Var(T, domain=Binary)
    model.z_anc_t = Var(T, domain=Binary)
    model.SoC = Var(T, bounds=(SoC_min, SoC_max))
    
    # Objective function: Maximize revenue
    model.objective = Objective(
        expr=sum(P_DA_t[t] * (model.e_DA_t_plus[t] - model.e_DA_t_minus[t]) for t in T) +
             sum(P_imb_t_omega[t] * (model.e_imb_plus[t] - model.e_imb_minus[t]) for t in T) +
             sum(P_anc_t[t] * model.e_anc_t[t] for t in T),
        sense=maximize
    )
    
    # Constraints
    model.soc_init = Constraint(expr=model.SoC[0] == SoC_init)
    
    def soc_rule(model, t):
        if t < len(T) - 1:
            return model.SoC[t+1] == model.SoC[t] + (model.e_DA_t_plus[t] + model.e_imb_plus[t]) * n_c - (model.e_DA_t_minus[t] + model.e_imb_minus[t]) / n_d
        return Constraint.Skip
    
    model.soc_constraints = Constraint(T, rule=soc_rule)
    
    model.charge_DA = Constraint(T, rule=lambda model, t: model.e_DA_t_plus[t] <= Pd_max * model.z_DA_t[t] * delta_t * n_d)
    model.discharge_DA = Constraint(T, rule=lambda model, t: model.e_DA_t_minus[t] <= Pc_max * (1 - model.z_DA_t[t]) * delta_t / n_c)
    model.charge_imb = Constraint(T, rule=lambda model, t: model.e_imb_plus[t] <= Pd_max * model.z_t[t] * delta_t * n_d)
    model.discharge_imb = Constraint(T, rule=lambda model, t: model.e_imb_minus[t] <= Pc_max * (1 - model.z_t[t]) * delta_t / n_c)
    model.ancillary = Constraint(T, rule=lambda model, t: model.e_anc_t[t] <= Pd_max * model.z_anc_t[t] * delta_t)
    
    # Solve model
    opt = SolverFactory('gurobi')
    opt.solve(model, tee=True)
    
    # Extract results
    charging_DA = {capacity: [model.e_DA_t_plus[t].value for t in T]}
    discharging_DA = {capacity: [model.e_DA_t_minus[t].value for t in T]}
    charging_imb = {capacity: [model.e_imb_plus[t].value for t in T]}
    discharging_imb = {capacity: [model.e_imb_minus[t].value for t in T]}
    ancillary_output = {capacity: [model.e_anc_t[t].value for t in T]}
    
    ancillary_revenue = sum(model.e_anc_t[t].value * P_anc_t[t] for t in T)
    electricity_revenue = model.objective()
    total_revenue = electricity_revenue + ancillary_revenue
    net_revenue = total_revenue - (capacity * annualized_cost_value)
    
    return charging_DA, discharging_DA, charging_imb, discharging_imb, ancillary_output, electricity_revenue, total_revenue, net_revenue
