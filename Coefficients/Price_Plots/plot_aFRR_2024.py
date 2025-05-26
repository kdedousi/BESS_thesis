import pandas as pd
import matplotlib.pyplot as plt

# File paths
up_path = 'aFRR_hourly_prices_Up.xlsx'
down_path = 'aFRR_hourly_prices_Down.xlsx'

# Load data
df_up = pd.read_excel(up_path)
df_down = pd.read_excel(down_path)

# Convert to datetime
df_up['Timestamp'] = pd.to_datetime(df_up['Timestamp'])
df_down['Timestamp'] = pd.to_datetime(df_down['Timestamp'])

# --- Plot 1: Hourly Reserve Prices ---
plt.figure(figsize=(14, 5))
plt.plot(df_up['Timestamp'], df_up['Hourly price Reserve (€/MW)'], label='aFRR Up Price', color='mediumorchid', linewidth=1.5)
plt.plot(df_down['Timestamp'], df_down['Hourly price Reserve (€/MW)'], label='aFRR Down Price', color='steelblue', linewidth=1.5)
plt.xlabel('Hourly timestep - 2024', fontsize=16)
plt.ylabel('aFRR Reserve Price (€/MW)', fontsize=16)
plt.legend()
plt.grid(True)

# Set x-axis to months
months = pd.date_range(start='2024-01-01', end='2024-12-31', freq='MS')
plt.xticks(months, months.strftime('%b'), rotation=45, fontsize=14)
plt.yticks(fontsize=14)
plt.tight_layout()
plt.show()

# --- Plot 2: Reserve Volume ---
plt.figure(figsize=(14, 5))
plt.plot(df_up['Timestamp'], df_up['Volume Reserve (MW)'], label='aFRR Up Volume', color='mediumorchid', linewidth=1)
plt.plot(df_down['Timestamp'], df_down['Volume Reserve (MW)'], label='aFRR Down Volume', color='steelblue', linewidth=1)
plt.xlabel('Hourly timestep - 2024', fontsize=16)
plt.ylabel('Reserve Volume (MW)', fontsize=16)
plt.legend()
plt.grid(True)

plt.xticks(months, months.strftime('%b'), rotation=45, fontsize=14)
plt.yticks(fontsize=14)
plt.tight_layout()
plt.show()
