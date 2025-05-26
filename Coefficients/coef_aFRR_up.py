import pandas as pd
import statsmodels.api as sm

def bess_coefficients_aFRR_up(file_path):
    df = pd.read_excel(file_path, sheet_name="aFRR_up_monthly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['BESS_Capacity (MWh)', 'Renewable_Share (%)', 'Renewable_energy (MWh)', 'Demand (MWh)', 'Gas_Prices (€/MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_aFRR_up_contracted (€/MWh)"]

    model = sm.OLS(y, X).fit()

    return model.params.get("BESS_Capacity (MWh)", None)

coeff_aFRR_up = bess_coefficients_aFRR_up("bess_price_data.xlsx")
print(f"aFRR Up Coefficient: {coeff_aFRR_up:.4f}")
