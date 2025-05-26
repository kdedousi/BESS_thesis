import pandas as pd
import matplotlib.pyplot as plt

# Load the Excel file and the DA_hourly sheet
file_path = "bess_price_data.xlsx"
df = pd.read_excel(file_path, sheet_name="DA_hourly")

# Convert the time column to datetime
df['Time step'] = pd.to_datetime(df['Time step'])

# Plot gas and coal prices
plt.figure(figsize=(12, 6))
plt.plot(df['Time step'], df['Gas_Prices (€/MWh)'], label='Gas Price (€/MWh)', color='teal', linewidth=2)
plt.plot(df['Time step'], df['Coal_Prices (€/MWh)'], label='Coal Price (€/MWh)', color='brown', linewidth=2)

# Add labels, title, larger legend
plt.xlabel("Time", fontsize=14)
plt.ylabel("Price [€/MWh]", fontsize=14)
plt.legend(fontsize=16)
plt.grid(True)
plt.tight_layout()

# Show the plot
plt.show()

import pandas as pd
import matplotlib.pyplot as plt

# Load the Excel file and the DA_hourly sheet
file_path = "bess_price_data.xlsx"
df = pd.read_excel(file_path, sheet_name="DA_hourly")

# Convert the time column to datetime
df['Time step'] = pd.to_datetime(df['Time step'])



# --- Plot 2: Demand vs Renewable Energy ---
plt.plot(df['Time step'], df['Demand (MWh)'], label='Demand (MWh)', color='gray' , linewidth=2)
plt.plot(df['Time step'], df['Renewable_energy (MWh)'], label='Renewable Energy (MWh)', color='green', linewidth=2)
plt.xlabel("Time", fontsize=14)
plt.ylabel("Energy [MWh]", fontsize=14)
plt.legend(fontsize=16)
plt.grid(True)

# Adjust layout
plt.tight_layout()
plt.show()

