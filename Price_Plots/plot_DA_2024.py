import pandas as pd
import matplotlib.pyplot as plt

# Load the Excel file
file_path = 'py_2024_DAM_prices_hourly.xlsx'  # Replace with the correct path if needed
df = pd.read_excel(file_path, sheet_name="Sheet1")

# Convert 'Date' column to datetime format
df['Date'] = pd.to_datetime(df['Date'])

# Plot
plt.figure(figsize=(14, 6))
plt.plot(df['Date'], df['Price'], linewidth=1)
plt.xlabel('Hourly timestep - 2024', fontsize=16)
plt.ylabel('DA Price (€/MWh)', fontsize=16)
plt.grid(True)

# Set x-axis ticks to be the first day of each month
months = pd.date_range(start='2024-01-01', end='2024-12-31', freq='MS')
plt.xticks(months, months.strftime('%b'), rotation=45, fontsize=14)
plt.yticks(fontsize=14)

plt.tight_layout()
plt.show()
