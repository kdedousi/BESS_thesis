using DataFrames
using XLSX
using Tables

# Function to run multiple capacity iterations
function run_iterations(df::DataFrame, max_capacity::Float64, step::Float64, SoC_init::Float64, annualized_cost_value)
    global results  # Ensure results is accessible across iterations

    results = DataFrame()

    capacity = 50  # Start capacity (not using a global variable)
    
    # Put output excels in one file
    output_dir = joinpath(pwd(), "results")
    mkpath(output_dir)
    initial_prices_path = joinpath(output_dir, "initial_extrapolated_prices.xlsx")
    XLSX.writetable(initial_prices_path, Tables.columntable(df))

    while capacity <= max_capacity

        # Ensure bess_optimization uses updated prices
        P_DA_t = df.Extrapolated_DAM_Price  # Use the updated prices
        P_imb_t_ω = df.Extrapolated_Imbalance_Price

        # Run BESS optimization
        charging_DA, discharging_DA, charging_imb, discharging_imb, ancillary_output, electricity_revenue, total_revenue, net_revenue =
            bess_optimization(P_DA_t, P_imb_t_ω, fill(50, length(P_DA_t)), SoC_init, capacity, annualized_cost_value)

        # Extract JuMP variables from the dictionary using capacity as the key
        charging_DA_var = charging_DA[capacity]
        discharging_DA_var = discharging_DA[capacity]
        charging_imb_var = charging_imb[capacity]
        discharging_imb_var = discharging_imb[capacity]

        # Convert JuMP DenseAxisArray to Vector{Float64}
        charging_DA_vec = [value(charging_DA_var[t]) for t in eachindex(charging_DA_var)]
        discharging_DA_vec = [value(discharging_DA_var[t]) for t in eachindex(discharging_DA_var)]
        charging_imb_vec = [value(charging_imb_var[t]) for t in eachindex(charging_imb_var)]
        discharging_imb_vec = [value(discharging_imb_var[t]) for t in eachindex(discharging_imb_var)]

        # Update prices in DataFrame
        update_prices!(df, charging_DA_vec, discharging_DA_vec, charging_imb_vec, discharging_imb_vec)

        ## Generate a unique filename with the full path
        filename = joinpath(output_dir, "updated_prices_capacity_$(capacity).xlsx")
        XLSX.writetable(filename, Tables.columntable(df))

        # Append results to dataframe
        new_results = DataFrame(
            Capacity=fill(capacity, length(P_DA_t)), 
            Time=collect(1:length(P_DA_t)), 
            Charging_DA=charging_DA_vec, 
            Discharging_DA=discharging_DA_vec, 
            Charging_Imb=charging_imb_vec, 
            Discharging_Imb=discharging_imb_vec, 
            Electricity_Revenue=fill(electricity_revenue, length(P_DA_t)), 
            Total_Revenue=fill(total_revenue, length(P_DA_t)), 
            Net_Revenue=fill(net_revenue, length(P_DA_t)), 
            DAM_Price=P_DA_t, 
            Imbalance_Price=P_imb_t_ω
        )

        # Accumulate results correctly
        results = vcat(results, new_results)

        capacity += step

        SoC_init = charging_DA_vec[end] - discharging_DA_vec[end]  # Approximate SoC update
    end

    final_results_path = joinpath(output_dir, "final_results.xlsx")
    XLSX.writetable(final_results_path, Tables.columntable(results))
    println("Final results saved to '$final_results_path'")

end

redirect_stdout(devnull) do
    # Include external scripts
    include("script1_prices_hourly.jl")
    include("script2_BESS_optimization_daily.jl")
    include("script3_updated_prices_daily.jl")

    # Load initial prices
    df = load_initial_prices()

    # Compute annualized cost
    CAPEX = 200_000  # € per MWh
    OPEX = 1_000     # € per MWh/year
    lifetime = 30     # years
    discount_rate = 0.05  

    function annualized_cost(capex, opex, lifetime, discount_rate)
        annuity_factor = (discount_rate * (1 + discount_rate)^lifetime) / ((1 + discount_rate)^lifetime - 1)
        annualized_capex = capex * annuity_factor
        return annualized_capex + opex
    end

    annualized_cost_value = annualized_cost(CAPEX, OPEX, lifetime, discount_rate)

    # Run multiple capacity iterations
    run_iterations(df, 200.0, 50.0, 50.0, annualized_cost_value)
end

println("Results saved to final_results.xlsx'")