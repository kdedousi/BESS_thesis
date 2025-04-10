import pandas as pd
import statsmodels.api as sm

def bess_coefficients_aFRR_down(file_path):
    df = pd.read_excel(file_path, sheet_name="aFRR_down_monthly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['BESS_Capacity (MWh)', 'Renewable_Share (%)', 'Renewable_energy (MWh)', 'Demand (MWh)', 'Gas_Prices (€/MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_aFRR_down_contracted (€/MWh)"]

    model = sm.OLS(y, X).fit()

    return model.params.get("BESS_Capacity (MWh)", None)

coeff_aFRR_down = bess_coefficients_aFRR_down("bess_price_data.xlsx")
print(f"aFRR Down Coefficient: {coeff_aFRR_down:.4f}")
