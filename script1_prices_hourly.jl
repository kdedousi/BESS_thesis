using XLSX
using DataFrames

function load_initial_prices()

    # Load historical energy prices
    raw_data_dam = XLSX.readtable("2024_DAM_prices_hourly.xlsx", "Sheet1")
    raw_data_imbalance = XLSX.readtable("2024_imbalance_prices_hourly_surplus.xlsx", "Sheet1")

    data_dam = DataFrame(raw_data_dam[1], raw_data_dam[2])
    data_imbalance = DataFrame(raw_data_imbalance[1], raw_data_imbalance[2])
    
    data_dam = data_dam[1:100, :]
    data_imbalance = data_imbalance[1:100, :]
    
    # Define stable RES values
    RES_current = 50000000
    RES_future = 60000000
    price_per_mwh_res = -0.00075 / 1000

    delta_res = RES_future - RES_current
    data_dam.Price_future = data_dam.Price .+ price_per_mwh_res .* delta_res
    data_imbalance.Price_future = data_imbalance.Price .+ price_per_mwh_res .* delta_res

    # Combine results into one DataFrame
    data_combined = DataFrame(
        Date = data_dam.Date,
        Historical_DAM_Price = data_dam.Price,
        Extrapolated_DAM_Price = data_dam.Price_future,
        Historical_Imbalance_Price = data_imbalance.Price,
        Extrapolated_Imbalance_Price = data_imbalance.Price_future
    )

    return data_combined
end

df = load_initial_prices()
println(df)
