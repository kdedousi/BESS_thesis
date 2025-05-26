import pandas as pd
import matplotlib.pyplot as plt

# File paths
shortage_path = 'py_2024_imbalance_prices_hourly_shortage.xlsx'
surplus_path = 'py_2024_imbalance_prices_hourly_surplus.xlsx'

# Load Sheet 2 from shortage file
df_shortage = pd.read_excel(shortage_path, sheet_name='Sheet2')
df_shortage['Time'] = pd.to_datetime(df_shortage['Time'])

# Load surplus file (Sheet 1)
df_surplus = pd.read_excel(surplus_path, sheet_name='Sheet1')
df_surplus['Date'] = pd.to_datetime(df_surplus['Date'])

# Merge or align by date
df_plot = pd.DataFrame({
    'Date': df_shortage['Time'],
    'Shortage': df_shortage['Price'].values,
    'Surplus': df_surplus['Price'].values
})

# Plot
plt.figure(figsize=(14, 6))
plt.plot(df_plot['Date'], df_plot['Shortage'], label='Shortage Price', color='rebeccapurple', linewidth=1)
plt.plot(df_plot['Date'], df_plot['Surplus'], label='Surplus Price', color='mediumseagreen', linewidth=1)
plt.xlabel('Hourly timestep - 2024', fontsize=16)
plt.ylabel('Imbalance Price (€/MWh)', fontsize=16)
plt.grid(True)
plt.legend()

# Set x-axis ticks to months
months = pd.date_range(start='2024-01-01', end='2024-12-31', freq='MS')
plt.xticks(months, months.strftime('%b'), rotation=45, fontsize=14)
plt.yticks(fontsize=14)

plt.tight_layout()
plt.show()

