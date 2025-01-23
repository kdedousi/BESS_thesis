using XLSX
using DataFrames
using Plots

# Load historical energy prices from Excel
# The Excel file should have a sheet with columns: `Date` and `Price`
raw_data = XLSX.readtable("2024_DAM_prices.xlsx", "Sheet1")
data = DataFrame(raw_data[1], raw_data[2])  # Construct DataFrame from raw data

# Define stable RES values
RES_current = 49156000  # Current RES generation (MWh)
RES_future = 66755062   # 2030 moderate RES generation (MWh)

# Define the slope (€/MWh per MWh of RES generation)
price_per_mwh_res = -0.00075 /1000 #convert slope to match GWh

# Perform extrapolation
delta_res = RES_future - RES_current  # Change in RES generation
data.Price_future = data.Price .+ delta_res .* price_per_mwh_res

# Save extrapolated prices to a new Excel file
XLSX.writetable("extrapolated_prices_stable_res.xlsx", Tables.columntable(data))

# Plot historical vs extrapolated prices
plot(data.Date, data.Price, label="Historical Prices", xlabel="Date", ylabel="Price (€/MWh)", color=:blue)
plot!(data.Date, data.Price_future, label="Extrapolated Prices (Stable RES)", color=:red)
