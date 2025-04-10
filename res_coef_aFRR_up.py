import pandas as pd
import statsmodels.api as sm

def res_coefficients_aFRR_up(file_path):
    df = pd.read_excel(file_path, sheet_name="aFRR_up_monthly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['BESS_Capacity (MWh)', 'Renewable_energy (MWh)', 'Renewable_Share (%)', 'Demand (MWh)', 'Gas_Prices (€/MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_aFRR_up_contracted (€/MWh)"]

    model = sm.OLS(y, X).fit()

    return model.params.get("Renewable_Share (%)", None)

coeff_aFRR_up = res_coefficients_aFRR_up("bess_price_data.xlsx")
print(f"α_aFRR_up (per % RES): {coeff_aFRR_up:.4f} €/MWh")