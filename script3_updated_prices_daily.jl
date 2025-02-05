using DataFrames
using XLSX

function update_prices!(df::DataFrame, charging_DA::Vector{Float64}, 
                        discharging_DA::Vector{Float64}, 
                        charging_imb::Vector{Float64}, 
                        discharging_imb::Vector{Float64})
    price_per_mwh_res = 0.02 

    df.Extrapolated_DAM_Price .+= +price_per_mwh_res .* discharging_DA .- price_per_mwh_res .* charging_DA
    df.Extrapolated_Imbalance_Price .+= +price_per_mwh_res .* discharging_imb .- price_per_mwh_res .* charging_imb

end