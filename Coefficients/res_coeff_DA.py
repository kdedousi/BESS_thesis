import pandas as pd
import statsmodels.api as sm

def res_coefficients_DA(file_path):
    df = pd.read_excel(file_path, sheet_name="DA_hourly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['Renewable_energy (MWh)', 'Renewable_Share (%)', 'Demand (MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_DA (€/MWh)"]

    model = sm.OLS(y, X).fit()
    alpha_percent = model.params.get('Renewable_Share (%)')

    return alpha_percent

alpha_percent = res_coefficients_DA("bess_price_data.xlsx")
print(f"α_DA (per % RES): {alpha_percent:.4f} €/MWh")