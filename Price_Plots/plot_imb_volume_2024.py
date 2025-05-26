import pandas as pd
import matplotlib.pyplot as plt

# Load the Excel file
file_volumes = 'settled_imbalance_volumes.xlsx'
df_volumes = pd.read_excel(file_volumes, sheet_name="MWh")

# Extract and rename relevant columns
df_plot = pd.DataFrame({
    'Timestamp': pd.to_datetime(df_volumes['Time']),
    'Surplus': df_volumes['Surplus (MWh)'],
    'Shortage': df_volumes['Shortage (MWh)']
})

# Generate monthly ticks
months = pd.date_range(start='2024-01-01', end='2024-12-31', freq='MS')

# Plot
plt.figure(figsize=(14, 5))
plt.plot(df_plot['Timestamp'], df_plot['Shortage'], label='Shortage Volume', color='rebeccapurple', linewidth=1)
plt.plot(df_plot['Timestamp'], df_plot['Surplus'], label='Surplus Volume', color='mediumseagreen', linewidth=1)

plt.xlabel('Hourly timestep - 2024', fontsize=16)
plt.ylabel('Imbalance Volume (MWh)', fontsize=16)
plt.legend()
plt.grid(True)
plt.xticks(months, months.strftime('%b'), rotation=45, fontsize=14)
plt.yticks(fontsize=14)
plt.tight_layout()
plt.show()
