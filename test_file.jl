# Load necessary packages
using JuMP
using HiGHS

# Create the model with HiGHS solver
model = Model(HiGHS.Optimizer)

# Define variables
@variable(model, x >= 0)
@variable(model, 0 <= y <= 3)

# Define the objective function
@objective(model, Min, 12x + 20y)

# Add constraints
@constraint(model, c1, 6x + 8y >= 100)
@constraint(model, c2, 7x + 12y >= 120)

# Print the model to check
println("Model:")
print(model)

# Optimize the model
optimize!(model)

# Display results
println("\nResults:")
println("Termination status: ", termination_status(model))
println("Primal status: ", primal_status(model))
println("Dual status: ", dual_status(model))
println("Objective value: ", objective_value(model))
println("Value of x: ", value(x))
println("Value of y: ", value(y))
println("Shadow price of constraint c1: ", shadow_price(c1))
println("Shadow price of constraint c2: ", shadow_price(c2))
