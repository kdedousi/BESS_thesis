import pandas as pd
import statsmodels.api as sm

def res_coefficients_aFRR_down(file_path):
    df = pd.read_excel(file_path, sheet_name="aFRR_down_monthly").apply(pd.to_numeric, errors='coerce').dropna()

    X = sm.add_constant(df[['BESS_Capacity (MWh)', 'Renewable_energy (MWh)', 'Renewable_Share (%)', 'Demand (MWh)', 'Gas_Prices (€/MWh)', 'Coal_Prices (€/MWh)']])
    y = df["Electricity_Price_aFRR_down_contracted (€/MWh)"]

    model = sm.OLS(y, X).fit()

    return model.params.get("Renewable_Share (%)", None)

coeff_aFRR_down = res_coefficients_aFRR_down("bess_price_data.xlsx")
print(f"α_aFRR_down (per % RES): {coeff_aFRR_down:.4f} €/MWh")
