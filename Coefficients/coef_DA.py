import pandas as pd
import statsmodels.api as sm

def bess_coefficients_DA(file_path):
    df = pd.read_excel(file_path, sheet_name="DA_hourly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['Renewable_Share (%)', 'Renewable_energy (MWh)', 'Demand (MWh)', 'Gas_Prices (€/MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_DA (€/MWh)"]

    model = sm.OLS(y, X).fit()

    return model.params.get("Demand (MWh)", None)

coeff_DA = bess_coefficients_DA("bess_price_data.xlsx")
print(f"DA Coefficient: {coeff_DA:.4f}")
